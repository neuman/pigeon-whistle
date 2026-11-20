"""Evaluators for what the printer is given, tier 0: three sizes the model publishes.

The fdm-print pack (claim C11) holds the shell to three lines and does not look at the airway.
These hold the shell to the four perimeters that print airtight, the windway slot to a gap that
stays open, and the labium to a flat the nozzle can draw.  Each reads one number build() publishes
and recomputes nothing.  All are `model-only`: plain comparisons written for this project; the
limits, and the sources of those limits, are in the claims.

They say what was DRAWN.  What a printer makes of it is C24.
"""
from __future__ import annotations

from nopekit.gates import gate, GateContext
from nopekit.models import NegativeControl, Tier, Verdict

_BAD = "selftest/bad_configs.py:"


@gate(
    id="whistle.wall_airtight",
    basis="model-only",
    title="The shell is at least four perimeters thick, as designed",
    claims=["wall-airtight"],
    tier=Tier.INSTANT,
    settles="thinnest shell wall",
    negative_control=NegativeControl(
        fixture=_BAD + "three_perimeters",
        note="a shell of three perimeters, 1.35 mm: enough for the pack's wall rule, not for the "
             "water tests the limit comes from",
    ),
)
def wall_airtight(ctx: GateContext) -> Verdict:
    """Thinnest section of the shell as designed (the smaller of shell wall and chamber floor),
    against C15.  The labium tip and the bore rims are not shell; they have their own claims."""
    acc = ctx.acceptance("C15")
    wall = round(float(ctx.params["shell_wall_min_mm"]), 2)
    width = float(ctx.params["extrusion_width_mm"])
    return Verdict(
        gate="whistle.wall_airtight", passed=acc.holds(wall), measured=wall, limit=acc.limit,
        units="mm", comparator=acc.comparator.value,
        detail=f"thinnest shell section as designed {wall:.2f} mm = {wall / width:.1f} lines of {width:g} mm "
               f"(wall {float(ctx.params['shell_wall_mm']):g}, floor {float(ctx.params['floor_mm']):g}; "
               f"limit {acc.limit} mm)",
    )


@gate(
    id="whistle.windway_printable",
    basis="model-only",
    title="The windway slot is wide enough to stay open",
    claims=["windway-printable"],
    tier=Tier.INSTANT,
    settles="windway exit gap",
    negative_control=NegativeControl(
        fixture=_BAD + "pinched_windway",
        note="the windway exit gap 0.9 mm, 1.0 mm as drawn for the printer: two perimeter walls "
             "that close up by 0.1 to 0.3 mm",
    ),
)
def windway_printable(ctx: GateContext) -> Verdict:
    """Windway exit gap as drawn for the printer (acoustic gap + compensation), against C16."""
    acc = ctx.acceptance("C16")
    gap = round(float(ctx.params["windway_exit_gap_cad_mm"]), 2)
    return Verdict(
        gate="whistle.windway_printable", passed=acc.holds(gap), measured=gap, limit=acc.limit,
        units="mm", comparator=acc.comparator.value,
        detail=f"windway exit gap {gap:.2f} mm in the print file ({float(ctx.params['windway_gap_exit_mm']):g} "
               f"acoustic + {float(ctx.params['windway_gap_comp_mm']):g} compensation; limit {acc.limit} mm)",
    )


@gate(
    id="whistle.labium_printable",
    basis="model-only",
    title="The labium tip is a flat the nozzle can draw",
    claims=["labium-printable"],
    tier=Tier.INSTANT,
    settles="labium tip width",
    negative_control=NegativeControl(
        fixture=_BAD + "knife_edge",
        note="a 0.2 mm labium tip: under one line, so the slicer decides where the edge ends",
    ),
)
def labium_printable(ctx: GateContext) -> Verdict:
    """Width of the flat on the labium tip, against C17."""
    acc = ctx.acceptance("C17")
    tip = round(float(ctx.params["labium_tip_mm"]), 2)
    width = float(ctx.params["extrusion_width_mm"])
    return Verdict(
        gate="whistle.labium_printable", passed=acc.holds(tip), measured=tip, limit=acc.limit,
        units="mm", comparator=acc.comparator.value,
        detail=f"labium tip flat {tip:.2f} mm against a {width:g} mm line (limit {acc.limit} mm)",
    )
