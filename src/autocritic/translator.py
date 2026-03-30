"""
LLM-driven parameter translation.

Takes a scored critique + current parameter state + parameter space definition
and asks an LLM to reason about what parameters should change. No hardcoded
mapping tables — the LLM understands both the aesthetic language and the
parameter semantics.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from autocritic.scoring import ScoredCritique


# ---------------------------------------------------------------------------
# Parameter space definition
# ---------------------------------------------------------------------------

@dataclass
class ParamSpec:
    """Definition of a single tunable parameter."""
    name: str
    type: str           # "int", "float", "enum"
    range: tuple        # (min, max) for numeric, or tuple of valid values for enum
    default: Any
    description: str    # plain English: what this does visually


@dataclass
class ParamSpace:
    """Definition of an entire parameter space for a generative system."""
    specs: list[ParamSpec]

    def describe(self) -> str:
        """Format the parameter space for LLM consumption."""
        lines = []
        for s in self.specs:
            if s.type == "enum":
                range_str = f"options: {', '.join(str(v) for v in s.range)}"
            else:
                range_str = f"range: {s.range[0]} to {s.range[1]}"
            lines.append(
                f"- **{s.name}** ({s.type}, {range_str}, default={s.default}): "
                f"{s.description}"
            )
        return "\n".join(lines)

    def clamp(self, params: dict[str, Any]) -> dict[str, Any]:
        """Enforce valid ranges on a parameter dict."""
        clamped = dict(params)
        spec_map = {s.name: s for s in self.specs}
        for name, value in clamped.items():
            if name not in spec_map:
                continue
            spec = spec_map[name]
            if spec.type == "enum":
                if value not in spec.range:
                    clamped[name] = spec.default
            elif spec.type in ("int", "float"):
                lo, hi = spec.range
                if spec.type == "int":
                    value = int(round(value))
                clamped[name] = max(lo, min(hi, value))
        return clamped

    def defaults(self) -> dict[str, Any]:
        """Return default values for all parameters."""
        return {s.name: s.default for s in self.specs}


# ---------------------------------------------------------------------------
# Translation result
# ---------------------------------------------------------------------------

@dataclass
class TranslationResult:
    """Output from the parameter translator."""
    deltas: dict[str, Any]   # parameter name -> new target value
    reasoning: str           # LLM's reasoning about the changes
    raw_text: str            # full LLM response


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_translator_system_prompt() -> str:
    return (
        "You are a parameter tuner for a generative art system. "
        "You receive an art-theoretic critique of the current output and "
        "the system's tunable parameters. Your job is to reason about which "
        "parameters to adjust to address the critique's findings.\n\n"
        "Rules:\n"
        "- Change at most 3 parameters per iteration (focus on the most impactful)\n"
        "- Respect the preservations — do not change parameters that would "
        "undo things the critic said to keep\n"
        "- Stay within parameter ranges\n"
        "- For numeric parameters, output the NEW target value (not a delta)\n"
        "- For enum parameters, output the new value\n"
        "- Think step by step about which critique points map to which parameters\n"
        "- If the critique is mostly positive, make small adjustments or none"
    )


def _build_translator_user_prompt(
    scored_critique: ScoredCritique,
    current_params: dict[str, Any],
    param_space: ParamSpace,
    preservations: list[str] | None = None,
) -> str:
    lines = ["## Critique Summary"]

    # Axis scores
    if scored_critique.axis_scores:
        lines.append("")
        lines.append("Axis scores:")
        for s in scored_critique.axis_scores:
            lines.append(f"  {s.label}: {s.score:.2f} — {s.reasoning}")

    # Directives
    if scored_critique.critique.directives:
        lines.append("")
        lines.append("Directives for next iteration:")
        for d in scored_critique.critique.directives:
            lines.append(f"  - {d}")

    # Weaknesses
    if scored_critique.critique.weaknesses:
        lines.append("")
        lines.append("Weaknesses:")
        for w in scored_critique.critique.weaknesses:
            lines.append(f"  - {w}")

    # Preservations
    if preservations:
        lines.append("")
        lines.append("## Preservations (do NOT undo these)")
        for p in preservations:
            lines.append(f"  - {p}")
    elif scored_critique.critique.strengths:
        lines.append("")
        lines.append("## Preservations (do NOT undo these)")
        for s in scored_critique.critique.strengths:
            lines.append(f"  - {s}")

    # Current parameters
    lines.append("")
    lines.append("## Current Parameters")
    lines.append("```json")
    lines.append(json.dumps(current_params, indent=2))
    lines.append("```")

    # Parameter space
    lines.append("")
    lines.append("## Parameter Space")
    lines.append(param_space.describe())

    # Output format
    lines.extend([
        "",
        "## Output",
        "Reason step by step, then output exactly this JSON format:",
        "",
        "```json",
        "{",
        '  "deltas": {"param_name": new_value, ...},',
        '  "reasoning": "one paragraph explaining your choices"',
        "}",
        "```",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------

def translate_critique_to_params(
    scored_critique: ScoredCritique,
    current_params: dict[str, Any],
    param_space: ParamSpace,
    model: str = "claude-sonnet-4-20250514",
    preservations: list[str] | None = None,
) -> TranslationResult:
    """Ask the LLM to reason about parameter changes.

    Returns a TranslationResult with target values for changed parameters.
    """
    from autocritic.llm import _call_llm

    system = _build_translator_system_prompt()
    user = _build_translator_user_prompt(
        scored_critique, current_params, param_space, preservations,
    )

    raw = _call_llm(
        model=model,
        system=system,
        user=user,
        max_tokens=2048,
        temperature=0.0,
    )

    # Parse JSON from response
    deltas, reasoning = _parse_translation(raw)

    return TranslationResult(
        deltas=deltas,
        reasoning=reasoning,
        raw_text=raw,
    )


def _parse_translation(raw: str) -> tuple[dict[str, Any], str]:
    """Extract deltas and reasoning from the translator response."""
    # Find fenced JSON blocks
    pattern = r"```json\s*\n(.*?)```"
    matches = re.findall(pattern, raw, re.DOTALL)

    if matches:
        raw_json = matches[-1].strip()
    else:
        # Try to find bare JSON
        pattern2 = r"\{[^{}]*\"deltas\"[^{}]*\{.*?\}.*?\}"
        m = re.search(pattern2, raw, re.DOTALL)
        if m:
            raw_json = m.group(0)
        else:
            return {}, raw.strip()

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        return {}, raw.strip()

    deltas = data.get("deltas", {})
    reasoning = data.get("reasoning", "")

    return deltas, reasoning


# ---------------------------------------------------------------------------
# Delta application
# ---------------------------------------------------------------------------

def apply_deltas(
    current_params: dict[str, Any],
    deltas: dict[str, Any],
    param_space: ParamSpace,
    damping: float = 1.0,
) -> dict[str, Any]:
    """Apply parameter changes with optional damping.

    For numeric params: new = current + damping * (target - current)
    For enum params: set directly (damping doesn't apply).
    Clamps all values to valid ranges.
    """
    result = dict(current_params)
    spec_map = {s.name: s for s in param_space.specs}

    for name, target in deltas.items():
        if name not in spec_map:
            continue
        spec = spec_map[name]

        if spec.type == "enum":
            if target in spec.range:
                result[name] = target
        elif spec.type in ("int", "float"):
            current = result.get(name, spec.default)
            target = float(target)
            new_val = current + damping * (target - current)
            if spec.type == "int":
                new_val = int(round(new_val))
            result[name] = new_val

    return param_space.clamp(result)
