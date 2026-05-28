"""
Discord Gateway Bot — listens to all messages and auto-replies using AI.
Method: Discord Gateway (WebSocket) — no ngrok, no public URL needed.
Run with: python manage.py run_discord_bot

Architecture mirrors slack_hub/bot_service.py:
  Discord message → AI classify → AI reply → save to DB → send if rule allows
"""
import asyncio
import logging
from datetime import datetime, timezone

import discord
from asgiref.sync import sync_to_async
from django.conf import settings

logger = logging.getLogger(__name__)


# ── Sync-to-async DB helpers ──────────────────────────────────────────────────

@sync_to_async
def _get_integration():
    from integrations.models import CompanyIntegration
    return CompanyIntegration.objects.filter(service="discord", status="active").first()


@sync_to_async
def _get_rule(company, channel_id):
    from .models import DiscordAutoReplyRule
    # Exact channel rule first, then wildcard
    rule = DiscordAutoReplyRule.objects.filter(
        company=company, channel_id=channel_id, is_enabled=True
    ).first()
    if not rule:
        rule = DiscordAutoReplyRule.objects.filter(
            company=company, channel_id="*", is_enabled=True
        ).first()
    return rule


@sync_to_async
def _save_message(company, message_id, guild_id, guild_name, channel_id,
                  channel_name, sender_id, sender_name, text, is_dm,
                  classification, reply_text):
    from .models import DiscordMessage
    msg, created = DiscordMessage.objects.get_or_create(
        company=company,
        message_id=message_id,
        defaults={
            "guild_id": guild_id,
            "guild_name": guild_name,
            "channel_id": channel_id,
            "channel_name": channel_name,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "text": text,
            "is_dm": is_dm,
            "ai_classification": classification["classification"],
            "ai_summary": classification["summary"],
            "ai_reply": reply_text,
        },
    )
    return msg, created


@sync_to_async
def _mark_replied(msg):
    msg.is_auto_replied = True
    msg.reply_sent_at = datetime.now(timezone.utc)
    msg.save()


# ── Discord Bot Client ────────────────────────────────────────────────────────

class WorkHubDiscordBot(discord.Client):
    """Discord Gateway bot — receives messages and auto-replies with AI."""

    async def on_ready(self):
        logger.info(f"✅ Discord bot online: {self.user} (ID: {self.user.id})")
        logger.info(f"   Watching {len(self.guilds)} server(s)")

    async def on_message(self, message: discord.Message):
        # Skip our own messages and other bots
        if message.author.bot:
            return

        text = message.content.strip()
        if not text:
            return  # ignore empty / embed-only messages

        is_dm = isinstance(message.channel, discord.DMChannel)
        channel_id = str(message.channel.id)
        channel_name = getattr(message.channel, "name", "DM")
        sender_id = str(message.author.id)
        sender_name = message.author.display_name
        message_id = str(message.id)
        guild_id = str(message.guild.id) if message.guild else ""
        guild_name = message.guild.name if message.guild else ""

        logger.info(
            f"📨 [{'DM' if is_dm else '#' + channel_name}] "
            f"{sender_name}: {text[:70]}"
        )

        # ── Find connected integration ────────────────────────────────────
        integration = await _get_integration()
        if not integration:
            return

        company = integration.company

        # ── Check auto-reply rule ─────────────────────────────────────────
        rule = await _get_rule(company, channel_id)
        should_reply = is_dm or (rule is not None)
        should_auto_send = is_dm or (rule is not None and rule.auto_send)

        # Keyword filter (channels only, not DMs)
        if rule and rule.keywords and not is_dm:
            kws = [k.strip().lower() for k in rule.keywords.split(",") if k.strip()]
            if kws and not any(kw in text.lower() for kw in kws):
                should_reply = False
                should_auto_send = False

        # ── AI: classify (always, even if no reply) ───────────────────────
        try:
            from slack_hub.ai_service import classify_message
            classification = await asyncio.to_thread(classify_message, text)
            logger.info(
                f"🧠 {classification['classification'].upper()} — {classification['summary']}"
            )
        except Exception as e:
            logger.error(f"AI classify error: {e}")
            classification = {"classification": "general", "summary": text[:100]}

        # ── AI: generate reply ────────────────────────────────────────────
        reply_text = ""
        if should_reply:
            custom_instructions = rule.custom_instructions if rule else ""
            try:
                from slack_hub.ai_service import generate_reply
                reply_text = await asyncio.to_thread(
                    generate_reply, text, "", custom_instructions
                )
                logger.info(f"💬 Reply: {reply_text[:80]}...")
            except Exception as e:
                logger.error(f"AI reply error: {e}")

        # ── Save to DB ────────────────────────────────────────────────────
        msg, _ = await _save_message(
            company, message_id, guild_id, guild_name, channel_id,
            channel_name, sender_id, sender_name, text, is_dm,
            classification, reply_text,
        )

        # ── Send reply ────────────────────────────────────────────────────
        if should_auto_send and reply_text:
            try:
                await message.channel.send(reply_text)
                await _mark_replied(msg)
                logger.info(
                    f"✅ Replied in {'DM' if is_dm else '#' + channel_name}"
                )
            except discord.Forbidden:
                logger.error(
                    f"Bot lacks Send Messages permission in #{channel_name}"
                )
            except discord.HTTPException as e:
                logger.error(f"Discord send failed: {e}")
        elif reply_text:
            logger.info(f"📝 Draft saved for {'DM' if is_dm else '#' + channel_name}")
        else:
            logger.info(
                f"📊 Tracked (no reply) in {'DM' if is_dm else '#' + channel_name}"
            )


# ── Entry point ───────────────────────────────────────────────────────────────

def run_discord_bot():
    """
    Load the bot token from the active Discord CompanyIntegration
    and start the Gateway connection. Blocks until stopped (Ctrl+C).
    """
    from integrations.models import CompanyIntegration
    from integrations.utils import decrypt_token

    integration = CompanyIntegration.objects.filter(
        service="discord", status="active"
    ).first()
    if not integration:
        raise RuntimeError(
            "No active Discord integration found.\n"
            "Connect Discord at http://127.0.0.1:8000/integrations/ first."
        )

    bot_token = decrypt_token(integration.discord_bot_token_enc)
    if not bot_token:
        raise RuntimeError("Discord bot token is missing or corrupted.")

    # Intents: message_content is a Privileged Intent — must be enabled in
    # Discord Developer Portal → Bot → Privileged Gateway Intents
    intents = discord.Intents.default()
    intents.message_content = True   # read message text (Privileged)
    intents.messages = True          # MESSAGE_CREATE events
    intents.dm_messages = True       # DM messages
    intents.guild_messages = True    # server channel messages

    bot = WorkHubDiscordBot(intents=intents)
    logger.info("Connecting to Discord Gateway...")
    # log_handler=None → use our own logging config (no duplicate output)
    bot.run(bot_token, log_handler=None)
