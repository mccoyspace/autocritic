"""
Distillation evals: test whether critic cards faithfully represent their
source theories.

Two eval types:
1. Programmatic checks (no API): structural validation, vocabulary presence
2. LLM-as-judge (requires API): semantic fidelity, lens specificity
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.ground_truth import THEORISTS
from evals.ground_truth import wolfflin as wolfflin_gt
from evals.fixtures.generic_baseline import GENERIC_VOCABULARY

CRITICS_DIR = Path("critics")


# ---------------------------------------------------------------------------
# Programmatic checks (fast, no API key needed)
# ---------------------------------------------------------------------------

class TestCriticCardStructure:
    """
    Verify structural requirements for all critic cards.
    """

    @pytest.fixture(params=sorted(CRITICS_DIR.glob("*.json")), ids=lambda p: p.stem)
    def card_data(self, request) -> tuple[Path, dict]:
        path = request.param
        return path, json.loads(path.read_text())

    def test_has_required_top_level_fields(self, card_data):
        path, card = card_data
        for field in ["critic_id", "theorist", "book", "thesis", "anti_goals", "tensions"]:
            assert field in card, f"{path.stem}: missing '{field}'"

    def test_has_items(self, card_data):
        path, card = card_data
        from autocritic.critic import load_critic
        critic = load_critic(path)
        assert len(critic.items) >= 2, f"{path.stem}: needs at least 2 items"

    def test_items_have_core_fields(self, card_data):
        path, card = card_data
        from autocritic.critic import load_critic
        critic = load_critic(path)
        for item in critic.items:
            label = item.get("label", "?")
            assert "label" in item, f"{path.stem}/{label}: missing 'label'"
            assert "definition" in item, f"{path.stem}/{label}: missing 'definition'"
            assert "diagnostic_questions" in item, f"{path.stem}/{label}: missing 'diagnostic_questions'"

    def test_has_anti_goals(self, card_data):
        path, card = card_data
        assert len(card.get("anti_goals", [])) >= 2, f"{path.stem}: need at least 2 anti-goals"

    def test_has_citations(self, card_data):
        path, card = card_data
        assert len(card.get("citations", [])) >= 3, f"{path.stem}: need at least 3 citations"

    def test_critic_id_matches_filename(self, card_data):
        path, card = card_data
        assert card.get("critic_id") == path.stem, (
            f"critic_id '{card.get('critic_id')}' != filename '{path.stem}'"
        )


class TestDistinctiveVocabularyPresence:
    """
    Check that critic cards use the theorist's actual vocabulary,
    not generic art-school language.
    """

    @staticmethod
    def extract_text(card: dict) -> str:
        """Flatten a critic card into searchable text."""
        from autocritic.critic import load_critic, _ITEMS_KEYS
        parts = [card.get("thesis", "")]
        for key in _ITEMS_KEYS:
            for item in card.get(key, []):
                parts.append(item.get("definition", ""))
                parts.extend(item.get("diagnostic_questions", []))
                # feedback_directions may be a dict of lists
                fd = item.get("feedback_directions", {})
                if isinstance(fd, dict):
                    for v in fd.values():
                        if isinstance(v, list):
                            parts.extend(v)
                elif isinstance(fd, list):
                    parts.extend(fd)
                # Some items use examples instead of feedback_directions
                parts.extend(item.get("examples", []))
                # Include indicators text
                ind = item.get("indicators", {})
                if isinstance(ind, dict):
                    for v in ind.values():
                        if isinstance(v, list):
                            parts.extend(v)
                parts.extend(item.get("common_misreadings", []))
        for ag in card.get("anti_goals", []):
            parts.append(ag)
        return " ".join(parts).lower()

    @pytest.fixture(
        params=[
            (name, gt) for name, gt in THEORISTS.items()
            if (CRITICS_DIR / f"{name}.json").exists()
        ],
        ids=lambda x: x[0],
    )
    def theorist_data(self, request):
        name, gt = request.param
        card_path = CRITICS_DIR / f"{name}.json"
        card = json.loads(card_path.read_text())
        return name, gt, card

    def test_uses_distinctive_terms(self, theorist_data):
        """At least 40% of the theorist's distinctive vocabulary should appear."""
        name, gt, card = theorist_data
        text = self.extract_text(card)
        vocab = [v.lower() for v in gt.DISTINCTIVE_VOCABULARY]
        hits = [v for v in vocab if v in text]
        ratio = len(hits) / len(vocab)
        assert ratio >= 0.4, (
            f"{name}: only {len(hits)}/{len(vocab)} ({ratio:.0%}) distinctive terms found. "
            f"Missing: {set(vocab) - set(hits)}"
        )

    def test_not_dominated_by_generic_terms(self, theorist_data):
        """Generic design vocabulary should not vastly outnumber distinctive terms.

        A small margin is allowed because some theorists (e.g. Dow) use terms
        that became "generic" precisely because of their influence.
        """
        name, gt, card = theorist_data
        text = self.extract_text(card)
        distinctive_hits = sum(1 for v in gt.DISTINCTIVE_VOCABULARY if v.lower() in text)
        generic_hits = sum(1 for v in GENERIC_VOCABULARY if v.lower() in text)
        assert distinctive_hits >= generic_hits * 0.8, (
            f"{name}: generic vocabulary ({generic_hits}) vastly outnumbers "
            f"distinctive ({distinctive_hits})"
        )


