"""The first whistle's print package: what `nopekit export print-v0-1` hands whoever prints it.

`print_package(ctx)` writes three files into `ctx.out_dir`:

* `pigeon-whistle-<geometry hash>.stl`  the print file, copied byte for byte from the path the
  model publishes (`fdm.mesh_path`), in print pose;
* `PRINT.md`    what the slicer is told that the file cannot say;
* `TUNING.md`   how to trim the two notes after printing, with the model's own shifts.

What it reads is what the export calls the article, so it reads the design ONLY through
`ctx.params` and the one print file:

* every Config field the solid is built from (GEOMETRY below), and `geometry_hash`, the model's
  hash over exactly those fields and its geometry code version.  The hash is the backstop: a
  geometry field the model grows later moves it, and so moves the article, before anyone adds
  the name here.  GEOMETRY was checked equal to model/pigeon.py GEOMETRY_FIELDS when written;
* the print settings a print in other settings would not share (nozzle, layer, line, perimeters,
  infill, filament density);
* for TUNING.md, the conductances and end factors the trim table is worked out from, and the
  two reaches and two targets the model publishes.

Never the speed of sound, the blowing pressure, the bed size or a note in Hz: none of them
changes the object printed, so a change to one asks for no new print.  Every shift in TUNING.md
is in cents and is a ratio, the same at any speed of sound.

It imports nothing from model/.  A module it imported would be part of the article too, and an
edit to the solver would then rename a whistle that is already printed.  The price is one line of
the model's law restated here (`_conductance`); `_table` holds that line to the two reaches the
model publishes and refuses to write a package if they part (METHOD rule 6).

Standard library only.  Deterministic: no clock, fixed number formats, "\n" line ends; two exports
of one design are byte-identical.
"""
from __future__ import annotations

import math
import os

#: Config fields that define the solid: model/pigeon.py GEOMETRY_FIELDS, by name.
GEOMETRY = (
    "body_center_x_mm", "body_center_z_mm", "body_radius_x_mm", "body_radius_y_mm", "body_radius_z_mm",
    "chest_lead_mm", "head_center_x_mm", "head_center_z_mm", "head_radius_mm", "beak_length_mm",
    "beak_pitch_deg", "beak_base_radius_mm", "beak_tip_radius_mm", "eye_radius_mm", "eye_depth_mm",
    "eye_azimuth_deg", "eye_elevation_deg", "wing_center_z_mm", "wing_pitch_deg", "wing_bar_width_mm",
    "wing_bar_proud_mm", "wing_bar_length_mm", "foot_length_mm", "foot_width_mm", "foot_height_mm",
    "tail_half_width_mm", "tail_tip_half_width_mm", "tail_top_z_mm", "lip_stop_x_mm", "lip_stop_rise_mm",
    "self_support_deg", "shell_wall_mm", "floor_mm", "roof_angle_deg", "lobe_ridge_z_mm", "lobe_width_mm",
    "windway_length_mm", "windway_height_mm", "windway_floor_z_mm", "windway_gap_inlet_mm",
    "windway_gap_exit_mm", "windway_skew_deg", "windway_exit_chamfer_mm", "cutup_mm", "window_wall_mm",
    "lintel_flat_mm", "labium_tip_mm", "labium_ramp_deg", "labium_offset_mm", "hole_d_mm", "hole_x_mm",
    "hole_chimney_mm", "dimple_radius_mm", "dimple_depth_mm", "vent_d_mm", "vent_x_mm", "hole_comp_mm",
    "windway_gap_comp_mm",
)

DRILLS_MM = (2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0)
"""Drill sizes a person has: the ream steps the vent table offers, up to vent_ream_max_mm."""

HOLE_STEP_MM = 0.1
"""Step the finger-hole sensitivity is quoted for: the smallest a hand reamer or a drill set gives."""

AGREE_CENTS = 0.05
"""`_table` refuses when its two reaches part from the model's by more than this: the model
publishes them rounded to 1e-4 cents, so anything more is a different law, not rounding."""

PLA_G_CM3 = 1.24


def _conductance(d_mm: float, depth_mm: float, k: float) -> float:
    """G = A / (t + k r) of a round bore: the model's law (model/acoustics.py `conductance`)."""
    return 0.25 * math.pi * d_mm * d_mm / (depth_mm + k * 0.5 * d_mm)


def _cents(g_new: float, g_old: float) -> float:
    """Shift of a note when the summed conductance goes from g_old to g_new: f goes as sqrt(G)."""
    return 600.0 * math.log2(g_new / g_old)


