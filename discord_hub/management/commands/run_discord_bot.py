"""
Django management command to run the Discord bot via Gateway API.
Usage: python manage.py run_discord_bot
"""
import logging

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Start the Discord bot (Gateway Mode) — listens for messages and auto-replies using AI"

    def handle(self, *args, **options):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )

        self.stdout.write(self.style.SUCCESS("Starting Discord AI Bot (Gateway Mode)..."))
        self.stdout.write("=" * 55)
        self.stdout.write("  • No ngrok needed — connects via WebSocket")
        self.stdout.write("  • Reads ALL messages the bot can see")
        self.stdout.write("  • DMs → always AI auto-reply")
        self.stdout.write("  • Channels → reply only if DiscordAutoReplyRule set")
        self.stdout.write("  • Every message is classified + saved to DB")
        self.stdout.write("  • Press Ctrl+C to stop")
        self.stdout.write("=" * 55)

        from discord_hub.bot_service import run_discord_bot

        try:
            run_discord_bot()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nDiscord bot stopped."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Bot error: {e}"))
            raise
