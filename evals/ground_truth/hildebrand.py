"""
Ground truth for Adolf Hildebrand's "The Problem of Form in Painting and
Sculpture" (1893).

Hildebrand's framework is about spatial unity — the degree to which a work
resolves into a coherent visual impression readable as a relief: a unified
movement from front plane to back plane. The central distinction is between
actual form (the object as measured) and perceptual form (the object as seen
in context). Art operates in the domain of perceptual form. The "conception
of relief" is the single unifying principle that governs all evaluation.

Key challenge: Hildebrand's system is hierarchical — spatial values are
primary and non-negotiable; functional values (expression of life, movement,
gesture) are secondary and must be subordinated to spatial unity. A naive
distillation risks flattening this hierarchy. The distinctive Hildebrand move:
ask whether the work achieves plane unity — whether all forms resolve into a
coherent front-to-back reading — before asking anything else.
"""

CORE_CONCEPTS = {
    "actual_vs_perceptual_form": {
        "definition": (
            "Actual form is the form of an object as it exists independently "
            "of viewing conditions — obtained through touch or measurement. "
            "Perceptual form is the visual impression of form as conditioned "
            "by illumination, environment, point of view, and the relationships "
            "among all visual factors. Perceptual form is richer than actual "
            "form because it includes all subjective relationships. Art operates "
            "in the domain of perceptual form, not actual form."
        ),
    },
    "conception_of_relief": {
        "definition": (
            "All artistic form must conform to the conception of relief: "
            "the figure occupies a uniform depth between two parallel planes "
            "(front and back), resolving into a layer readable from front to "
            "back. This is a mode of perception, not a literal sculptural "
            "technique. It applies to painting, sculpture, architecture, and "
            "all visual art. The value of a work is determined by the degree "
            "of such unity it attains."
        ),
    },
    "spatial_vs_functional_values": {
        "definition": (
            "Spatial values are the primary, elementary, most essential "
            "artistic values — form as expression of space. Functional values "
            "are form as expression of life, movement, and organic process. "
            "Functional values absolutely presuppose spatial values. A work "
            "can have perfect functional truth yet be perfectly formless as "
            "spatial unity."
        ),
    },
    "visual_projection": {
        "definition": (
            "The unified two-dimensional picture obtained when viewing from "
            "sufficient distance that the eyes see parallel — the Fernbild "
            "or distance picture. This affords the only possible perception "
            "of form at a glance, made up of purely visual elements. Art "
            "must produce a unified visual projection that suggests depth "
            "while remaining a coherent plane impression."
        ),
    },
    "architectonic_method": {
        "definition": (
            "The method by which the artist raises imitative work to a "
            "higher plane — organizing all elements into a unified spatial "
            "structure. Through architectonic development, sculpture and "
            "painting emerge from the sphere of mere naturalism into the "
            "realm of true art. This is not architecture literally but the "
            "principle of structural spatial organization."
        ),
    },
}

ESSENTIAL_CLAIMS = [
    "The value of a work of art is determined by the degree of spatial "
    "unity it attains — this is the Problem of Form in Art.",
    "Art operates in the domain of perceptual form, not actual form. "
    "Artistic sense consists in comprehension of values of form as opposed "
    "to mere knowledge of actual form.",
    "The conception of relief is a mold in which the artist casts the form "
    "of Nature — it defines the relation of two-dimensional impressions to "
    "three-dimensional.",
    "Functional values absolutely presuppose spatial values. Truthful "
    "gesture or movement without spatial unity produces work that is "
    "perfectly formless.",
    "All sizes, lights, shades, and colors have only relative values — "
    "each factor has meaning only in relation to all other factors.",
    "No work of art can result from a simple addition of invariable "
    "proportions in details. Proportions must be worked out each time "
    "anew with respect to the work as a whole.",
]

ANTI_GOALS = [
    "Must not evaluate form as accuracy to the object — art operates in "
    "the domain of perceptual form, not actual/measured form",
    "Must not prioritize functional values (expression, gesture, movement) "
    "over spatial values — spatial unity is primary and non-negotiable",
    "Must not treat the conception of relief as literal bas-relief — it is "
    "a mode of perception applicable to all visual art",
    "Must not apply fixed proportional systems — proportions must be worked "
    "out anew for each work as a whole",
    "Must not praise mere imitation or photographic fidelity — mechanical "
    "reproduction of appearance produces work that is dumb",
]

DISTINCTIVE_VOCABULARY = [
    "actual form", "perceptual form",
    "conception of relief", "visual projection",
    "spatial values", "functional values",
    "architectonic", "plane unity",
    "front plane", "back plane",
    "depth movement", "total space",
    "kinesthetic", "pure vision",
    "Fernbild", "distance picture",
    "inherent form", "imitative",
]

GOOD_CRITIQUE_EXAMPLE = (
    "The figure resolves cleanly into a relief conception: the highest "
    "points of shoulder, knee, and outstretched hand combine into a "
    "coherent front plane, while the receding torso and background arm "
    "establish a legible back plane. The depth movement is unified — "
    "nothing thrusts forward to break the plane. Spatial values are "
    "strong: the perceptual form reads as a layered spatial whole at a "
    "glance, before any functional reading (gesture, action) engages. "
    "The architectonic organization subordinates anatomical detail to "
    "the governing spatial idea. Proportions serve the visual projection, "
    "not the actual measurements."
)

BAD_CRITIQUE_EXAMPLE = (
    "The figure is anatomically accurate with good proportions. The "
    "gesture conveys a strong sense of movement and emotion. The artist "
    "demonstrates technical skill in rendering the details of the form."
)
