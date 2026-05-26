"""
Calendly AI Agent — standalone agent that handles scheduling intents.
Completely decoupled from Slack. Can be invoked by any consumer (Slack bot, web API, etc.).

Uses OpenAI function calling to detect scheduling actions and return structured responses.

Usage:
    from slack_hub.calendly_agent import CalendlyAgent
    agent = CalendlyAgent(company)
    result = agent.process_message("Schedule a 30-min meeting tomorrow")
    # result = {"action": "create_scheduling_link", "params": {...}, "reply_text": "..."}
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from django.conf import settings
import openai

from integrations.calendly_service import (
    CalendlyService,
    CalendlyNotConnectedError,
    CalendlyServiceError,
    CalendlyTokenExpiredError,
)

logger = logging.getLogger(__name__)

# ── OpenAI Tool Definitions ─────────────────────────────────────────────────

CALENDLY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_scheduling_link",
            "description": (
                "Create a single-use scheduling link for a specific meeting type. "
                "Use when user wants to schedule/book a meeting or share a booking link."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_type": {
                        "type": "string",
                        "description": (
                            "Name or keyword of the meeting type (e.g. '30 minute', "
                            "'quick call', '1 hour'). Leave empty to use default."
                        ),
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": (
                "Check available time slots for scheduling. "
                "Use when user asks about availability or free times."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_type": {
                        "type": "string",
                        "description": "Name or keyword of the meeting type.",
                    },
                    "days_ahead": {
                        "type": "integer",
                        "description": "How many days ahead to check. Default 7.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_upcoming_meetings",
            "description": (
                "List upcoming scheduled meetings/events. "
                "Use when user asks about their schedule or upcoming meetings."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "days_ahead": {
                        "type": "integer",
                        "description": "How many days ahead to look. Default 7.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_event_types",
            "description": (
                "List available meeting types (event types) the user can schedule. "
                "Use when user asks what kinds of meetings they can book."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_meeting",
            "description": (
                "Cancel a scheduled meeting. Use when user wants to cancel an event."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_name": {
                        "type": "string",
                        "description": "Name or description of the meeting to cancel.",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for cancellation (optional).",
                    },
                },
                "required": ["meeting_name"],
            },
        },
    },
]

SYSTEM_PROMPT = (
    "You are a scheduling assistant with access to Calendly. "
    "You can help users schedule meetings, check availability, and manage their calendar. "
    "When a user wants to schedule a meeting, use the appropriate tool. "
    "If the message is NOT related to scheduling, reply normally without using any tools. "
    "Keep replies concise and professional (under 100 words)."
)


def _get_client() -> openai.OpenAI:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OpenAI API key not configured.")
    return openai.OpenAI(api_key=settings.OPENAI_API_KEY)


class CalendlyAgent:
    """
    Standalone Calendly scheduling agent.
    Detects scheduling intent via OpenAI function calling,
    then executes Calendly API actions through CalendlyService.
    """

    def __init__(self, company):
        self.company = company
        self.service = CalendlyService(company)

    def process_message(self, message_text: str, context: str = "") -> dict:
        """
        Process a user message and return a structured response.

        Returns:
            {
                "action": str | None,      # Action taken (or None if plain reply)
                "reply_text": str,         # Human-readable response
                "data": dict | None,       # Structured data (e.g. event list, link)
                "error": bool,             # Whether an error occurred
            }
        """
        # Check if Calendly is connected before engaging tools
        if not self.service.is_connected():
            return {
                "action": None,
                "reply_text": "",
                "data": None,
                "error": False,
                "calendly_available": False,
            }

        # Call OpenAI with function calling
        try:
            ai_response = self._call_ai(message_text, context)
        except Exception as e:
            logger.error(f"[CalendlyAgent] AI call failed: {e}")
            return {
                "action": None,
                "reply_text": "Sorry, I'm having trouble processing that request.",
                "data": None,
                "error": True,
            }

        # If no tool call → return plain text (not a scheduling request)
        if not ai_response.get("tool_call"):
            return {
                "action": None,
                "reply_text": ai_response.get("content", ""),
                "data": None,
                "error": False,
            }

        # Execute the tool call
        tool_name = ai_response["tool_call"]["name"]
        tool_args = ai_response["tool_call"]["arguments"]

        return self._execute_action(tool_name, tool_args)

    def _call_ai(self, message_text: str, context: str = "") -> dict:
        """
        Call OpenAI with tools defined. Returns either a tool_call or plain content.
        """
        user_msg = message_text
        if context:
            user_msg = f"Context: {context}\n\nMessage: {message_text}"

        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            tools=CALENDLY_TOOLS,
            tool_choice="auto",
            max_tokens=200,
            temperature=0.3,
        )

        message = response.choices[0].message

        # Check if AI wants to call a tool
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            return {
                "tool_call": {
                    "name": tool_call.function.name,
                    "arguments": json.loads(tool_call.function.arguments),
                },
                "content": message.content or "",
            }

        return {"tool_call": None, "content": message.content or ""}

    def _execute_action(self, action: str, params: dict) -> dict:
        """
        Execute a Calendly action and return a structured result.
        """
        logger.info(f"[CalendlyAgent] Executing: {action}({params})")

        try:
            if action == "get_scheduling_link":
                return self._action_get_scheduling_link(params)
            elif action == "check_availability":
                return self._action_check_availability(params)
            elif action == "list_upcoming_meetings":
                return self._action_list_upcoming_meetings(params)
            elif action == "list_event_types":
                return self._action_list_event_types(params)
            elif action == "cancel_meeting":
                return self._action_cancel_meeting(params)
            else:
                return {
                    "action": action,
                    "reply_text": f"Unknown action: {action}",
                    "data": None,
                    "error": True,
                }
        except CalendlyNotConnectedError as e:
            return {
                "action": action,
                "reply_text": str(e),
                "data": None,
                "error": True,
            }
        except CalendlyTokenExpiredError as e:
            return {
                "action": action,
                "reply_text": str(e),
                "data": None,
                "error": True,
            }
        except CalendlyServiceError as e:
            logger.error(f"[CalendlyAgent] Service error: {e}")
            return {
                "action": action,
                "reply_text": "Something went wrong with Calendly. Please try again later.",
                "data": None,
                "error": True,
            }
        except Exception as e:
            logger.error(f"[CalendlyAgent] Unexpected error in {action}: {e}")
            return {
                "action": action,
                "reply_text": "An unexpected error occurred. Please try again.",
                "data": None,
                "error": True,
            }

    # ── Action Implementations ──────────────────────────────────────────────

    def _action_get_scheduling_link(self, params: dict) -> dict:
        """Create and return a scheduling link."""
        meeting_type_query = params.get("meeting_type", "")

        # Find matching event type
        event_type = self._find_event_type(meeting_type_query)
        if not event_type:
            event_types = self.service.get_event_types()
            if not event_types:
                return {
                    "action": "get_scheduling_link",
                    "reply_text": "No event types configured in Calendly. Please set up at least one event type.",
                    "data": None,
                    "error": True,
                }
            # Use the first one as default
            event_type = event_types[0]

        # Create the link
        booking_url = self.service.create_scheduling_link(event_type["uri"])

        reply = (
            f"Here's your scheduling link for **{event_type['name']}** "
            f"({event_type['duration']} min):\n{booking_url}"
        )

        return {
            "action": "get_scheduling_link",
            "reply_text": reply,
            "data": {
                "booking_url": booking_url,
                "event_type_name": event_type["name"],
                "duration": event_type["duration"],
            },
            "error": False,
        }

    def _action_check_availability(self, params: dict) -> dict:
        """Check availability for an event type."""
        meeting_type_query = params.get("meeting_type", "")
        days_ahead = params.get("days_ahead", 7)

        event_type = self._find_event_type(meeting_type_query)
        if not event_type:
            event_types = self.service.get_event_types()
            if not event_types:
                return {
                    "action": "check_availability",
                    "reply_text": "No event types configured in Calendly.",
                    "data": None,
                    "error": True,
                }
            event_type = event_types[0]

        now = datetime.now(timezone.utc)
        end_time = now + timedelta(days=min(days_ahead, 14))

        slots = self.service.get_availability(event_type["uri"], now, end_time)

        if not slots:
            reply = f"No available slots found for **{event_type['name']}** in the next {days_ahead} days."
        else:
            # Show up to 10 slots
            slot_lines = []
            for slot in slots[:10]:
                start = slot["start_time"]
                if isinstance(start, str) and "T" in start:
                    # Parse and format nicely
                    dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    slot_lines.append(f"• {dt.strftime('%a %b %d, %I:%M %p')} UTC")
                else:
                    slot_lines.append(f"• {start}")

            reply = (
                f"Available slots for **{event_type['name']}** "
                f"(next {days_ahead} days):\n" + "\n".join(slot_lines)
            )
            if len(slots) > 10:
                reply += f"\n...and {len(slots) - 10} more slots available."

        return {
            "action": "check_availability",
            "reply_text": reply,
            "data": {"slots": slots[:10], "event_type": event_type["name"]},
            "error": False,
        }

    def _action_list_upcoming_meetings(self, params: dict) -> dict:
        """List upcoming scheduled events."""
        days_ahead = params.get("days_ahead", 7)

        now = datetime.now(timezone.utc)
        end_time = now + timedelta(days=min(days_ahead, 30))

        events = self.service.get_scheduled_events(now, end_time)

        if not events:
            reply = f"No meetings scheduled in the next {days_ahead} days."
        else:
            event_lines = []
            for ev in events[:10]:
                start = ev["start_time"]
                if isinstance(start, str) and "T" in start:
                    dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    event_lines.append(
                        f"• **{ev['name']}** — {dt.strftime('%a %b %d, %I:%M %p')} UTC"
                    )
                else:
                    event_lines.append(f"• **{ev['name']}** — {start}")

            reply = f"Upcoming meetings (next {days_ahead} days):\n" + "\n".join(event_lines)
            if len(events) > 10:
                reply += f"\n...and {len(events) - 10} more."

        return {
            "action": "list_upcoming_meetings",
            "reply_text": reply,
            "data": {"events": events[:10]},
            "error": False,
        }

    def _action_list_event_types(self, params: dict) -> dict:
        """List available event types."""
        event_types = self.service.get_event_types()

        if not event_types:
            reply = "No event types configured in Calendly."
        else:
            lines = []
            for et in event_types:
                lines.append(f"• **{et['name']}** ({et['duration']} min)")
            reply = "Available meeting types:\n" + "\n".join(lines)

        return {
            "action": "list_event_types",
            "reply_text": reply,
            "data": {"event_types": event_types},
            "error": False,
        }

    def _action_cancel_meeting(self, params: dict) -> dict:
        """Cancel a meeting by matching name."""
        meeting_name = params.get("meeting_name", "")
        reason = params.get("reason", "")

        # Find the event to cancel
        now = datetime.now(timezone.utc)
        events = self.service.get_scheduled_events(now, now + timedelta(days=30))

        # Match by name (case-insensitive partial match)
        match = None
        for ev in events:
            if meeting_name.lower() in ev["name"].lower():
                match = ev
                break

        if not match:
            return {
                "action": "cancel_meeting",
                "reply_text": (
                    f"Couldn't find a meeting matching '{meeting_name}'. "
                    "Please check the meeting name and try again."
                ),
                "data": None,
                "error": True,
            }

        # Extract UUID from URI
        event_uuid = match["uri"].rstrip("/").split("/")[-1]
        self.service.cancel_event(event_uuid, reason)

        reply = f"✅ Cancelled: **{match['name']}** (scheduled for {match['start_time'][:10]})"
        if reason:
            reply += f"\nReason: {reason}"

        return {
            "action": "cancel_meeting",
            "reply_text": reply,
            "data": {"cancelled_event": match},
            "error": False,
        }

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _find_event_type(self, query: str) -> dict | None:
        """Find an event type by name/keyword match. Returns None if no match."""
        if not query:
            return None

        event_types = self.service.get_event_types()
        query_lower = query.lower()

        # Exact name match
        for et in event_types:
            if et["name"].lower() == query_lower:
                return et

        # Partial match
        for et in event_types:
            if query_lower in et["name"].lower():
                return et

        # Duration match (e.g. "30 min", "30")
        for et in event_types:
            if str(et["duration"]) in query_lower:
                return et

        return None
