"""Tests for the rewriteDrawer adapter: parameter space, HTTP client, SVG conversion."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from autocritic.adapters.rewriter import (
    DEFAULT_REWRITER_PARAMS,
    REWRITER_PARAM_SPACE,
    check_server,
    export_frame,
    fetch_file,
    simulate,
)


# ---------------------------------------------------------------------------
# Parameter space
# ---------------------------------------------------------------------------

class TestRewriterParamSpace:
    def test_has_all_params(self):
        names = {s.name for s in REWRITER_PARAM_SPACE.specs}
        expected = {
            "seed_type", "frames", "events_per_frame", "event_selection",
            "random_seed", "layout_iterations", "layout_spread",
            "spawn_jitter", "draw_mode", "keep_percent", "stroke_width_mm",
        }
        assert names == expected

    def test_defaults_valid(self):
        defaults = REWRITER_PARAM_SPACE.defaults()
        clamped = REWRITER_PARAM_SPACE.clamp(defaults)
        assert defaults == clamped

    def test_default_params_match_space(self):
        assert DEFAULT_REWRITER_PARAMS == REWRITER_PARAM_SPACE.defaults()

    def test_describe_readable(self):
        desc = REWRITER_PARAM_SPACE.describe()
        assert "seed_type" in desc
        assert "frames" in desc
        assert "layout_spread" in desc

    def test_clamp_enforces_ranges(self):
        bad = {"frames": 200, "layout_spread": -1.0, "seed_type": "invalid"}
        clamped = REWRITER_PARAM_SPACE.clamp(bad)
        assert clamped["frames"] == 120
        assert clamped["layout_spread"] == 0.1
        assert clamped["seed_type"] == "path3"  # reset to default

    def test_enum_types(self):
        for spec in REWRITER_PARAM_SPACE.specs:
            if spec.type == "enum":
                assert spec.default in spec.range, (
                    f"{spec.name} default {spec.default} not in {spec.range}"
                )

    def test_numeric_defaults_in_range(self):
        for spec in REWRITER_PARAM_SPACE.specs:
            if spec.type in ("int", "float"):
                lo, hi = spec.range
                assert lo <= spec.default <= hi, (
                    f"{spec.name} default {spec.default} not in [{lo}, {hi}]"
                )


# ---------------------------------------------------------------------------
# HTTP client (mocked)
# ---------------------------------------------------------------------------

class TestSimulateMocked:
    def test_sends_correct_params(self):
        with patch("autocritic.adapters.rewriter._post_json") as mock_post:
            mock_post.return_value = {"frames": [], "settings": {}}
            simulate(DEFAULT_REWRITER_PARAMS, base_url="http://test:8010")

        call_args = mock_post.call_args
        url = call_args[0][0]
        data = call_args[0][1]
        assert "simulate" in url
        assert data["seed_type"] == "path3"
        assert data["frames"] == 24
        assert data["events_per_frame"] == 30

    def test_only_sends_sim_params(self):
        params = dict(DEFAULT_REWRITER_PARAMS)
        params["draw_mode"] = "short"  # display param, not sim param
        params["stroke_width_mm"] = 2.0

        with patch("autocritic.adapters.rewriter._post_json") as mock_post:
            mock_post.return_value = {"frames": [], "settings": {}}
            simulate(params, base_url="http://test:8010")

        data = mock_post.call_args[0][1]
        assert "draw_mode" not in data
        assert "stroke_width_mm" not in data


class TestExportFrameMocked:
    def test_exports_last_frame(self):
        with patch("autocritic.adapters.rewriter._post_json") as mock_post:
            mock_post.return_value = {
                "files": [
                    {"label": "Raw SVG", "path": "/exports/test/raw.svg"},
                    {"label": "Metadata", "path": "/exports/test/metadata.json"},
                ],
            }
            path = export_frame(DEFAULT_REWRITER_PARAMS)

        assert path == "/exports/test/raw.svg"
        data = mock_post.call_args[0][1]
        assert data["frame_index"] == 23  # last frame of 24

    def test_includes_display_params(self):
        params = dict(DEFAULT_REWRITER_PARAMS)
        params["draw_mode"] = "short"
        params["keep_percent"] = 50.0

        with patch("autocritic.adapters.rewriter._post_json") as mock_post:
            mock_post.return_value = {
                "files": [{"label": "Raw SVG", "path": "/exports/t/raw.svg"}],
            }
            export_frame(params)

        data = mock_post.call_args[0][1]
        assert data["draw_mode"] == "short"
        assert data["keep_percent"] == 50.0


class TestCheckServer:
    def test_server_up(self):
        with patch("autocritic.adapters.rewriter._get_bytes") as mock_get:
            mock_get.return_value = b'{"options": {}}'
            assert check_server("http://test:8010") is True

    def test_server_down(self):
        with patch("autocritic.adapters.rewriter._get_bytes") as mock_get:
            mock_get.side_effect = OSError("Connection refused")
            assert check_server("http://test:8010") is False


# ---------------------------------------------------------------------------
# SVG to PNG (requires cairosvg)
# ---------------------------------------------------------------------------

cairosvg = pytest.importorskip("cairosvg", reason="cairosvg not installed")


class TestSvgToPng:
    def test_converts_minimal_svg(self):
        from autocritic.adapters.rewriter import svg_to_png

        svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40" fill="black"/></svg>'
        png = svg_to_png(svg, width=64)
        assert png[:4] == b"\x89PNG"
        assert len(png) > 100
