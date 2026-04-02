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


# ---------------------------------------------------------------------------
# Albers: color interaction and simultaneous contrast
# ---------------------------------------------------------------------------

def make_simultaneous_contrast(size: int = 512) -> Image.Image:
    """
    Same physical gray on two radically different grounds.
    An Albers critic should identify simultaneous contrast and the
    subtraction principle — the ground alters the apparent color.
    """
    img = Image.new("RGB", (size, size), (128, 128, 128))
    draw = ImageDraw.Draw(img)
    half = size // 2
    # Left ground: dark blue-gray
    draw.rectangle([0, 0, half, size], fill=(40, 40, 80))
    # Right ground: warm orange
    draw.rectangle([half, 0, size, size], fill=(220, 160, 60))
    # Identical mid-gray rectangles on each ground
    pad, rw, rh = 78, 128, 152
    gray = (128, 128, 128)
    draw.rectangle([pad, 180, pad + rw, 180 + rh], fill=gray)
    draw.rectangle([half + pad, 180, half + pad + rw, 180 + rh], fill=gray)
    # Connecting line to make "same color" explicit
    draw.line([pad + rw, 256, half + pad, 256], fill=gray, width=1)
    return img


def make_color_no_interaction(size: int = 512) -> Image.Image:
    """
    Isolated color swatches on white — no adjacency, no interaction.
    An Albers critic should note the absence of color interaction,
    no simultaneous contrast, no subtraction.
    """
    img = Image.new("RGB", (size, size), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    sq = 60
    colors = [
        ((200, 60, 60), (50, 226)),
        ((60, 60, 200), (160, 226)),
        ((60, 180, 60), (270, 226)),
        ((220, 220, 60), (380, 226)),
        ((128, 128, 128), (215, 100)),
    ]
    for color, (x, y) in colors:
        draw.rectangle([x, y, x + sq, y + sq], fill=color)
    return img


# ---------------------------------------------------------------------------
# Klee: movement, line energy, dynamic balance
# ---------------------------------------------------------------------------

def make_active_line_walk(size: int = 512) -> Image.Image:
    """
    A wandering active line (point on a walk), an arrow, a spiral,
    a pendulum arc. Records of movement and energy.
    A Klee critic should read active line, genesis, gravitational dynamics.
    """
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    # Active line: a point on a walk
    waypoints = [
        (40, 400), (100, 350), (130, 280), (180, 310),
        (220, 200), (280, 230), (310, 150), (370, 180),
        (400, 100), (440, 130),
    ]
    for i in range(len(waypoints) - 1):
        draw.line([waypoints[i], waypoints[i + 1]], fill="black", width=3)
    # Spiral at termination (decreasing arcs)
    cx, cy = 440, 130
    import math
    for j, r in enumerate([30, 20, 12, 6]):
        start = j * 90
        draw.arc([cx - r, cy - r, cx + r, cy + r], start, start + 270,
                 fill="black", width=2)
    # Arrow: directed energy, aspiration against gravity
    draw.line([(60, 460), (200, 340)], fill="black", width=4)
    # Arrowhead
    draw.polygon([(200, 340), (190, 360), (210, 355)], fill="black")
    # Pendulum arc at bottom
    draw.arc([300, 350, 460, 500], start=200, end=340,
             fill=(100, 100, 100), width=2)
    # Pendulum swing limits
    draw.ellipse([310, 410, 320, 420], fill=(100, 100, 100))
    draw.ellipse([445, 410, 455, 420], fill=(100, 100, 100))
    return img


def make_passive_static_grid(size: int = 512) -> Image.Image:
    """
    Rigid grid of horizontal/vertical lines, points at rest, mirror symmetry.
    A Klee critic should note passive line, no movement, dead symmetry.
    """
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    positions = [64, 128, 192, 256, 320, 384, 448]
    for y in positions:
        draw.line([64, y, 448, y], fill="black", width=2)
    for x in positions:
        draw.line([x, 64, x, 448], fill="black", width=2)
    # Points at rest at intersections
    for x in positions:
        for y in positions:
            draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill="black")
    return img


# ---------------------------------------------------------------------------
# Ruskin: gradation, mystery, delicacy
# ---------------------------------------------------------------------------

