"""
Unit tests for the AI setup generation service (ADR-015 Session 3).

Tests cover:
- Schema validation (GeneratedSetup cross-field validators)
- Service happy path with mocked Anthropic client
- Timeout handling → SetupGenerationTimeout
- API error handling → SetupGenerationFailed
- Invalid tool output → SetupValidationError
- Missing API key → SetupGenerationFailed
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import anthropic
import pytest

from app.schemas.onboarding import GeneratedSetup
from app.services.onboarding_generation import (
    SetupGenerationFailed,
    SetupGenerationTimeout,
    SetupValidationError,
    generate_setup,
    set_client,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_SETUP_PAYLOAD = {
    "meal_types": [
        {"name": "Breakfast", "description": "Morning meal", "tags": ["quick"]},
        {"name": "Lunch", "description": "Midday meal", "tags": []},
        {"name": "Dinner", "description": "Evening meal", "tags": ["hearty"]},
    ],
    "day_templates": [
        {
            "name": "Workday",
            "notes": "Standard workday schedule",
            "max_calories_kcal": 2000,
            "max_protein_g": "150.0",
            "slots": [
                {"position": 1, "meal_type_name": "Breakfast"},
                {"position": 2, "meal_type_name": "Lunch"},
                {"position": 3, "meal_type_name": "Dinner"},
            ],
        },
        {
            "name": "Weekend",
            "notes": "Relaxed weekend schedule",
            "slots": [
                {"position": 1, "meal_type_name": "Breakfast"},
                {"position": 2, "meal_type_name": "Lunch"},
                {"position": 3, "meal_type_name": "Dinner"},
            ],
        },
    ],
    "week_plan": {
        "name": "My Week",
        "is_default": True,
        "days": [
            {"weekday": 0, "day_template_name": "Workday"},
            {"weekday": 1, "day_template_name": "Workday"},
            {"weekday": 2, "day_template_name": "Workday"},
            {"weekday": 3, "day_template_name": "Workday"},
            {"weekday": 4, "day_template_name": "Workday"},
            {"weekday": 5, "day_template_name": "Weekend"},
            {"weekday": 6, "day_template_name": "Weekend"},
        ],
    },
}

SAMPLE_INTAKE = {
    "meals_per_day": 3,
    "schedule": "9-5 office job, weekends free",
    "goals": "maintain weight, eat healthier",
    "dietary_restrictions": "none",
}


def _make_tool_use_block(payload: dict):
    """Build a mock content block mimicking anthropic ToolUseBlock."""
    return SimpleNamespace(type="tool_use", name="submit_setup", input=payload)


def _make_response(content_blocks: list):
    """Build a mock anthropic Message response."""
    return SimpleNamespace(content=content_blocks)


def _make_mock_client(response=None, exception=None):
    """Build a mock AsyncAnthropic client."""
    client = AsyncMock(spec=anthropic.AsyncAnthropic)
    if exception:
        client.messages.create = AsyncMock(side_effect=exception)
    else:
        client.messages.create = AsyncMock(return_value=response)
    return client


@pytest.fixture(autouse=True)
def cleanup_client():
    """Ensure client override is cleared after each test."""
    yield
    set_client(None)


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestGeneratedSetupSchema:
    def test_valid_setup_passes(self):
        result = GeneratedSetup.model_validate(VALID_SETUP_PAYLOAD)
        assert len(result.meal_types) == 3
        assert len(result.day_templates) == 2
        assert len(result.week_plan.days) == 7

    def test_duplicate_meal_type_names_rejected(self):
        payload = {**VALID_SETUP_PAYLOAD}
        payload["meal_types"] = [
            {"name": "Breakfast", "tags": []},
            {"name": "Breakfast", "tags": []},
            {"name": "Dinner", "tags": []},
        ]
        with pytest.raises(Exception, match="Duplicate meal type names"):
            GeneratedSetup.model_validate(payload)

    def test_duplicate_day_template_names_rejected(self):
        payload = {
            **VALID_SETUP_PAYLOAD,
            "day_templates": [
                {**VALID_SETUP_PAYLOAD["day_templates"][0], "name": "Same"},
                {**VALID_SETUP_PAYLOAD["day_templates"][1], "name": "Same"},
            ],
        }
        with pytest.raises(Exception, match="Duplicate day template names"):
            GeneratedSetup.model_validate(payload)

    def test_unknown_meal_type_in_slot_rejected(self):
        payload = {
            **VALID_SETUP_PAYLOAD,
            "day_templates": [
                {
                    "name": "Workday",
                    "slots": [{"position": 1, "meal_type_name": "NonExistent"}],
                },
            ],
        }
        with pytest.raises(Exception, match="unknown meal type"):
            GeneratedSetup.model_validate(payload)

    def test_unknown_day_template_in_week_plan_rejected(self):
        payload = {
            **VALID_SETUP_PAYLOAD,
            "week_plan": {
                "name": "Bad Week",
                "days": [
                    {"weekday": i, "day_template_name": "NonExistent"}
                    for i in range(7)
                ],
            },
        }
        with pytest.raises(Exception, match="unknown day template"):
            GeneratedSetup.model_validate(payload)

    def test_missing_weekday_rejected(self):
        payload = {
            **VALID_SETUP_PAYLOAD,
            "week_plan": {
                "name": "Short Week",
                "days": [
                    {"weekday": i, "day_template_name": "Workday"}
                    for i in range(6)  # only 6 days
                ],
            },
        }
        with pytest.raises(Exception, match="(weekdays 0-6|too_short|at least 7)"):
            GeneratedSetup.model_validate(payload)

    def test_duplicate_weekday_rejected(self):
        payload = {
            **VALID_SETUP_PAYLOAD,
            "week_plan": {
                "name": "Dup Week",
                "days": [
                    {"weekday": 0, "day_template_name": "Workday"},
                    {"weekday": 0, "day_template_name": "Workday"},
                    *[
                        {"weekday": i, "day_template_name": "Workday"}
                        for i in range(1, 6)
                    ],
                ],
            },
        }
        with pytest.raises(Exception):
            GeneratedSetup.model_validate(payload)

    def test_empty_meal_types_rejected(self):
        payload = {**VALID_SETUP_PAYLOAD, "meal_types": []}
        with pytest.raises(Exception):
            GeneratedSetup.model_validate(payload)

    def test_json_roundtrip(self):
        setup = GeneratedSetup.model_validate(VALID_SETUP_PAYLOAD)
        dumped = setup.model_dump(mode="json")
        restored = GeneratedSetup.model_validate(dumped)
        assert restored.meal_types[0].name == "Breakfast"
        assert restored.week_plan.name == "My Week"


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class TestGenerateSetup:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        response = _make_response([_make_tool_use_block(VALID_SETUP_PAYLOAD)])
        client = _make_mock_client(response=response)
        set_client(client)

        result = await generate_setup(SAMPLE_INTAKE)

        assert isinstance(result, GeneratedSetup)
        assert len(result.meal_types) == 3
        assert result.week_plan.name == "My Week"
        client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_timeout_raises_setup_generation_timeout(self):
        client = _make_mock_client(
            exception=anthropic.APITimeoutError(request=None)
        )
        set_client(client)

        with pytest.raises(SetupGenerationTimeout, match="timed out"):
            await generate_setup(SAMPLE_INTAKE)

    @pytest.mark.asyncio
    async def test_api_error_raises_setup_generation_failed(self):
        client = _make_mock_client(
            exception=anthropic.APIStatusError(
                message="Server error",
                response=SimpleNamespace(
                    status_code=500,
                    headers={},
                    text="Internal Server Error",
                    json=lambda: {},
                    request=SimpleNamespace(
                        method="POST",
                        url="https://api.anthropic.com/v1/messages",
                        headers={},
                    ),
                ),
                body=None,
            )
        )
        set_client(client)

        with pytest.raises(SetupGenerationFailed, match="Claude API error"):
            await generate_setup(SAMPLE_INTAKE)

    @pytest.mark.asyncio
    async def test_invalid_tool_output_raises_validation_error(self):
        bad_payload = {
            "meal_types": [{"name": "Breakfast", "tags": []}],
            "day_templates": [
                {
                    "name": "Workday",
                    "slots": [{"position": 1, "meal_type_name": "Breakfast"}],
                }
            ],
            "week_plan": {
                "name": "Bad",
                "days": [
                    {"weekday": i, "day_template_name": "NonExistent"}
                    for i in range(7)
                ],
            },
        }
        response = _make_response([_make_tool_use_block(bad_payload)])
        client = _make_mock_client(response=response)
        set_client(client)

        with pytest.raises(SetupValidationError, match="invalid"):
            await generate_setup(SAMPLE_INTAKE)

    @pytest.mark.asyncio
    async def test_no_tool_use_block_raises_failed(self):
        text_block = SimpleNamespace(type="text", text="Sorry, I can't do that.")
        response = _make_response([text_block])
        client = _make_mock_client(response=response)
        set_client(client)

        with pytest.raises(SetupGenerationFailed, match="did not call"):
            await generate_setup(SAMPLE_INTAKE)

    @pytest.mark.asyncio
    async def test_missing_api_key_raises_failed(self):
        set_client(None)
        # Temporarily blank out the key — the service checks it in _get_client
        import app.services.onboarding_generation as mod
        original_key = mod.settings.anthropic_api_key
        try:
            mod.settings.anthropic_api_key = ""
            with pytest.raises(SetupGenerationFailed, match="not configured"):
                await generate_setup(SAMPLE_INTAKE)
        finally:
            mod.settings.anthropic_api_key = original_key

    @pytest.mark.asyncio
    async def test_empty_intake_answers(self):
        response = _make_response([_make_tool_use_block(VALID_SETUP_PAYLOAD)])
        client = _make_mock_client(response=response)
        set_client(client)

        result = await generate_setup({})
        assert isinstance(result, GeneratedSetup)
        # Verify the user message was constructed (any content is fine)
        call_kwargs = client.messages.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        assert len(messages) == 1
        assert "default" in messages[0]["content"].lower() or len(messages[0]["content"]) > 0
