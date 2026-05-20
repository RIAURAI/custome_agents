"""
Django management command to run the Slack bot in Socket Mode.
Usage: python manage.py run_slack_bot
"""
import logging

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Start the Slack bot (Socket Mode) — listens for messages and auto-replies using AI"

    def handle(self, *args, **options):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )

        self.stdout.write(self.style.SUCCESS("Starting Slack AI Bot (Socket Mode)..."))
        self.stdout.write("=" * 50)
        self.stdout.write("  • No ngrok needed — connects via WebSocket")
        self.stdout.write("  • Auto-replies to messages based on your rules")
        self.stdout.write("  • AI analyzes & classifies every message")
        self.stdout.write("=" * 50)

        from slack_hub.bot_service import run_bot

        try:
            run_bot()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nBot stopped."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Bot error: {e}"))
            raise
