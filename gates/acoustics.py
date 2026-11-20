"""Evaluators for the whistle's two notes, tier 0: what the model's CLOSED FORM says they are.

Nothing here has heard a whistle.  Every pitch below is the passive resonance of the geometry as
designed (c = 346 m/s); the note a person plays lies within about +-5 % of it, +-10 % with print
tolerance (model/acoustics.py, "Honest error bands").  The claims these evaluators settle say the
model is centred and self-consistent.  Whether a printed whistle sounds is C21, C22 and C24.

The closed form is in model/pigeon.py build(): the lumped Helmholtz law
f = c/(2 pi) sqrt(sum G / V), G = A / (t + k r_eq) per opening.  The law is a cited one (NOTES
section 1.1: the UNSW Helmholtz page; Csoka 2018, section 3.2), so the pitch and trim evaluators
are `sourced`.  Its three end factors k_window, k_hole, k_vent are NOT from a source: they are
Config fields calibrated against this project's own potential-flow solve.  So these evaluators
are sourced in their law and no better than `whistle.forms_agree` (gates/acoustics_solved.py) in
their numbers.  The Strouhal evaluators follow a measured recorder band (NOTES section 2.2).

NOTES = inputs/references/vessel-flute-acoustics-notes.md (input id vessel-flute-acoustics-notes).

`whistle.compact` is the validity guard: every evaluator whose number is a frequency names it in
`needs=`, here and in acoustics_solved.py, so a chamber that is no longer compact reads Skipped on
them, never a confident pass.  It is bound to its own claim (C7) only.

Every evaluator reads numbers build() publishes and recomputes nothing (METHOD rule 2); it rounds
what it reports and judges the rounded value against the limit it read from the claim.  Nothing
but the spine is imported here: these run in milliseconds and an edit to the solver does not
touch their verdicts.
"""
from __future__ import annotations

from nopekit.gates import gate, GateContext
from nopekit.models import NegativeControl, Tier, Verdict

_BAD = "selftest/bad_configs.py:"


# --------------------------------------------------------------------------------------------
# the validity guard
# --------------------------------------------------------------------------------------------
@gate(
    id="whistle.compact",
    basis="model-only",
    title="The chamber is short beside the wavelength",
    claims=["compact"],
    tier=Tier.INSTANT,
    settles="chamber length over wavelength",
    negative_control=NegativeControl(
        fixture=_BAD + "huge_hole",
        note="a 12 mm finger hole: the open note rises to 561 Hz while the chamber stays 82 mm "
             "long, 0.133 of a wavelength",
    ),
)
def compact(ctx: GateContext) -> Verdict:
    """Longest chamber dimension over the wavelength of the open note, against C7.

    The lumped law treats the chamber air as one spring; that holds while the chamber is short
    beside the wavelength.  The ratio is the model's (cavity_length_mm x f_open / c); what counts
    as the chamber's length, and the limit, are this project's judgement (NOTES section 5 gives
    the first-order correction, no published limit), hence model-only.
    """
    acc = ctx.acceptance("C7")
    ratio = round(float(ctx.params["lumped_ratio"]), 4)
    return Verdict(
        gate="whistle.compact", passed=acc.holds(ratio), measured=ratio, limit=acc.limit,
        units="wavelengths", comparator=acc.comparator.value,
        detail=f"chamber {float(ctx.params['cavity_length_mm']):.1f} mm long is {ratio:.3f} of the "
               f"wavelength at the open note, {float(ctx.params['f_open_hz']):.1f} Hz (limit {acc.limit})",
    )


# --------------------------------------------------------------------------------------------
# tier 0: the closed form
# --------------------------------------------------------------------------------------------
def _pitch_closed_form(ctx, gate_id, claim, error_key, hz_key, target_key, state):
    acc = ctx.acceptance(claim)
    signed = float(ctx.params[error_key])
    off = round(abs(signed), 2)
    return Verdict(
        gate=gate_id, passed=acc.holds(off), measured=off, limit=acc.limit, units="cents",
        comparator=acc.comparator.value,
        detail=f"closed form: {float(ctx.params[hz_key]):.2f} Hz with the hole {state}, {signed:+.2f} cents "
               f"from {float(ctx.params[target_key]):.0f} Hz (limit {acc.limit} cents); the model's note, "
               f"not a played one",
    )


