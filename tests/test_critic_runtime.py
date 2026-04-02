"""Tests for the critic runtime: loading, prompt assembly, and response parsing."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from autocritic.critic import (
    CriticCard,
    CritiqueResult,
    _build_comparison_user_prompt,
    _build_critique_user_prompt,
    _build_system_prompt,
    _extract_bullet_list,
    _extract_criterion_notes,
    _parse_critique,
    load_critic,
)

CRITICS_DIR = Path(__file__).parent.parent / "critics"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
ALL_CARDS = sorted(CRITICS_DIR.glob("*.json"))


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

class TestLoadCritic:
    """Every critic card loads without error and has the right shape."""

    @pytest.mark.parametrize(
        "card_path", ALL_CARDS, ids=[p.stem for p in ALL_CARDS]
    )
    def test_loads_successfully(self, card_path: Path):
        c = load_critic(card_path)
        assert isinstance(c, CriticCard)
        assert c.critic_id == card_path.stem

    @pytest.mark.parametrize(
        "card_path", ALL_CARDS, ids=[p.stem for p in ALL_CARDS]
    )
    def test_has_required_fields(self, card_path: Path):
        c = load_critic(card_path)
        assert c.theorist
        assert c.book
        assert c.thesis
        assert len(c.items) >= 2
        assert len(c.anti_goals) >= 1

    @pytest.mark.parametrize(
        "card_path", ALL_CARDS, ids=[p.stem for p in ALL_CARDS]
    )
    def test_items_have_ids(self, card_path: Path):
        c = load_critic(card_path)
        for item in c.items:
            assert c.item_id_field in item, (
                f"{card_path.stem}: item missing {c.item_id_field}"
            )

    @pytest.mark.parametrize(
        "card_path", ALL_CARDS, ids=[p.stem for p in ALL_CARDS]
    )
    def test_items_have_definitions(self, card_path: Path):
        c = load_critic(card_path)
        for item in c.items:
            assert "definition" in item, (
                f"{card_path.stem}: item missing definition"
            )

    def test_label_property(self):
        c = load_critic(CRITICS_DIR / "wolfflin.json")
        assert "Wölfflin" in c.label or "Wolfflin" in c.label
        assert "Principles of Art History" in c.label

    def test_invalid_card_raises(self, tmp_path: Path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"critic_id": "bad", "foo": []}))
        with pytest.raises(ValueError, match="No recognized items key"):
            load_critic(bad)


# ---------------------------------------------------------------------------
# Items key detection
# ---------------------------------------------------------------------------

class TestItemsKeyDetection:
    """Verify that each card type maps to the correct items_key."""

    EXPECTED = {
        "wolfflin": "criteria",
        "kandinsky": "elements",
        "dow": "elements",
        "arnheim": "principles",
        "gombrich": "core_concepts",
        "worringer": "impulses",
        "albers": "core_concepts",
        "klee": "core_concepts",
        "ruskin": "core_concepts",
        "hildebrand": "core_concepts",
    }

    @pytest.mark.parametrize("name,expected_key", EXPECTED.items())
    def test_items_key(self, name: str, expected_key: str):
        c = load_critic(CRITICS_DIR / f"{name}.json")
        assert c.items_key == expected_key


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------

class TestPromptAssembly:
    """System and user prompts are well-formed."""

    @pytest.mark.parametrize(
        "card_path", ALL_CARDS, ids=[p.stem for p in ALL_CARDS]
    )
    def test_system_prompt_contains_theorist(self, card_path: Path):
        c = load_critic(card_path)
        prompt = _build_system_prompt(c)
        assert c.theorist in prompt

    @pytest.mark.parametrize(
        "card_path", ALL_CARDS, ids=[p.stem for p in ALL_CARDS]
    )
    def test_system_prompt_contains_thesis(self, card_path: Path):
        c = load_critic(card_path)
        prompt = _build_system_prompt(c)
        # First 100 chars of thesis should appear
        assert c.thesis[:100] in prompt

    @pytest.mark.parametrize(
        "card_path", ALL_CARDS, ids=[p.stem for p in ALL_CARDS]
    )
    def test_system_prompt_contains_anti_goals(self, card_path: Path):
        c = load_critic(card_path)
        prompt = _build_system_prompt(c)
        assert "Anti-Goals" in prompt
        for ag in c.anti_goals[:3]:  # spot-check first 3
            assert ag in prompt

    @pytest.mark.parametrize(
        "card_path", ALL_CARDS, ids=[p.stem for p in ALL_CARDS]
    )
    def test_system_prompt_contains_all_items(self, card_path: Path):
        c = load_critic(card_path)
        prompt = _build_system_prompt(c)
        for item in c.items:
            item_id = item[c.item_id_field]
            label = item.get("label", item_id)
            assert label in prompt, f"Missing item label: {label}"

    def test_user_prompt_has_required_sections(self):
        prompt = _build_critique_user_prompt()
        for section in [
            "Lens Summary",
            "Strengths To Preserve",
            "Weaknesses To Address",
            "Criterion Notes",
            "Next Iteration Directives",
        ]:
            assert section in prompt

    def test_user_prompt_includes_intent(self):
        prompt = _build_critique_user_prompt(intent="abstract expressionism")
        assert "abstract expressionism" in prompt
        assert "Project Intent" in prompt

    def test_user_prompt_without_intent_has_no_intent_section(self):
        prompt = _build_critique_user_prompt()
        assert "Project Intent" not in prompt

    def test_comparison_prompt_has_required_sections(self):
        prompt = _build_comparison_user_prompt()
        for section in [
            "Progress Since Last Iteration",
            "Regressions Or New Problems",
            "Criteria Still Unresolved",
            "Highest-Priority Next Changes",
            "Elements That Must Be Preserved",
        ]:
            assert section in prompt

    def test_comparison_prompt_includes_prev_critique(self):
        prompt = _build_comparison_user_prompt(
            prev_critique_text="Previous analysis here"
        )
        assert "Previous analysis here" in prompt
        assert "Previous Critique For Reference" in prompt


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

SAMPLE_RESPONSE = """## Lens Summary
Wölfflin's linear-painterly axis dominates this image.

