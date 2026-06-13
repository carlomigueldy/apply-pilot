"""Unit tests for the salary_strategy tool.

Verifies:
- below_target=True when job ceiling < candidate floor.
- below_target=False when job ceiling >= candidate floor.
- recommended_range anchors correctly for below/at/above-target scenarios.
- Period parsing: hourly, daily, weekly, monthly, annual, unknown.
- Remote/hybrid/onsite notes appended to rationale when preference provided.
- No parseable salary -> falls back to candidate band.
- Determinism: same inputs always produce identical outputs.
"""

from __future__ import annotations

from applypilot.agents.tools.salary_strategy import salary_strategy


class TestSalaryStrategyBelowTarget:
    def test_job_ceiling_below_candidate_floor_flags_below_target(self) -> None:
        result = salary_strategy(
            target_min=8_000,
            target_max=10_000,
            job_salary_text="$3,000 - $5,000 per month",
        )
        assert result["below_target"] is True

    def test_rationale_mentions_floor_when_below_target(self) -> None:
        result = salary_strategy(
            target_min=8_000,
            target_max=10_000,
            job_salary_text="$3,000 - $5,000 per month",
        )
        assert "$8,000" in result["rationale"] or "floor" in result["rationale"].lower()

    def test_recommended_range_still_present_when_below_target(self) -> None:
        result = salary_strategy(
            target_min=8_000,
            target_max=10_000,
            job_salary_text="$3,000 - $5,000 per month",
        )
        assert "recommended_range" in result
        assert result["recommended_range"]  # non-empty


class TestSalaryStrategyAtTarget:
    def test_job_at_target_is_not_below(self) -> None:
        result = salary_strategy(
            target_min=8_000,
            target_max=10_000,
            job_salary_text="$8,000 - $10,000 per month",
        )
        assert result["below_target"] is False

    def test_rationale_mentions_target_band(self) -> None:
        result = salary_strategy(
            target_min=8_000,
            target_max=10_000,
            job_salary_text="$8,000 - $10,000 per month",
        )
        assert "overlap" in result["rationale"].lower() or "$8,000" in result["rationale"]


class TestSalaryStrategyAboveTarget:
    def test_job_above_target_ceiling_is_not_below(self) -> None:
        result = salary_strategy(
            target_min=5_000,
            target_max=7_000,
            job_salary_text="$10,000 - $15,000 per month",
        )
        assert result["below_target"] is False

    def test_recommended_range_anchors_at_target_max_when_job_above(self) -> None:
        result = salary_strategy(
            target_min=5_000,
            target_max=7_000,
            job_salary_text="$10,000 - $15,000 per month",
        )
        # rec_low anchors to tmax when job is above
        assert "$7,000" in result["recommended_range"]


class TestSalaryStrategyPeriodParsing:
    def test_annual_salary_converted_to_monthly(self) -> None:
        result = salary_strategy(
            target_min=5_000,
            target_max=10_000,
            job_salary_text="$120,000 per year",
        )
        # $120,000/yr = $10,000/mo -> at target, not below
        assert result["below_target"] is False

    def test_hourly_salary_converted_to_monthly(self) -> None:
        result = salary_strategy(
            target_min=5_000,
            target_max=10_000,
            job_salary_text="$40 per hour",
        )
        # $40 * 173.33 ~ $6,933/mo -> within range
        assert result["below_target"] is False

    def test_k_suffix_annual_parsed_correctly(self) -> None:
        result = salary_strategy(
            target_min=5_000,
            target_max=8_000,
            job_salary_text="$60k - $90k/yr",
        )
        # $90k/yr = $7,500/mo -> within range
        assert result["below_target"] is False

    def test_monthly_salary_text(self) -> None:
        result = salary_strategy(
            target_min=5_000,
            target_max=8_000,
            job_salary_text="$6,000/mo",
        )
        assert result["below_target"] is False

    def test_weekly_salary_converted(self) -> None:
        result = salary_strategy(
            target_min=5_000,
            target_max=8_000,
            job_salary_text="$2,000 per week",
        )
        # $2,000 * 4.33 = $8,666/mo -> above target max, not below
        assert result["below_target"] is False


class TestSalaryStrategyNoSalaryInPosting:
    def test_no_parseable_salary_falls_back_to_candidate_band(self) -> None:
        result = salary_strategy(
            target_min=5_000,
            target_max=8_000,
            job_salary_text="Salary to be discussed during the interview process.",
        )
        assert result["below_target"] is False
        assert "$5,000" in result["recommended_range"]
        assert "$8,000" in result["recommended_range"]

    def test_rationale_notes_unparseable_salary(self) -> None:
        result = salary_strategy(
            target_min=5_000,
            target_max=8_000,
            job_salary_text="Competitive salary offered.",
        )
        assert "No parseable salary" in result["rationale"]


class TestSalaryStrategyRemoteNotes:
    def test_remote_note_appended(self) -> None:
        result = salary_strategy(
            target_min=5_000,
            target_max=8_000,
            job_salary_text="$6,000/mo",
            remote_preference="remote_only",
        )
        assert "remote" in result["rationale"].lower() or "distributed" in result["rationale"].lower()

    def test_hybrid_note_appended(self) -> None:
        result = salary_strategy(
            target_min=5_000,
            target_max=8_000,
            job_salary_text="$6,000/mo",
            remote_preference="hybrid",
        )
        assert "hybrid" in result["rationale"].lower() or "commut" in result["rationale"].lower()

    def test_onsite_note_appended(self) -> None:
        result = salary_strategy(
            target_min=5_000,
            target_max=8_000,
            job_salary_text="$6,000/mo",
            remote_preference="onsite",
        )
        assert "on-site" in result["rationale"].lower() or "cost-of-living" in result["rationale"].lower()

    def test_no_remote_preference_no_remote_note(self) -> None:
        result = salary_strategy(
            target_min=5_000,
            target_max=8_000,
            job_salary_text="$6,000/mo",
        )
        # Without remote_preference, none of the remote-note phrases should appear
        rationale = result["rationale"]
        assert "distributed" not in rationale and "commut" not in rationale


class TestSalaryStrategyDeterminism:
    def test_same_inputs_produce_identical_output(self) -> None:
        kwargs = {
            "target_min": 6_000,
            "target_max": 9_000,
            "job_salary_text": "$80,000 - $110,000 per year",
            "remote_preference": "remote_only",
        }
        r1 = salary_strategy(**kwargs)
        r2 = salary_strategy(**kwargs)
        assert r1 == r2

    def test_output_has_required_keys(self) -> None:
        result = salary_strategy(5_000, 8_000, "$6,000/mo")
        assert set(result.keys()) == {"recommended_range", "rationale", "below_target"}

    def test_below_target_is_bool(self) -> None:
        result = salary_strategy(5_000, 8_000, "$6,000/mo")
        assert isinstance(result["below_target"], bool)

    def test_rationale_is_non_empty_string(self) -> None:
        result = salary_strategy(5_000, 8_000, "$6,000/mo")
        assert isinstance(result["rationale"], str)
        assert len(result["rationale"]) > 0