@gate(
    id="whistle.pitch_closed",
    basis="sourced",
    title="Closed note, by the closed form",
    claims=["pitch-closed"],
    tier=Tier.INSTANT,
    settles="closed pitch error",
    needs=["whistle.compact"],
    negative_control=NegativeControl(
        fixture=_BAD + "wide_vent",
        note="the tuning vent at 3.0 mm, not 2.1: the closed note rises to 349.6 Hz, 48 cents sharp",
    ),
)
def pitch_closed(ctx: GateContext) -> Verdict:
    """Distance of the closed-form note (finger hole closed, vent open) from 340 Hz, against C1.

    Helmholtz law with summed conductances (NOTES 1.1); cents = 1200 log2(f / target).  The end
    factors in it are this project's calibration, held to the solve by whistle.forms_agree.
    """
    return _pitch_closed_form(ctx, "whistle.pitch_closed", "C1", "closed_error_cents",
                              "f_closed_hz", "target_closed_hz", "closed")


@gate(
    id="whistle.pitch_open",
    basis="sourced",
    title="Open note, by the closed form",
    claims=["pitch-open"],
    tier=Tier.INSTANT,
    settles="open pitch error",
    needs=["whistle.compact"],
    negative_control=NegativeControl(
        fixture=_BAD + "first_build_hole",
        note="the finger hole at 6.6 mm, as first built: the open note falls to 461 Hz, 34 cents flat",
    ),
)
def pitch_open(ctx: GateContext) -> Verdict:
    """Distance of the closed-form note (finger hole open, vent open) from 470 Hz, against C2.

    The interval a hole makes is the best-conditioned part of the law: the window's badly known
    end correction cancels in f_open^2 - f_closed^2 (NOTES 1.1, corollary).
    """
    return _pitch_closed_form(ctx, "whistle.pitch_open", "C2", "open_error_cents",
                              "f_open_hz", "target_open_hz", "open")


@gate(
    id="whistle.trim_reach",
    basis="sourced",
    title="How far the vent can move the closed note",
    claims=["trim-reach"],
    tier=Tier.INSTANT,
    settles="smaller trim reach",
    needs=["whistle.compact"],
    negative_control=NegativeControl(
        fixture=_BAD + "short_ream",
        note="the vent reamed no further than 2.5 mm: the upward reach falls to 22 cents, the "
             "downward reach is untouched",
    ),
)
def trim_reach(ctx: GateContext) -> Verdict:
    """The smaller of the two ways the vent trims the closed note, against C4.

    Down: plug the vent (f_closed over f_closed_plugged).  Up: ream it to vent_ream_max_mm
    (f_closed_reamed over f_closed).  Same law as the pitch evaluators.  The upward figure is the
    closed form's and is low: the solve gives 89 cents where this gives 78 (the vent's end factor
    falls as the bore grows; model/pigeon.py notes()).
    """
    acc = ctx.acceptance("C4")
    down = float(ctx.params["tune_down_reach_cents"])
    up = float(ctx.params["tune_up_reach_cents"])
    reach = round(min(down, up), 1)
    return Verdict(
        gate="whistle.trim_reach", passed=acc.holds(reach), measured=reach, limit=acc.limit,
        units="cents", comparator=acc.comparator.value,
        detail=f"vent plugged: {down:.1f} cents down; reamed to {float(ctx.params['vent_ream_max_mm']):g} mm: "
               f"{up:.1f} cents up (limit {acc.limit} each way); a first print further off than this needs "
               f"a reprint",
    )


