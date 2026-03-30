"""
Evaluation engine for autocritic — both programmatic and LLM-as-judge.

This module provides two modes:
1. Programmatic checks: fast, no API key, pure Python logic → EvalResult
2. LLM-as-judge: sends artifacts to an LLM for rubric scoring → EvalResult

Both modes return the same EvalResult type so tests can mix freely.

Design principles:
- The judge is a function, not a framework
- Rubrics are plain Python dicts, not JSON schemas
- Scores are 0-4 integers per dimension, with required evidence
- The judge prompt is assembled from parts, not templated from strings

LLM provider routing:
- Model strings with no prefix default to Anthropic (e.g. "claude-sonnet-4-20250514")
- Prefixed strings route to other providers:
    "openai:gpt-4o"                        → OpenAI
    "google:gemini-2.5-pro"                → Google Gemini
    "xai:grok-3"                           → xAI (OpenAI-compatible)
    "ollama:llama3"                        → local Ollama (OpenAI-compatible)
    "openrouter:meta-llama/llama-3-70b"    → OpenRouter (OpenAI-compatible)
    "mlx:mlx-community/Meta-Llama-3-8B"   → local MLX via mlx_lm.server
    "llamacpp:model"                       → local llama.cpp server
    "local:my-model"                       → any local OpenAI-compatible server

Required env vars per provider:
- Anthropic:   ANTHROPIC_API_KEY
- OpenAI:      OPENAI_API_KEY
- Google:      GOOGLE_API_KEY
- xAI:         XAI_API_KEY
- Ollama:      (none — localhost:11434)
- OpenRouter:  OPENROUTER_API_KEY
- mlx:         (none — localhost:8080, start with: mlx_lm.server --model <hf_repo>)
- llamacpp:    (none — localhost:8080, start with: llama-server -m <model.gguf>)
- local:       LOCAL_LLM_URL (default http://localhost:8080/v1)
               LOCAL_LLM_API_KEY (optional, default "none")
"""

from __future__ import annotations

import base64
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DimensionScore:
    dimension: str
    score: int  # 0-4
    evidence: str


@dataclass
class EvalResult:
    eval_name: str
    scores: list[DimensionScore]
    failure_evidence: list[str]
    judge_reasoning: str
    passed: bool

    @property
    def total_score(self) -> int:
        return sum(s.score for s in self.scores)

    @property
    def max_score(self) -> int:
        return len(self.scores) * 4

    def summary(self) -> str:
        lines = [f"Eval: {self.eval_name}  {'PASS' if self.passed else 'FAIL'}  "
                 f"({self.total_score}/{self.max_score})"]
        for s in self.scores:
            lines.append(f"  {s.dimension}: {s.score}/4 — {s.evidence}")
        if self.failure_evidence:
            lines.append("  Failures:")
            for f in self.failure_evidence:
                lines.append(f"    - {f}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# LLM provider routing
# ---------------------------------------------------------------------------

# Provider configs: prefix → (base_url, api_key_env)
# Providers using the OpenAI-compatible API.
_OPENAI_COMPAT_PROVIDERS: dict[str, tuple[str | None, str | None]] = {
    "openai":      (None, "OPENAI_API_KEY"),                                # native OpenAI
    "xai":         ("https://api.x.ai/v1", "XAI_API_KEY"),
    "ollama":      ("http://localhost:11434/v1", None),                      # no key needed
    "openrouter":  ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "mlx":         ("http://localhost:8080/v1", None),                       # mlx_lm.server
    "llamacpp":    ("http://localhost:8080/v1", None),                       # llama-server
}


def _parse_provider(model: str) -> tuple[str, str]:
    """Split 'provider:model_name' → (provider, model_name).

    Bare model strings (no colon) default to 'anthropic'.
    """
    if ":" in model:
        provider, _, model_name = model.partition(":")
        return provider.lower(), model_name
    return "anthropic", model


def _call_anthropic(model: str, system: str, user: str,
                    max_tokens: int, temperature: float) -> str:
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "anthropic package required for Anthropic models. "
            "Install with: pip install anthropic"
        )
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def _call_openai_compat(model: str, system: str, user: str,
                        max_tokens: int, temperature: float,
                        base_url: str | None, api_key_env: str | None,
                        api_key_override: str | None = None) -> str:
    try:
        import openai
    except ImportError:
        raise ImportError(
            "openai package required for OpenAI-compatible models. "
            "Install with: pip install openai"
        )
    if api_key_override is not None:
        api_key = api_key_override
    elif api_key_env:
        api_key = os.environ.get(api_key_env)
    else:
        api_key = "ollama"
    client = openai.OpenAI(base_url=base_url, api_key=api_key)
    # Newer OpenAI models require max_completion_tokens; older ones
    # and third-party providers use max_tokens. Use the new name for
    # native OpenAI (base_url is None), fall back for everything else.
    token_kwarg = (
        {"max_completion_tokens": max_tokens}
        if base_url is None
        else {"max_tokens": max_tokens}
    )
    response = client.chat.completions.create(
        model=model,
        **token_kwarg,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content


def _call_google(model: str, system: str, user: str,
                 max_tokens: int, temperature: float) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError(
            "google-genai package required for Google models. "
            "Install with: pip install google-genai"
        )
    client = genai.Client()
    response = client.models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            temperature=temperature,
        ),
    )
    return response.text


