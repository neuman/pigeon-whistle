"""Known-bad fixtures for the whistle's evaluators: one per evaluator.

Each returns the context an evaluator reads for the KNOWN-GOOD design (selftest/known_good.py)
with ONE physically meaningful change, in the direction that evaluator detects.  Nothing here
reads the live design: a control is a pure function of known_good.CONFIG and its one change.

Where the design panel or the tuning step already rejected a value for the very reason an
evaluator exists, that value is the fixture (the 8.2 mm finger hole, the 10 mm lobe, the window
7.4 mm from the lips, the 8 mm high window whose end factor was never recalibrated).  The numbers
in each docstring were read off a run of that fixture.

Two kinds of change:
  _with(ctx, field=value)        one Config field, rebuilt through the model's build();
  _print_file(ctx, name, ...)    the same design, with one defect in the stand-in print file
                                 (selftest/standin.py) the mesh evaluators read.
"""
from __future__ import annotations

import os

from nopekit.modelio import load_path

#: By path, like the model inside it.
known_good = load_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "known_good.py"))


def _with(ctx, **overrides):
    """The known-good design with `overrides` applied.  An override naming no Config field raises
    TypeError from pigeon.Config: a typo is a broken control and reads as one."""
    config = dict(known_good.CONFIG)
    config.update(overrides)
    return known_good.context(ctx, config)


def _print_file(ctx, name, **changes):
    """The known-good design with one defect in its (stand-in) print file."""
    return known_good.context(ctx, None, name, **changes)


# ------------------------------------------------------------------ pitch (closed form and solve)
def wide_vent(ctx):
    """whistle.pitch_closed, whistle.pitch_closed_solved - the tuning vent at 3.0 mm, not 2.1.

    The vent's conductance adds to the window's, so the closed note rises: 349.6 Hz in the closed
    form (48 cents sharp), 351 Hz in the solve (56 cents).  The open note moves half as far, and
    the chamber, window and finger hole are untouched."""
    return _with(ctx, vent_d_mm=3.0)


def first_build_hole(ctx):
    """whistle.pitch_open, whistle.pitch_open_solved - the finger hole at 6.6 mm, as first built.

    The open note falls to 461 Hz, 32 to 34 cents flat of 470; the closed note does not move
    (340.09 Hz).  It is the value the tuning step replaced with 7.05 mm."""
    return _with(ctx, hole_d_mm=6.6)


def uncalibrated_window(ctx):
    """whistle.forms_agree - the window 8.0 mm high, as first drawn, with k_window left alone.

    k_window was calibrated for the 6.3 mm window.  In the solve the window's conductance goes as
    height^0.43, in the closed form as height^0.69, so the two part: 366.1 Hz against 354.9 Hz on
    the closed note, 3.1 % apart.  This is the change the evaluator exists for: geometry moved, end
    factor not recalibrated."""
    return _with(ctx, windway_height_mm=8.0)


def short_ream(ctx):
    """whistle.trim_reach - the vent reamed no further than 2.5 mm, not 3.5.

    The upward reach falls to 22 cents (limit 50); the downward reach, plugging the vent, stays
    89.7 cents.  Nothing about the whistle as printed changes."""
    return _with(ctx, vent_ream_max_mm=2.5)


def hard_blow(ctx):
    """whistle.strouhal_low - blown at 800 Pa, four times the nominal pressure.

    Jet speed doubles, so every Strouhal number halves: 0.065 on the closed note, under the 0.07
    at which the edge tone stops being fed.  The geometry and both notes are untouched."""
    return _with(ctx, blow_pressure_pa=800.0)


def soft_blow(ctx):
    """whistle.strouhal_high - blown at 80 Pa.

    The jet is 1.6 times slower, so the open note's Strouhal number rises to 0.282, past the 0.27
    at which the jet no longer drives the note.  The geometry and both notes are untouched."""
    return _with(ctx, blow_pressure_pa=80.0)


def huge_hole(ctx):
    """whistle.compact - a 12 mm finger hole.

    The open note rises to 561 Hz while the chamber stays 82 mm long: 0.133 of a wavelength,
    past the 0.125 at which the lumped law is held to mean something."""
    return _with(ctx, hole_d_mm=12.0)


def throat(ctx):
    """whistle.no_throat - the rump lobe 10 mm wide, not 15.

    The chamber section beside the jet falls to 3.7 times the window (limit 4.5): the window
    opens into a neck again, the layout of the two quiet, breathy panel concepts."""
    return _with(ctx, lobe_width_mm=10.0)


