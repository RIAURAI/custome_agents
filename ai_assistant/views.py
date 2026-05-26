import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from companies.middleware import has_platform_access, log_activity

import openai


@login_required
def home(request):
    ctx = {
        "has_ms_access": bool(has_platform_access(request, "microsoft")),
        "has_slack_access": bool(has_platform_access(request, "slack")),
    }
    return render(request, "ai_assistant/assistant.html", ctx)


@login_required
@require_POST
def ask(request):
    """
    POST /ai/ask/
    Body: { "type": "summarize"|"reply", "text": "<email body>" }
    Returns: { "result": "<AI response>" }
    """
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    action_type = payload.get("type", "summarize")
    text = payload.get("text", "").strip()

    if not text:
        return JsonResponse({"error": "No text provided."}, status=400)

    if not settings.OPENAI_API_KEY:
        return JsonResponse({"error": "OpenAI API key not configured."}, status=503)

    if action_type == "reply":
        system_msg = (
            "You are a professional business email assistant. "
            "Write a concise, polite, and professional reply to the email below. "
            "Keep it under 150 words."
        )
        user_msg = f"Email to reply to:\n\n{text}"
    else:
        system_msg = (
            "You are a business productivity assistant. "
            "Summarize the following email in 3-5 bullet points, highlighting key action items."
        )
        user_msg = f"Email to summarize:\n\n{text}"

    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=400,
            temperature=0.4,
        )
        result = response.choices[0].message.content.strip()
        log_activity(request, "ai_summarize" if action_type == "summarize" else "ai_reply", "microsoft", f"{action_type}: {text[:100]}")
        return JsonResponse({"result": result})
    except openai.AuthenticationError:
        return JsonResponse({"error": "Invalid OpenAI API key."}, status=401)
    except openai.RateLimitError:
        return JsonResponse({"error": "OpenAI rate limit reached. Try again shortly."}, status=429)
    except Exception as e:
        return JsonResponse({"error": f"AI error: {str(e)}"}, status=500)