def _call_llm(model: str, system: str, user: str,
              max_tokens: int = 2048, temperature: float = 0.0) -> str:
    """Route a model string to the appropriate LLM provider and return text."""
    provider, model_name = _parse_provider(model)

    if provider == "anthropic":
        return _call_anthropic(model_name, system, user, max_tokens, temperature)
    elif provider == "google":
        return _call_google(model_name, system, user, max_tokens, temperature)
    elif provider == "local":
        base_url = os.environ.get("LOCAL_LLM_URL", "http://localhost:8080/v1")
        api_key = os.environ.get("LOCAL_LLM_API_KEY", "none")
        return _call_openai_compat(
            model_name, system, user, max_tokens, temperature,
            base_url=base_url, api_key_env=None,
            api_key_override=api_key,
        )
    elif provider in _OPENAI_COMPAT_PROVIDERS:
        base_url, api_key_env = _OPENAI_COMPAT_PROVIDERS[provider]
        return _call_openai_compat(
            model_name, system, user, max_tokens, temperature,
            base_url, api_key_env,
        )
    else:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Supported: anthropic, google, local, {', '.join(_OPENAI_COMPAT_PROVIDERS)}"
        )


def _load_image(image_path: str | Path) -> tuple[str, str]:
    """Load an image file and return (base64_data, media_type)."""
    path = Path(image_path)
    suffix = path.suffix.lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(suffix, "image/png")
    b64 = base64.b64encode(path.read_bytes()).decode()
    return b64, media_type


def _call_anthropic_with_image(
    model: str, system: str, user: str,
    image_b64: str, media_type: str,
    max_tokens: int, temperature: float,
) -> str:
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "anthropic package required for Anthropic models. "
            "Install with: pip install anthropic"
        )
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_b64,
                    },
                },
                {"type": "text", "text": user},
            ],
        }],
    )
    return response.content[0].text


def _call_openai_compat_with_image(
    model: str, system: str, user: str,
    image_b64: str, media_type: str,
    max_tokens: int, temperature: float,
    base_url: str | None, api_key_env: str | None,
    api_key_override: str | None = None,
) -> str:
    try:
        import openai
    except ImportError:
        raise ImportError(
            "openai package required for OpenAI-compatible models. "
            "Install with: pip install openai"
        )
    if api_key_override is not None:
        api_key = api_key_override
    elif api_key_env:
        api_key = os.environ.get(api_key_env)
    else:
        api_key = "ollama"
    client = openai.OpenAI(base_url=base_url, api_key=api_key)
    image_url = f"data:{media_type};base64,{image_b64}"
    token_kwarg = (
        {"max_completion_tokens": max_tokens}
        if base_url is None
        else {"max_tokens": max_tokens}
    )
    response = client.chat.completions.create(
        model=model,
        **token_kwarg,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": user},
            ]},
        ],
    )
    return response.choices[0].message.content