# ------------------------------------------------------------------ hand, mouth, desk
def child_cannot_seal(ctx):
    """whistle.hole_sealable - the 8.2 mm finger hole the 145 cm^3 concept needed.

    Printed with its 0.2 mm compensation it is 8.4 mm across (limit 8)."""
    return _with(ctx, hole_d_mm=8.2)


def lips_on_window(ctx):
    """whistle.lips_clear - the lip stop at x = 22.6 mm.

    The lips then stop 7.4 mm from the window, the distance the character judge measured on the
    concept whose player's mouth corner reached the window (limit 12)."""
    return _with(ctx, lip_stop_x_mm=22.6)


def long_body(ctx):
    """whistle.palm_size - the body 6.5 mm longer in half-length (44 mm).

    The breast moves forward and the bird is 121.9 mm long, past the 120 mm end of the band."""
    return _with(ctx, body_radius_x_mm=44.0)


def sliver(ctx):
    """whistle.not_small_part - a body 20 mm wide.

    The whole bird is then 30.4 mm across at its widest (the rump and wings), under the 31.7 mm
    of the small-parts cylinder.  Its length and height do not change."""
    return _with(ctx, body_radius_y_mm=10.0)


def narrow_foot(ctx):
    """whistle.desk_stable - the same solid standing on a 27.7 mm wide strip.

    Both lower long edges of the stand-in are cut away at 45 degrees for 20 mm.  The centre of mass
    stays on the centre line and about as high; the support under it shrinks to 13.8 mm each
    side, so it tips at 19.3 degrees (limit 30; the uncut stand-in tips at 43.3)."""
    return _print_file(ctx, "narrow-foot", keel_mm=20.0)


# ------------------------------------------------------------------ printing
def three_perimeters(ctx):
    """whistle.wall_airtight - a shell of three perimeters, 1.35 mm.

    The fdm-print pack accepts it (three lines); the water tests the limit comes from do not."""
    return _with(ctx, shell_wall_mm=1.35)


def thin_floor_printed(ctx):
    """whistle.wall_as_meshed - the print file's chamber floor is 1.2 mm, the model says 2.1.

    The design is the known-good one; the stand-in is cut with a 1.2 mm floor and its sidecar
    records that as its thinnest wall."""
    return _print_file(ctx, "thin-floor", floor_mm=1.2)


def pinched_windway(ctx):
    """whistle.windway_printable - the windway exit gap 0.9 mm (1.0 mm as drawn for the printer).

    Two perimeter walls 1.0 mm apart close up by 0.1 to 0.3 mm: at or under two line widths."""
    return _with(ctx, windway_gap_exit_mm=0.9)


def knife_edge(ctx):
    """whistle.labium_printable - a 0.2 mm labium tip.

    Under one 0.45 mm line: the slicer drops or widens it, and the cut-up becomes what the
    slicer decides."""
    return _with(ctx, labium_tip_mm=0.2)


def drooping_beak(ctx):
    """whistle.no_islands - a beak whose tip hangs 10 mm lower than its root.

    The stand-in gains a 4 mm rod leaving the head end and running down and outward at 45
    degrees.  Its tip is the lowest point of the rod and nothing is under it: the first layer of
    the tip is an island (the fault the character judge found in one concept's beak).  Every face
    of the rod is within the 45 degree overhang rule, which is why the pack cannot see it."""
    return _print_file(ctx, "drooping-beak", beak=True)


def pinhole(ctx):
    """whistle.mesh_closed - a 1 mm pinhole through the chamber floor.

    A fifth opening: the surface is still closed and one piece, and its genus is 4 where the
    four intended openings give 3.  A whistle with this leak does not speak."""
    return _print_file(ctx, "pinhole", leak=True)


def short_chamber(ctx):
    """whistle.mesh_agrees - the print file's chamber is 4 mm shorter than the model's.

    The stand-in's chamber holds 114 107 mm^3 where the model publishes 118 775 mm^3: 3.9 %
    apart (limit 0.5), about 34 cents sharp if it were printed.  Its outside is unchanged.  (The
    known-good stand-in is 0.3 mm short, 0.29 %: inside the limit.)"""
    return _print_file(ctx, "short-chamber", short_mm=4.0)