# ---------------------------------------------------------------------------
# LLM-as-judge evals (require ANTHROPIC_API_KEY)
# ---------------------------------------------------------------------------

from tests.conftest import skip_no_api


@skip_no_api
class TestCitationGrounding:
    """
    LLM judge checks whether each criterion in the critic card can be
    traced back to something the theorist actually wrote.
    """

    def test_wolfflin_citations_grounded(self, wolfflin_text: str):
        from evals.judge import run_judge

        artifact = json.dumps({
            "theorist": "Wölfflin",
            "essential_claims": wolfflin_gt.ESSENTIAL_CLAIMS,
            "polarities": {
                k: v["definition"] for k, v in wolfflin_gt.POLARITIES.items()
            },
        }, indent=2)

        source_sample = wolfflin_text[:3000]

        result = run_judge(
            eval_name="citation_grounding_wolfflin",
            artifact_description=(
                "A Wölfflin critic card's essential claims and polarity definitions, "
                "checked against a sample of the source text"
            ),
            artifact_content=(
                f"## Critic Card Claims\n{artifact}\n\n"
                f"## Source Text Sample\n{source_sample}"
            ),
            rubric_dimensions=[
                "claim-to-source alignment",
                "fidelity to theorist vocabulary",
                "preservation of nuance",
                "absence of invented doctrine",
            ],
            failure_modes=[
                "criteria with no evidence in the source",
                "modern jargon inserted as if from the book",
                "flattening a complex theory into generic advice",
            ],
            pass_threshold=12,
        )
        print(result.summary())
        assert result.passed, result.summary()


@skip_no_api
class TestLensSpecificity:
    """
    LLM judge compares a critic card against the generic baseline.
    The critic should be sharply distinct.
    """

    def test_wolfflin_distinct_from_generic(self):
        from evals.judge import run_comparative_judge
        from evals.fixtures.generic_baseline import GENERIC_CRITIQUE

        result = run_comparative_judge(
            eval_name="lens_specificity_wolfflin",
            description=(
                "Compare a Wölfflin-informed critique against a generic "
                "design critique to verify the lens is specific"
            ),
            artifact_a=wolfflin_gt.GOOD_CRITIQUE_EXAMPLE,
            artifact_b=GENERIC_CRITIQUE,
            comparison_dimensions=[
                "distinctive evaluative vocabulary",
                "clear exclusions and anti-goals",
                "priority structure specific to theorist",
                "recognizable theorist fingerprint",
            ],
            pass_threshold=12,
        )
        print(result.summary())
        assert result.passed, result.summary()
