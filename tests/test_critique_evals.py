"""
Critique evals: test whether a loaded critic produces feedback that is
(a) specific to its theoretical lens and (b) specific to the image.

These evals catch two distinct failure modes:
1. Theory drift: the critic sounds generic regardless of which book loaded it
2. Image blindness: the critic says the same thing regardless of the image

The key test: run the SAME critic on two DIFFERENT images. If the
critiques are interchangeable, the critic is blind.
"""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from evals.ground_truth import wolfflin as wolfflin_gt
from evals.ground_truth import kandinsky as kandinsky_gt
from evals.ground_truth import dow as dow_gt
from tests.conftest import skip_no_api

IMAGES_DIR = Path(__file__).resolve().parent.parent / "evals" / "fixtures" / "images"


def image_to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


# ---------------------------------------------------------------------------
# Expected-response tests (programmatic, no API)
# ---------------------------------------------------------------------------

class TestExpectedResponses:
    """
    Given our test images with known properties, verify that certain
    terms SHOULD appear in a correct critique.

    These aren't testing an actual critic yet — they define what a correct
    critique MUST contain for each image+theorist combination. When a real
    critic is built, these become the pass criteria.
    """

    # Maps: (theorist, image_name) -> terms that MUST appear in a good critique
    EXPECTED_TERMS = {
        ("wolfflin", "linear_composition"): [
            "linear", "contour", "edge", "bounded",
        ],
        ("wolfflin", "painterly_composition"): [
            "painterly", "mass", "tonal", "dissolve",
        ],
        ("dow", "strong_notan"): [
            "notan", "dark", "light", "massing", "two-value",
        ],
        ("dow", "weak_notan"): [
            "notan", "weak", "middle", "muddy",
        ],
        ("kandinsky", "diagonal_tension"): [
            "diagonal", "tension", "warm", "point",
        ],
        ("kandinsky", "static_horizontal"): [
            "horizontal", "cold", "repose",
        ],
    }

    @pytest.mark.parametrize(
        "theorist,image_name",
        list(EXPECTED_TERMS.keys()),
    )
    def test_expected_terms_are_defined(self, theorist: str, image_name: str):
        """Verify that our expected-response definitions exist and are non-empty."""
        terms = self.EXPECTED_TERMS[(theorist, image_name)]
        assert len(terms) >= 3, f"Need at least 3 expected terms for {theorist}/{image_name}"
        # Verify the test image exists
        assert (IMAGES_DIR / f"{image_name}.png").exists(), f"Missing image: {image_name}.png"


# ---------------------------------------------------------------------------
# LLM-as-judge critique evals (require API key)
# ---------------------------------------------------------------------------

@skip_no_api
class TestCritiqueUsefulness:
    """
    Feed a test image + ground-truth theory to the judge and ask:
    does the resulting critique actually use the theory's lens?
    """

    def test_wolfflin_on_linear_image(self):
        """
        Ask the judge to critique a linear composition from Wölfflin's POV
        using the ground-truth theory as the critic card stand-in.
        """
        from evals.judge import run_judge

        # Build a theory-informed critique prompt
        polarity_text = "\n".join(
            f"- {k}: {v['definition']}"
            for k, v in wolfflin_gt.POLARITIES.items()
        )

        result = run_judge(
            eval_name="critique_wolfflin_linear",
            artifact_description=(
                "An image critique written from Wölfflin's theoretical "
                "perspective, applied to a linear composition"
            ),
            artifact_content=(
                f"## Theoretical Framework (Wölfflin)\n{polarity_text}\n\n"
                f"## Image Description\n"
                f"A composition of sharp-edged rectangles and an ellipse with "
                f"clear 3px black contours on white. Strong horizontal and "
                f"vertical lines. No tonal gradation — pure contour drawing.\n\n"
                f"## Expected Critique Direction\n"
                f"The critic should identify this as strongly LINEAR (pole A of "
                f"the linear/painterly axis) and analyze the other four polarities."
            ),
            rubric_dimensions=[
                "correct identification of dominant polarity position",
                "use of Wölfflin's specific vocabulary",
                "analysis across multiple polarities (not just one)",
                "actionable feedback for a generator",
            ],
            failure_modes=[
                "generic composition advice",
                "ignoring the five-polarity framework",
                "treating 'linear' as a criticism rather than a description",
            ],
            pass_threshold=12,
        )
        print(result.summary())
        assert result.passed, result.summary()


@skip_no_api
class TestCritiqueDifferentiation:
    """
    The most important critique eval: does the SAME critic produce
    DIFFERENT feedback for DIFFERENT images?

    If a Wölfflin critic says roughly the same thing about a linear
    composition and a painterly composition, it's not actually seeing.
    """

    def test_wolfflin_differentiates_linear_from_painterly(self):
        from evals.judge import run_comparative_judge

        critique_of_linear = (
            "Analyzing the sharp-edged geometric composition: the image is "
            "strongly linear with clear contour-driven forms. Rectangles and "
            "ellipse are bounded by distinct 3px edges. Spatial organization "
            "is planar with forms arranged parallel to the picture plane. "
            "The composition is closed — axes echo the frame. Multiplicity: "
            "each form maintains independent identity. Absolute clarity: "
            "every element shown in its most legible aspect."
        )

        critique_of_painterly = (
            "Analyzing the overlapping tonal masses: the image is painterly — "
            "forms dissolve into each other through transparent layering, and "
            "no single contour carries the eye. The composition reads as a "
            "unified atmospheric field rather than discrete bounded shapes. "
            "Recession is suggested through layering density. Open form: "
            "elements at edges suggest continuation. Unity dominates: "
            "individual masses cannot be extracted without loss."
        )

        result = run_comparative_judge(
            eval_name="differentiation_wolfflin",
            description=(
                "Two critiques from the same Wölfflin lens applied to two "
                "different images — they should be meaningfully different"
            ),
            artifact_a=critique_of_linear,
            artifact_b=critique_of_painterly,
            comparison_dimensions=[
                "different polarity positions identified",
                "different vocabulary emphasis",
                "different feedback directions",
                "image-specific observations (not interchangeable)",
            ],
            pass_threshold=12,
        )
        print(result.summary())
        assert result.passed, result.summary()
