#!/usr/bin/env python3
"""
Generate programmatic test images with known visual properties.

Each image is designed so that a specific theorist's framework should
produce a distinct, predictable response. This lets us test whether
critics actually see what their theory tells them to look for.

No external assets needed — everything is drawn with Pillow.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


OUTPUT_DIR = Path(__file__).resolve().parent.parent / "evals" / "fixtures" / "images"


def make_linear_composition(size: int = 512) -> Image.Image:
    """
    Strong contours, discrete bounded forms, clear edges.
    A Wölfflin critic should call this 'linear' (pole A).
    """
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    # Sharp-edged geometric forms with clear contours
    draw.rectangle([80, 80, 230, 350], outline="black", width=3)
    draw.rectangle([270, 120, 430, 400], outline="black", width=3)
    draw.ellipse([150, 200, 350, 380], outline="black", width=3)
    # Strong horizontal and vertical lines
    draw.line([50, 420, 460, 420], fill="black", width=2)
    draw.line([250, 50, 250, 460], fill="black", width=1)
    return img


def make_painterly_composition(size: int = 512) -> Image.Image:
    """
    Soft edges, tonal masses, forms blending into each other.
    A Wölfflin critic should call this 'painterly' (pole B).
    """
    img = Image.new("RGB", (size, size), (240, 235, 225))
    draw = ImageDraw.Draw(img)
    # Overlapping soft-edged ellipses creating tonal masses
    for x, y, r, color in [
        (180, 200, 120, (80, 70, 90)),
        (280, 250, 100, (100, 90, 80)),
        (220, 300, 140, (70, 80, 70)),
        (320, 180, 90, (90, 80, 100)),
        (150, 280, 110, (85, 85, 75)),
    ]:
        overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([x - r, y - r, x + r, y + r], fill=color + (60,))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    return img


def make_strong_notan(size: int = 512) -> Image.Image:
    """
    High-contrast two-value design with clear dark/light massing.
    A Dow critic should identify strong notan structure.
    """
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    # Bold dark masses creating a clear two-value pattern
    draw.polygon([(50, 50), (250, 50), (200, 250), (80, 200)], fill="black")
    draw.polygon([(300, 300), (480, 280), (460, 480), (280, 460)], fill="black")
    draw.rectangle([200, 150, 310, 310], fill="black")
    return img


def make_weak_notan(size: int = 512) -> Image.Image:
    """
    Muddy middle tones, no clear dark/light separation.
    A Dow critic should identify weak notan — no clear massing.
    """
    img = Image.new("RGB", (size, size), (160, 155, 150))
    draw = ImageDraw.Draw(img)
    # Everything in close middle values
    for x, y, w, h, v in [
        (60, 80, 150, 120, 140), (220, 60, 180, 160, 170),
        (100, 250, 200, 150, 145), (320, 280, 140, 180, 165),
        (180, 180, 160, 140, 155),
    ]:
        draw.rectangle([x, y, x + w, y + h], fill=(v, v - 5, v - 10))
    return img


def make_diagonal_tension(size: int = 512) -> Image.Image:
    """
    Strong diagonal forces, point concentrations, directional energy.
    A Kandinsky critic should read warmth, tension, and counterpoint.
    """
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    # Dominant diagonal
    draw.line([80, 430, 420, 80], fill="black", width=4)
    # Counter-diagonal (creating tension)
    draw.line([100, 100, 350, 380], fill=(80, 80, 80), width=2)
    # Point concentrations
    draw.ellipse([390, 60, 430, 100], fill="black")  # upper right: high tension
    draw.ellipse([240, 240, 270, 270], fill="black")  # center: low tension
    # Horizontal (cold) counterpoint
    draw.line([50, 350, 460, 350], fill=(120, 120, 120), width=2)
    return img


def make_static_horizontal(size: int = 512) -> Image.Image:
    """
    Dominated by horizontals, few verticals, no diagonals.
    A Kandinsky critic should read coldness and repose.
    """
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    for y in [100, 180, 260, 340, 420]:
        draw.line([60, y, 450, y], fill="black", width=2)
    # Single small point
    draw.ellipse([245, 245, 265, 265], fill="black")
    return img


def make_regular_pattern(size: int = 512) -> Image.Image:
    """
    Highly regular repeat pattern — maximum redundancy.
    A Gombrich critic should note high redundancy, habituation risk.
    """
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    unit = 64
    for row in range(size // unit):
        for col in range(size // unit):
            x, y = col * unit, row * unit
            draw.rectangle([x + 8, y + 8, x + unit - 8, y + unit - 8],
                           outline="black", width=2)
            draw.ellipse([x + 16, y + 16, x + unit - 16, y + unit - 16],
                         fill=(60, 60, 60))
    return img


def make_varied_pattern(size: int = 512) -> Image.Image:
    """
    Pattern with intentional variation — balanced redundancy and information.
    A Gombrich critic should note effective monotony/variety balance.
    """
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    unit = 64
    for row in range(size // unit):
        for col in range(size // unit):
            x, y = col * unit, row * unit
            # Base pattern
            draw.rectangle([x + 8, y + 8, x + unit - 8, y + unit - 8],
                           outline="black", width=2)
            # Variation: rotate, shift, or change every 3rd unit
            if (row + col) % 3 == 0:
                draw.ellipse([x + 12, y + 12, x + unit - 12, y + unit - 12],
                             fill=(120, 40, 40))
            elif (row * col) % 5 == 0:
                draw.line([x + 8, y + 8, x + unit - 8, y + unit - 8],
                          fill="black", width=2)
            else:
                draw.ellipse([x + 16, y + 16, x + unit - 16, y + unit - 16],
                             fill=(60, 60, 60))
    return img


def make_unbalanced_composition(size: int = 512) -> Image.Image:
    """
    Deliberately off-balance: heavy mass at upper-right, nothing to counterweight.
    An Arnheim critic should detect unresolved perceptual stress.
    """
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    # Heavy dark mass at upper right
    draw.ellipse([320, 40, 480, 200], fill=(30, 30, 30))
    # Tiny element at lower left (insufficient counterweight)
    draw.ellipse([60, 400, 90, 430], fill=(100, 100, 100))
    return img


def make_balanced_asymmetry(size: int = 512) -> Image.Image:
    """
    Asymmetric but balanced through weight distribution.
    An Arnheim critic should recognize equilibrium of forces.
    """
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    # Large light mass at left
    draw.ellipse([40, 120, 250, 380], fill=(180, 180, 180))
    # Small dark mass at right (balances through higher weight)
    draw.ellipse([350, 200, 430, 310], fill=(30, 30, 30))
    # Connecting directional element
    draw.line([250, 250, 350, 255], fill=(120, 120, 120), width=2)
    return img


def generate_all():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    images = {
        "linear_composition": make_linear_composition,
        "painterly_composition": make_painterly_composition,
        "strong_notan": make_strong_notan,
        "weak_notan": make_weak_notan,
        "diagonal_tension": make_diagonal_tension,
        "static_horizontal": make_static_horizontal,
        "regular_pattern": make_regular_pattern,
        "varied_pattern": make_varied_pattern,
        "unbalanced_composition": make_unbalanced_composition,
        "balanced_asymmetry": make_balanced_asymmetry,
    }
    for name, fn in images.items():
        path = OUTPUT_DIR / f"{name}.png"
        fn().save(path)
        print(f"  {path}")
    print(f"\nGenerated {len(images)} test images in {OUTPUT_DIR}")


if __name__ == "__main__":
    generate_all()
