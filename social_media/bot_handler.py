"""
Social Media Bot Handler — processes incoming messages, runs AI analysis,
auto-replies based on rules, and logs all bot activity.

This is the core engine that handles:
- Incoming webhook messages from all platforms (WhatsApp, LinkedIn, etc.)
- AI classification and analysis
- Auto-reply generation and sending
- Message read tracking
- Escalation to human agents
"""
import logging
from datetime import datetime, timezone

from django.utils import timezone as dj_timezone

from .models import (
    AutoReplyRule,
    BotConversationLog,
    SocialMediaAccount,
    SocialMediaMessage,
)
from .ai_service import classify_message, generate_reply, analyze_conversation
from .platform_apis import send_message_to_platform, mark_as_read_on_platform

logger = logging.getLogger(__name__)


class SocialMediaBotHandler:
    """
    Central bot handler that processes all incoming social media messages.
    Usage:
        handler = SocialMediaBotHandler(company)
        handler.process_incoming_message(account, message_data)
    """

    def __init__(self, company):
        self.company = company

    def process_incoming_message(self, account: SocialMediaAccount, message_data: dict) -> dict:
        """
        Process an incoming message through the AI bot pipeline.

        message_data keys:
            - sender_id: str
            - sender_name: str (optional)
            - content: str
            - message_type: str (text, image, etc.)
            - platform_message_id: str
            - timestamp: datetime or str
            - is_group: bool (optional)
            - contact_id: str (same as sender_id for DMs)

        Returns: {"action": str, "reply": str, "classification": dict}
        """
        sender_id = message_data.get("sender_id", "")
        sender_name = message_data.get("sender_name", "")
        content = message_data.get("content", "").strip()
        msg_type = message_data.get("message_type", "text")
        platform_msg_id = message_data.get("platform_message_id", "")
        timestamp = message_data.get("timestamp", dj_timezone.now())
        is_group = message_data.get("is_group", False)
        # For Telegram, use chat_id as reply destination (handles groups correctly)
        reply_to_id = message_data.get("chat_id") or sender_id

        if not content:
            return {"action": "ignored", "reply": "", "classification": {}}

        logger.info(
            f"[{account.get_platform_display()}] Incoming from {sender_name or sender_id}: {content[:60]}"
        )

        # ── Save incoming message to DB ─────────────────────────────────────
        message, _ = SocialMediaMessage.objects.get_or_create(
            account=account,
            platform_message_id=platform_msg_id or f"{sender_id}_{timestamp}",
            defaults={
                "direction": "inbound",
                "sender_name": sender_name,
                "sender_id": sender_id,
                "recipient_id": account.account_id,
                "content": content,
                "message_type": msg_type,
                "timestamp": timestamp if isinstance(timestamp, datetime) else dj_timezone.now(),
            },
        )

        # ── Mark as read on platform ────────────────────────────────────────
        try:
            mark_as_read_on_platform(account, platform_msg_id)
            message.is_read = True
            message.save(update_fields=["is_read"])
        except Exception as e:
            logger.warning(f"Failed to mark as read: {e}")

        # ── Find applicable auto-reply rule ─────────────────────────────────
        rule = self._find_matching_rule(account, is_group=is_group)

        # ── AI Classification (always) ──────────────────────────────────────
        classification = {}
        try:
            classification = classify_message(content, platform=account.get_platform_display())
            logger.info(
                f"[AI] {classification['classification']} / {classification['sentiment']} — "
                f"{classification['summary']}"
            )
        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            classification = {
                "classification": "general",
                "sentiment": "neutral",
                "summary": content[:100],
                "confidence": 0.0,
            }

        # ── Decide whether to reply ─────────────────────────────────────────
        should_reply = False
        if rule and rule.is_enabled:
            # Check keyword filter
            if rule.keywords:
                kws = [k.strip().lower() for k in rule.keywords.split(",") if k.strip()]
                should_reply = any(kw in content.lower() for kw in kws)
            else:
                should_reply = True

            # Skip spam
            if classification.get("classification") == "spam":
                should_reply = False

        # ── Generate AI Reply ───────────────────────────────────────────────
        reply_text = ""
        action = "classified"

        if should_reply:
            try:
                # Get conversation context (last 5 messages)
                recent_msgs = SocialMediaMessage.objects.filter(
                    account=account,
                ).filter(
                    models.Q(sender_id=sender_id) | models.Q(recipient_id=sender_id)
                ).order_by("-timestamp")[:5]

                context_str = "\n".join(
                    f"{'Customer' if m.direction == 'inbound' else 'Business'}: {m.content[:100]}"
                    for m in reversed(recent_msgs)
                )

                # Get company-level bot profile info
                company_info = ""

                reply_text = generate_reply(
                    message_text=content,
                    platform=account.get_platform_display(),
                    custom_instructions=rule.custom_instructions if rule else "",
                    persona_name=rule.persona_name if rule else "",
                    conversation_context=context_str,
                    company_info=company_info,
                )
                action = "auto_replied"
                logger.info(f"[AI] Reply: {reply_text[:80]}...")
            except Exception as e:
                logger.error(f"AI reply generation failed: {e}")
                reply_text = ""
                action = "classified"

        # ── Send reply if auto_send is enabled ──────────────────────────────
        was_sent = False
        if reply_text and rule and rule.auto_send:
            try:
                send_message_to_platform(account, reply_to_id, reply_text)
                was_sent = True

                # Save outbound message
                SocialMediaMessage.objects.create(
                    account=account,
                    direction="outbound",
                    sender_id=account.account_id,
                    recipient_id=reply_to_id,
                    content=reply_text,
                    message_type="text",
                    timestamp=dj_timezone.now(),
                )
                logger.info(f"[BOT] Reply sent to {sender_id}")
            except Exception as e:
                logger.error(f"Failed to send reply: {e}")
                was_sent = False

        # ── Log bot activity ────────────────────────────────────────────────
        BotConversationLog.objects.create(
            account=account,
            message=message,
            action=action,
            ai_classification=classification.get("classification", ""),
            ai_summary=classification.get("summary", ""),
            ai_reply_text=reply_text,
            ai_confidence=classification.get("confidence"),
            was_sent=was_sent,
        )

        return {
            "action": action,
            "reply": reply_text,
            "was_sent": was_sent,
            "classification": classification,
        }

    def _find_matching_rule(self, account: SocialMediaAccount, is_group: bool = False) -> AutoReplyRule | None:
        """Find the best matching auto-reply rule for this account."""
        # Try account-specific rule first
        rule = AutoReplyRule.objects.filter(
            company=self.company,
            account=account,
            platform=account.platform,
            is_enabled=True,
        ).first()

        # Fallback: platform-wide rule (account=None)
        if not rule:
            rule = AutoReplyRule.objects.filter(
                company=self.company,
                account__isnull=True,
                platform=account.platform,
                is_enabled=True,
            ).first()

        if not rule:
            return None

        # Check message type filters
        if is_group and not rule.reply_to_groups:
            return None
        if not is_group and not rule.reply_to_dms:
            return None

        return rule

    def get_analytics(self, account: SocialMediaAccount = None, days: int = 7) -> dict:
        """Get bot analytics for the company."""
        from django.db.models import Count, Q
        from django.utils.timezone import now
        from datetime import timedelta

        since = now() - timedelta(days=days)

        logs_qs = BotConversationLog.objects.filter(
            account__company=self.company,
            created_at__gte=since,
        )
        if account:
            logs_qs = logs_qs.filter(account=account)

        total = logs_qs.count()
        replied = logs_qs.filter(action="auto_replied").count()
        sent = logs_qs.filter(was_sent=True).count()

        classification_breakdown = (
            logs_qs.values("ai_classification")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return {
            "total_processed": total,
            "auto_replied": replied,
            "actually_sent": sent,
            "reply_rate": (replied / total * 100) if total else 0,
            "classification_breakdown": list(classification_breakdown),
        }


# ── Import fix for models.Q in process_incoming_message ──
from django.db import models
