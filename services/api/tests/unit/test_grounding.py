"""Unit tests for the grounding convention helpers.

Verifies:
- build_context_block / parse_context_block form a round-trip (encode then decode).
- parse_context_block returns {} when the markers are absent, incomplete, or malformed.
- Non-JSON-serialisable values (UUID, Enum) survive the round-trip as strings.
- The *last* CONTEXT_JSON block wins when multiple are present.
- strip_context_block removes only the block and leaves the instruction intact.
"""

from __future__ import annotations

import json
import uuid
from enum import StrEnum

from applypilot.agents.grounding import (
    CONTEXT_CLOSE,
    CONTEXT_OPEN,
    build_context_block,
    parse_context_block,
    strip_context_block,
)

# ---------------------------------------------------------------------------
# round-trip tests
# ---------------------------------------------------------------------------


class TestBuildParseRoundTrip:
    def test_simple_dict_round_trips(self) -> None:
        data = {"key": "value", "number": 42, "nested": {"a": True}}
        block = build_context_block(data)
        parsed = parse_context_block(block)
        assert parsed == data

    def test_block_contains_open_and_close_markers(self) -> None:
        block = build_context_block({"x": 1})
        assert block.startswith(CONTEXT_OPEN)
        assert block.endswith(CONTEXT_CLOSE)

    def test_round_trip_with_list_values(self) -> None:
        data = {"items": ["a", "b", "c"], "count": 3}
        block = build_context_block(data)
        assert parse_context_block(block) == data

    def test_round_trip_with_empty_dict(self) -> None:
        block = build_context_block({})
        assert parse_context_block(block) == {}

    def test_uuid_serialised_as_string(self) -> None:
        uid = uuid.uuid4()
        data = {"id": uid}
        block = build_context_block(data)
        parsed = parse_context_block(block)
        assert parsed["id"] == str(uid)

    def test_enum_serialised_as_string(self) -> None:
        class Color(StrEnum):
            RED = "red"

        data = {"color": Color.RED}
        block = build_context_block(data)
        parsed = parse_context_block(block)
        assert parsed["color"] == "red"

    def test_deep_nesting_survives(self) -> None:
        data = {"level1": {"level2": {"level3": "deep_value"}}}
        block = build_context_block(data)
        assert parse_context_block(block) == data

    def test_prompt_prefix_does_not_interfere(self) -> None:
        data = {"company": "Acme", "role": "Engineer"}
        prompt = "Analyse this job post." + build_context_block(data)
        assert parse_context_block(prompt) == data


# ---------------------------------------------------------------------------
# parse_context_block edge cases (returns {} when absent/malformed)
# ---------------------------------------------------------------------------


class TestParseContextBlockEdgeCases:
    def test_returns_empty_dict_when_no_markers(self) -> None:
        assert parse_context_block("Just a plain prompt, no markers.") == {}

    def test_returns_empty_dict_for_empty_string(self) -> None:
        assert parse_context_block("") == {}

    def test_returns_empty_dict_when_only_open_marker(self) -> None:
        assert parse_context_block(f"{CONTEXT_OPEN}{{\"key\": \"value\"}}") == {}

    def test_returns_empty_dict_when_only_close_marker(self) -> None:
        assert parse_context_block(f'{{\"key\": \"value\"}}{CONTEXT_CLOSE}') == {}

    def test_returns_empty_dict_for_malformed_json(self) -> None:
        bad = f"{CONTEXT_OPEN}{{not valid json}}{CONTEXT_CLOSE}"
        assert parse_context_block(bad) == {}

    def test_returns_empty_dict_when_json_is_list_not_dict(self) -> None:
        payload = json.dumps([1, 2, 3])
        prompt = f"{CONTEXT_OPEN}{payload}{CONTEXT_CLOSE}"
        assert parse_context_block(prompt) == {}

    def test_returns_empty_dict_when_json_is_string_not_dict(self) -> None:
        payload = json.dumps("just a string")
        prompt = f"{CONTEXT_OPEN}{payload}{CONTEXT_CLOSE}"
        assert parse_context_block(prompt) == {}

    def test_empty_block_returns_empty_dict(self) -> None:
        prompt = f"{CONTEXT_OPEN}{{}}{CONTEXT_CLOSE}"
        assert parse_context_block(prompt) == {}

    def test_last_block_wins_when_multiple_present(self) -> None:
        """When the prompt contains multiple CONTEXT_JSON blocks, the last one wins."""
        first = build_context_block({"which": "first"})
        second = build_context_block({"which": "second"})
        prompt = "Instructions. " + first + " More text. " + second
        result = parse_context_block(prompt)
        assert result["which"] == "second"


# ---------------------------------------------------------------------------
# strip_context_block
# ---------------------------------------------------------------------------


class TestStripContextBlock:
    def test_removes_block_from_end_of_prompt(self) -> None:
        instruction = "Analyse this job post."
        block = build_context_block({"key": "value"})
        prompt = instruction + block
        stripped = strip_context_block(prompt)
        assert stripped == instruction
        assert CONTEXT_OPEN not in stripped
        assert CONTEXT_CLOSE not in stripped

    def test_returns_prompt_unchanged_when_no_block(self) -> None:
        prompt = "Just a plain prompt."
        assert strip_context_block(prompt) == prompt

    def test_preserves_instruction_text_before_block(self) -> None:
        instruction = "You are an AI. Summarise the job. "
        block = build_context_block({"raw_job_post": "Engineer role at Acme."})
        stripped = strip_context_block(instruction + block)
        assert stripped.startswith("You are an AI.")

    def test_incomplete_block_returns_original(self) -> None:
        prompt = f"{CONTEXT_OPEN}{{\"key\": \"value\"}}"  # no close marker
        assert strip_context_block(prompt) == prompt
