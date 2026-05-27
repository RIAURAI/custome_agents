"""Shared helper for all Microsoft views."""
from integrations.utils import get_company_integration, get_valid_access_token


def get_ms_token(request):
    """Return (integration, token) or (None, None)."""
    integration = get_company_integration(request, "microsoft")
    if not integration:
        return None, None
    token = get_valid_access_token(integration)
    return integration, token
