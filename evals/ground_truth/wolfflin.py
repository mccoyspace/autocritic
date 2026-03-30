"""
Ground truth for Heinrich Wölfflin's "Principles of Art History" (1915).

This file encodes what we KNOW the theory says, derived from reading the text.
It serves as the authoritative reference for evaluating any distillation,
critic card, or critique output that claims to represent Wölfflin's framework.

The five polarities are the entire theory. They are:
- Descriptive (not normative): neither pole is "better"
- Spectra (not binaries): images fall somewhere along each axis
- Independent: an image can be linear in contour but recessional in space
- Historical but reusable: Wölfflin mapped them to Renaissance→Baroque,
  but they describe visual properties, not periods
"""

# The five opposed categories. Each is a spectrum with two poles.
# Wölfflin's German terms are included because the English translations
# sometimes lose precision (e.g., "malerisch" → "painterly" is imperfect).
POLARITIES = {
    "linear_painterly": {
        "german": ("linear", "malerisch"),
        "pole_a": "linear",
        "pole_b": "painterly",
        "definition": (
            "Linear: the eye follows boundaries; form is apprehended through "
            "its tangible edges and silhouettes. Painterly: the eye grasps "
            "masses of light, shadow, and color; edges dissolve into tonal "
            "relations and visual movement."
        ),
        "what_to_look_for": [
            "Are contours carrying the composition or are tonal masses?",
            "Can you trace distinct edges, or do forms bleed into each other?",
            "Is the drawing 'tactile' (you could feel the edge) or 'visual' "
            "(you see light and atmosphere)?",
        ],
        "common_misreadings": [
            "Treating 'painterly' as a compliment and 'linear' as stiff",
            "Confusing 'painterly' with 'blurry' — painterly has its own order",
            "Equating 'linear' with 'outline drawing' — linear includes "
            "fully modeled form where edges still dominate",
        ],
    },
    "plane_recession": {
        "german": ("flächenhaft", "tiefenhaft"),
        "pole_a": "planar",
        "pole_b": "recessional",
        "definition": (
            "Planar: the composition is organized in layers parallel to the "
            "picture plane; figures and objects are arranged in a stage-like "
            "frieze. Recessional: the composition pulls the eye into depth "
            "through diagonals, overlapping, and atmospheric perspective."
        ),
        "what_to_look_for": [
            "Do the main forms line up in parallel planes (front, middle, back)?",
            "Or do diagonals and foreshortened forms pull the eye inward?",
            "Is depth achieved by layering or by continuous spatial flow?",
        ],
        "common_misreadings": [
            "Confusing 'planar' with 'flat' — planar images can have depth, "
            "but it is organized in discrete layers",
            "Treating recession as automatically better or more sophisticated",
        ],
    },
    "closed_open": {
        "german": ("geschlossene Form", "offene Form"),
        "pole_a": "closed",
        "pole_b": "open",
        "definition": (
            "Closed: the composition is self-contained; verticals and "
            "horizontals stabilize the frame, and the image refers inward. "
            "Open: the composition suggests continuation beyond the frame; "
            "diagonals, asymmetry, and cut-off forms imply a world larger "
            "than what is shown."
        ),
        "what_to_look_for": [
            "Does the composition resolve within its borders?",
            "Do major axes echo the frame edges (closed) or cut across them (open)?",
            "Would cropping the image tighter change its meaning?",
        ],
        "common_misreadings": [
            "Confusing 'closed' with 'rigid' or 'boring'",
            "Confusing 'open' with 'unfinished' or 'cropped badly'",
            "Treating this as only about edge behavior — it's about the "
            "whole compositional logic",
        ],
    },
    "multiplicity_unity": {
        "german": ("Vielheit", "Einheit"),
        "pole_a": "multiplicity",
        "pole_b": "unity",
        "definition": (
            "Multiplicity: each part maintains independent significance; "
            "the whole is a coordination of self-sufficient elements. "
            "Unity: one dominant motif governs; parts are subordinated "
            "to the overall effect and cannot be isolated without loss."
        ),
        "what_to_look_for": [
            "Can you extract individual elements and they still 'work'?",
            "Or does meaning collapse without the whole?",
            "Is the image a 'team of soloists' or an 'orchestra'?",
        ],
        "common_misreadings": [
            "Treating 'unity' as always superior to 'multiplicity'",
            "Confusing multiplicity with clutter — multiplicity is articulated, "
            "each part has dignity",
            "Confusing unity with simplicity — a unified image can be very complex",
        ],
    },
    "clearness_unclearness": {
        "german": ("Klarheit", "Unklarheit"),
        "pole_a": "absolute clarity",
        "pole_b": "relative clarity",
        "definition": (
            "Absolute clarity: every form is presented in its most "
            "characteristic, exhaustive aspect; nothing is hidden or "
            "ambiguous. Relative clarity: forms are partly concealed, "
            "suggested, or revealed only enough to be grasped; the image "
            "withholds full disclosure and relies on the viewer's active "
            "completion."
        ),
        "what_to_look_for": [
            "Is every element shown in its most legible aspect?",
            "Or are forms partially hidden, overlapping, in shadow?",
            "Does the image explain itself fully or ask you to complete it?",
        ],
        "common_misreadings": [
            "Wölfflin uses 'unclearness' (Unklarheit) non-pejoratively — "
            "it is a deliberate aesthetic strategy, not a flaw",
            "Confusing absolute clarity with photographic detail",
            "Confusing relative clarity with poor execution",
        ],
    },
}