def _call_google_with_image(
    model: str, system: str, user: str,
    image_b64: str, media_type: str,
    max_tokens: int, temperature: float,
) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError(
            "google-genai package required for Google models. "
            "Install with: pip install google-genai"
        )
    client = genai.Client()
    image_part = types.Part.from_bytes(
        data=base64.b64decode(image_b64),
        mime_type=media_type,
    )
    response = client.models.generate_content(
        model=model,
        contents=[image_part, user],
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            temperature=temperature,
        ),
    )
    return response.text


def _call_llm_with_image(
    model: str, system: str, user: str,
    image_path: str | Path,
    max_tokens: int = 4096, temperature: float = 0.0,
) -> str:
    """Route a model string to the appropriate LLM provider with image input."""
    provider, model_name = _parse_provider(model)
    image_b64, media_type = _load_image(image_path)

    if provider == "anthropic":
        return _call_anthropic_with_image(
            model_name, system, user, image_b64, media_type,
            max_tokens, temperature,
        )
    elif provider == "google":
        return _call_google_with_image(
            model_name, system, user, image_b64, media_type,
            max_tokens, temperature,
        )
    elif provider == "local":
        base_url = os.environ.get("LOCAL_LLM_URL", "http://localhost:8080/v1")
        api_key = os.environ.get("LOCAL_LLM_API_KEY", "none")
        return _call_openai_compat_with_image(
            model_name, system, user, image_b64, media_type,
            max_tokens, temperature,
            base_url=base_url, api_key_env=None,
            api_key_override=api_key,
        )
    elif provider in _OPENAI_COMPAT_PROVIDERS:
        base_url, api_key_env = _OPENAI_COMPAT_PROVIDERS[provider]
        return _call_openai_compat_with_image(
            model_name, system, user, image_b64, media_type,
            max_tokens, temperature, base_url, api_key_env,
        )
    else:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Supported: anthropic, google, local, {', '.join(_OPENAI_COMPAT_PROVIDERS)}"
        )


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def _parse_judge_response(raw: str) -> dict[str, Any]:
    """Extract JSON from an LLM response, handling markdown fences."""
    # Try to find JSON in code fences first
    match = re.search(r"```(?:json)?\s*\n(.*?)\n```", raw, re.DOTALL)
    text = match.group(1) if match else raw
    return json.loads(text)