def _table(p) -> dict:
    """The vent rows (state, closed-note shift, open-note shift) and the finger-hole sensitivity."""
    g_window, g_vent, g_hole = float(p["g_window_mm"]), float(p["g_vent_mm"]), float(p["g_hole_mm"])
    vent_d, vent_depth, k_vent = float(p["vent_d_mm"]), float(p["vent_depth_mm"]), float(p["k_vent"])
    hole_d, hole_depth, k_hole = float(p["hole_d_mm"]), float(p["hole_depth_mm"]), float(p["k_hole"])
    ream_max = float(p["vent_ream_max_mm"])
    down, up = float(p["tune_down_reach_cents"]), float(p["tune_up_reach_cents"])

    def vent_row(g_v):
        return (_cents(g_window + g_v, g_window + g_vent),
                _cents(g_window + g_hole + g_v, g_window + g_hole + g_vent))

    plugged = vent_row(0.0)
    reamed = vent_row(_conductance(ream_max, vent_depth, k_vent))
    # the law as restated here against the model's own numbers, each as a shift of the closed note
    mine = {"vent as printed": abs(vent_row(_conductance(vent_d, vent_depth, k_vent))[0]),
            "vent plugged": abs(-plugged[0] - down), "vent reamed": abs(reamed[0] - up)}
    worst = max(mine, key=mine.get)
    if mine[worst] > AGREE_CENTS:
        raise RuntimeError("generators/print_package.py and the model disagree on the vent (%s: %.2f cents "
                           "apart): the trim table would be wrong, nothing written" % (worst, mine[worst]))
    rows = [("plugged (wax or tape)", plugged)]
    rows.append(("as printed, %s mm" % _mm(vent_d), (0.0, 0.0)))
    for d in DRILLS_MM:
        if vent_d + 1e-9 < d <= ream_max + 1e-9:
            rows.append(("reamed to %s mm" % _mm(d), vent_row(_conductance(d, vent_depth, k_vent))))
    g_open = g_window + g_vent + g_hole
    wider = _conductance(hole_d + HOLE_STEP_MM, hole_depth, k_hole) - _conductance(hole_d, hole_depth, k_hole)
    return {"rows": rows, "hole_cents_per_step": _cents(g_open + wider, g_open)}


def _mm(value: float) -> str:
    text = "%.2f" % float(value)
    return text.rstrip("0").rstrip(".") if "." in text else text


def _signed(cents: float) -> str:
    return "0" if abs(cents) < 0.05 else "%+.0f" % cents


