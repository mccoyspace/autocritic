"""
Critic runtime: load a critic card and use it to evaluate images.

Usage:
    from autocritic.critic import load_critic, critique_image

    critic = load_critic("critics/wolfflin.json")
    result = critique_image(critic, "path/to/image.png")
    print(result.summary())

    # Compare iterations:
    result = compare_iterations(critic, "v1.png", "v2.png")
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Avoid importing judge at module level — keep it lazy for fast imports.


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class CriticCard:
    """A loaded critic card ready for use."""
    critic_id: str
    theorist: str
    book: str
    thesis: str
    items: list[dict[str, Any]]       # the criteria/concepts/elements/etc.
    items_key: str                     # "criteria", "core_concepts", etc.
    item_id_field: str                 # "criterion_id", "concept_id", etc.
    anti_goals: list[str]
    tensions: list[dict[str, str]]
    raw: dict[str, Any]               # the full parsed JSON

    @property
    def label(self) -> str:
        return f"{self.theorist} ({self.book})"


@dataclass
class CritiqueResult:
    """Structured output from a critic evaluating an image."""
    critic_id: str
    image_path: str
    model: str
    raw_text: str                      # the full LLM response
    lens_summary: str = ""
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    criterion_notes: list[dict[str, str]] = field(default_factory=list)
    directives: list[str] = field(default_factory=list)
    preservations: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Critique by {self.critic_id} | model={self.model}",
            f"Image: {self.image_path}",
            "",
        ]
        if self.lens_summary:
            lines.append(f"Lens: {self.lens_summary}")
            lines.append("")
        if self.strengths:
            lines.append("Strengths:")
            for s in self.strengths:
                lines.append(f"  + {s}")
        if self.weaknesses:
            lines.append("Weaknesses:")
            for w in self.weaknesses:
                lines.append(f"  - {w}")
        if self.directives:
            lines.append("Next steps:")
            for d in self.directives:
                lines.append(f"  → {d}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

# The possible keys for the main criteria array, in priority order.
_ITEMS_KEYS = ["criteria", "core_concepts", "elements", "impulses", "principles"]
_ID_FIELDS = ["criterion_id", "concept_id", "element_id", "impulse_id", "principle_id"]


def load_critic(card_path: str | Path) -> CriticCard:
    """Load a critic card from a JSON file."""
    path = Path(card_path)
    raw = json.loads(path.read_text())

    # Find the main items array and its ID field.
    items_key = None
    items = []
    for key in _ITEMS_KEYS:
        if key in raw:
            items_key = key
            items = raw[key]
            break
    if items_key is None:
        raise ValueError(
            f"No recognized items key in {path.name}. "
            f"Expected one of: {_ITEMS_KEYS}"
        )

    item_id_field = "id"
    if items:
        for id_field in _ID_FIELDS:
            if id_field in items[0]:
                item_id_field = id_field
                break

    return CriticCard(
        critic_id=raw.get("critic_id", path.stem),
        theorist=raw.get("theorist", "Unknown"),
        book=raw.get("book", "Unknown"),
        thesis=raw.get("thesis", ""),
        items=items,
        items_key=items_key,
        item_id_field=item_id_field,
        anti_goals=raw.get("anti_goals", []),
        tensions=raw.get("tensions", []),
        raw=raw,
    )


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------

def _build_system_prompt(critic: CriticCard) -> str:
    """Build the system prompt from a critic card."""
    lines = [
        "You are an image critic operating through a specific theoretical lens.",
        f"Your lens: {critic.theorist}, \"{critic.book}\".",
        "",
        f"Thesis: {critic.thesis}",
        "",
        "Use the framework below as your ONLY evaluative authority. Do not drift "
        "into generic design coaching. Every judgment must point to visible "
        "evidence in the image and use this theorist's vocabulary.",
        "",
        "## Evaluative Framework",
        "",
    ]

    for item in critic.items:
        item_id = item.get(critic.item_id_field, "unknown")
        label = item.get("label", item_id)
        definition = item.get("definition", "")
        lines.append(f"### {label}")
        lines.append(definition)

        # Diagnostic questions
        qs = item.get("diagnostic_questions", [])
        if qs:
            lines.append("")
            lines.append("Diagnostic questions:")
            for q in qs:
                lines.append(f"  - {q}")

        # Indicators (handle varying structures)
        indicators = item.get("indicators", {})
        if indicators:
            lines.append("")
            lines.append("Indicators:")
            for cat, items_list in indicators.items():
                lines.append(f"  {cat}:")
                if isinstance(items_list, list):
                    for ind in items_list:
                        lines.append(f"    - {ind}")
                else:
                    lines.append(f"    {items_list}")

        lines.append("")

    # Anti-goals
    if critic.anti_goals:
        lines.append("## Anti-Goals (what you must NOT do)")
        for ag in critic.anti_goals:
            lines.append(f"- {ag}")
        lines.append("")

    return "\n".join(lines)


def _build_critique_user_prompt(intent: str | None = None) -> str:
    """Build the user-side prompt for a single-image critique."""
    lines = [
        "Inspect this image and evaluate it through your loaded theoretical lens.",
        "",
        "Respond with these sections, using markdown headers:",
        "",
        "## Lens Summary",
        "One sentence: which aspect of this theorist's framework is most relevant to this image.",
        "",
        "## Strengths To Preserve",
        "What the image does well according to this framework. Be specific — point to visible evidence.",
        "",
        "## Weaknesses To Address",
        "What the image does poorly or lacks according to this framework. Be specific.",
        "",
        "## Criterion Notes",
        "Brief observations for each criterion/concept in the framework. Use the framework's own terms.",
        "",
        "## Next Iteration Directives",
        "3-5 concrete, prioritized changes for a software-driven image generator. "
        "Each directive should be specific enough to act on. "
        "Name what should change AND what should be preserved.",
    ]

    if intent:
        lines.extend([
            "",
            f"## Project Intent",
            f"The creator's intent: {intent}",
            "Factor this into your evaluation where relevant.",
        ])

    return "\n".join(lines)


def _build_comparison_user_prompt(
    prev_critique_text: str | None = None,
) -> str:
    """Build the user-side prompt for comparing two iterations."""
    lines = [
        "You are comparing two iterations of an image using a fixed critical lens.",
        "The first image is the PREVIOUS iteration. The second image is the CURRENT iteration.",
        "",
        "Identify what improved, what regressed, and what the next iteration should prioritize.",
        "Do NOT reset the analysis from zero — compare against the previous state.",
        "",
        "Respond with these sections, using markdown headers:",
        "",
        "## Progress Since Last Iteration",
        "What improved from the previous image to the current one.",
        "",
        "## Regressions Or New Problems",
        "What got worse or what new issues appeared.",
        "",
        "## Criteria Still Unresolved",
        "What remains unaddressed from the theoretical framework.",
        "",
        "## Highest-Priority Next Changes",
        "The smallest set of changes likely to matter most. Reduce, don't expand.",
        "",
        "## Elements That Must Be Preserved",
        "Gains from previous iterations that must not be lost.",
    ]

    if prev_critique_text:
        lines.extend([
            "",
            "## Previous Critique For Reference",
            prev_critique_text,
        ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _parse_critique(raw: str) -> dict[str, Any]:
    """Parse a structured critique response into sections."""
    sections: dict[str, str] = {}
    current_header = ""
    current_lines: list[str] = []

    for line in raw.split("\n"):
        if line.startswith("## "):
            if current_header:
                sections[current_header] = "\n".join(current_lines).strip()
            current_header = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_header:
        sections[current_header] = "\n".join(current_lines).strip()

    return sections


def _extract_bullet_list(text: str) -> list[str]:
    """Extract bullet points from a section of text."""
    items = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith(("- ", "* ", "• ", "→ ")):
            items.append(stripped[2:].strip())
        elif stripped and len(stripped) > 10 and not stripped.startswith("#"):
            # Non-bullet substantial lines
            items.append(stripped)
    return items


def _extract_criterion_notes(text: str) -> list[dict[str, str]]:
    """Extract per-criterion notes, handling ### sub-headers or bold labels."""
    notes = []
    current_label = ""
    current_lines: list[str] = []

    for line in text.split("\n"):
        if line.startswith("### "):
            if current_label:
                notes.append({
                    "criterion": current_label,
                    "note": "\n".join(current_lines).strip(),
                })
            current_label = line[4:].strip()
            current_lines = []
        elif line.strip().startswith("**") and line.strip().endswith("**"):
            if current_label:
                notes.append({
                    "criterion": current_label,
                    "note": "\n".join(current_lines).strip(),
                })
            current_label = line.strip().strip("*").strip()
            current_lines = []
        elif line.strip().startswith("**") and "**" in line.strip()[2:]:
            # Bold label followed by content: **Label**: content
            if current_label:
                notes.append({
                    "criterion": current_label,
                    "note": "\n".join(current_lines).strip(),
                })
            parts = line.strip().split("**", 2)
            if len(parts) >= 3:
                current_label = parts[1].strip().rstrip(":")
                current_lines = [parts[2].lstrip(": ").strip()]
            else:
                current_lines.append(line)
        else:
            current_lines.append(line)

    if current_label:
        notes.append({
            "criterion": current_label,
            "note": "\n".join(current_lines).strip(),
        })

    return notes


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def critique_image(
    critic: CriticCard,
    image_path: str | Path,
    model: str = "claude-sonnet-4-20250514",
    intent: str | None = None,
) -> CritiqueResult:
    """
    Critique a single image through a loaded critic's lens.

    Args:
        critic: A loaded CriticCard
        image_path: Path to the image file
        model: LLM model string (supports all providers via prefix routing)
        intent: Optional project intent to factor into the evaluation

    Returns:
        CritiqueResult with structured sections and the raw response
    """
    from autocritic.llm import _call_llm_with_image

    system = _build_system_prompt(critic)
    user = _build_critique_user_prompt(intent)

    raw = _call_llm_with_image(
        model=model,
        system=system,
        user=user,
        image_path=image_path,
        max_tokens=4096,
        temperature=0.0,
    )

    sections = _parse_critique(raw)

    return CritiqueResult(
        critic_id=critic.critic_id,
        image_path=str(image_path),
        model=model,
        raw_text=raw,
        lens_summary=sections.get("Lens Summary", ""),
        strengths=_extract_bullet_list(
            sections.get("Strengths To Preserve", "")
        ),
        weaknesses=_extract_bullet_list(
            sections.get("Weaknesses To Address", "")
        ),
        criterion_notes=_extract_criterion_notes(
            sections.get("Criterion Notes", "")
        ),
        directives=_extract_bullet_list(
            sections.get("Next Iteration Directives", "")
        ),
        preservations=[],  # populated in compare_iterations
    )


