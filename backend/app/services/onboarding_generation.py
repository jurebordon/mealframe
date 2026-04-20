"""AI setup generation via Claude Sonnet tool-calling (ADR-015 Session 3).

Takes onboarding intake answers and generates a personalized meal planning
setup: meal types, day templates, and week plan. Uses Anthropic's tool-calling
to force structured output through a ``submit_setup`` tool whose input schema
matches ``GeneratedSetup``.
"""
import logging

import anthropic

from ..config import settings
from ..schemas.onboarding import GeneratedSetup

logger = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096
REQUEST_TIMEOUT = 20.0  # seconds; SPEC target is <15s, buffer for network

# ---------------------------------------------------------------------------
# Test-injectable client override (mirrors nutrition/_http.py pattern)
# ---------------------------------------------------------------------------
_client_override: anthropic.AsyncAnthropic | None = None


def set_client(client: anthropic.AsyncAnthropic | None) -> None:
    """Override the Anthropic client (tests only)."""
    global _client_override
    _client_override = client


def _get_client() -> anthropic.AsyncAnthropic:
    """Return the active Anthropic client, creating one if needed."""
    if _client_override is not None:
        return _client_override
    if not settings.anthropic_api_key:
        raise SetupGenerationFailed("ANTHROPIC_API_KEY is not configured")
    return anthropic.AsyncAnthropic(
        api_key=settings.anthropic_api_key,
        timeout=REQUEST_TIMEOUT,
    )


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SetupGenerationFailed(Exception):
    """Claude API returned an error or is misconfigured."""


class SetupGenerationTimeout(Exception):
    """Claude API request exceeded the timeout."""


class SetupValidationError(Exception):
    """Claude returned structurally invalid setup data."""

    def __init__(self, message: str, raw_payload: dict | None = None):
        super().__init__(message)
        self.raw_payload = raw_payload


# ---------------------------------------------------------------------------
# Tool definition — schema derived from GeneratedSetup
# ---------------------------------------------------------------------------

SUBMIT_SETUP_TOOL: dict = {
    "name": "submit_setup",
    "description": (
        "Submit the complete meal planning setup. Call this exactly once with "
        "the generated meal types, day templates, and week plan."
    ),
    "input_schema": GeneratedSetup.model_json_schema(),
}

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a meal planning assistant for MealFrame. Your job is to generate a \
personalized meal planning setup from the user's intake answers.

You MUST call the submit_setup tool exactly once with a complete setup.

## What you generate

1. **Meal types** — categories like Breakfast, Lunch, Dinner, Snack. \
Typically 2-5 types based on the user's described eating pattern.
2. **Day templates** — named daily eating patterns (e.g. "Workday", \
"Weekend", "Rest Day"). Each template has ordered slots that reference meal \
types by name.
3. **Week plan** — assigns a day template to each weekday (0=Monday through \
6=Sunday). Must cover all 7 days.

## Rules

- Match the user's stated meal count and schedule. If they say "3 meals a day", \
create 3 slots per template — not 4 or 5.
- Use clear, user-friendly names. "Workday" not "Template A".
- If the user mentions different schedules for different days (e.g. weekdays \
vs weekends), create separate day templates.
- If the user mentions calorie or protein targets, set max_calories_kcal and \
max_protein_g on the day templates.
- Keep tags practical: ["high-protein"], ["quick"], ["meal-prep"].
- Every meal type you create must be used in at least one day template slot.
- Every day template you create must be used in at least one week plan day.
- Slot positions start at 1 and increment sequentially.
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _format_intake_for_prompt(intake_answers: dict) -> str:
    """Convert intake answers dict into a readable markdown message."""
    if not intake_answers:
        return "No intake answers provided. Generate a sensible default setup."

    lines = ["Here are my onboarding answers:\n"]
    for key, value in sorted(intake_answers.items()):
        label = key.replace("_", " ").title()
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        lines.append(f"- **{label}**: {value}")
    return "\n".join(lines)


async def generate_setup(intake_answers: dict) -> GeneratedSetup:
    """Generate a meal planning setup from intake answers via Claude tool-calling.

    Returns a validated ``GeneratedSetup`` on success.

    Raises:
        SetupGenerationFailed: API error or missing configuration.
        SetupGenerationTimeout: Request exceeded timeout.
        SetupValidationError: Claude returned data that fails schema validation.
    """
    client = _get_client()
    user_message = _format_intake_for_prompt(intake_answers)

    try:
        response = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=[SUBMIT_SETUP_TOOL],
            tool_choice={"type": "tool", "name": "submit_setup"},
            messages=[{"role": "user", "content": user_message}],
        )
    except anthropic.APITimeoutError as e:
        raise SetupGenerationTimeout("Claude API request timed out") from e
    except anthropic.APIError as e:
        raise SetupGenerationFailed(f"Claude API error: {e}") from e

    # Extract the tool_use block
    tool_input: dict | None = None
    for block in response.content:
        if block.type == "tool_use" and block.name == "submit_setup":
            tool_input = block.input
            break

    if tool_input is None:
        logger.error("Claude response contained no submit_setup tool_use block")
        raise SetupGenerationFailed(
            "Claude did not call the submit_setup tool"
        )

    # Validate through Pydantic
    try:
        result = GeneratedSetup.model_validate(tool_input)
    except Exception as e:
        logger.error(
            "Generated setup failed validation: %s | raw: %s", e, tool_input
        )
        raise SetupValidationError(
            f"Generated setup is invalid: {e}", raw_payload=tool_input
        ) from e

    logger.info(
        "Setup generated: %d meal types, %d day templates",
        len(result.meal_types),
        len(result.day_templates),
    )
    return result