def _strouhal(ctx, gate_id, claim, pick, word):
    acc = ctx.acceptance(claim)
    closed = float(ctx.params["strouhal_closed"])
    opened = float(ctx.params["strouhal_open"])
    st = round(pick(closed, opened), 4)
    return Verdict(
        gate=gate_id, passed=acc.holds(st), measured=st, limit=acc.limit, units="St",
        comparator=acc.comparator.value,
        detail=f"{word} Strouhal number {st:.3f} (closed note {closed:.3f}, open note {opened:.3f}) at "
               f"{float(ctx.params['blow_pressure_pa']):.0f} Pa, jet {float(ctx.params['jet_speed_m_s']):.1f} m/s "
               f"over a {float(ctx.params['cutup_mm']):g} mm cut-up (limit {acc.limit})",
    )


@gate(
    id="whistle.strouhal_low",
    basis="sourced",
    title="The jet is not too fast for the closed note",
    claims=["strouhal-low"],
    tier=Tier.INSTANT,
    settles="lowest Strouhal number",
    needs=["whistle.compact"],
    negative_control=NegativeControl(
        fixture=_BAD + "hard_blow",
        note="blown at 800 Pa: jet speed doubles and the closed note's Strouhal number halves to 0.065",
    ),
)
def strouhal_low(ctx: GateContext) -> Verdict:
    """Lowest Strouhal number of the two notes at the nominal blowing pressure, against C5.

    St = f W / U with W the cut-up and U = sqrt(2 P / rho) (Bernoulli).  The band in which a
    recorder head feeds its note was measured as St 0.07 to about 0.27 (NOTES 2.2: Price; the
    McKinnon thesis re-analysis of Verge).  Below 0.07 the jet crosses the mouth too fast.
    A recorder's band, applied to a vessel flute; f is the closed form's.
    """
    return _strouhal(ctx, "whistle.strouhal_low", "C5", min, "lowest")


@gate(
    id="whistle.strouhal_high",
    basis="sourced",
    title="The jet is not too slow for the open note",
    claims=["strouhal-high"],
    tier=Tier.INSTANT,
    settles="highest Strouhal number",
    needs=["whistle.compact"],
    negative_control=NegativeControl(
        fixture=_BAD + "soft_blow",
        note="blown at 80 Pa: the jet is 1.6 times slower and the open note's Strouhal number rises to 0.282",
    ),
)
def strouhal_high(ctx: GateContext) -> Verdict:
    """Highest Strouhal number of the two notes at the nominal blowing pressure, against C6.

    Same number and source as whistle.strouhal_low; 0.27 is the measured low-pressure boundary
    of the recorder's gain region (NOTES 2.2: Price).
    """
    return _strouhal(ctx, "whistle.strouhal_high", "C6", max, "highest")


@gate(
    id="whistle.no_throat",
    basis="model-only",
    title="The window opens into chamber air, not into a neck",
    claims=["no-throat"],
    tier=Tier.INSTANT,
    settles="lobe to window area ratio",
    negative_control=NegativeControl(
        fixture=_BAD + "throat",
        note="the rump lobe 10 mm wide, not 15: the section beside the jet falls to 3.7 times the window",
    ),
)
def no_throat(ctx: GateContext) -> Verdict:
    """Chamber cross-section beside the jet over the window area, against C9.

    A geometric ratio the model integrates (geom.derive: the lobe's section on the plane across
    the jet at mid cut-up).  No outside source says where a neck starts; the limit is the design
    panel's (claims/C9.json).
    """
    acc = ctx.acceptance("C9")
    ratio = round(float(ctx.params["lobe_to_window_ratio"]), 2)
    return Verdict(
        gate="whistle.no_throat", passed=acc.holds(ratio), measured=ratio, limit=acc.limit,
        units="ratio", comparator=acc.comparator.value,
        detail=f"lobe section {float(ctx.params['lobe_area_mm2']):.0f} mm^2 beside the jet is {ratio:.2f} x the "
               f"{float(ctx.params['window_area_mm2']):.1f} mm^2 window (limit {acc.limit})",
    )