def _write(ctx, name: str, text: str) -> None:
    with open(os.path.join(ctx.out_dir, name), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def print_package(ctx) -> None:
    p = ctx.params
    for name in GEOMETRY:                       # each one is a read: it names the article
        _ = p[name]
    ghash = str(p["geometry_hash"])
    rel = str(p["fdm.mesh_path"])
    stl_name = os.path.basename(rel)
    if ghash not in stl_name:
        raise RuntimeError("the model's print file %s does not carry its geometry hash %s" % (rel, ghash))
    try:
        with open(os.path.join(ctx.root, rel), "rb") as fh:
            stl = fh.read()
    except FileNotFoundError:
        raise RuntimeError("no print file %s for geometry %s: run python3 model/mesh.py" % (rel, ghash)) from None
    with open(os.path.join(ctx.out_dir, stl_name), "wb") as fh:
        fh.write(stl)

    nozzle, layer, line = float(p["nozzle_d_mm"]), float(p["layer_height_mm"]), float(p["extrusion_width_mm"])
    walls, infill, density = int(p["perimeters"]), float(p["infill_fraction"]), float(p["filament_density_g_cm3"])
    hole_comp, gap_comp = float(p["hole_comp_mm"]), float(p["windway_gap_comp_mm"])
    hole_d, vent_d, gap = float(p["hole_d_mm"]), float(p["vent_d_mm"]), float(p["windway_gap_exit_mm"])
    material = ("PLA's" if abs(density - PLA_G_CM3) < 0.005
                else "not PLA's %s: check which material the model was set for" % _mm(PLA_G_CM3))
    _write(ctx, "PRINT.md", "\n".join([
        "# Printing the pigeon whistle",
        "",
        "File: `%s` (geometry %s). Nothing has been printed from this design yet; these are the" % (stl_name, ghash),
        "settings the model and its checks assume, not settings proven on a printer.",
        "",
        "## Orientation",
        "",
        "- Print it as it sits in the file: belly down, tail lying on the bed, Z up. Do not rotate it,",
        "  lay it on its side or stand it on end: every check was made in this pose.",
        "- Do not scale it. Pitch, windway and labium all change with scale.",
        "",
        "## Slicer settings",
        "",
        "- Supports: OFF. Every overhang was drawn to print without them, and a support inside the",
        "  chamber or the windway cannot be taken out.",
        "- Nozzle: %s mm." % _mm(nozzle),
        "- Layer height: %s mm." % _mm(layer),
        "- Line width: %s mm." % _mm(line),
        "- Walls (perimeters): %d. The shell is %s mm thick and is meant to be all walls, so no" % (walls, _mm(float(p["shell_wall_mm"]))),
        "  infill line touches the airway.",
        "- Infill: %.0f %%. It fills only the thick parts (head, tail block, roof)." % (100.0 * infill),
        "- Filament: the model assumes %s g/cm^3, which is %s. Print the first one in PLA; PETG" % (_mm(density), material),
        "  strings across the windway.",
        "- Hole and slot compensation in the slicer: leave it at 0. The file already carries it: the",
        "  finger hole is drawn %s mm for %s, the vent %s mm for %s, the windway gap %s mm for %s" % (
            _mm(hole_d + hole_comp), _mm(hole_d), _mm(vent_d + hole_comp), _mm(vent_d), _mm(gap + gap_comp), _mm(gap)),
        "  (bores +%s mm, gap +%s mm)." % (_mm(hole_comp), _mm(gap_comp)),
        "- Seam: keep it off the labium edge and the windway exit. Look at the layers between",
        "  %s and %s mm in the preview before printing." % (
            _mm(float(p["windway_floor_z_mm"])), _mm(float(p["windway_floor_z_mm"]) + float(p["windway_height_mm"]))),
        "- Part cooling on. The windway roof and the window lintel are two short flat bridges.",
        "",
        "## What you should get",
        "",
        "- One piece, %s x %s x %s mm, about %.0f g by the model's estimate (trust the slicer's)." % (
            _mm(round(float(p["overall_length_mm"]), 1)), _mm(round(float(p["overall_width_mm"]), 1)),
            _mm(round(float(p["overall_height_mm"]), 1)), float(p["mass_g"])),
        "- Four openings and no others: the windway slot in the tail tip, the window on the bird's",
        "  left flank behind the body, the finger hole on the back, the small vent on the rump.",
        "- Before blowing: nothing rattles inside, and a 1 mm drill shank passes through the windway.",
        "",
        "Then TUNING.md.",
        "",
    ]))

    table = _table(p)
    lines = [
        "# Tuning the pigeon whistle",
        "",
        "Targets: %s Hz with the finger hole closed, %s Hz with it open. These are the model's" % (
            _mm(float(p["target_closed_hz"])), _mm(float(p["target_open_hz"]))),
        "design centre. No whistle has been printed or blown: expect the first print to be off, and",
        "see the test card for the band each note has to land in.",
        "",
        "## Reading the pitch",
        "",
        "- Hold it as it is played: tail in the mouth up to the lip stop, fingers forward of the window,",
        "  in the hand and not on a desk. A surface under the belly, or a finger near the window,",
        "  lowers the note.",
        "- Blow a few breaths first so the air inside is warm. Then a gentle, steady breath.",
        "- Tuner app at arm's length. Three blows, take the middle reading.",
        "",
        "## 1. The closed note: the vent",
        "",
        "The small hole on the rump is a tuning vent. It is printed open at %s mm. Plugging it" % _mm(vent_d),
        "lowers both notes, reaming it raises them, and it moves the closed note about twice as far",
        "as the open one. Do this first.",
        "",
        "| vent | closed note, cents | open note, cents |",
        "|---|---|---|",
    ]
    for state, (closed, opened) in table["rows"]:
        lines.append("| %s | %s | %s |" % (state, _signed(closed), _signed(opened)))
    lines += [
        "",
        "100 cents is one semitone. The table is the model's closed form. It reads low on the reaming",
        "side: the potential-flow solve gave more shift than this when the design was tuned. So ream one",
        "drill size at a time, by hand, and measure after each. Do not go past %s mm: nothing larger" % _mm(float(p["vent_ream_max_mm"])),
        "was modelled. If the closed note is still outside its band with the vent plugged or fully",
        "reamed, the vent cannot fix this print: the window has to change, and that is a reprint.",
        "",
        "## 2. The open note: the finger hole",
        "",
        "The finger hole is printed %s mm across (the model's %s mm plus %s mm). Reaming it" % (
            _mm(hole_d + hole_comp), _mm(hole_d), _mm(hole_comp)),
        "raises the open note only: about %.0f cents for each %s mm of diameter. The closed note" % (
            table["hole_cents_per_step"], _mm(HOLE_STEP_MM)),
        "does not move. Ream a little, measure, repeat; a hole made too large is hard to undo, and it",
        "must still seal under a fingertip. To lower the open note, a film of wax or varnish on the",
        "wall of the hole makes it smaller.",
        "",
        "## 3. Write down what you did",
        "",
        "The note before, what was done to the vent and the hole, the note after. Those go with the",
        "results of the test card.",
        "",
    ]
    _write(ctx, "TUNING.md", "\n".join(lines))
