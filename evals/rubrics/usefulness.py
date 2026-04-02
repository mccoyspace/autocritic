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
]

# Quick lookup by (critic_id, image_name)
EXPECTATIONS_MAP: dict[tuple[str, str], CritiqueExpectation] = {
    (e.critic_id, e.image_name): e for e in EXPECTATIONS
}

# Minimum directive length (words) to count as substantive
MIN_DIRECTIVE_WORDS = 5

# Minimum number of non-empty sections for completeness
REQUIRED_SECTIONS = ["lens_summary", "strengths", "weaknesses", "directives"]