def compare_iterations(
    critic: CriticCard,
    prev_image_path: str | Path,
    curr_image_path: str | Path,
    prev_critique: CritiqueResult | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> CritiqueResult:
    """
    Compare two iterations of an image through a loaded critic's lens.

    The LLM sees both images and the previous critique (if provided),
    and produces a comparison focused on progress, regressions, and next steps.
    """
    from autocritic.llm import _call_llm_with_image, _load_image

    system = _build_system_prompt(critic)
    user = _build_comparison_user_prompt(
        prev_critique_text=prev_critique.raw_text if prev_critique else None,
    )

    # For comparison, we need to send two images. Build the messages manually.
    provider_mod = model  # keep the full model string for routing
    prev_b64, prev_mt = _load_image(prev_image_path)
    curr_b64, curr_mt = _load_image(curr_image_path)

    # Use the image-aware call with the current image,
    # and embed the previous image description/reference in the prompt.
    # Most vision APIs support multiple images in one message.
    from autocritic.llm import _parse_provider

    provider, model_name = _parse_provider(model)

    raw = _call_two_images(
        provider=provider,
        model_name=model_name,
        model_full=model,
        system=system,
        user=user,
        prev_b64=prev_b64,
        prev_mt=prev_mt,
        curr_b64=curr_b64,
        curr_mt=curr_mt,
    )

    sections = _parse_critique(raw)

    return CritiqueResult(
        critic_id=critic.critic_id,
        image_path=str(curr_image_path),
        model=model,
        raw_text=raw,
        lens_summary="",
        strengths=_extract_bullet_list(
            sections.get("Progress Since Last Iteration", "")
        ),
        weaknesses=_extract_bullet_list(
            sections.get("Regressions Or New Problems", "")
        ),
        criterion_notes=_extract_criterion_notes(
            sections.get("Criteria Still Unresolved", "")
        ),
        directives=_extract_bullet_list(
            sections.get("Highest-Priority Next Changes", "")
        ),
        preservations=_extract_bullet_list(
            sections.get("Elements That Must Be Preserved", "")
        ),
    )


def _call_two_images(
    provider: str, model_name: str, model_full: str,
    system: str, user: str,
    prev_b64: str, prev_mt: str,
    curr_b64: str, curr_mt: str,
) -> str:
    """Send two images (prev + current) to an LLM for comparison."""
    import os

    if provider == "anthropic":
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package required")
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model_name,
            max_tokens=4096,
            temperature=0.0,
            system=system,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Previous iteration:"},
                    {"type": "image", "source": {
                        "type": "base64", "media_type": prev_mt, "data": prev_b64,
                    }},
                    {"type": "text", "text": "Current iteration:"},
                    {"type": "image", "source": {
                        "type": "base64", "media_type": curr_mt, "data": curr_b64,
                    }},
                    {"type": "text", "text": user},
                ],
            }],
        )
        return response.content[0].text

    elif provider == "google":
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ImportError("google-genai package required")
        import base64 as b64mod
        client = genai.Client()
        prev_part = types.Part.from_bytes(
            data=b64mod.b64decode(prev_b64), mime_type=prev_mt,
        )
        curr_part = types.Part.from_bytes(
            data=b64mod.b64decode(curr_b64), mime_type=curr_mt,
        )
        response = client.models.generate_content(
            model=model_name,
            contents=[
                "Previous iteration:", prev_part,
                "Current iteration:", curr_part,
                user,
            ],
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=4096,
                temperature=0.0,
            ),
        )
        return response.text

    else:
        # OpenAI-compatible (covers openai, xai, ollama, mlx, llamacpp, local)
        try:
            import openai
        except ImportError:
            raise ImportError("openai package required")

        from autocritic.llm import _OPENAI_COMPAT_PROVIDERS

        if provider == "local":
            base_url = os.environ.get("LOCAL_LLM_URL", "http://localhost:8080/v1")
            api_key = os.environ.get("LOCAL_LLM_API_KEY", "none")
        elif provider in _OPENAI_COMPAT_PROVIDERS:
            base_url, api_key_env = _OPENAI_COMPAT_PROVIDERS[provider]
            api_key = os.environ.get(api_key_env) if api_key_env else "ollama"
        else:
            raise ValueError(f"Unknown provider: {provider}")

        client = openai.OpenAI(base_url=base_url, api_key=api_key)
        prev_url = f"data:{prev_mt};base64,{prev_b64}"
        curr_url = f"data:{curr_mt};base64,{curr_b64}"
        token_kwarg = (
            {"max_completion_tokens": 4096}
            if base_url is None
            else {"max_tokens": 4096}
        )
        response = client.chat.completions.create(
            model=model_name,
            **token_kwarg,
            temperature=0.0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": [
                    {"type": "text", "text": "Previous iteration:"},
                    {"type": "image_url", "image_url": {"url": prev_url}},
                    {"type": "text", "text": "Current iteration:"},
                    {"type": "image_url", "image_url": {"url": curr_url}},
                    {"type": "text", "text": user},
                ]},
            ],
        )
        return response.choices[0].message.content
