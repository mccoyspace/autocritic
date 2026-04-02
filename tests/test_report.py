"""Tests for the report module: narrative generation, contact sheet, bipolar awareness."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from autocritic.report import (
    build_narrative,
    generate_contact_sheet,
    save_narrative_md,
    _infer_bipolar,
    _readable_stop,
    _wrap_narrative,
)


# ---------------------------------------------------------------------------
# Fixtures: fabricate minimal run directories
# ---------------------------------------------------------------------------

def _make_run_dir(
    tmp_path: Path,
    *,
    n_iters: int = 3,
    scores: list[float] | None = None,
    best_iter: int = 2,
    best_score: float = 0.7,
    stop_reason: str = "max_iterations",
    bipolar: bool = False,
    accepted: list[bool] | None = None,
) -> Path:
    """Create a minimal run directory with summary and per-iteration artifacts."""
    if scores is None:
        scores = [0.3, 0.5, 0.7][:n_iters]
    if accepted is None:
        accepted = [True] * n_iters

    run_dir = tmp_path / "test_run"
    run_dir.mkdir()

    summary = {
        "run_id": "test_run_123",
        "stop_reason": stop_reason,
        "total_iterations": n_iters,
        "best_iteration": best_iter,
        "best_score": best_score,
        "bipolar": bipolar,
        "score_progression": scores,
        "final_params": {"density": 0.5},
    }
    (run_dir / "summary.json").write_text(json.dumps(summary))

    for i in range(n_iters):
        iter_dir = run_dir / f"iter_{i:03d}"
        iter_dir.mkdir()

        crit = {
            "iteration": i,
            "composite_score": scores[i],
            "accepted": accepted[i],
            "lens_summary": f"Lens for iteration {i}",
            "directives": [f"Adjust parameter X for iteration {i}"],
            "axis_scores": [],
        }
        (iter_dir / "critique_summary.json").write_text(json.dumps(crit))

        # Create a small test image
        img = Image.new("RGB", (100, 100), (200, 200, 200))
        img.save(iter_dir / "image.png")

    return run_dir


# ---------------------------------------------------------------------------
# _readable_stop
# ---------------------------------------------------------------------------

class TestReadableStop:
    def test_known_reasons(self):
        assert "max iterations" in _readable_stop("max_iterations")
        assert "high score" in _readable_stop("high_score")
        assert "plateaued" in _readable_stop("plateaued")

    def test_unknown_reason_passes_through(self):
        assert _readable_stop("custom_reason") == "custom_reason"


# ---------------------------------------------------------------------------
# _wrap_narrative
# ---------------------------------------------------------------------------

class TestWrapNarrative:
    def test_short_lines_unchanged(self):
        text = "Short line\nAnother short line"
        assert _wrap_narrative(text, 80) == text

    def test_long_line_wraps(self):
        text = "x" * 120
        wrapped = _wrap_narrative(text, 80)
        lines = wrapped.split("\n")
        assert len(lines) > 1
        assert all(len(line) <= 80 for line in lines)

    def test_preserves_empty_lines(self):
        text = "Line one\n\nLine three"
        assert _wrap_narrative(text, 80) == text

    def test_indented_lines_preserve_indent(self):
        text = "  " + "y" * 120
        wrapped = _wrap_narrative(text, 80)
        lines = wrapped.split("\n")
        # Continuation lines should be indented
        for line in lines[1:]:
            assert line.startswith("  ")


# ---------------------------------------------------------------------------
# build_narrative — unipolar
# ---------------------------------------------------------------------------

class TestBuildNarrativeUnipolar:
    def test_contains_run_id(self, tmp_path):
        run_dir = _make_run_dir(tmp_path)
        narrative = build_narrative(run_dir)
        assert "test_run_123" in narrative

    def test_contains_stop_reason(self, tmp_path):
        run_dir = _make_run_dir(tmp_path)
        narrative = build_narrative(run_dir)
        assert "max iterations" in narrative

    def test_contains_score_progression(self, tmp_path):
        run_dir = _make_run_dir(tmp_path, scores=[0.3, 0.5, 0.7])
        narrative = build_narrative(run_dir)
        assert "0.30" in narrative
        assert "0.70" in narrative

    def test_unipolar_uses_score_label(self, tmp_path):
        run_dir = _make_run_dir(tmp_path, bipolar=False)
        narrative = build_narrative(run_dir)
        assert "Score:" in narrative
        assert "best" in narrative

    def test_unipolar_marks_best_iteration(self, tmp_path):
        run_dir = _make_run_dir(tmp_path, bipolar=False, best_iter=2)
        narrative = build_narrative(run_dir)
        # Best iteration should have a star
        lines = narrative.split("\n")
        iter2_lines = [l for l in lines if "Iter 2" in l]
        assert any("★" in l for l in iter2_lines)

    def test_unipolar_non_best_has_no_star(self, tmp_path):
        run_dir = _make_run_dir(tmp_path, bipolar=False, best_iter=2)
        narrative = build_narrative(run_dir)
        lines = narrative.split("\n")
        iter0_lines = [l for l in lines if "Iter 0" in l]
        assert not any("★" in l for l in iter0_lines)

    def test_includes_lens_summary(self, tmp_path):
        run_dir = _make_run_dir(tmp_path)
        narrative = build_narrative(run_dir)
        assert "Focus: Lens for iteration 0" in narrative

    def test_includes_directive(self, tmp_path):
        run_dir = _make_run_dir(tmp_path)
        narrative = build_narrative(run_dir)
        assert "Adjust parameter X" in narrative

    def test_rejected_iteration_marked(self, tmp_path):
        run_dir = _make_run_dir(
            tmp_path, scores=[0.5, 0.3, 0.6], accepted=[True, False, True]
        )
        narrative = build_narrative(run_dir)
        lines = narrative.split("\n")
        iter1_lines = [l for l in lines if "Iter 1" in l]
        assert any("\u2717" in l for l in iter1_lines)  # ✗

    def test_no_summary_returns_message(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        assert build_narrative(empty_dir) == "No summary found."


# ---------------------------------------------------------------------------
# build_narrative — bipolar
# ---------------------------------------------------------------------------

class TestBuildNarrativeBipolar:
    def test_bipolar_uses_pole_commitment_label(self, tmp_path):
        run_dir = _make_run_dir(tmp_path, bipolar=True)
        narrative = build_narrative(run_dir)
        assert "Pole commitment:" in narrative
        assert "peak" in narrative
        # Should NOT use unipolar "Score:" or "best" language
        assert "Score:" not in narrative

    def test_bipolar_no_star_on_any_iteration(self, tmp_path):
        run_dir = _make_run_dir(tmp_path, bipolar=True, best_iter=0)
        narrative = build_narrative(run_dir)
        lines = narrative.split("\n")
        iter_lines = [l for l in lines if "Iter " in l]
        assert not any("★" in l for l in iter_lines)

    def test_bipolar_still_shows_scores(self, tmp_path):
        run_dir = _make_run_dir(tmp_path, bipolar=True, scores=[0.8, 0.2, 0.7])
        narrative = build_narrative(run_dir)
        assert "0.80" in narrative
        assert "0.70" in narrative


# ---------------------------------------------------------------------------
# _infer_bipolar — legacy summary fallback
# ---------------------------------------------------------------------------

class TestInferBipolar:
    def test_explicit_flag_true(self):
        assert _infer_bipolar({"bipolar": True}) is True

    def test_explicit_flag_false(self):
        assert _infer_bipolar({"bipolar": False}) is False

    def test_legacy_summary_with_critic_id(self):
        """A legacy summary with critic_id (no bipolar key) should infer from card."""
        assert _infer_bipolar({"critic_id": "wolfflin"}) is True
        assert _infer_bipolar({"critic_id": "arnheim"}) is False

    def test_legacy_summary_unknown_critic_defaults_false(self):
        assert _infer_bipolar({"critic_id": "nonexistent_critic"}) is False

    def test_empty_summary_defaults_false(self):
        assert _infer_bipolar({}) is False

    def test_falls_back_to_config_json(self, tmp_path):
        """Real legacy shape: critic_id is only in config.json, not summary.json."""
        run_dir = tmp_path / "legacy_run"
        run_dir.mkdir()
        # summary has no critic_id and no bipolar
        (run_dir / "summary.json").write_text(json.dumps({"run_id": "test"}))
        # config.json has the critic_id
        (run_dir / "config.json").write_text(json.dumps({"critic_id": "wolfflin"}))
        assert _infer_bipolar({}, run_dir) is True

    def test_config_json_unipolar(self, tmp_path):
        run_dir = tmp_path / "legacy_run"
        run_dir.mkdir()
        (run_dir / "config.json").write_text(json.dumps({"critic_id": "arnheim"}))
        assert _infer_bipolar({}, run_dir) is False

    def test_no_config_json_defaults_false(self, tmp_path):
        run_dir = tmp_path / "empty_run"
        run_dir.mkdir()
        assert _infer_bipolar({}, run_dir) is False

    def test_end_to_end_legacy_config_only(self, tmp_path):
        """End-to-end: legacy run with critic_id only in config.json gets bipolar narrative."""
        run_dir = tmp_path / "legacy_run"
        run_dir.mkdir()
        # Summary has NO critic_id and NO bipolar — the real legacy shape
        summary = {
            "run_id": "legacy_wolfflin_123",
            "stop_reason": "max_iterations",
            "total_iterations": 2,
            "best_iteration": 0,
            "best_score": 0.8,
            "score_progression": [0.8, 0.5],
        }
        (run_dir / "summary.json").write_text(json.dumps(summary))
        # critic_id lives in config.json only
        (run_dir / "config.json").write_text(json.dumps({"critic_id": "wolfflin"}))
        for i in range(2):
            iter_dir = run_dir / f"iter_{i:03d}"
            iter_dir.mkdir()
            crit = {
                "composite_score": summary["score_progression"][i],
                "accepted": True,
                "lens_summary": "test",
                "directives": ["do something"],
            }
            (iter_dir / "critique_summary.json").write_text(json.dumps(crit))

        narrative = build_narrative(run_dir)
        assert "Pole commitment:" in narrative
        assert "Score:" not in narrative


# ---------------------------------------------------------------------------
# generate_contact_sheet
# ---------------------------------------------------------------------------

class TestGenerateContactSheet:
    def test_generates_png(self, tmp_path):
        run_dir = _make_run_dir(tmp_path)
        sheet_path = generate_contact_sheet(run_dir)
        assert sheet_path.exists()
        assert sheet_path.suffix == ".png"
        img = Image.open(sheet_path)
        assert img.width > 0
        assert img.height > 0

    def test_custom_output_path(self, tmp_path):
        run_dir = _make_run_dir(tmp_path)
        custom = tmp_path / "custom_sheet.png"
        sheet_path = generate_contact_sheet(run_dir, output_path=custom)
        assert sheet_path == custom
        assert custom.exists()

    def test_missing_summary_raises(self, tmp_path):
        empty_dir = tmp_path / "no_summary"
        empty_dir.mkdir()
        with pytest.raises(FileNotFoundError):
            generate_contact_sheet(empty_dir)

    def test_zero_iterations_raises(self, tmp_path):
        run_dir = tmp_path / "zero_iters"
        run_dir.mkdir()
        summary = {"total_iterations": 0, "score_progression": []}
        (run_dir / "summary.json").write_text(json.dumps(summary))
        with pytest.raises(ValueError, match="No iterations"):
            generate_contact_sheet(run_dir)

    def test_handles_missing_images_gracefully(self, tmp_path):
        """Contact sheet should still generate even if iteration images are missing."""
        run_dir = _make_run_dir(tmp_path)
        # Remove one image
        (run_dir / "iter_001" / "image.png").unlink()
        sheet_path = generate_contact_sheet(run_dir)
        assert sheet_path.exists()


# ---------------------------------------------------------------------------
# save_narrative_md
# ---------------------------------------------------------------------------

class TestSaveNarrativeMd:
    def test_saves_markdown_file(self, tmp_path):
        run_dir = _make_run_dir(tmp_path)
        md_path = save_narrative_md(run_dir)
        assert md_path.exists()
        assert md_path.suffix == ".md"
        content = md_path.read_text()
        assert "test_run_123" in content

    def test_content_matches_build_narrative(self, tmp_path):
        run_dir = _make_run_dir(tmp_path)
        narrative = build_narrative(run_dir)
        md_path = save_narrative_md(run_dir)
        assert md_path.read_text() == narrative + "\n"
