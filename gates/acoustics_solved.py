"""Evaluators for the whistle's two notes, tier 1: what the POTENTIAL-FLOW SOLVE says they are.

The second representation of the same pitches (METHOD rule 6).  model/solve.py rasterises the
acoustic-nominal geometry and solves the quasi-static flow from the chamber to the far field; it
replaces the closed form's guessed end corrections by a field solve.  It was written for this
project and is validated against analytic cases only (model/acoustics_check.py), never against a
blown instrument: `model-only`.

One grid, 0.6 mm, taken to zero grid size by the first-order law solve.py measured on this
geometry; it is good to 0.4 % in frequency (7 cents), and every verdict line says so beside the
limit it is held to.  The three evaluators here share one solve per design (gates/_shared.py).

`whistle.forms_agree` is the one that protects the closed form: its end factors were calibrated on
ONE geometry and do not move when the geometry does.

All three name the guard `whistle.compact` (gates/acoustics.py) in `needs=`: the solve carries the
first-order non-compact term, nothing carries higher chamber modes.

The limits are in the claims.  Each evaluator rounds what it reports and judges the rounded value.
"""
from __future__ import annotations

import os

from nopekit.gates import gate, GateContext
from nopekit.modelio import load_path
from nopekit.models import NegativeControl, Tier, Verdict

shared = load_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_shared.py"))

_BAD = "selftest/bad_configs.py:"
_NEEDS_PY = ["numpy", "scipy", "skimage", "trimesh", "manifold3d"]
"""What the model's geometry and solver modules import, somewhere.  The solve itself runs on numpy
and scipy alone; the other three are named so that a machine without them reads these evaluators
as skipped, not crashed."""


def _pitch_solved(ctx, gate_id, claim, state, target_key, word):
    acc = ctx.acceptance(claim)
    target = float(ctx.params[target_key])
    hz = shared.solved(ctx, [state])[state]
    signed = shared.acoustics.cents(hz, target)
    off = round(abs(signed), 2)
    return Verdict(
        gate=gate_id, passed=acc.holds(off), measured=off, limit=acc.limit, units="cents",
        comparator=acc.comparator.value,
        detail=f"solve: {hz:.2f} Hz with the hole {word}, {signed:+.2f} cents from {target:.0f} Hz "
               f"(limit {acc.limit} cents); one {shared.SOLVE_H_MM:g} mm grid taken to h = 0, good to "
               f"{shared.SOLVE_SCATTER_PCT:.1f} % = {shared.SOLVE_SCATTER_CENTS:.0f} cents; passive "
               f"resonance, not a played note",
    )


@gate(
    id="whistle.pitch_closed_solved",
    basis="model-only",
    title="Closed note, by the potential-flow solve",
    claims=["pitch-closed"],
    tier=Tier.BUILD,
    settles="closed pitch error",
    needs=["whistle.compact"],
    requires_python=_NEEDS_PY,
    negative_control=NegativeControl(
        fixture=_BAD + "wide_vent",
        note="the tuning vent at 3.0 mm, not 2.1: the solved closed note rises to 351 Hz, 56 cents sharp",
    ),
)
def pitch_closed_solved(ctx: GateContext) -> Verdict:
    """Distance of the SOLVED closed note from 340 Hz, against C1.

    model/solve.py solve_states on the acoustic-nominal geometry, every choice of it read
    through ctx.params (gates/_shared.py ParamsConfig), hole closed and vent open.  The solve carries the first-order non-compact term; the guard is still
    needed because nothing carries higher chamber modes.
    """
    return _pitch_solved(ctx, "whistle.pitch_closed_solved", "C1", "closed", "target_closed_hz", "closed")


@gate(
    id="whistle.pitch_open_solved",
    basis="model-only",
    title="Open note, by the potential-flow solve",
    claims=["pitch-open"],
    tier=Tier.BUILD,
    settles="open pitch error",
    needs=["whistle.compact"],
    requires_python=_NEEDS_PY,
    negative_control=NegativeControl(
        fixture=_BAD + "first_build_hole",
        note="the finger hole at 6.6 mm, as first built: the solved open note falls to 461.5 Hz, 32 cents flat",
    ),
)
def pitch_open_solved(ctx: GateContext) -> Verdict:
    """Distance of the SOLVED open note from 470 Hz, against C2.  As whistle.pitch_closed_solved,
    with the finger hole open."""
    return _pitch_solved(ctx, "whistle.pitch_open_solved", "C2", "open", "target_open_hz", "open")


@gate(
    id="whistle.forms_agree",
    basis="model-only",
    title="The closed form and the solve say the same four notes",
    claims=["forms-agree"],
    tier=Tier.BUILD,
    settles="closed form to solve disagreement",
    needs=["whistle.compact"],
    requires_python=_NEEDS_PY,
    negative_control=NegativeControl(
        fixture=_BAD + "uncalibrated_window",
        note="the window 8.0 mm high, as first drawn, with k_window left as calibrated for 6.3 mm: "
             "closed form 366.1 Hz against the solve's 354.9 Hz on the closed note, 3.3 % apart at worst",
    ),
)
def forms_agree(ctx: GateContext) -> Verdict:
    """Largest disagreement between build()'s closed form and the solve over the four states
    (finger hole closed / open x vent open / plugged), against C3.

    This is what keeps the calibrated end factors honest: they were fitted to the solve of ONE
    geometry, and a changed window, hole or vent moves the solve and not the factors.  It compares
    two models with each other and neither with a whistle.
    """
    acc = ctx.acceptance("C3")
    states = list(shared.CLOSED_FORM_KEY)
    solved = shared.solved(ctx, states)
    apart = {s: 100.0 * (float(ctx.params[shared.CLOSED_FORM_KEY[s]]) / solved[s] - 1.0) for s in states}
    worst = max(states, key=lambda s: abs(apart[s]))
    measured = round(abs(apart[worst]), 3)
    return Verdict(
        gate="whistle.forms_agree", passed=acc.holds(measured), measured=measured, limit=acc.limit,
        units="%", comparator=acc.comparator.value,
        detail=f"closed form vs solve, worst of four states: {shared.STATE_WORDS[worst]}, "
               f"{float(ctx.params[shared.CLOSED_FORM_KEY[worst]]):.2f} vs {solved[worst]:.2f} Hz = "
               f"{apart[worst]:+.2f} % (limit {acc.limit} %); the solve on one {shared.SOLVE_H_MM:g} mm grid is "
               f"itself good to {shared.SOLVE_SCATTER_PCT:.1f} %",
    )