## Strengths To Preserve
- Strong contour definition throughout
- Clear planar separation in the background
- Effective use of closed form

## Weaknesses To Address
- Lacks painterly dissolution
- Depth cues are too uniform
- No atmospheric perspective

## Criterion Notes
### Linear vs Painterly
The image is strongly linear with clean edges.

### Plane vs Recession
Background planes are well separated but flat.

**Closed vs Open Form**: The central object uses closed form effectively.

## Next Iteration Directives
- Introduce selective edge softening in shadow areas
- Add atmospheric perspective to distant planes
- Preserve the strong contour of the central form
- Experiment with one area of tonal merging
"""


class TestParseCritique:
    """Parsing of markdown critique responses."""

    def test_extracts_all_sections(self):
        sections = _parse_critique(SAMPLE_RESPONSE)
        assert "Lens Summary" in sections
        assert "Strengths To Preserve" in sections
        assert "Weaknesses To Address" in sections
        assert "Criterion Notes" in sections
        assert "Next Iteration Directives" in sections

    def test_lens_summary_content(self):
        sections = _parse_critique(SAMPLE_RESPONSE)
        assert "linear-painterly" in sections["Lens Summary"]

    def test_empty_input(self):
        sections = _parse_critique("")
        assert sections == {}

    def test_no_headers(self):
        sections = _parse_critique("Just some text without headers.")
        assert sections == {}


class TestExtractBulletList:
    def test_dash_bullets(self):
        result = _extract_bullet_list("- one\n- two\n- three")
        assert result == ["one", "two", "three"]

    def test_star_bullets(self):
        result = _extract_bullet_list("* alpha\n* beta")
        assert result == ["alpha", "beta"]

    def test_arrow_bullets(self):
        result = _extract_bullet_list("→ do this\n→ do that")
        assert result == ["do this", "do that"]

    def test_mixed_content(self):
        text = "Some preamble.\n\n- item one\n- item two\n\nShort."
        result = _extract_bullet_list(text)
        assert "item one" in result
        assert "item two" in result

    def test_empty(self):
        assert _extract_bullet_list("") == []


class TestExtractCriterionNotes:
    def test_h3_headers(self):
        text = "### First\nNote about first.\n### Second\nNote about second."
        notes = _extract_criterion_notes(text)
        assert len(notes) == 2
        assert notes[0]["criterion"] == "First"
        assert "first" in notes[0]["note"].lower()

    def test_bold_labels(self):
        text = "**Alpha**: This is alpha.\n**Beta**: This is beta."
        notes = _extract_criterion_notes(text)
        assert len(notes) == 2
        assert notes[0]["criterion"] == "Alpha"
        assert notes[1]["criterion"] == "Beta"

    def test_mixed_h3_and_bold(self):
        text = "### First\nFirst note.\n**Second**: Second note."
        notes = _extract_criterion_notes(text)
        assert len(notes) == 2

    def test_empty(self):
        assert _extract_criterion_notes("") == []


# ---------------------------------------------------------------------------
# CritiqueResult
# ---------------------------------------------------------------------------

class TestCritiqueResult:
    def test_summary_output(self):
        r = CritiqueResult(
            critic_id="wolfflin",
            image_path="test.png",
            model="test-model",
            raw_text="raw",
            lens_summary="Linear axis dominates.",
            strengths=["Strong contours"],
            weaknesses=["No depth"],
            directives=["Add shadows"],
        )
        s = r.summary()
        assert "wolfflin" in s
        assert "Strong contours" in s
        assert "No depth" in s
        assert "Add shadows" in s

    def test_summary_minimal(self):
        r = CritiqueResult(
            critic_id="test",
            image_path="img.png",
            model="m",
            raw_text="",
        )
        s = r.summary()
        assert "test" in s


# ---------------------------------------------------------------------------
# Integration: full parse pipeline
# ---------------------------------------------------------------------------

class TestFullParsePipeline:
    """Simulate what critique_image does without calling an LLM."""

    def test_parse_into_critique_result(self):
        sections = _parse_critique(SAMPLE_RESPONSE)
        result = CritiqueResult(
            critic_id="wolfflin",
            image_path="test.png",
            model="test",
            raw_text=SAMPLE_RESPONSE,
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
        )
        assert result.lens_summary
        assert len(result.strengths) == 3
        assert len(result.weaknesses) == 3
        assert len(result.criterion_notes) == 3
        assert len(result.directives) == 4

    @pytest.mark.parametrize(
        "card_path", ALL_CARDS, ids=[p.stem for p in ALL_CARDS]
    )
    def test_prompt_roundtrip_all_cards(self, card_path: Path):
        """Load card → build prompt → verify it's non-trivial."""
        c = load_critic(card_path)
        system = _build_system_prompt(c)
        user = _build_critique_user_prompt()
        # System prompt should be substantial
        assert len(system) > 1000, f"{card_path.stem} system prompt too short"
        # User prompt should be consistent
        assert "Lens Summary" in user
        assert "Criterion Notes" in user


