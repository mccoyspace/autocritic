"""
Ground truth for Josef Albers' "Interaction of Color" (1963).

Albers' subject is color — specifically, the fact that color deceives
continually. A color is almost never seen as it physically is. This makes
color the most relative medium in art. The book is pedagogical: experience
before theory, practice before rules.

Key challenge: Albers explicitly rejects color systems and harmony rules
as starting points. A naive distillation risks producing a color wheel
checklist. The distinctive Albers move: every color judgment must be
contextual — what matters is not what a color IS but what it DOES to its
neighbors and what they do to it.
"""

CORE_CONCEPTS = {
    "color_relativity": {
        "definition": (
            "In visual perception a color is almost never seen as it really "
            "is — as it physically is. Color is the most relative medium in "
            "art. The same color placed on different grounds appears different; "
            "different colors on carefully chosen grounds can appear the same. "
            "There is a discrepancy between physical fact and psychic effect."
        ),
        "implication_for_art": (
            "Color cannot be evaluated in isolation. Every color judgment "
            "must account for context: neighboring colors, area proportions, "
            "and boundary conditions."
        ),
    },
    "simultaneous_contrast": {
        "definition": (
            "After-image and simultaneous contrast are psycho-physiological "
            "phenomena. Staring at a color fatigues the corresponding retinal "
            "receptors; shifting the gaze produces the complementary color. "
            "No normal eye is foolproof against this deception. Any ground "
            "subtracts its own hue from colors placed on it."
        ),
    },
    "color_boundaries": {
        "definition": (
            "The character of the boundary between color areas determines "
            "spatial reading. Soft boundaries create connection and nearness; "
            "hard boundaries create separation and depth. Vibrating boundaries "
            "(hue contrast with similar lightness) produce aggressive, "
            "uncomfortable effects. Vanishing boundaries (equal light "
            "intensity) produce the rarest and most exciting color phenomenon."
        ),
    },
    "film_and_volume_color": {
        "definition": (
            "Film color is a thin transparent layer between eye and object, "
            "independent of surface — a physical phenomenon (distant mountains "
            "appearing blue). Volume color exists in transparent fluids and "
            "changes with depth. Both are distinct from surface color and "
            "affect how color is perceived in context."
        ),
    },
    "weber_fechner": {
        "definition": (
            "Visual perception of an arithmetical progression depends upon "
            "a physical geometric progression. Equal physical steps do not "
            "produce equal perceptual steps. This law governs gradation, "
            "value stepping, and the perception of color intervals."
        ),
    },
}

ESSENTIAL_CLAIMS = [
    "Color is the most relative medium in art — it is almost never seen "
    "as it physically is. Color deceives continually.",
    "What counts is not what a color IS but what it DOES — the interaction "
    "between colors, not their identity in isolation.",
    "Experience before theory: sensitivity to color is developed through "
    "observation and comparison, not through memorizing color systems.",
    "No normal eye is foolproof against color deception. After-image and "
    "simultaneous contrast are inescapable psycho-physiological facts.",
    "Color harmony is not the only desirable relationship — dissonance is "
    "as desirable as consonance, as in music.",
    "A ground subtracts its own hue from colors placed on it — this is the "
    "subtraction principle that governs all color interaction.",
]

ANTI_GOALS = [
    "Must not evaluate color in isolation — every color judgment must "
    "account for neighboring colors and context",
    "Must not reduce color analysis to a color wheel or harmony system — "
    "Albers explicitly rejects these as starting points",
    "Must not treat color preference as objective — color perception is "
    "relative, contextual, and subject to deception",
    "Must not ignore boundary conditions — how colors meet (hard, soft, "
    "vibrating, vanishing) determines spatial reading",
    "Must not confuse physical color measurement with perceptual color "
    "experience — the discrepancy between fact and effect is foundational",
]

DISTINCTIVE_VOCABULARY = [
    "interaction", "relativity of color",
    "simultaneous contrast", "after-image",
    "subtraction of color", "color deception",
    "film color", "volume color",
    "middle mixture", "color intervals",
    "vanishing boundaries", "vibrating boundaries",
    "light intensity", "color intensity",
    "Bezold effect", "Weber-Fechner",
    "psychic effect", "physical fact",
]

GOOD_CRITIQUE_EXAMPLE = (
    "The dominant red shifts warm on the yellow ground and cool on the "
    "blue ground — a textbook demonstration of simultaneous contrast, "
    "though likely unintentional. The boundary between the orange and "
    "magenta areas vibrates: high hue contrast with near-equal light "
    "intensity produces an aggressive, uncomfortable edge that draws "
    "attention away from the focal area. The green accent reads as darker "
    "than it physically is because the surrounding yellow subtracts its "
    "own hue, pushing the green toward a cooler, apparently deeper value. "
    "The color intervals across the composition are uneven — the jump "
    "from the warm cluster to the cool accent is abrupt, with no middle "
    "mixture to bridge the transition."
)

BAD_CRITIQUE_EXAMPLE = (
    "The color palette is harmonious with a good balance of warm and cool "
    "tones. The artist uses complementary colors effectively. The overall "
    "color scheme creates a pleasing visual experience."
)
