"""Evaluators for the whistle as an object in a hand and at a mouth: four lengths the model publishes.

All tier 0 and `model-only`: plain geometry written for this project, each reading numbers build()
publishes.  The limits, and where each comes from, are in the claims.

None of these says the bird looks like a pigeon (C23, a person's judgment) or that a child can
play it (C25, a printed whistle).  Whether it sits steady on a desk is measured on the print file:
whistle.desk_stable, in gates/print_file.py.
"""
from __future__ import annotations

from nopekit.gates import gate, GateContext
from nopekit.models import NegativeControl, Tier, Verdict

_BAD = "selftest/bad_configs.py:"


@gate(
    id="whistle.hole_sealable",
    basis="model-only",
    title="A fingertip covers the finger hole",
    claims=["hole-sealable"],
    tier=Tier.INSTANT,
    settles="finger hole diameter",
    negative_control=NegativeControl(
        fixture=_BAD + "child_cannot_seal",
        note="the 8.2 mm finger hole the 145 cm^3 concept needed: 8.4 mm across as printed",
    ),
)
def hole_sealable(ctx: GateContext) -> Verdict:
    """Finger hole diameter as drawn for the printer (acoustic diameter + compensation), against
    C8.  The larger of the two diameters, because that is the rim a fingertip has to cover."""
    acc = ctx.acceptance("C8")
    d = round(float(ctx.params["hole_cad_d_mm"]), 2)
    return Verdict(
        gate="whistle.hole_sealable", passed=acc.holds(d), measured=d, limit=acc.limit,
        units="mm", comparator=acc.comparator.value,
        detail=f"finger hole {d:.2f} mm in the print file ({float(ctx.params['hole_d_mm']):g} acoustic + "
               f"{float(ctx.params['hole_comp_mm']):g} compensation; limit {acc.limit} mm)",
    )


@gate(
    id="whistle.lips_clear",
    basis="model-only",
    title="The lips stop short of the window",
    claims=["lips-clear"],
    tier=Tier.INSTANT,
    settles="lip stop to window distance",
    negative_control=NegativeControl(
        fixture=_BAD + "lips_on_window",
        note="the lip stop at x = 22.6 mm: the lips stop 7.4 mm from the window, the distance at "
             "which the character judge found the mouth corner on it",
    ),
)
def lips_clear(ctx: GateContext) -> Verdict:
    """Distance along the tail from the lip stop to the windway exit, where the window starts,
    against C10.  A length in the model: it does not know where a given mouth really stops."""
    acc = ctx.acceptance("C10")
    gap = round(float(ctx.params["lip_to_window_mm"]), 1)
    return Verdict(
        gate="whistle.lips_clear", passed=acc.holds(gap), measured=gap, limit=acc.limit,
        units="mm", comparator=acc.comparator.value,
        detail=f"lip stop at x = {float(ctx.params['lip_stop_x_mm']):g} mm, window from x = "
               f"{float(ctx.params['lip_stop_x_mm']) + gap:g} mm: {gap:.1f} mm between them (limit {acc.limit} mm)",
    )


@gate(
    id="whistle.palm_size",
    basis="model-only",
    title="Palm size",
    claims=["palm-size"],
    tier=Tier.INSTANT,
    settles="overall length",
    negative_control=NegativeControl(
        fixture=_BAD + "long_body",
        note="the body 6.5 mm longer in half-length: the breast moves forward and the bird is 121.9 mm long",
    ),
)
def palm_size(ctx: GateContext) -> Verdict:
    """Overall length, tail tip to breast, against C18's band."""
    acc = ctx.acceptance("C18")
    length = round(float(ctx.params["overall_length_mm"]), 1)
    return Verdict(
        gate="whistle.palm_size", passed=acc.holds(length), measured=length, limit=acc.limit,
        units="mm", comparator=acc.comparator.value,
        detail=f"{length:.1f} mm long, {float(ctx.params['overall_width_mm']):.1f} wide, "
               f"{float(ctx.params['overall_height_mm']):.1f} high (length band {acc.limit:g} to {acc.limit_hi:g} mm)",
    )


@gate(
    id="whistle.not_small_part",
    basis="model-only",
    title="Too big for the small-parts cylinder",
    claims=["not-small-part"],
    tier=Tier.INSTANT,
    settles="smallest overall dimension",
    negative_control=NegativeControl(
        fixture=_BAD + "sliver",
        note="a body 20 mm wide: the whole bird is 30.4 mm across, under the cylinder's 31.7 mm",
    ),
)
def not_small_part(ctx: GateContext) -> Verdict:
    """Smallest of the three overall dimensions, against C19.

    The limit is the diameter of the small-parts cylinder (claims/C19.json cites it).  The rule
    used here, "no overall dimension is as small as the cylinder is wide", is this project's
    stand-in for the standards' test (does the toy fit wholly inside the cylinder in any pose),
    written for a chubby one-piece body; it is not that test, and not a safety assessment.
    """
    acc = ctx.acceptance("C19")
    dims = [float(ctx.params[k]) for k in ("overall_length_mm", "overall_width_mm", "overall_height_mm")]
    smallest = round(min(dims), 1)
    return Verdict(
        gate="whistle.not_small_part", passed=acc.holds(smallest), measured=smallest, limit=acc.limit,
        units="mm", comparator=acc.comparator.value,
        detail=f"{dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f} mm overall: smallest {smallest:.1f} mm against the "
               f"{acc.limit} mm cylinder; a size rule, not a toy-safety test",
    )
