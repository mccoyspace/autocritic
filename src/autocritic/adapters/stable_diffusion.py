"""
Stable Diffusion adapter: parameter space and image acquisition via
the AUTOMATIC1111 webui API (POST /sdapi/v1/txt2img).

Requires a running AUTOMATIC1111 server started with the --api flag.
Default URL: http://127.0.0.1:7860
"""

from __future__ import annotations

import base64
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

from autocritic.translator import ParamSpec, ParamSpace


# ---------------------------------------------------------------------------
# Parameter space definition
# ---------------------------------------------------------------------------

SD_PARAM_SPACE = ParamSpace(specs=[
    ParamSpec(
        "prompt", "string", (), "",
        "The Stable Diffusion generation prompt. Use natural language to "
        "describe the desired image. SD supports emphasis syntax: (word:1.3) "
        "increases weight, (word:0.7) decreases it. Terms earlier in the "
        "prompt have more influence. Keep the prompt concise — SD has a ~75 "
        "token effective limit. Replace or restructure terms rather than "
        "always appending.",
    ),
    ParamSpec(
        "negative_prompt", "string", (), "",
        "Terms to exclude from generation. Common entries: 'blurry, "
        "low quality, watermark, text'. Helps steer away from undesired "
        "artifacts.",
    ),
    ParamSpec(
        "steps", "int", (1, 150), 30,
        "Number of denoising steps. More steps = finer detail but slower. "
        "20-30 is usually sufficient; above 50 has diminishing returns.",
    ),
    ParamSpec(
        "cfg_scale", "float", (1.0, 30.0), 7.0,
        "Classifier-free guidance scale — how strongly the image follows "
        "the prompt. Low (1-5) = more creative/loose. High (10-20) = more "
        "literal but can oversaturate. 7 is a good default.",
    ),
    ParamSpec(
        "width", "int", (256, 2048), 512,
        "Image width in pixels. Must be a multiple of 8. Common values: "
        "512, 768, 1024. Larger = slower and more VRAM.",
    ),
    ParamSpec(
        "height", "int", (256, 2048), 512,
        "Image height in pixels. Must be a multiple of 8. Common values: "
        "512, 768, 1024. Larger = slower and more VRAM.",
    ),
    ParamSpec(
        "seed", "int", (-1, 2**32 - 1), -1,
        "Random seed. -1 = random each time. Set a specific seed for "
        "reproducibility — same seed + same params = same image.",
    ),
    ParamSpec(
        "sampler_name", "enum",
        ("Euler", "Euler a", "DPM++ 2M Karras", "DPM++ SDE Karras",
         "DPM++ 2M SDE Karras", "DDIM", "UniPC"),
        "DPM++ 2M Karras",
        "Sampling algorithm. 'DPM++ 2M Karras' is a good general default. "
        "'Euler a' is fast and creative. 'DDIM' is deterministic.",
    ),
])

DEFAULT_SD_PARAMS = SD_PARAM_SPACE.defaults()


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _post_json(
    url: str,
    data: dict[str, Any],
    timeout: float = 120.0,
) -> dict[str, Any]:
    """POST JSON to a URL and return parsed JSON response."""
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_server(base_url: str = "http://127.0.0.1:7860") -> bool:
    """Check if the AUTOMATIC1111 server is reachable."""
    try:
        req = urllib.request.Request(
            f"{base_url}/sdapi/v1/options", method="GET",
        )
        with urllib.request.urlopen(req, timeout=5.0):
            pass
        return True
    except (urllib.error.URLError, OSError):
        return False


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------

def generate_image(
    params: dict[str, Any],
    base_url: str = "http://127.0.0.1:7860",
) -> bytes:
    """Generate an image via txt2img and return PNG bytes.

    Raises RuntimeError if the response contains no image data.
    """
    # Round dimensions to multiples of 8
    width = max(256, min(2048, int(round(params.get("width", 512) / 8)) * 8))
    height = max(256, min(2048, int(round(params.get("height", 512) / 8)) * 8))

    payload = {
        "prompt": params.get("prompt", ""),
        "negative_prompt": params.get("negative_prompt", ""),
        "steps": params.get("steps", 30),
        "cfg_scale": params.get("cfg_scale", 7.0),
        "width": width,
        "height": height,
        "seed": params.get("seed", -1),
        "sampler_name": params.get("sampler_name", "DPM++ 2M Karras"),
    }

    result = _post_json(f"{base_url}/sdapi/v1/txt2img", payload)

    images = result.get("images", [])
    if not images:
        raise RuntimeError(
            "AUTOMATIC1111 returned no images. Check server logs."
        )

    return base64.b64decode(images[0])


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def acquire_image(
    params: dict[str, Any],
    output_path: Path,
    base_url: str = "http://127.0.0.1:7860",
) -> Path:
    """Generate an image and save it as PNG.

    Returns the path to the saved file.
    """
    png_bytes = generate_image(params, base_url)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(png_bytes)
    return output_path
