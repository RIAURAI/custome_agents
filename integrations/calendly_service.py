"""
Calendly Scheduling Service — high-level functions for the AI agent.
Completely independent of Slack; can be used by any consumer (bot, web view, API).

Usage:
    from integrations.calendly_service import CalendlyService
    service = CalendlyService(company)
    event_types = service.get_event_types()
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from .calendly_utils import (
    calendly_api_get,
    calendly_api_post,
    get_valid_calendly_token,
)
from .models import CompanyIntegration

logger = logging.getLogger(__name__)


class CalendlyServiceError(Exception):
    """Raised when a Calendly API call fails."""
    pass


class CalendlyNotConnectedError(CalendlyServiceError):
    """Raised when Calendly integration is not active for the company."""
    pass


class CalendlyTokenExpiredError(CalendlyServiceError):
    """Raised when the token cannot be refreshed."""
    pass


class CalendlyService:
    """
    Stateless service layer for Calendly scheduling operations.
    Instantiate per-request with a company object.
    """

    def __init__(self, company):
        self.company = company
        self._integration: CompanyIntegration | None = None
        self._token: str | None = None

    # ── Private helpers ─────────────────────────────────────────────────────

    def _ensure_connected(self) -> None:
        """Load integration + validate token. Raises on failure."""
        if self._token:
            return

        self._integration = CompanyIntegration.objects.filter(
            company=self.company, service="calendly", status="active"
        ).first()

        if not self._integration:
            raise CalendlyNotConnectedError(
                "Calendly is not connected for this company. "
                "Ask your admin to connect it in Settings → Integrations."
            )

        self._token = get_valid_calendly_token(self._integration)
        if not self._token:
            raise CalendlyTokenExpiredError(
                "Calendly connection has expired. "
                "Admin needs to reconnect in Settings → Integrations."
            )

    @property
    def user_uri(self) -> str:
        self._ensure_connected()
        return self._integration.calendly_user_uri

    @property
    def organization_uri(self) -> str:
        self._ensure_connected()
        return self._integration.calendly_organization_uri

    # ── Public API ──────────────────────────────────────────────────────────

    def get_event_types(self) -> list[dict]:
        """
        Fetch all active event types for the connected user.
        Returns list of dicts: [{name, slug, duration, uri, scheduling_url}, ...]
        """
        self._ensure_connected()
        data = calendly_api_get(
            self._token,
            "/event_types",
            params={"user": self.user_uri, "active": "true"},
        )
        results = []
        for et in data.get("collection", []):
            results.append({
                "name": et.get("name", ""),
                "slug": et.get("slug", ""),
                "duration": et.get("duration", 0),
                "uri": et.get("uri", ""),
                "scheduling_url": et.get("scheduling_url", ""),
                "description": et.get("description_plain", ""),
            })
        logger.info(f"[Calendly] Fetched {len(results)} event types for {self.company.name}")
        return results

    def get_availability(
        self,
        event_type_uri: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[dict]:
        """
        Get available time slots for an event type.
        Returns list of dicts: [{start_time, end_time, status}, ...]
        """
        self._ensure_connected()

        if not start_time:
            start_time = datetime.now(timezone.utc)
        if not end_time:
            end_time = start_time + timedelta(days=7)

        data = calendly_api_get(
            self._token,
            "/event_type_available_times",
            params={
                "event_type": event_type_uri,
                "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%S.000000Z"),
                "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%S.000000Z"),
            },
        )
        results = []
        for slot in data.get("collection", []):
            results.append({
                "start_time": slot.get("start_time", ""),
                "end_time": slot.get("end_time", ""),
                "status": slot.get("status", "available"),
            })
        logger.info(f"[Calendly] Found {len(results)} available slots")
        return results

    def get_scheduled_events(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        status: str = "active",
    ) -> list[dict]:
        """
        List scheduled events for the connected user.
        Returns list of dicts: [{name, start_time, end_time, status, uri, invitees_counter}, ...]
        """
        self._ensure_connected()

        if not start_time:
            start_time = datetime.now(timezone.utc)
        if not end_time:
            end_time = start_time + timedelta(days=7)

        data = calendly_api_get(
            self._token,
            "/scheduled_events",
            params={
                "user": self.user_uri,
                "min_start_time": start_time.strftime("%Y-%m-%dT%H:%M:%S.000000Z"),
                "max_start_time": end_time.strftime("%Y-%m-%dT%H:%M:%S.000000Z"),
                "status": status,
            },
        )
        results = []
        for ev in data.get("collection", []):
            results.append({
                "name": ev.get("name", ""),
                "start_time": ev.get("start_time", ""),
                "end_time": ev.get("end_time", ""),
                "status": ev.get("status", ""),
                "uri": ev.get("uri", ""),
                "event_type": ev.get("event_type", ""),
                "location": ev.get("location", {}),
                "invitees_counter": ev.get("invitees_counter", {}),
            })
        logger.info(f"[Calendly] Fetched {len(results)} scheduled events")
        return results

    def create_scheduling_link(self, event_type_uri: str) -> str:
        """
        Create a single-use scheduling link for an event type.
        Returns the booking URL string that can be shared.
        """
        self._ensure_connected()
        data = calendly_api_post(
            self._token,
            "/scheduling_links",
            payload={
                "max_event_count": 1,
                "owner": event_type_uri,
                "owner_type": "EventType",
            },
        )
        booking_url = data.get("resource", {}).get("booking_url", "")
        logger.info(f"[Calendly] Created scheduling link: {booking_url}")
        return booking_url

    def cancel_event(self, event_uuid: str, reason: str = "") -> dict:
        """
        Cancel a scheduled event by UUID.
        Returns cancellation details.
        """
        self._ensure_connected()
        payload = {}
        if reason:
            payload["reason"] = reason

        data = calendly_api_post(
            self._token,
            f"/scheduled_events/{event_uuid}/cancellation",
            payload=payload,
        )
        logger.info(f"[Calendly] Cancelled event {event_uuid}")
        return data

    def get_user_info(self) -> dict:
        """Fetch the connected Calendly user's profile info."""
        self._ensure_connected()
        data = calendly_api_get(self._token, "/users/me")
        resource = data.get("resource", {})
        return {
            "name": resource.get("name", ""),
            "email": resource.get("email", ""),
            "scheduling_url": resource.get("scheduling_url", ""),
            "timezone": resource.get("timezone", ""),
            "avatar_url": resource.get("avatar_url", ""),
        }

    def is_connected(self) -> bool:
        """Check if Calendly is connected and token is valid (non-raising)."""
        try:
            self._ensure_connected()
            return True
        except CalendlyServiceError:
            return False