def run_judge(
    eval_name: str,
    artifact_description: str,
    artifact_content: str,
    rubric_dimensions: list[str],
    failure_modes: list[str],
    pass_threshold: int,
    model: str = "claude-sonnet-4-20250514",
) -> EvalResult:
    """
    Run an LLM-as-judge evaluation.

    Args:
        eval_name: Human-readable name for this eval
        artifact_description: What is being evaluated (e.g., "a Wölfflin critic card")
        artifact_content: The actual content to judge (text, JSON, etc.)
        rubric_dimensions: List of dimension names to score (each 0-4)
        failure_modes: Known failure patterns to watch for
        pass_threshold: Minimum total score to pass

    Returns:
        EvalResult with per-dimension scores and pass/fail determination
    """
    dimensions_block = "\n".join(
        f"  {i+1}. {dim}: score 0 (absent/wrong) to 4 (excellent)"
        for i, dim in enumerate(rubric_dimensions)
    )
    failures_block = "\n".join(f"  - {fm}" for fm in failure_modes)

    system = (
        "You are an evaluation judge for an art-theory critic system. "
        "Your job is to score artifacts against a rubric with precision and evidence. "
        "Be strict. Generic or vague artifacts should score low. "
        "Artifacts that demonstrate specific, grounded knowledge of the theorist should score high.\n\n"
        "Return ONLY a JSON object with this exact structure:\n"
        '{"dimensions": {"dimension_name": {"score": N, "evidence": "..."}}, '
        '"failure_evidence": ["...", "..."], '
        '"reasoning": "..."}'
    )

    user = (
        f"## Evaluating: {artifact_description}\n\n"
        f"## Rubric Dimensions\n{dimensions_block}\n\n"
        f"## Known Failure Modes (check for these specifically)\n{failures_block}\n\n"
        f"## Artifact\n{artifact_content}\n\n"
        f"Score this artifact now. Be specific in your evidence."
    )

    raw = _call_llm(model, system, user)
    parsed = _parse_judge_response(raw)

    scores = []
    for dim in rubric_dimensions:
        dim_data = parsed.get("dimensions", {}).get(dim, {})
        scores.append(DimensionScore(
            dimension=dim,
            score=min(4, max(0, int(dim_data.get("score", 0)))),
            evidence=dim_data.get("evidence", "no evidence provided"),
        ))

    failure_evidence = parsed.get("failure_evidence", [])
    total = sum(s.score for s in scores)

    return EvalResult(
        eval_name=eval_name,
        scores=scores,
        failure_evidence=failure_evidence,
        judge_reasoning=parsed.get("reasoning", raw),
        passed=total >= pass_threshold,
    )


def run_comparative_judge(
    eval_name: str,
    description: str,
    artifact_a: str,
    artifact_b: str,
    comparison_dimensions: list[str],
    pass_threshold: int,
    model: str = "claude-sonnet-4-20250514",
) -> EvalResult:
    """
    Run a comparative eval — judge whether artifact_a is meaningfully
    different from artifact_b along the given dimensions.

    Used for lens_specificity (critic card vs. generic baseline) and
    differentiation (same critic on different images should produce
    different feedback).
    """
    dimensions_block = "\n".join(
        f"  {i+1}. {dim}: score 0 (identical) to 4 (sharply distinct)"
        for i, dim in enumerate(comparison_dimensions)
    )

    system = (
        "You are an evaluation judge comparing two artifacts for meaningful "
        "difference. Score how DISTINCT artifact A is from artifact B along "
        "each dimension. High scores mean A says things B could never say. "
        "Low scores mean A could be swapped for B without anyone noticing.\n\n"
        "Return ONLY a JSON object with this exact structure:\n"
        '{"dimensions": {"dimension_name": {"score": N, "evidence": "..."}}, '
        '"failure_evidence": ["...", "..."], '
        '"reasoning": "..."}'
    )

    user = (
        f"## Comparison: {description}\n\n"
        f"## Dimensions of Distinction\n{dimensions_block}\n\n"
        f"## Artifact A\n{artifact_a}\n\n"
        f"## Artifact B\n{artifact_b}\n\n"
        f"Score how distinct A is from B. Be specific."
    )

    raw = _call_llm(model, system, user)
    parsed = _parse_judge_response(raw)

    scores = []
    for dim in comparison_dimensions:
        dim_data = parsed.get("dimensions", {}).get(dim, {})
        scores.append(DimensionScore(
            dimension=dim,
            score=min(4, max(0, int(dim_data.get("score", 0)))),
            evidence=dim_data.get("evidence", "no evidence provided"),
        ))

    failure_evidence = parsed.get("failure_evidence", [])
    total = sum(s.score for s in scores)

    return EvalResult(
        eval_name=eval_name,
        scores=scores,
        failure_evidence=failure_evidence,
        judge_reasoning=parsed.get("reasoning", raw),
        passed=total >= pass_threshold,
    )


