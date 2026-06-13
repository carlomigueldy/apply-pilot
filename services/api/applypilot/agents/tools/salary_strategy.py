"""salary_strategy tool — deterministic salary negotiation guidance.

A pure, network-free function that produces a recommended range and rationale
by comparing the candidate's monthly salary targets against the salary text
extracted from a job posting.

All values are normalised to **monthly USD** before comparison.  The function
is fully deterministic: identical inputs always produce identical outputs.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Internal parsing helpers
# ---------------------------------------------------------------------------

# Matches a USD amount like "$4,000", "$100k", "4000", "4.5K"
_SALARY_NUMBER_RE = re.compile(r"\$?\s?(\d[\d,]*(?:\.\d+)?)\s*([kK]?)")

# Matches a time-period qualifier anywhere in the salary text
_PERIOD_RE = re.compile(
    r"\b(?:per\s+)?"
    r"(hr|hour|hourly|day|daily|week|weekly|month|monthly|mo|yr|year|annual|annum)"
    r"\b",
    re.IGNORECASE,
)

# Industry-standard conversion constants
_HOURS_PER_MONTH: float = 173.33
_WORKING_DAYS_PER_MONTH: float = 21.67
_WEEKS_PER_MONTH: float = 4.33


def _match_to_float(m: re.Match[str]) -> float:
    """Parse a ``_SALARY_NUMBER_RE`` match into a plain float, expanding k/K suffix."""
    raw = float(m.group(1).replace(",", ""))
    if m.group(2) in ("k", "K"):
        raw *= 1_000
    return raw


def _parse_range(text: str) -> tuple[float, float] | None:
    """Extract the first and last numeric salary values from *text*.

    Returns:
        ``(low, high)`` when at least one number is found; ``None`` otherwise.
        When only a single number is found, both elements of the tuple are equal.
    """
    matches = list(_SALARY_NUMBER_RE.finditer(text))
    # Discard zero-value matches (e.g. spurious "$0" artefacts)
    matches = [m for m in matches if _match_to_float(m) > 0]
    if not matches:
        return None
    if len(matches) == 1:
        v = _match_to_float(matches[0])
        return v, v
    return _match_to_float(matches[0]), _match_to_float(matches[-1])


def _detect_period(text: str) -> str:
    """Detect the salary cadence from *text*.

    Returns:
        One of ``"hourly"``, ``"daily"``, ``"weekly"``, ``"monthly"``,
        ``"annual"``, or ``"unknown"``.
    """
    m = _PERIOD_RE.search(text)
    if not m:
        return "unknown"
    token = m.group(1).lower()
    if token in ("hr", "hour", "hourly"):
        return "hourly"
    if token in ("day", "daily"):
        return "daily"
    if token in ("week", "weekly"):
        return "weekly"
    if token in ("month", "monthly", "mo"):
        return "monthly"
    if token in ("yr", "year", "annual", "annum"):
        return "annual"
    return "unknown"


def _to_monthly(amount: float, period: str) -> float:
    """Convert *amount* to its monthly USD equivalent.

    When *period* is ``"unknown"``, applies a heuristic: values ≥ 10 000 are
    treated as annual (divided by 12); smaller values are treated as already
    monthly.
    """
    if period == "hourly":
        return round(amount * _HOURS_PER_MONTH, 2)
    if period == "daily":
        return round(amount * _WORKING_DAYS_PER_MONTH, 2)
    if period == "weekly":
        return round(amount * _WEEKS_PER_MONTH, 2)
    if period == "monthly":
        return round(amount, 2)
    if period == "annual":
        return round(amount / 12, 2)
    # Heuristic for "unknown"
    return round(amount / 12 if amount >= 10_000 else amount, 2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def salary_strategy(
    target_min: int | float,
    target_max: int | float,
    job_salary_text: str,
    remote_preference: str | None = None,
) -> dict[str, object]:
    """Return a salary negotiation strategy for a given job posting.

    Normalises *job_salary_text* to monthly USD and compares it against the
    candidate's target band (*target_min* … *target_max*) to produce an
    actionable, deterministic recommendation.

    Args:
        target_min: Candidate's minimum acceptable **monthly** salary (USD).
        target_max: Candidate's ideal **monthly** salary ceiling (USD).
        job_salary_text: Raw salary text from the job posting, e.g.
            ``"$4000/mo"``, ``"$100k–$150k/yr"``, ``"$45/hr"``.
        remote_preference: Optional work-arrangement preference string (e.g.
            ``"remote_only"``, ``"hybrid"``, ``"onsite"``).  When provided, an
            arrangement-specific note is appended to the rationale.

    Returns:
        A :class:`dict` with three keys:

        * ``"recommended_range"`` (:class:`str`) — the negotiation-ready range
          to quote, expressed as monthly USD (e.g. ``"$5,500–$7,500/mo"``).
        * ``"rationale"`` (:class:`str`) — a concise, plain-English explanation
          of the strategy.
        * ``"below_target"`` (:class:`bool`) — ``True`` when the job's posted
          salary ceiling normalises to below *target_min*, signalling a mismatch
          that should be surfaced to the user.
    """
    tmin = float(target_min)
    tmax = float(target_max)

    period = _detect_period(job_salary_text)
    salary_range = _parse_range(job_salary_text)

    job_low: float | None
    job_high: float | None
    if salary_range is not None:
        job_low = _to_monthly(salary_range[0], period)
        job_high = _to_monthly(salary_range[1], period)
    else:
        job_low = job_high = None

    # --- below_target flag ---------------------------------------------------
    below_target = job_high is not None and job_high < tmin

    # --- recommended_range ---------------------------------------------------
    if job_low is not None and job_high is not None:
        midpoint = (job_low + job_high) / 2

        if job_low > tmax:
            # Posted range is entirely above the candidate's target; anchor to
            # target_max to avoid under-asking when the job pays generously.
            rec_low = tmax
            rec_high = job_high
        else:
            # Anchor recommended low at the higher of target_min or 95 % of the
            # job midpoint (to stay competitive), and high at target_max or the
            # job ceiling, whichever is greater.
            rec_low = max(tmin, midpoint * 0.95)
            rec_high = max(tmax, job_high)

        recommended_range = f"${rec_low:,.0f}–${rec_high:,.0f}/mo"
    else:
        # No parseable salary in the posting — fall back to the candidate's band.
        recommended_range = f"${tmin:,.0f}–${tmax:,.0f}/mo"

    # --- rationale -----------------------------------------------------------
    parts: list[str] = []

    if job_low is not None and job_high is not None:
        if job_low == job_high:
            parts.append(f"The posted salary normalises to ${job_high:,.0f}/mo.")
        else:
            parts.append(
                f"The posted salary normalises to ${job_low:,.0f}–${job_high:,.0f}/mo."
            )
    else:
        parts.append("No parseable salary range was found in the job posting.")

    if below_target:
        parts.append(
            f"The posted ceiling (${job_high:,.0f}/mo) falls below your floor"
            f" (${tmin:,.0f}/mo). Clarify total compensation, equity, or benefits"
            " before proceeding, or decline if the gap is non-negotiable."
        )
    else:
        if job_high is not None and job_high >= tmin:
            parts.append(
                f"The posting overlaps your target band (${tmin:,.0f}–${tmax:,.0f}/mo);"
                " open the negotiation at or above the midpoint to preserve room to land."
            )
        else:
            parts.append(
                f"Anchor your ask to your preferred range: ${tmin:,.0f}–${tmax:,.0f}/mo."
            )

    _REMOTE_NOTES: dict[str, str] = {
        "remote_only": (
            "As a fully-remote role, benchmark against distributed-team comps"
            " globally rather than a single metro area."
        ),
        "hybrid": (
            "Hybrid roles may carry geographically-adjusted bands;"
            " factor in commuting costs when evaluating the offer."
        ),
        "onsite": (
            "On-site roles often include location-specific cost-of-living adjustments;"
            " verify the base against local market data."
        ),
    }
    if remote_preference:
        note = _REMOTE_NOTES.get(
            str(remote_preference).lower(),
            f"Remote preference '{remote_preference}' noted; adjust comparables accordingly.",
        )
        parts.append(note)

    return {
        "recommended_range": recommended_range,
        "rationale": " ".join(parts),
        "below_target": below_target,
    }