def make_continuous_gradation(size: int = 512) -> Image.Image:
    """
    Soft radial gradation, no outlines, partial visibility, delicate forms.
    A Ruskin critic should identify gradation, roundness, mystery, delicacy.
    """
    bg = (245, 240, 230)
    img = Image.new("RGBA", (size, size), bg + (255,))
    # Main gradated ellipse — roundness through tonal transition
    for center, max_r, base_color in [
        ((256, 256), 180, (60, 50, 40)),
        ((360, 160), 80, (50, 55, 70)),   # partially off-canvas = mystery
        ((140, 380), 60, (70, 60, 50)),    # very faint = delicacy
    ]:
        cx, cy = center
        steps = 50
        for i in range(steps, 0, -1):
            r = int(max_r * i / steps)
            t = i / steps  # 1.0 at center, 0.0 at edge
            alpha = int(80 * t) if center == (256, 256) else int(50 * t)
            color = tuple(int(base_color[c] * t + bg[c] * (1 - t))
                          for c in range(3)) + (alpha,)
            overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
            img = Image.alpha_composite(img, overlay)
    return img.convert("RGB")


def make_flat_outlined_shapes(size: int = 512) -> Image.Image:
    """
    Flat-filled shapes with hard black outlines, uniform tones, total visibility.
    A Ruskin critic should diagnose: no gradation, outline drawing, no mystery,
    mechanical boldness over delicacy.
    """
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    # Rectangle: flat medium gray
    draw.rectangle([100, 100, 300, 350], fill=(140, 140, 140), outline="black", width=3)
    # Circle: flat dark gray
    draw.ellipse([290, 160, 470, 340], fill=(80, 80, 80), outline="black", width=3)
    # Triangle: flat light gray
    draw.polygon([(200, 420), (350, 420), (275, 320)],
                 fill=(190, 190, 190), outline="black")
    # Small square: flat black
    draw.rectangle([420, 80, 480, 140], fill="black", outline="black", width=3)
    return img


# ---------------------------------------------------------------------------
# Hildebrand: spatial unity, relief conception
# ---------------------------------------------------------------------------

def make_coherent_relief(size: int = 512) -> Image.Image:
    """
    Clear front-to-back layered relief: three distinct depth planes,
    no outlines, forms differentiated by tonal plane membership.
    A Hildebrand critic should praise relief conception, plane unity,
    coherent visual projection.
    """
    bg = (210, 205, 195)
    img = Image.new("RGB", (size, size), bg)
    draw = ImageDraw.Draw(img)
    # Back layer (lightest, closest to background)
    draw.rectangle([40, 60, 240, 400], fill=(195, 190, 180))
    draw.rectangle([280, 80, 480, 380], fill=(195, 190, 180))
    # Middle layer
    draw.rectangle([80, 150, 350, 340], fill=(150, 145, 135))
    draw.ellipse([250, 120, 430, 300], fill=(140, 135, 130))
    # Front layer (darkest)
    draw.rectangle([150, 200, 320, 380], fill=(60, 55, 50))
    return img


def make_spatial_chaos(size: int = 512) -> Image.Image:
    """
    Contradictory depth cues: light forms occlude dark, dark sits atop light,
    a diagonal pierces all planes. No coherent relief reading.
    A Hildebrand critic should diagnose spatial incoherence, no plane unity.
    """
    img = Image.new("RGB", (size, size), (160, 155, 150))
    draw = ImageDraw.Draw(img)
    # Dark form at top (suggests "front" by tone)
    draw.rectangle([300, 30, 460, 150], fill=(40, 35, 30))
    # Light form overlapping it (suggests "back" but occludes "front")
    draw.rectangle([320, 100, 480, 280], fill=(220, 215, 210))
    # Medium ellipse
    draw.ellipse([60, 60, 220, 200], fill=(130, 125, 120))
    # Near-white form in center (lightest = farthest but centrally placed)
    draw.rectangle([100, 180, 260, 350], fill=(240, 235, 230))
    # Very dark ellipse at bottom
    draw.ellipse([200, 350, 400, 480], fill=(30, 25, 25))
    # Diagonal piercing all planes
    draw.line([(50, 480), (480, 50)], fill="black", width=3)
    return img


# ---------------------------------------------------------------------------
# Worringer: empathy vs abstraction
# ---------------------------------------------------------------------------

