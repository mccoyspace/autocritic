"""
Usefulness eval rubric: defines image-critic pairings, expected terms,
and scoring criteria for critique usefulness evaluation.

Each pairing maps a critic card to a test image with known formal properties.
The expected_terms list defines what a correct critique MUST mention —
these are the ground-truth visual features that the theorist's framework
should surface for that specific image.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


IMAGES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "images"
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "critiques"


@dataclass
class CritiqueExpectation:
    """What we expect from a specific critic + image combination."""
    critic_id: str
    image_name: str           # stem only, e.g. "linear_composition"
    expected_terms: list[str]  # terms that MUST appear in a correct critique
    description: str = ""     # human-readable description of what the image tests

    @property
    def image_path(self) -> Path:
        return IMAGES_DIR / f"{self.image_name}.png"

    @property
    def fixture_path(self) -> Path:
        return FIXTURES_DIR / f"{self.critic_id}_{self.image_name}.json"


# ---------------------------------------------------------------------------
# Image-critic pairings with expected terms
# ---------------------------------------------------------------------------

EXPECTATIONS: list[CritiqueExpectation] = [
    # Wolfflin: linear vs painterly
    CritiqueExpectation(
        critic_id="wolfflin",
        image_name="linear_composition",
        expected_terms=["linear", "contour", "edge", "bounded"],
        description="Sharp-edged geometric forms with clear contours. "
                    "Should be identified as strongly linear (pole A).",
    ),
    CritiqueExpectation(
        critic_id="wolfflin",
        image_name="painterly_composition",
        expected_terms=["painterly", "mass", "tonal", "dissolve"],
        description="Overlapping soft-edged tonal masses. "
                    "Should be identified as painterly (pole B).",
    ),

    # Dow: notan strength
    CritiqueExpectation(
        critic_id="dow",
        image_name="strong_notan",
        expected_terms=["notan", "dark", "light", "massing"],
        description="High-contrast two-value design with clear dark/light massing. "
                    "Should identify strong notan structure.",
    ),
    CritiqueExpectation(
        critic_id="dow",
        image_name="weak_notan",
        expected_terms=["notan", "weak", "middle", "muddy"],
        description="All middle tones, no clear dark/light separation. "
                    "Should identify weak notan.",
    ),

    # Kandinsky: tension and temperature
    CritiqueExpectation(
        critic_id="kandinsky",
        image_name="diagonal_tension",
        expected_terms=["diagonal", "tension", "warm", "point"],
        description="Strong diagonals and point concentrations. "
                    "Should read warmth, tension, and counterpoint.",
    ),
    CritiqueExpectation(
        critic_id="kandinsky",
        image_name="static_horizontal",
        expected_terms=["horizontal", "cold", "repose"],
        description="Dominated by horizontals, no diagonals. "
                    "Should read coldness and repose.",
    ),

    # Arnheim: perceptual balance
    CritiqueExpectation(
        critic_id="arnheim",
        image_name="balanced_asymmetry",
        expected_terms=["balance", "weight", "equilibrium", "asymmetry"],
        description="Asymmetric but balanced through weight distribution. "
                    "Should recognize equilibrium of forces.",
    ),
    CritiqueExpectation(
        critic_id="arnheim",
        image_name="unbalanced_composition",
        expected_terms=["unbalanced", "weight", "tension", "stress"],
        description="Heavy mass at upper-right with insufficient counterweight. "
                    "Should detect unresolved perceptual stress.",
    ),

    # Gombrich: redundancy and information
    CritiqueExpectation(
        critic_id="gombrich",
        image_name="regular_pattern",
        expected_terms=["redundancy", "repetition", "pattern", "habituation"],
        description="Highly regular repeat pattern — maximum redundancy. "
                    "Should note high redundancy and habituation risk.",
    ),
    CritiqueExpectation(
        critic_id="gombrich",
        image_name="varied_pattern",
        expected_terms=["variation", "pattern", "information", "expectation"],
        description="Pattern with intentional variation. "
                    "Should note effective monotony/variety balance.",
    ),
    # Albers: color interaction
    CritiqueExpectation(
        critic_id="albers",
        image_name="simultaneous_contrast",
        expected_terms=["simultaneous contrast", "ground", "relativity", "boundary"],
        description="Same gray on two different grounds — should identify "
                    "simultaneous contrast, the subtraction principle, and "
                    "context-dependent color perception.",
    ),
    CritiqueExpectation(
        critic_id="albers",
        image_name="color_no_interaction",
        expected_terms=["isolated", "interact", "context", "separated"],
        description="Isolated color swatches on white with no adjacency. "
                    "Should note the absence of color interaction.",
    ),

    # Klee: movement and energy
    CritiqueExpectation(
        critic_id="klee",
        image_name="active_line_walk",
        expected_terms=["active", "movement", "arrow", "energy"],
        description="Wandering line, arrow, spiral, pendulum. "
                    "Should read active line, genesis, directed energy.",
    ),
    CritiqueExpectation(
        critic_id="klee",
        image_name="passive_static_grid",
        expected_terms=["passive", "static", "symmetry", "repetition"],
        description="Rigid grid with points at rest. "
                    "Should note passive line, dead symmetry, no movement.",
    ),

    # Ruskin: gradation and mystery
    CritiqueExpectation(
        critic_id="ruskin",
        image_name="continuous_gradation",
        expected_terms=["gradation", "roundness", "mystery", "delicacy"],
        description="Soft radial gradation, no outlines, partial visibility. "
                    "Should identify continuous gradation and mystery.",
    ),
    CritiqueExpectation(
        critic_id="ruskin",
        image_name="flat_outlined_shapes",
        expected_terms=["outline", "flat", "gradation", "absent"],
        description="Flat-filled shapes with hard outlines. "
                    "Should diagnose absence of gradation and mystery.",
    ),

    # Hildebrand: spatial unity
    CritiqueExpectation(
        critic_id="hildebrand",
        image_name="coherent_relief",
        expected_terms=["relief", "plane", "spatial", "depth"],
        description="Clear front-to-back layered relief. "
                    "Should praise plane unity and coherent visual projection.",
    ),
    CritiqueExpectation(
        critic_id="hildebrand",
        image_name="spatial_chaos",
        expected_terms=["no coherent", "undeveloped", "plane", "spatial"],
        description="Contradictory depth cues, piercing diagonal. "
                    "Should diagnose failure of spatial unity.",
    ),

    # Worringer: empathy vs abstraction
    CritiqueExpectation(
        critic_id="worringer",
        image_name="organic_empathy",
        expected_terms=["empathy", "organic", "vitality", "depth"],
        description="Organic curvilinear forms with spatial depth. "
                    "Should identify the empathy impulse.",
    ),
    CritiqueExpectation(
        critic_id="worringer",
        image_name="crystalline_abstraction",
        expected_terms=["abstraction", "geometric", "planar", "crystalline"],
        description="Rigid hexagonal tessellation, flat plane. "
                    "Should identify the abstraction impulse.",
    ),
]

# Quick lookup by (critic_id, image_name)
EXPECTATIONS_MAP: dict[tuple[str, str], CritiqueExpectation] = {
    (e.critic_id, e.image_name): e for e in EXPECTATIONS
}

# Minimum directive length (words) to count as substantive
MIN_DIRECTIVE_WORDS = 5

# Minimum number of non-empty sections for completeness
REQUIRED_SECTIONS = ["lens_summary", "strengths", "weaknesses", "directives"]
