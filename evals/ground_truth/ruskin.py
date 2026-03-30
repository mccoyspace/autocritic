"""
Ground truth for John Ruskin's "The Elements of Drawing" (1857).

Ruskin's framework is about perception — the recovery of what he calls
"the innocence of the eye," seeing flat stains of colour as they actually
are rather than as what we know them to signify. All great art is delicate.
The excellence of an artist depends wholly on refinement of perception.

Key challenge: Ruskin systematically opposes bravura, dash, and cleverness.
A naive distillation risks producing generic composition rules. The distinctive
Ruskin move: every evaluation begins with how the artist sees, not how the
artist executes. Gradation is the supreme technical value. Nature teaches
obedience, not mastery. Composition cannot be taught by rule — but one can
learn to recognize it.
"""

CORE_CONCEPTS = {
    "innocence_of_the_eye": {
        "definition": (
            "The whole technical power of painting depends on the recovery "
            "of a sort of childish perception of flat stains of colour, "
            "merely as such, without consciousness of what they signify — "
            "as a blind man would see them if suddenly gifted with sight. "
            "The trained artist has reduced himself to this condition of "
            "infantine sight."
        ),
        "implication_for_art": (
            "Perception must precede execution. The critic should ask what "
            "the artist actually saw, not what technique was deployed. "
            "Conceptual knowledge (knowing a wall is flat, a tree is green) "
            "is the enemy of accurate seeing."
        ),
    },
    "gradation": {
        "definition": (
            "All drawing depends on the power of representing roundness — "
            "the continuous, subtle transition from one tone or colour to "
            "another. Nature is all made up of roundnesses: not perfect "
            "globes, but variously curved surfaces. Gradation is visible "
            "on everything in Nature and is the supreme technical value."
        ),
    },
    "laws_of_composition": {
        "definition": (
            "Nine laws govern composition: Principality (one element must "
            "dominate), Repetition (echoing forms create unity), Continuity "
            "(orderly succession with gradual change), Curvature (beautiful "
            "objects are terminated by delicately curved lines), Radiation "
            "(lines spring from or converge to a point), Contrast (every "
            "form gains power from its opponent), Interchange (opposites "
            "borrow qualities from each other), Consistency (aggregate "
            "force of unified tone), and Harmony (proportional relationship "
            "of all elements). Great composers conceal their compositional "
            "artifice — in vulgar pictures the law is strikingly manifest."
        ),
    },
    "mystery_and_partial_seeing": {
        "definition": (
            "Nothing is ever seen perfectly, but only by fragments and "
            "under various conditions of obscurity. Mystery is never to be "
            "either fathomed or withdrawn. The incompleteness of perception "
            "is not a defect but a law of nature — the artist who renders "
            "everything with equal clarity violates truth."
        ),
    },
    "delicacy_and_patience": {
        "definition": (
            "All great art is delicate — this is the only rule without "
            "exception respecting art. True boldness and power are only "
            "to be gained by care. The excellence of an artist depends "
            "wholly on refinement of perception; invention distinguishes "
            "individuals, but perception distinguishes schools. Nature is "
            "never bold — no boldness in the way a flower or a bird's "
            "wing is painted."
        ),
    },
}

ESSENTIAL_CLAIMS = [
    "The whole technical power of painting depends on the recovery of the "
    "innocence of the eye — seeing flat stains of colour without consciousness "
    "of what they signify.",
    "All great art is delicate. This is the only rule without exception "
    "respecting art. Coarse art is always bad art.",
    "The excellence of an artist depends wholly on refinement of perception. "
    "Invention distinguishes individuals; perception distinguishes schools.",
    "Nature teaches obedience, not mastery. She will show you nothing if "
    "you set yourself up for her master.",
    "Colour is wholly relative — every hue throughout your work is altered "
    "by every touch you add in other places. Form is absolute.",
    "Composition cannot be taught by rule. It is the operation of an "
    "individual mind of range and power exalted above others. But one can "
    "learn to recognize it.",
]

ANTI_GOALS = [
    "Must not praise boldness, dash, or bravura — Ruskin systematically "
    "opposes virtuosity for its own sake. Power comes from patience and "
    "delicacy, never from speed or cleverness",
    "Must not apply the nine laws of composition as a mechanical checklist — "
    "great composition conceals its artifice; vulgar pictures make the law "
    "strikingly manifest",
    "Must not evaluate technique before perception — the primary question is "
    "how the artist sees, not how the artist handles the brush",
    "Must not treat outlines as real — Nature relieves one mass against "
    "another but outlines none. Drawing by outline falsifies seeing",
    "Must not separate light and shade from local colour — the attempt is "
    "destructive of accurate sight and taste",
]

DISTINCTIVE_VOCABULARY = [
    "innocence of the eye", "gradation",
    "mystery", "delicacy",
    "refinement of perception", "roundness",
    "local colour", "obedience",
    "principality", "curvature",
    "radiation", "interchange",
    "repose", "organic unity",
    "infantine sight", "flat stains of colour",
    "patience", "truth to nature",
]

GOOD_CRITIQUE_EXAMPLE = (
    "The foliage is rendered with genuine mystery — not every leaf is "
    "articulated, yet the mass reads as structurally coherent, obeying the "
    "law of radiation from the central branch. Gradation across the "
    "shadowed bank is continuous and subtle, conveying roundness without "
    "resorting to exaggerated shadow. The warm local colour of the stone "
    "is inseparable from its light — not drawn first and then tinted. "
    "The single bright figure establishes principality: one element "
    "dominates, but without shouting. The overall handling shows delicacy "
    "and patience — no dash, no bravura, only careful refinement of "
    "perception translated into marks."
)

BAD_CRITIQUE_EXAMPLE = (
    "The composition has a strong focal point and good balance. The artist "
    "uses bold strokes effectively to create visual interest. The contrast "
    "between light and dark areas adds drama to the piece."
)
