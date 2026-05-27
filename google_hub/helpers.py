"""
google_hub/helpers.py  –  Shared helpers for all Google Hub views.
"""
from integrations.utils import get_company_integration
from integrations.google_utils import get_valid_google_access_token


def get_google_token(request):
    """Return (integration, token) for the current company's Google connection.
    Returns (None, None) if not connected or token refresh failed.
    """
    integration = get_company_integration(request, "google")
    if not integration:
        return None, None
    token = get_valid_google_access_token(integration)
    return integration, token
