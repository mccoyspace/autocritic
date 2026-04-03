"""Tests for the Stable Diffusion adapter (all mocked, no server needed)."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from autocritic.adapters.stable_diffusion import (
    SD_PARAM_SPACE,
    DEFAULT_SD_PARAMS,
    check_server,
    generate_image,
    acquire_image,
)


# ---------------------------------------------------------------------------
# Parameter space
# ---------------------------------------------------------------------------

class TestSDParamSpace:
    def test_defaults_valid(self):
        defaults = SD_PARAM_SPACE.defaults()
        assert defaults["prompt"] == ""
        assert defaults["negative_prompt"] == ""
        assert defaults["steps"] == 30
        assert defaults["cfg_scale"] == 7.0
        assert defaults["width"] == 512
        assert defaults["height"] == 512
        assert defaults["seed"] == -1
        assert defaults["sampler_name"] == "DPM++ 2M Karras"

    def test_clamp_numeric_ranges(self):
        params = dict(DEFAULT_SD_PARAMS)
        params["steps"] = 200
        params["cfg_scale"] = 50.0
        params["width"] = 5000
        clamped = SD_PARAM_SPACE.clamp(params)
        assert clamped["steps"] == 150
        assert clamped["cfg_scale"] == 30.0
        assert clamped["width"] == 2048

    def test_clamp_string_passthrough(self):
        params = dict(DEFAULT_SD_PARAMS)
        params["prompt"] = "anything at all, (detailed:1.4)"
        clamped = SD_PARAM_SPACE.clamp(params)
        assert clamped["prompt"] == "anything at all, (detailed:1.4)"

    def test_clamp_invalid_sampler(self):
        params = dict(DEFAULT_SD_PARAMS)
        params["sampler_name"] = "NonexistentSampler"
        clamped = SD_PARAM_SPACE.clamp(params)
        assert clamped["sampler_name"] == "DPM++ 2M Karras"  # reset to default

    def test_describe_shows_free_text(self):
        desc = SD_PARAM_SPACE.describe()
        assert "free-text" in desc
        assert "prompt" in desc
        assert "options:" in desc  # for sampler_name


# ---------------------------------------------------------------------------
# check_server
# ---------------------------------------------------------------------------

class TestCheckServer:
    def test_server_up(self):
        with patch("autocritic.adapters.stable_diffusion.urllib.request.urlopen"):
            assert check_server("http://localhost:7860") is True

    def test_server_down(self):
        import urllib.error
        with patch(
            "autocritic.adapters.stable_diffusion.urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            assert check_server("http://localhost:7860") is False


# ---------------------------------------------------------------------------
# generate_image
# ---------------------------------------------------------------------------

# Minimal 1x1 red PNG for test fixtures
_TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
    b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
    b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)
_TINY_PNG_B64 = base64.b64encode(_TINY_PNG).decode()


def _mock_urlopen(response_data: dict):
    """Create a mock urlopen that returns JSON response_data."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return patch(
        "autocritic.adapters.stable_diffusion.urllib.request.urlopen",
        return_value=mock_resp,
    )


class TestGenerateImage:
    def test_returns_png_bytes(self):
        with _mock_urlopen({"images": [_TINY_PNG_B64]}):
            result = generate_image(DEFAULT_SD_PARAMS)
        assert result == _TINY_PNG

    def test_correct_payload(self):
        params = dict(DEFAULT_SD_PARAMS)
        params["prompt"] = "a red circle"
        params["steps"] = 20
        with _mock_urlopen({"images": [_TINY_PNG_B64]}) as mock_open:
            generate_image(params)
        # Inspect what was POSTed
        call_args = mock_open.call_args
        req = call_args[0][0]
        payload = json.loads(req.data.decode())
        assert payload["prompt"] == "a red circle"
        assert payload["steps"] == 20

    def test_rounds_dimensions_to_multiple_of_8(self):
        params = dict(DEFAULT_SD_PARAMS)
        params["width"] = 515  # should round to 512
        params["height"] = 769  # should round to 768
        with _mock_urlopen({"images": [_TINY_PNG_B64]}) as mock_open:
            generate_image(params)
        payload = json.loads(mock_open.call_args[0][0].data.decode())
        assert payload["width"] % 8 == 0
        assert payload["height"] % 8 == 0

    def test_empty_images_raises(self):
        with _mock_urlopen({"images": []}):
            with pytest.raises(RuntimeError, match="no images"):
                generate_image(DEFAULT_SD_PARAMS)

    def test_missing_images_key_raises(self):
        with _mock_urlopen({}):
            with pytest.raises(RuntimeError, match="no images"):
                generate_image(DEFAULT_SD_PARAMS)


# ---------------------------------------------------------------------------
# acquire_image
# ---------------------------------------------------------------------------

class TestAcquireImage:
    def test_writes_png_to_path(self, tmp_path):
        output = tmp_path / "output.png"
        with _mock_urlopen({"images": [_TINY_PNG_B64]}):
            result = acquire_image(DEFAULT_SD_PARAMS, output)
        assert result == output
        assert output.exists()
        assert output.read_bytes() == _TINY_PNG

    def test_creates_parent_dirs(self, tmp_path):
        output = tmp_path / "nested" / "dir" / "output.png"
        with _mock_urlopen({"images": [_TINY_PNG_B64]}):
            acquire_image(DEFAULT_SD_PARAMS, output)
        assert output.exists()
