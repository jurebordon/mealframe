"""OpenAI GPT-4o vision service for AI meal capture (ADR-013).

Analyzes food photos and returns structured macro estimates.
Processing is synchronous — result returned in the HTTP response.
"""
import base64
import json
import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from openai import AsyncOpenAI, APIError, APITimeoutError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.openai_usage import OpenAIUsage
from ..schemas.meal import AICaptureAnalysis, IdentifiedItem

logger = logging.getLogger(__name__)

MODEL = "gpt-4o"
REQUEST_TIMEOUT = 15.0  # seconds

# Cost constants for gpt-4o (as of 2024, approximate)
_COST_PER_INPUT_TOKEN = 0.000005   # $5 per 1M input tokens
_COST_PER_OUTPUT_TOKEN = 0.000015  # $15 per 1M output tokens

VISION_PROMPT = """You are a food nutrition analyzer. Look at this photo and identify what food is shown.

Return ONLY valid JSON matching this exact structure — no extra text, no markdown:
{
  "meal_name": "Descriptive name of the meal",
  "portion_description": "Xg item1 + Yg item2 + item3 (use + delimiter, estimate weights)",
  "calories_kcal": 0,
  "protein_g": 0.0,
  "carbs_g": 0.0,
  "fat_g": 0.0,
  "confidence_score": 0.0,
  "identified_items": [
    {"name": "food item name", "estimated_quantity": "Xg or X pieces"}
  ],
  "suggested_meal_type": "breakfast"
}

Rules:
- confidence_score is 0.0 to 1.0 (your confidence in the macro estimates)
- suggested_meal_type must be one of: breakfast, lunch, dinner, snack
- portion_description must use the "+" delimiter format (e.g., "200g chicken + 250g rice + 100g salad")
- If you cannot identify food clearly, still return your best guess with confidence_score below 0.3
- Never return null values; use 0 for unknown numeric fields
- calories_kcal must be an integer"""


class AICaptureFailed(Exception):
    """Vision API returned an error response."""
    pass


class AITimeoutError(Exception):
    """Vision API request timed out."""
    pass


class FoodNotDetected(Exception):
    """Image does not appear to contain recognizable food."""
    pass


async def analyze_food_image(
    image_bytes: bytes,
    user_id: UUID,
    db: AsyncSession,
) -> AICaptureAnalysis:
    """
    Call GPT-4o vision API synchronously and return structured meal data.

    Logs token usage to openai_usage table after each successful call.

    Raises:
        AICaptureFailed: Vision API returned an error
        AITimeoutError: Request exceeded REQUEST_TIMEOUT seconds
        FoodNotDetected: Model returned confidence < 0.15 (likely not food)
        ValueError: If OPENAI_API_KEY is not configured
    """
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured")

    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=REQUEST_TIMEOUT)
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}",
                                "detail": "auto",
                            },
                        },
                    ],
                }
            ],
            max_tokens=500,
            response_format={"type": "json_object"},
        )
    except APITimeoutError as e:
        raise AITimeoutError("Vision API request timed out") from e
    except APIError as e:
        raise AICaptureFailed(f"Vision API error: {e}") from e

    # Log usage
    usage = response.usage
    if usage:
        cost = (
            (usage.prompt_tokens * _COST_PER_INPUT_TOKEN)
            + (usage.completion_tokens * _COST_PER_OUTPUT_TOKEN)
        )
        db.add(OpenAIUsage(
            id=uuid4(),
            user_id=user_id,
            model=MODEL,
            tokens_prompt=usage.prompt_tokens,
            tokens_completion=usage.completion_tokens,
            cost_estimate_usd=round(cost, 6),
            created_at=datetime.now(timezone.utc),
        ))
        await db.flush()

    # Parse response
    raw_content = response.choices[0].message.content or ""
    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as e:
        logger.error("GPT-4o returned non-JSON: %s", raw_content[:500])
        raise AICaptureFailed("Vision model returned invalid JSON") from e

    # Normalize identified_items
    raw_items = data.get("identified_items", [])
    items = []
    for item in raw_items:
        if isinstance(item, dict) and "name" in item:
            items.append(IdentifiedItem(
                name=item.get("name", ""),
                estimated_quantity=item.get("estimated_quantity", ""),
            ))

    try:
        analysis = AICaptureAnalysis(
            meal_name=data.get("meal_name", "Unknown meal"),
            portion_description=data.get("portion_description", ""),
            calories_kcal=data.get("calories_kcal") or None,
            protein_g=data.get("protein_g") or None,
            carbs_g=data.get("carbs_g") or None,
            fat_g=data.get("fat_g") or None,
            confidence_score=float(data.get("confidence_score", 0.5)),
            identified_items=items,
            suggested_meal_type=data.get("suggested_meal_type"),
        )
    except (ValidationError, TypeError) as e:
        logger.error("Failed to parse AI response: %s | raw: %s", e, data)
        raise AICaptureFailed("Vision model returned unexpected data structure") from e

    if analysis.confidence_score < 0.15:
        raise FoodNotDetected(
            f"Could not identify food in this image (confidence: {analysis.confidence_score:.2f})"
        )

    return analysis
