"""
Post-run report: contact sheet with narrative summary.

Generates a single PNG that answers 'what happened this run?' —
thumbnail per iteration with score labels, best-iteration marker,
and a narrative text block at the bottom.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

THUMB_W = 400
THUMB_H = 300
PAD = 24
LABEL_H = 60
NARRATIVE_LINE_W = 100  # characters per line in narrative block
FONT_SIZE = 18
FONT_SIZE_SMALL = 14
FONT_SIZE_NARRATIVE = 15
BG_COLOR = (255, 255, 255)
TEXT_COLOR = (30, 30, 30)
ACCENT_COLOR = (60, 130, 60)
BEST_COLOR = (180, 130, 0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try system monospace, fall back to default."""
    for name in [
        "/System/Library/Fonts/SFMono-Regular.otf",
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.dfont",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _swap_dark_bg(img: Image.Image, threshold: int = 40) -> Image.Image:
    """Replace near-black pixels with white, preserving colored content."""
    arr = np.array(img)
    dark = np.all(arr < threshold, axis=2)
    arr[dark] = [255, 255, 255]
    return Image.fromarray(arr)


def _thumbnail(img_path: Path, size: tuple[int, int]) -> Image.Image:
    """Load and resize image to fit within size, centered on white bg."""
    thumb = Image.new("RGB", size, BG_COLOR)
    try:
        src = Image.open(img_path).convert("RGB")
    except Exception:
        return thumb
    src = _swap_dark_bg(src)
    src.thumbnail(size, Image.LANCZOS)
    x = (size[0] - src.width) // 2
    y = (size[1] - src.height) // 2
    thumb.paste(src, (x, y))
    return thumb


# ---------------------------------------------------------------------------
# Narrative generation
# ---------------------------------------------------------------------------

def build_narrative(run_dir: Path) -> str:
    """Build a short human-readable narrative from the run artifacts."""
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        return "No summary found."

    summary = json.loads(summary_path.read_text())
    run_id = summary.get("run_id", "unknown")
    stop_reason = summary.get("stop_reason", "unknown")
    total = summary.get("total_iterations", 0)
    best_iter = summary.get("best_iteration", 0)
    best_score = summary.get("best_score", 0)
    scores = summary.get("score_progression", [])

    # Load critique summaries for each iteration
    iter_narratives = []
    for i in range(total):
        crit_path = run_dir / f"iter_{i:03d}" / "critique_summary.json"
        if not crit_path.exists():
            continue
        crit = json.loads(crit_path.read_text())
        lens = crit.get("lens_summary", "")
        directives = crit.get("directives", [])
        score = crit.get("composite_score", 0)
        accepted = crit.get("accepted", True)

        # Extract first directive's core idea (strip markdown bold markers)
        first_directive = ""
        if directives:
            d = directives[0]
            # Remove leading number and bold markers
            d = d.lstrip("0123456789. ")
            d = d.replace("**", "")
            # Take just the part before the colon or first sentence
            if ":" in d:
                d = d.split(":")[0]
            elif "." in d:
                d = d.split(".")[0]
            first_directive = d.strip()

        iter_narratives.append({
            "i": i,
            "score": score,
            "accepted": accepted,
            "lens": lens,
            "first_directive": first_directive,
        })

    # Build the narrative text
    lines = []
    lines.append(f"Run: {run_id}")
    lines.append(f"Stopped: {_readable_stop(stop_reason)} after {total} iteration{'s' if total != 1 else ''}")
    if scores:
        lines.append(f"Score: {scores[0]:.2f} → {scores[-1]:.2f} (best {best_score:.2f} at iter {best_iter})")
    lines.append("")

    for n in iter_narratives:
        tag = "★" if n["i"] == best_iter else " "
        status = "✓" if n["accepted"] else "✗"
        line = f"{tag} Iter {n['i']} [{n['score']:.2f}] {status}"
        lines.append(line)

        # One-line lens summary (truncated)
        if n["lens"]:
            # Strip markdown bold
            lens_clean = n["lens"].replace("**", "")
            if len(lens_clean) > 90:
                lens_clean = lens_clean[:87] + "..."
            lines.append(f"  Focus: {lens_clean}")

        if n["first_directive"]:
            d = n["first_directive"]
            if len(d) > 80:
                d = d[:77] + "..."
            lines.append(f"  → {d}")
        lines.append("")

    return "\n".join(lines).strip()


def _readable_stop(reason: str) -> str:
    return {
        "max_iterations": "reached max iterations",
        "high_score": "achieved high score (>0.9)",
        "plateaued": "score plateaued",
    }.get(reason, reason)


# ---------------------------------------------------------------------------
# Contact sheet
# ---------------------------------------------------------------------------

def generate_contact_sheet(run_dir: Path, output_path: Path | None = None) -> Path:
    """Generate a contact sheet PNG with thumbnails, scores, and narrative.

    Args:
        run_dir: Path to the run directory (e.g. runs/wolfram_123456)
        output_path: Where to save. Defaults to run_dir/contact_sheet.png

    Returns:
        Path to the generated contact sheet.
    """
    if output_path is None:
        output_path = run_dir / "contact_sheet.png"

    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"No summary.json in {run_dir}")

    summary = json.loads(summary_path.read_text())
    total = summary.get("total_iterations", 0)
    best_iter = summary.get("best_iteration", 0)
    scores = summary.get("score_progression", [])

    if total == 0:
        raise ValueError("No iterations to report")

    # Load fonts
    font = _load_font(FONT_SIZE)
    font_small = _load_font(FONT_SIZE_SMALL)
    font_narrative = _load_font(FONT_SIZE_NARRATIVE)

    # Layout: thumbnails in a row, narrative below
    # For many iterations, wrap to multiple rows
    max_cols = min(total, 5)
    rows = (total + max_cols - 1) // max_cols
    thumb_area_w = max_cols * (THUMB_W + PAD) + PAD
    thumb_area_h = rows * (THUMB_H + LABEL_H + PAD) + PAD

    # Build narrative and measure text height
    narrative = build_narrative(run_dir)
    wrapped = _wrap_narrative(narrative, NARRATIVE_LINE_W)
    narrative_h = len(wrapped.split("\n")) * (FONT_SIZE_NARRATIVE + 4) + PAD * 2

    # Total canvas
    canvas_w = max(thumb_area_w, 800)
    canvas_h = thumb_area_h + narrative_h + PAD
    img = Image.new("RGB", (canvas_w, canvas_h), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Draw thumbnails
    for i in range(total):
        col = i % max_cols
        row = i // max_cols
        x = PAD + col * (THUMB_W + PAD)
        y = PAD + row * (THUMB_H + LABEL_H + PAD)

        # Image thumbnail
        iter_img_path = run_dir / f"iter_{i:03d}" / "image.png"
        thumb = _thumbnail(iter_img_path, (THUMB_W, THUMB_H))
        img.paste(thumb, (x, y))

        # Label
        score = scores[i] if i < len(scores) else 0
        label = f"iter {i}  —  {score:.3f}"
        if i == best_iter:
            label += "  ★ best"
            label_color = BEST_COLOR
        else:
            label_color = TEXT_COLOR

        label_y = y + THUMB_H + 6
        draw.text((x + 4, label_y), label, fill=label_color, font=font)

        # Accepted/rejected indicator
        crit_path = run_dir / f"iter_{i:03d}" / "critique_summary.json"
        if crit_path.exists():
            crit = json.loads(crit_path.read_text())
            accepted = crit.get("accepted", True)
            if i > 0:
                delta = score - (scores[i - 1] if i - 1 < len(scores) else 0)
                delta_str = f"{'✓' if accepted else '✗'}  Δ{delta:+.3f}"
                draw.text(
                    (x + 4, label_y + FONT_SIZE + 4),
                    delta_str,
                    fill=ACCENT_COLOR if accepted else (200, 100, 100),
                    font=font_small,
                )

    # Draw narrative
    narrative_y = thumb_area_h + PAD // 2
    # Divider line
    draw.line(
        [(PAD, narrative_y), (canvas_w - PAD, narrative_y)],
        fill=(80, 80, 80), width=1,
    )
    narrative_y += PAD // 2

    for line in wrapped.split("\n"):
        color = TEXT_COLOR
        if line.startswith("★"):
            color = BEST_COLOR
        elif line.startswith("  →"):
            color = ACCENT_COLOR
        draw.text((PAD, narrative_y), line, fill=color, font=font_narrative)
        narrative_y += FONT_SIZE_NARRATIVE + 4

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


def _wrap_narrative(text: str, width: int) -> str:
    """Wrap narrative text, preserving intentional line breaks."""
    lines = text.split("\n")
    wrapped_lines = []
    for line in lines:
        if len(line) <= width:
            wrapped_lines.append(line)
        else:
            indent = ""
            if line.startswith("  "):
                indent = "  "
            wrapped_lines.extend(
                textwrap.wrap(line, width=width, subsequent_indent=indent + "  ")
            )
    return "\n".join(wrapped_lines)


# ---------------------------------------------------------------------------
# Also save narrative as markdown for searchability
# ---------------------------------------------------------------------------

def save_narrative_md(run_dir: Path) -> Path:
    """Save the narrative as a markdown file alongside the contact sheet."""
    narrative = build_narrative(run_dir)
    out = run_dir / "narrative.md"
    out.write_text(narrative + "\n")
    return out
