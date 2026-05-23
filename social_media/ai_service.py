"""
AI service for Social Media — message classification, auto-reply, and analytics.
"""
from __future__ import annotations

import logging

from django.conf import settings
import openai

logger = logging.getLogger(__name__)


def _get_client() -> openai.OpenAI:
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured in settings.")
    return openai.OpenAI(api_key=api_key)


def classify_message(text: str, platform: str = "") -> dict:
    """
    Classify a social media message.
    Returns: {
        "classification": "question|complaint|inquiry|feedback|spam|general",
        "sentiment": "positive|neutral|negative",
        "summary": "...",
        "confidence": 0.0-1.0
    }
    """
    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are a social media message classifier for a business ({platform} platform). "
                    "Analyze the message and return:\n"
                    "1. classification: one of 'question', 'complaint', 'inquiry', 'feedback', 'spam', 'general'\n"
                    "2. sentiment: one of 'positive', 'neutral', 'negative'\n"
                    "3. summary: a one-line summary\n"
                    "4. confidence: a number between 0 and 1 indicating how confident you are\n\n"
                    "Respond in this exact format:\n"
                    "CLASSIFICATION: <type>\n"
                    "SENTIMENT: <sentiment>\n"
                    "SUMMARY: <one line>\n"
                    "CONFIDENCE: <number>"
                ),
            },
            {"role": "user", "content": f"Message:\n{text}"},
        ],
        max_tokens=150,
        temperature=0.2,
    )
    result = response.choices[0].message.content.strip()

    classification = "general"
    sentiment = "neutral"
    summary = text[:100]
    confidence = 0.5

    for line in result.split("\n"):
        if line.startswith("CLASSIFICATION:"):
            val = line.split(":", 1)[1].strip().lower()
            if val in ("question", "complaint", "inquiry", "feedback", "spam", "general"):
                classification = val
        elif line.startswith("SENTIMENT:"):
            val = line.split(":", 1)[1].strip().lower()
            if val in ("positive", "neutral", "negative"):
                sentiment = val
        elif line.startswith("SUMMARY:"):
            summary = line.split(":", 1)[1].strip()
        elif line.startswith("CONFIDENCE:"):
            try:
                confidence = float(line.split(":", 1)[1].strip())
            except ValueError:
                pass

    return {
        "classification": classification,
        "sentiment": sentiment,
        "summary": summary,
        "confidence": confidence,
    }


def generate_reply(
    message_text: str,
    platform: str = "",
    custom_instructions: str = "",
    persona_name: str = "",
    conversation_context: str = "",
    company_info: str = "",
) -> str:
    """
    Generate an AI reply for a social media message.
    """
    system_prompt = (
        f"You are a professional business assistant replying on {platform or 'social media'}. "
        "Generate a helpful, concise reply. Keep it under 150 words. Be friendly and professional. "
        "Match the appropriate tone for the platform."
    )
    if company_info:
        system_prompt += f"\n\nCompany information (use when relevant):\n{company_info}"
    if persona_name:
        system_prompt += f"\nYour name is '{persona_name}'."
    if custom_instructions:
        system_prompt += f"\n\nBusiness instructions: {custom_instructions}"

    user_msg = f"Customer message:\n{message_text}"
    if conversation_context:
        user_msg = f"Previous conversation:\n{conversation_context}\n\n{user_msg}"

    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=250,
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()


def analyze_conversation(messages: list[dict], platform: str = "") -> dict:
    """
    Analyze a conversation thread — summarize, detect intent, suggest next action.
    Each message: {"sender": "...", "text": "...", "direction": "inbound/outbound"}
    """
    if not messages:
        return {"summary": "No messages to analyze.", "intent": "none", "suggested_action": "none"}

    formatted = "\n".join(
        f"- {'Customer' if m.get('direction') == 'inbound' else 'Business'}: {m.get('text', '')[:200]}"
        for m in messages[:20]
    )

    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    f"Analyze this {platform or 'social media'} business conversation. Provide:\n"
                    "1. SUMMARY: 2-3 sentence summary\n"
                    "2. INTENT: customer's main intent (purchase, support, complaint, info, scheduling, other)\n"
                    "3. SUGGESTED_ACTION: what the business should do next\n"
                    "4. PRIORITY: low, medium, high"
                ),
            },
            {"role": "user", "content": f"Conversation:\n{formatted}"},
        ],
        max_tokens=300,
        temperature=0.3,
    )
    result = response.choices[0].message.content.strip()

    analysis = {"summary": "", "intent": "other", "suggested_action": "", "priority": "medium"}
    for line in result.split("\n"):
        if line.startswith("SUMMARY:"):
            analysis["summary"] = line.split(":", 1)[1].strip()
        elif line.startswith("INTENT:"):
            analysis["intent"] = line.split(":", 1)[1].strip().lower()
        elif line.startswith("SUGGESTED_ACTION:"):
            analysis["suggested_action"] = line.split(":", 1)[1].strip()
        elif line.startswith("PRIORITY:"):
            analysis["priority"] = line.split(":", 1)[1].strip().lower()

    return analysis


def generate_post_content(
    topic: str,
    platform: str = "",
    tone: str = "professional",
    max_length: int = 280,
) -> str:
    """
    Generate social media post content using AI.
    """
    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are a social media content creator for {platform or 'general'} platform. "
                    f"Create a {tone} post about the given topic. "
                    f"Keep it under {max_length} characters. Include relevant hashtags if appropriate."
                ),
            },
            {"role": "user", "content": f"Topic: {topic}"},
        ],
        max_tokens=200,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
