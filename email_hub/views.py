from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render

from companies.middleware import log_activity, platform_access_required
from integrations.utils import get_company_integration, get_valid_access_token, graph_get, graph_post


def _get_token_or_redirect(request):
    ms = get_company_integration(request, "microsoft")
    if not ms:
        messages.warning(request, "Please connect your Microsoft account first.")
        return None, None
    token = get_valid_access_token(ms)
    if not token:
        messages.error(request, "Microsoft session expired. Please reconnect.")
        return None, None
    return ms, token


@platform_access_required("microsoft")
def inbox(request):
    _, token = _get_token_or_redirect(request)
    emails = []
    error = None
    ms_connected = get_company_integration(request, "microsoft") is not None
    if token:
        try:
            data = graph_get(token, "/me/messages", {
                "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview",
                "$top": "25",
                "$orderby": "receivedDateTime desc",
            })
            emails = data.get("value", [])
        except Exception as e:
            error = str(e)
    return render(request, "email_hub/inbox.html", {"emails": emails, "error": error, "ms_connected": ms_connected})


@platform_access_required("microsoft")
def email_detail(request, email_id):
    _, token = _get_token_or_redirect(request)
    email = None
    error = None
    if token:
        try:
            email = graph_get(token, f"/me/messages/{email_id}")
            # Mark as read
            graph_post(token, f"/me/messages/{email_id}", {"isRead": True})
            log_activity(request, "email_viewed", "microsoft", email.get("subject", "")[:200])
        except Exception as e:
            error = str(e)
    return render(request, "email_hub/email_detail.html", {"email": email, "error": error})


@platform_access_required("microsoft", "reply")
def compose(request):
    _, token = _get_token_or_redirect(request)
    if not token:
        return redirect("integrations:connect")

    if request.method == "POST":
        to_email = request.POST.get("to_email", "").strip()
        subject = request.POST.get("subject", "").strip()
        body = request.POST.get("body", "").strip()

        if not (to_email and subject and body):
            messages.error(request, "All fields are required.")
            return render(request, "email_hub/compose.html", {
                "to_email": to_email, "subject": subject, "body": body
            })

        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "Text", "content": body},
                "toRecipients": [{"emailAddress": {"address": to_email}}],
            }
        }
        try:
            graph_post(token, "/me/sendMail", payload)
            log_activity(request, "email_sent", "microsoft", f"To: {to_email}, Subject: {subject}"[:200])
            messages.success(request, f"Email sent to {to_email}!")
            return redirect("email_hub:inbox")
        except Exception as e:
            messages.error(request, f"Failed to send: {e}")

    return render(request, "email_hub/compose.html", {})
