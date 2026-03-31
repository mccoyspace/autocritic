"""
rewriteDrawer adapter: HTTP client, parameter space, and image acquisition.

Connects to a running rewriteDrawer FastAPI server to generate graph-based
drawings and capture them as PNG images for critic evaluation.

Requires:
- rewriteDrawer server running (default http://127.0.0.1:8010)
- cairosvg package for SVG→PNG conversion: pip install cairosvg
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

from autocritic.translator import ParamSpec, ParamSpace


# ---------------------------------------------------------------------------
# Parameter space definition
# ---------------------------------------------------------------------------

WOLFRAM_PARAM_SPACE = ParamSpace(specs=[
    ParamSpec(
        "seed_type", "enum",
        ("path3", "star3", "triangle", "bowtie", "square"),
        "path3",
        "Starting graph topology. path3 = three-node linear chain (organic, "
        "asymmetric growth). star3 = radial hub (centralized, hierarchical). "
        "triangle = closed cycle (compact, balanced). bowtie = two triangles "
        "sharing a vertex (tension, duality). square = four-sided cycle "
        "(stable, grid-like).",
    ),
    ParamSpec(
        "frames", "int", (1, 120), 24,
        "Number of growth steps. Each frame applies events_per_frame rewriting "
        "events. More frames = larger, denser, more intricate graph. Fewer = "
        "simpler, sparser structure. Controls overall development time.",
    ),
    ParamSpec(
        "events_per_frame", "int", (1, 500), 30,
        "Graph rewriting events per growth step. Higher = faster, denser growth "
        "per step. Lower = more gradual, delicate evolution. Total events = "
        "frames × events_per_frame.",
    ),
    ParamSpec(
        "event_selection", "enum",
        ("random", "hub_first", "newest_bias"),
        "random",
        "Strategy for picking which node to rewrite. random = weighted by "
        "connectivity (organic). hub_first = always pick densest node "
        "(creates hierarchical, centralized structure). newest_bias = favor "
        "recently created nodes (creates extending tendrils, frontier growth).",
    ),
    ParamSpec(
        "random_seed", "int", (0, 9999999), 13,
        "Deterministic RNG seed. Same seed with same parameters = identical "
        "result. Change to explore variation while keeping other parameters "
        "fixed. Good for comparing the effect of a single parameter change.",
    ),
    ParamSpec(
        "layout_iterations", "int", (1, 300), 60,
        "Spring-layout relaxation steps per frame. More = smoother, more "
        "settled node arrangement with clearer spatial structure. Fewer = "
        "more chaotic, compressed, organic-feeling positioning.",
    ),
    ParamSpec(
        "layout_spread", "float", (0.1, 5.0), 1.15,
        "Controls spacing between nodes in the force-directed layout. Higher = "
        "more spread out, airier composition with more negative space. Lower = "
        "tighter clustering, denser visual mass.",
    ),
    ParamSpec(
        "spawn_jitter", "float", (0.0, 1.0), 0.08,
        "Random displacement when new nodes are created. Higher = more organic "
        "scatter, irregular growth. Lower = more structured, predictable "
        "placement near parent nodes.",
    ),
    ParamSpec(
        "draw_mode", "enum",
        ("all", "short", "recent"),
        "all",
        "Which edges to render. all = every edge (full density). short = only "
        "the shortest edges by length percentile (cleaner, shows tightest "
        "structure). recent = only newest edges (shows growth front, temporal "
        "layering).",
    ),
    ParamSpec(
        "keep_percent", "float", (1.0, 100.0), 65.0,
        "When draw_mode=short, what percentile of edge lengths to keep. "
        "Lower = sparser, showing only the tightest local connections. "
        "Higher = more edges visible. Only active when draw_mode=short.",
    ),
    ParamSpec(
        "stroke_width_mm", "float", (0.01, 20.0), 0.5,
        "Line thickness in millimeters. Thicker = bolder, more visual mass, "
        "more painterly. Thinner = more delicate, more linear, finer detail.",
    ),
])

DEFAULT_WOLFRAM_PARAMS = WOLFRAM_PARAM_SPACE.defaults()

# Fixed export dimensions (reasonable for screen display + LLM vision)
_EXPORT_PAGE_WIDTH_MM = 800.0
_EXPORT_PAGE_HEIGHT_MM = 600.0
_EXPORT_MARGIN_MM = 30.0


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

def _post_json(
    url: str,
    data: dict[str, Any],
    timeout: float = 60.0,
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


def _get_bytes(url: str, timeout: float = 30.0) -> bytes:
    """GET raw bytes from a URL."""
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def check_server(base_url: str = "http://127.0.0.1:8010") -> bool:
    """Check if the rewriteDrawer server is reachable."""
    try:
        _get_bytes(f"{base_url}/api/options", timeout=5.0)
        return True
    except (urllib.error.URLError, OSError):
        return False


# ---------------------------------------------------------------------------
# Simulation and export
# ---------------------------------------------------------------------------

def simulate(
    params: dict[str, Any],
    base_url: str = "http://127.0.0.1:8010",
) -> dict[str, Any]:
    """Run a simulation with the given parameters.

    Returns the full simulation response with frames, nodes, and edges.
    """
    # Only send simulation-relevant params
    sim_params = {
        "seed_type": params.get("seed_type", "path3"),
        "frames": params.get("frames", 24),
        "events_per_frame": params.get("events_per_frame", 30),
        "event_selection": params.get("event_selection", "random"),
        "random_seed": params.get("random_seed", 13),
        "layout_iterations": params.get("layout_iterations", 60),
        "layout_spread": params.get("layout_spread", 1.15),
        "spawn_jitter": params.get("spawn_jitter", 0.08),
    }
    return _post_json(f"{base_url}/api/simulate", sim_params)


def export_frame(
    params: dict[str, Any],
    base_url: str = "http://127.0.0.1:8010",
) -> str:
    """Export the last frame as SVG.

    Returns the server-relative path to the raw SVG file.
    """
    frames = params.get("frames", 24)
    export_params = {
        # Simulation params (re-run internally by export)
        "seed_type": params.get("seed_type", "path3"),
        "frames": frames,
        "events_per_frame": params.get("events_per_frame", 30),
        "event_selection": params.get("event_selection", "random"),
        "random_seed": params.get("random_seed", 13),
        "layout_iterations": params.get("layout_iterations", 60),
        "layout_spread": params.get("layout_spread", 1.15),
        "spawn_jitter": params.get("spawn_jitter", 0.08),
        # Export params
        "frame_index": frames - 1,  # last frame
        "draw_mode": params.get("draw_mode", "all"),
        "keep_percent": params.get("keep_percent", 65.0),
        "stroke_width_mm": params.get("stroke_width_mm", 0.5),
        "page_width_mm": _EXPORT_PAGE_WIDTH_MM,
        "page_height_mm": _EXPORT_PAGE_HEIGHT_MM,
        "margin_mm": _EXPORT_MARGIN_MM,
    }
    result = _post_json(f"{base_url}/api/export", export_params)

    # Find the raw SVG file path
    for f in result.get("files", []):
        if f.get("label") == "Raw SVG":
            return f["path"]

    # Fallback: first file
    files = result.get("files", [])
    if files:
        return files[0]["path"]

    raise RuntimeError("Export returned no files")


def fetch_file(
    path: str,
    base_url: str = "http://127.0.0.1:8010",
) -> bytes:
    """Fetch a file from the rewriteDrawer server by its path."""
    # Path is server-relative like /exports/folder/raw.svg
    url = f"{base_url}{path}"
    return _get_bytes(url)


# ---------------------------------------------------------------------------
# SVG to PNG conversion
# ---------------------------------------------------------------------------

def svg_to_png(svg_bytes: bytes, width: int = 1024) -> bytes:
    """Convert SVG bytes to PNG bytes.

    Requires cairosvg: pip install cairosvg
    """
    try:
        import cairosvg
    except ImportError:
        raise ImportError(
            "cairosvg package required for SVG→PNG conversion. "
            "Install with: pip install 'autocritic[wolfram]'"
        )
    return cairosvg.svg2png(bytestring=svg_bytes, output_width=width)


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def acquire_image(
    params: dict[str, Any],
    output_path: Path,
    base_url: str = "http://127.0.0.1:8010",
) -> Path:
    """Full pipeline: simulate → export → fetch SVG → convert to PNG → save.

    Returns the path to the saved PNG file.
    """
    # Export (internally runs simulation)
    svg_path = export_frame(params, base_url)

    # Fetch the SVG
    svg_bytes = fetch_file(svg_path, base_url)

    # Convert to PNG
    png_bytes = svg_to_png(svg_bytes)

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(png_bytes)

    return output_path
