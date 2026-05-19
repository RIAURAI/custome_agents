"""
AI service for Slack message analysis, classification, and auto-reply generation.
"""
from __future__ import annotations

from django.conf import settings
import openai


def _get_client() -> openai.OpenAI:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OpenAI API key not configured.")
    return openai.OpenAI(api_key=settings.OPENAI_API_KEY)


def classify_message(text: str) -> dict:
    """
    Classify a Slack message into a category and extract key info.
    Returns: {"classification": "question|request|fyi|urgent|general", "summary": "..."}
    """
    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Slack message classifier. Analyze the message and return:\n"
                    "1. classification: one of 'question', 'request', 'urgent', 'fyi', 'general'\n"
                    "2. summary: a one-line summary of what the message is about\n\n"
                    "Respond in this exact format:\n"
                    "CLASSIFICATION: <type>\n"
                    "SUMMARY: <one line summary>"
                ),
            },
            {"role": "user", "content": f"Slack message:\n{text}"},
        ],
        max_tokens=100,
        temperature=0.2,
    )
    result = response.choices[0].message.content.strip()

    classification = "general"
    summary = text[:100]

    for line in result.split("\n"):
        if line.startswith("CLASSIFICATION:"):
            val = line.split(":", 1)[1].strip().lower()
            if val in ("question", "request", "urgent", "fyi", "general"):
                classification = val
        elif line.startswith("SUMMARY:"):
            summary = line.split(":", 1)[1].strip()

    return {"classification": classification, "summary": summary}


def generate_reply(message_text: str, context: str = "", custom_instructions: str = "") -> str:
    """
    Generate an AI reply for a Slack message.
    """
    system_prompt = (
        "You are a professional Slack assistant. Generate a helpful, concise reply "
        "to the following Slack message. Keep it under 100 words. Be friendly but professional. "
        "Match the tone of the original message."
    )
    if custom_instructions:
        system_prompt += f"\n\nAdditional instructions: {custom_instructions}"

    user_msg = f"Message to reply to:\n{message_text}"
    if context:
        user_msg = f"Channel context:\n{context}\n\n{user_msg}"

    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=200,
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()


def summarize_channel(messages: list[dict]) -> str:
    """
    Summarize recent channel activity from a list of messages.
    Each message dict should have 'sender_name' and 'text' keys.
    """
    if not messages:
        return "No recent messages to summarize."

    formatted = "\n".join(
        f"- {m.get('sender_name', 'Unknown')}: {m.get('text', '')[:200]}"
        for m in messages[:20]
    )

    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Summarize the following Slack channel conversation in 3-5 bullet points. "
                    "Highlight key decisions, action items, and important updates."
                ),
            },
            {"role": "user", "content": f"Recent messages:\n{formatted}"},
        ],
        max_tokens=300,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()
