"""Tests for the improvement loop: accept/reject logic, stopping conditions."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from autocritic.critic import CritiqueResult
from autocritic.loop import LoopConfig, LoopResult, run_loop
from autocritic.scoring import AxisScore, ScoredCritique
from autocritic.translator import ParamSpec, ParamSpace, TranslationResult

CRITICS_DIR = Path(__file__).parent.parent / "critics"

# Minimal param space for testing
TEST_SPACE = ParamSpace(specs=[
    ParamSpec("density", "float", (0.0, 1.0), 0.5, "How dense"),
    ParamSpec("spread", "float", (0.1, 5.0), 1.0, "How spread"),
])


def _make_scored_critique(score: float) -> ScoredCritique:
    """Build a ScoredCritique with a given composite score."""
    critique = CritiqueResult(
        critic_id="test", image_path="test.png", model="test",
        raw_text="", lens_summary="test",
        strengths=["good thing"],
        weaknesses=["bad thing"],
        directives=["do something"],
    )
    return ScoredCritique(
        critique=critique,
        axis_scores=[AxisScore("a", "A", score, "reason")],
        composite_score=score,
    )


def _make_translation(deltas: dict) -> TranslationResult:
    return TranslationResult(
        deltas=deltas,
        reasoning="test reasoning",
        raw_text="test",
    )


# ---------------------------------------------------------------------------
# Full loop (all external calls mocked)
# ---------------------------------------------------------------------------

class TestRunLoopMocked:
    def test_basic_loop_runs(self, tmp_path):
        """Loop runs 3 iterations with improving scores."""
        scores = iter([0.3, 0.5, 0.7])

        def mock_acquire(params, output_path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"fake png")
            return output_path

        config = LoopConfig(
            critic_card_path=CRITICS_DIR / "wolfflin.json",
            model="test",
            max_iterations=3,
            output_dir=tmp_path,
        )

        with patch("autocritic.loop.score_critique") as mock_score, \
             patch("autocritic.loop.translate_critique_to_params") as mock_translate:

            mock_score.side_effect = lambda *a, **kw: _make_scored_critique(next(scores))
            mock_translate.return_value = _make_translation({"density": 0.6})

            result = run_loop(
                config=config,
                param_space=TEST_SPACE,
                acquire_image_fn=mock_acquire,
                initial_params=TEST_SPACE.defaults(),
            )

        assert isinstance(result, LoopResult)
        assert len(result.iterations) == 3
        assert result.best_score == pytest.approx(0.7)
        assert result.best_iteration == 2

    def test_stops_on_high_score(self, tmp_path):
        """Loop stops early when score exceeds 0.9."""
        scores = iter([0.5, 0.95])

        def mock_acquire(params, output_path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"fake png")
            return output_path

        config = LoopConfig(
            critic_card_path=CRITICS_DIR / "wolfflin.json",
            model="test",
            max_iterations=10,
            output_dir=tmp_path,
        )

        with patch("autocritic.loop.score_critique") as mock_score, \
             patch("autocritic.loop.translate_critique_to_params") as mock_translate:

            mock_score.side_effect = lambda *a, **kw: _make_scored_critique(next(scores))
            mock_translate.return_value = _make_translation({"density": 0.8})

            result = run_loop(
                config=config,
                param_space=TEST_SPACE,
                acquire_image_fn=mock_acquire,
                initial_params=TEST_SPACE.defaults(),
            )

        assert result.stop_reason == "high_score"
        assert len(result.iterations) == 2

    def test_rejection_reverts_params(self, tmp_path):
        """When score drops, params revert to accepted state (unipolar critic)."""
        scores = iter([0.5, 0.3, 0.6])  # drop then recover

        def mock_acquire(params, output_path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"fake png")
            return output_path

        # Use a unipolar critic — bipolar critics accept all iterations
        config = LoopConfig(
            critic_card_path=CRITICS_DIR / "arnheim.json",
            model="test",
            max_iterations=3,
            min_improvement=0.01,
            output_dir=tmp_path,
        )

        with patch("autocritic.loop.score_critique") as mock_score, \
             patch("autocritic.loop.translate_critique_to_params") as mock_translate:

            mock_score.side_effect = lambda *a, **kw: _make_scored_critique(next(scores))
            mock_translate.return_value = _make_translation({"density": 0.8})

            result = run_loop(
                config=config,
                param_space=TEST_SPACE,
                acquire_image_fn=mock_acquire,
                initial_params=TEST_SPACE.defaults(),
            )

        # Iteration 1 should be rejected (0.3 < 0.5)
        assert result.iterations[1].accepted is False

    def test_artifacts_saved(self, tmp_path):
        """Verify iteration artifacts are saved to disk."""
        def mock_acquire(params, output_path):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"fake png")
            return output_path

        config = LoopConfig(
            critic_card_path=CRITICS_DIR / "wolfflin.json",
            model="test",
            max_iterations=2,
            output_dir=tmp_path,
        )

        with patch("autocritic.loop.score_critique") as mock_score, \
             patch("autocritic.loop.translate_critique_to_params") as mock_translate:

            mock_score.return_value = _make_scored_critique(0.5)
            mock_translate.return_value = _make_translation({"density": 0.6})

            result = run_loop(
                config=config,
                param_space=TEST_SPACE,
                acquire_image_fn=mock_acquire,
                initial_params=TEST_SPACE.defaults(),
            )

        run_dir = result.output_dir
        assert (run_dir / "config.json").exists()
        assert (run_dir / "trajectory.json").exists()
        assert (run_dir / "summary.json").exists()
        assert (run_dir / "iter_000" / "params.json").exists()
        assert (run_dir / "iter_000" / "critique_summary.json").exists()
