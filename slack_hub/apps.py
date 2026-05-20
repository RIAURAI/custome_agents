import threading
import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class SlackHubConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "slack_hub"

    def ready(self):
        """Auto-start Slack bot in background thread when Django starts."""
        import os
        from django.conf import settings as django_settings

        # Avoid double-start during Django's autoreload (skip parent process)
        if os.environ.get("RUN_MAIN") == "false":
            return

        autostart = str(getattr(django_settings, "SLACK_BOT_AUTOSTART", "false")).lower() == "true"
        if not autostart:
            return

        def _start_bot():
            try:
                from slack_hub.bot_service import run_bot
                logger.info("🤖 Auto-starting Slack bot...")
                run_bot()
            except Exception as e:
                logger.warning(f"Slack bot not started: {e}")

        t = threading.Thread(target=_start_bot, daemon=True, name="slack-bot")
        t.start()
        logger.info("🚀 Slack bot thread launched (auto-start)")