# ---------------------------------------------------------------------------
# critique_image (mocked LLM)
# ---------------------------------------------------------------------------

class TestCritiqueImageMocked:
    """Test critique_image with a mocked LLM call."""

    def test_critique_image_returns_structured_result(self):
        from autocritic.critic import critique_image

        c = load_critic(CRITICS_DIR / "wolfflin.json")
        image_path = FIXTURES_DIR / "test_image.png"

        with patch(
            "autocritic.llm._call_llm_with_image",
            return_value=SAMPLE_RESPONSE,
        ):
            result = critique_image(c, image_path, model="test-model")

        assert isinstance(result, CritiqueResult)
        assert result.critic_id == "wolfflin"
        assert result.model == "test-model"
        assert len(result.strengths) == 3
        assert len(result.weaknesses) == 3
        assert len(result.directives) == 4

    def test_critique_image_passes_intent(self):
        from autocritic.critic import critique_image

        c = load_critic(CRITICS_DIR / "dow.json")
        image_path = FIXTURES_DIR / "test_image.png"

        calls = []

        def mock_call(**kwargs):
            calls.append(kwargs)
            return SAMPLE_RESPONSE

        with patch("autocritic.llm._call_llm_with_image", side_effect=mock_call):
            critique_image(c, image_path, intent="geometric abstraction")

        assert len(calls) == 1
        assert "geometric abstraction" in calls[0]["user"]


# ---------------------------------------------------------------------------
# Live end-to-end (requires ANTHROPIC_API_KEY)
# ---------------------------------------------------------------------------

@pytest.mark.eval
@pytest.mark.skipif(
    not __import__("os").environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)
class TestCritiqueImageLive:
    """Live LLM critique — requires API key and real images."""

    LIVE_IMAGE = Path(__file__).parent / "fixtures" / "Friedrich.jpg"

    @pytest.fixture(autouse=True)
    def _skip_if_no_image(self):
        if not self.LIVE_IMAGE.exists():
            pytest.skip("No test image at fixtures/Friedrich.jpg")

    @pytest.mark.parametrize("critic_name", ["wolfflin", "kandinsky", "ruskin"])
    def test_live_critique(self, critic_name: str):
        from autocritic.critic import critique_image

        c = load_critic(CRITICS_DIR / f"{critic_name}.json")
        result = critique_image(c, self.LIVE_IMAGE)

        # Should return structured output
        assert isinstance(result, CritiqueResult)
        assert result.critic_id == critic_name
        assert result.raw_text
        assert len(result.raw_text) > 200
        # Should have parsed sections
        assert result.lens_summary
        assert len(result.strengths) >= 1
        assert len(result.weaknesses) >= 1
        assert len(result.directives) >= 1