# ---------------------------------------------------------------------------
# Programmatic checks (no API key needed)
# ---------------------------------------------------------------------------

def run_programmatic_check(
    eval_name: str,
    checks: list[tuple[str, bool, str]],
) -> EvalResult:
    """
    Run a set of boolean checks and return a unified EvalResult.

    Each check is (dimension_name, passed: bool, evidence: str).
    A passing check scores 4; a failing check scores 0.
    The overall eval passes only if ALL checks pass.
    """
    scores = [
        DimensionScore(
            dimension=name,
            score=4 if passed else 0,
            evidence=evidence,
        )
        for name, passed, evidence in checks
    ]
    failures = [s.evidence for s in scores if s.score == 0]
    return EvalResult(
        eval_name=eval_name,
        scores=scores,
        failure_evidence=failures,
        judge_reasoning="programmatic check",
        passed=len(failures) == 0,
    )


def run_vocabulary_check(
    eval_name: str,
    text: str,
    distinctive_vocab: list[str],
    generic_vocab: list[str] | None = None,
    min_distinctive_ratio: float = 0.4,
) -> EvalResult:
    """
    Check that an artifact uses enough distinctive vocabulary and isn't
    dominated by generic terms.

    Returns an EvalResult with up to 2 dimensions:
    - "distinctive_coverage": ratio of distinctive terms found
    - "generic_dominance" (if generic_vocab provided): distinctive >= generic
    """
    text_lower = text.lower()
    distinctive_hits = [v for v in distinctive_vocab if v.lower() in text_lower]
    ratio = len(distinctive_hits) / len(distinctive_vocab) if distinctive_vocab else 0

    checks: list[tuple[str, bool, str]] = [
        (
            "distinctive_coverage",
            ratio >= min_distinctive_ratio,
            f"{len(distinctive_hits)}/{len(distinctive_vocab)} ({ratio:.0%}) distinctive terms found"
            + (f". Missing: {set(v.lower() for v in distinctive_vocab) - set(v.lower() for v in distinctive_hits)}"
               if ratio < min_distinctive_ratio else ""),
        ),
    ]

    if generic_vocab is not None:
        generic_hits = sum(1 for v in generic_vocab if v.lower() in text_lower)
        checks.append((
            "generic_dominance",
            len(distinctive_hits) >= generic_hits,
            f"distinctive={len(distinctive_hits)} vs generic={generic_hits}",
        ))

    return run_programmatic_check(eval_name, checks)


def run_structural_check(
    eval_name: str,
    card: dict,
    required_top_level: list[str],
    criteria_key: str = "criteria",
    required_criteria_fields: list[str] | None = None,
    min_criteria: int = 1,
) -> EvalResult:
    """
    Validate the shape of a critic card.

    Checks:
    - All required_top_level fields exist
    - The criteria/elements array has at least min_criteria entries
    - Each criterion has all required_criteria_fields
    """
    checks: list[tuple[str, bool, str]] = []

    # Top-level fields
    missing_top = [f for f in required_top_level if f not in card]
    checks.append((
        "top_level_fields",
        len(missing_top) == 0,
        f"missing: {missing_top}" if missing_top else f"all {len(required_top_level)} fields present",
    ))

    # Criteria count
    items = card.get(criteria_key, [])
    checks.append((
        f"{criteria_key}_count",
        len(items) >= min_criteria,
        f"found {len(items)}, need >= {min_criteria}",
    ))

    # Per-criterion fields
    if required_criteria_fields and items:
        bad = []
        for item in items:
            item_id = item.get("element_id", item.get("criterion_id", "?"))
            missing = [f for f in required_criteria_fields if f not in item]
            if missing:
                bad.append(f"{item_id} missing {missing}")
        checks.append((
            "criteria_fields",
            len(bad) == 0,
            "; ".join(bad) if bad else "all criteria have required fields",
        ))

    return run_programmatic_check(eval_name, checks)