def make_organic_empathy(size: int = 512) -> Image.Image:
    """
    Organic curvilinear forms with spatial depth, suggesting vitality
    and inhabitable space. Confidence in the visible world.
    A Worringer critic should identify the empathy impulse.
    """
    bg = (240, 235, 220)
    img = Image.new("RGBA", (size, size), bg + (255,))
    draw = ImageDraw.Draw(img)
    # Atmospheric depth: translucent warm ellipses
    for (x0, y0, x1, y1), alpha in [
        ((100, 100, 350, 300), 15),
        ((200, 350, 400, 500), 20),
    ]:
        layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.ellipse([x0, y0, x1, y1], fill=(120, 110, 100, alpha))
        img = Image.alpha_composite(img, layer)
    draw = ImageDraw.Draw(img)
    # Organic S-curve (main stem)
    stem = [
        (60, 450), (120, 380), (180, 350), (240, 300),
        (280, 250), (330, 220), (370, 180), (420, 120), (460, 80),
    ]
    for i in range(len(stem) - 1):
        draw.line([stem[i], stem[i + 1]], fill=(60, 80, 50, 255), width=4)
    # Branches with leaf-like ellipses
    branches = [
        ((180, 350), (140, 280), (120, 250, 160, 290)),
        ((280, 250), (320, 200), (300, 170, 340, 210)),
        ((370, 180), (400, 130), (380, 100, 420, 150)),
    ]
    for start, end, leaf_box in branches:
        draw.line([start, end], fill=(80, 100, 60, 255), width=2)
        layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.ellipse(leaf_box, fill=(70, 100, 50, 80))
        img = Image.alpha_composite(img, layer)
    # Ground gradient at bottom
    draw = ImageDraw.Draw(img)
    for y in range(400, size):
        t = (y - 400) / (size - 400)
        v = int(235 * (1 - t) + 180 * t)
        draw.line([(0, y), (size, y)], fill=(v + 5, v, v - 10, 255))
    return img.convert("RGB")


def make_crystalline_abstraction(size: int = 512) -> Image.Image:
    """
    Rigid hexagonal tessellation on a flat plane — geometric regularity,
    no depth, no organic form. Dread of space made visible.
    A Worringer critic should identify the abstraction impulse.
    """
    import math
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    r = 36
    row_h = r * math.sqrt(3)
    col_w = r * 1.5
    rows = int(size / row_h) + 2
    cols = int(size / col_w) + 2
    count = 0
    for row in range(rows):
        for col in range(cols):
            cx = col * col_w
            cy = row * row_h + (col % 2) * (row_h / 2)
            # Hexagon vertices
            verts = []
            for k in range(6):
                angle = math.radians(60 * k + 30)
                verts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
            fill = "black" if count % 2 == 0 else "white"
            draw.polygon(verts, fill=fill, outline="black", width=2)
            count += 1
    return img


def generate_all():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    images = {
        # Wölfflin
        "linear_composition": make_linear_composition,
        "painterly_composition": make_painterly_composition,
        # Dow
        "strong_notan": make_strong_notan,
        "weak_notan": make_weak_notan,
        # Kandinsky
        "diagonal_tension": make_diagonal_tension,
        "static_horizontal": make_static_horizontal,
        # Gombrich
        "regular_pattern": make_regular_pattern,
        "varied_pattern": make_varied_pattern,
        # Arnheim
        "unbalanced_composition": make_unbalanced_composition,
        "balanced_asymmetry": make_balanced_asymmetry,
        # Albers
        "simultaneous_contrast": make_simultaneous_contrast,
        "color_no_interaction": make_color_no_interaction,
        # Klee
        "active_line_walk": make_active_line_walk,
        "passive_static_grid": make_passive_static_grid,
        # Ruskin
        "continuous_gradation": make_continuous_gradation,
        "flat_outlined_shapes": make_flat_outlined_shapes,
        # Hildebrand
        "coherent_relief": make_coherent_relief,
        "spatial_chaos": make_spatial_chaos,
        # Worringer
        "organic_empathy": make_organic_empathy,
        "crystalline_abstraction": make_crystalline_abstraction,
    }
    for name, fn in images.items():
        path = OUTPUT_DIR / f"{name}.png"
        fn().save(path)
        print(f"  {path}")
    print(f"\nGenerated {len(images)} test images in {OUTPUT_DIR}")


if __name__ == "__main__":
    generate_all()