# Key claims from the text that any valid distillation must preserve.
# These are NOT optional refinements — they are core to the theory.
ESSENTIAL_CLAIMS = [
    "The five categories are descriptive, not normative. Neither pole is superior.",
    "The categories are independent of each other. An image can be linear but "
    "recessional, or painterly but planar.",
    "Wölfflin's categories describe visual organization, not subject matter. "
    "A still life and a history painting can both be analyzed through the same "
    "five axes.",
    "The shift from one pole to its opposite is not decay or progress but a "
    "different mode of seeing.",
    "Each polarity addresses a different aspect of visual experience: "
    "linear/painterly → edge and mass; plane/recession → spatial arrangement; "
    "closed/open → compositional self-containment; multiplicity/unity → "
    "part-whole relation; clearness/unclearness → disclosure and concealment.",
]

# What a Wölfflin critic must NOT do.
ANTI_GOALS = [
    "Must not rank one pole above the other (e.g., 'painterly is more advanced')",
    "Must not reduce the analysis to 'is this Renaissance or Baroque?'",
    "Must not treat the categories as a checklist of features to have or lack",
    "Must not give generic composition advice unrelated to the five axes",
    "Must not confuse the categories with other theoretical frameworks "
    "(e.g., Gestalt grouping, color theory)",
]

# Vocabulary Wölfflin actually uses. A good distillation should employ
# these terms or close equivalents, not replace them with generic art-school
# language.
DISTINCTIVE_VOCABULARY = [
    "linear", "painterly", "malerisch",
    "tactile", "visual",
    "plane", "recession", "depth",
    "closed form", "open form",
    "multiplicity", "unity",
    "clearness", "unclearness",
    "silhouette", "contour",
    "tectonic", "atectonic",
    "coordination", "subordination",
]

# What a Wölfflin critique SHOULD sound like vs. what it should NOT.
GOOD_CRITIQUE_EXAMPLE = (
    "The image is strongly linear: edges carry the entire composition, "
    "and each form can be apprehended through its silhouette alone. Spatial "
    "organization is planar — three distinct depth layers are stacked parallel "
    "to the picture plane. The closed compositional logic anchors all major "
    "axes to the frame edges. However, the part-whole relationship tends toward "
    "unity rather than multiplicity: removing any single element would collapse "
    "the visual argument. Clearness is absolute — every form is shown in its "
    "most legible aspect."
)

BAD_CRITIQUE_EXAMPLE = (
    "This image has good composition and interesting use of space. The colors "
    "are harmonious and the balance feels right. The artist has created a "
    "dynamic visual experience with strong formal qualities."
)
