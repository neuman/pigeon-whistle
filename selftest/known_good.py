"""The whistle's known-good design: the one every control is one change away from.

It is the tuned design as it stood when this file was written (geometry hash e93208370219): every
Config field of model/pigeon.py stated here by name and value, so a default edited in the model
later does not move it.  All 22 of the project's evaluators pass on it.  It was not picked to sit
close to the limits; it is the design the tuning step arrived at, and where it sits is recorded:

  closed note 340.09 Hz (0.45 cents off, limit 10)      open note 469.63 Hz (1.37 cents off, limit 10)
  closed form against the solve at h = 0.6 mm: 0.25 % apart at worst (limit 1)
  vent trim reach 77.6 cents up, 89.7 down (limit 50)    Strouhal 0.129 to 0.179 (band 0.07 to 0.27)
  chamber 0.111 of a wavelength long (limit 0.125)       finger hole 7.25 mm as printed (limit 8)
  lobe 5.73 x the window (limit 4.5)                     lips stop 15 mm from the window (limit 12)
  thinnest shell wall 2.1 mm (limit 1.8)                 windway gap 1.4 mm as printed (limit 1.2)
  labium tip 0.5 mm (limit 0.45)                         117.8 mm long (100 to 120)
  smallest overall dimension 67.7 mm (limit 31.7)

Three of those sit close to their limits, and an evaluator whose limit had drifted tighter would
show on them: the chamber length (0.111 of 0.125), the labium tip (0.5 of 0.45) and the length
(117.8 of 120).  On the stand-in print file (below): no island, no topology defect, 0.29 % less
chamber than the model says (limit 0.5), thinnest wall 2.1 mm (limit 1.8), tips at 43.3 degrees
(limit 30).

The print file.  A design is a Config; its print file is made by `python3 model/mesh.py` and kept
only for the live design.  The controls of the five evaluators that read a print file therefore
read a stand-in that selftest/standin.py builds into the run's output directory on every call: a
block with this design's envelope, its chamber volume (cut 0.29 % short on purpose, so the
control of whistle.mesh_agrees does not sit at a flat zero) and the same four openings.  `context`
points `fdm.mesh_path` (and `cad.meshes`) at it and changes nothing else.  What that does and does
not exercise is said in standin.py.

CLAIMS states every acceptance condition an evaluator reads, with the limit this design was
checked against.  Moving a live limit in claims/ re-runs the evaluator against the new limit and
leaves every control where it is.

The model is loaded by path.  solve.py goes first: it puts model/ on sys.path for its siblings
(acoustics, geom), which pigeon.py imports by plain name.
"""
from __future__ import annotations

import copy
import dataclasses
import os

from nopekit.modelio import flat_params, load_path
from nopekit.models import Claim, Ledger

_HERE = os.path.dirname(os.path.abspath(__file__))        # abspath, never resolve()
_MODEL = os.path.join(_HERE, os.pardir, "model")

solve = load_path(os.path.join(_MODEL, "solve.py"))
pigeon = load_path(os.path.join(_MODEL, "pigeon.py"))
standin = load_path(os.path.join(_HERE, "standin.py"))

#: One entry per pigeon.Config field.  A field the model grows later would take its default here
#: silently; `params` refuses instead (see below).
CONFIG: dict = {
    # shape
    "body_center_x_mm": 77.5,
    "body_center_z_mm": 24.0,
    "body_radius_x_mm": 37.5,
    "body_radius_y_mm": 33.4,
    "body_radius_z_mm": 35.0,
    "chest_lead_mm": 16.5,
    "head_center_x_mm": 96.0,
    "head_center_z_mm": 54.2,
    "head_radius_mm": 13.5,
    "beak_length_mm": 7.5,
    "beak_pitch_deg": 35.0,
    "beak_base_radius_mm": 3.2,
    "beak_tip_radius_mm": 1.5,
    "eye_radius_mm": 2.0,
    "eye_depth_mm": 1.1,
    "eye_azimuth_deg": 62.0,
    "eye_elevation_deg": 18.0,
    "wing_center_z_mm": 28.0,
    "wing_pitch_deg": -8.0,
    "wing_bar_width_mm": 2.5,
    "wing_bar_proud_mm": 0.6,
    "wing_bar_length_mm": 18.0,
    "foot_length_mm": 14.0,
    "foot_width_mm": 9.0,
    "foot_height_mm": 3.5,
    "tail_half_width_mm": 14.0,
    "tail_tip_half_width_mm": 12.3,
    "tail_top_z_mm": 14.0,
    "lip_stop_x_mm": 15.0,
    "lip_stop_rise_mm": 3.0,
    "self_support_deg": 40.0,
    # chamber
    "shell_wall_mm": 2.2,
    "floor_mm": 2.1,
    "roof_angle_deg": 42.0,
    "lobe_ridge_z_mm": 23.25,
    "lobe_width_mm": 15.0,
    # voicing (acoustic nominal sizes)
    "windway_length_mm": 30.0,
    "windway_height_mm": 6.3,
    "windway_floor_z_mm": 3.0,
    "windway_gap_inlet_mm": 2.6,
    "windway_gap_exit_mm": 1.3,
    "windway_skew_deg": 4.5,
    "windway_exit_chamfer_mm": 0.6,
    "cutup_mm": 7.0,
    "window_wall_mm": 4.0,
    "lintel_flat_mm": 4.0,
    "labium_tip_mm": 0.5,
    "labium_ramp_deg": 25.0,
    "labium_offset_mm": 0.05,
    # finger hole and vent (acoustic nominal sizes)
    "hole_d_mm": 7.05,
    "hole_x_mm": 70.0,
    "hole_chimney_mm": 2.5,
    "dimple_radius_mm": 13.0,
    "dimple_depth_mm": 0.8,
    "vent_d_mm": 2.1,
    "vent_x_mm": 35.5,
    # CAD compensation
    "hole_comp_mm": 0.2,
    "windway_gap_comp_mm": 0.1,
    # print settings
    "nozzle_d_mm": 0.4,
    "extrusion_width_mm": 0.45,
    "layer_height_mm": 0.12,
    "perimeters": 5,
    "infill_fraction": 0.18,
    "print_speed_mm_s": 40.0,
    "filament_density_g_cm3": 1.24,
    "bed_x_mm": 180.0,
    "bed_y_mm": 180.0,
    "bed_z_mm": 180.0,
    "brim_mm": 5.0,
    "overhang_limit_deg": 45.0,
    "max_bridge_mm": 5.0,
    # envelope
    "max_length_mm": 118.0,
    "max_width_mm": 68.0,
    "max_height_mm": 68.0,
    # acoustic inputs
    "c_air_m_s": 346.0,
    "target_closed_hz": 340.0,
    "target_open_hz": 470.0,
    "k_window": 1.811,
    "k_hole": 2.014,
    "k_vent": 4.69,
    "vent_ream_max_mm": 3.5,
    "blow_pressure_pa": 200.0,
}


def _claim(cid, statement, tag, quantity, comparator, limit, units, limit_hi=None):
    acceptance = {"quantity": quantity, "comparator": comparator, "limit": limit, "units": units}
    if limit_hi is not None:
        acceptance["limit_hi"] = limit_hi
    return {"id": cid, "statement": statement, "kind": "measurable", "acceptance": acceptance, "tags": [tag]}


#: The claims this design was checked against: quantity, comparator and units as in claims/, and
#: the limit each evaluator's control is run at.  C11 is not here: the pack's evaluators read no
#: claim, their limits are values the model publishes.
CLAIMS: list = [
    _claim("C1", "With the finger hole closed, the modelled note is within 10 cents of 340 Hz",
           "pitch-closed", "closed pitch error", "<=", 10.0, "cents"),
    _claim("C2", "With the finger hole open, the modelled note is within 10 cents of 470 Hz",
           "pitch-open", "open pitch error", "<=", 10.0, "cents"),
    _claim("C3", "The closed form and the potential-flow solve agree within 1 % in all four states",
           "forms-agree", "closed form to solve disagreement", "<=", 1.0, "%"),
    _claim("C4", "Trimming the vent moves the closed note at least 50 cents each way",
           "trim-reach", "smaller trim reach", ">=", 50.0, "cents"),
    _claim("C5", "At one blowing pressure the jet's Strouhal number is at least 0.07 on both notes",
           "strouhal-low", "lowest Strouhal number", ">=", 0.07, "St"),
    _claim("C6", "At the same blowing pressure the jet's Strouhal number is at most 0.27 on both notes",
           "strouhal-high", "highest Strouhal number", "<=", 0.27, "St"),
    _claim("C7", "The chamber is at most one eighth of the open note's wavelength long",
           "compact", "chamber length over wavelength", "<=", 0.125, "wavelengths"),
    _claim("C8", "A fingertip can seal the finger hole: its printed diameter is at most 8 mm",
           "hole-sealable", "finger hole diameter", "<=", 8.0, "mm"),
    _claim("C9", "The chamber section beside the jet is at least 4.5 times the window area",
           "no-throat", "lobe to window area ratio", ">=", 4.5, "ratio"),
    _claim("C10", "The lips stop at least 12 mm short of the window",
           "lips-clear", "lip stop to window distance", ">=", 12.0, "mm"),
    _claim("C12", "No layer starts in mid-air",
           "no-islands", "unsupported starts", "<=", 0.0, "count"),
    _claim("C13", "The print file is one closed solid with the four openings of the design and no other",
           "mesh-closed", "mesh topology defects", "<=", 0.0, "count"),
    _claim("C14", "The print file is the model: chamber volume and overall size within 0.5 %",
           "mesh-agrees", "mesh to model disagreement", "<=", 0.5, "%"),
    _claim("C15", "The shell is nowhere thinner than 1.8 mm",
           "wall-airtight", "thinnest shell wall", ">=", 1.8, "mm"),
    _claim("C16", "The windway exit gap as printed is at least 1.2 mm",
           "windway-printable", "windway exit gap", ">=", 1.2, "mm"),
    _claim("C17", "The labium tip is a flat at least 0.45 mm wide",
           "labium-printable", "labium tip width", ">=", 0.45, "mm"),
    _claim("C18", "It is between 100 and 120 mm long",
           "palm-size", "overall length", "between", 100.0, "mm", limit_hi=120.0),
    _claim("C19", "Its smallest overall dimension is more than 31.7 mm",
           "not-small-part", "smallest overall dimension", ">", 31.7, "mm"),
    _claim("C20", "It tips only past 30 degrees",
           "desk-stable", "tipping angle", ">=", 30.0, "deg"),
]


def params(config: dict | None = None) -> dict:
    """`config` (default: CONFIG) built and flattened exactly as `check` flattens the model: derived
    values, every Config field over the top.  A fresh dict on every call.

    pigeon.Config(**stated) raises on a name that is no field (a typo in a fixture is a broken
    control and must read as one).  A field missing from `stated` is refused here for the same
    reason: it would take the model's default and move this design with the model."""
    stated = dict(CONFIG if config is None else config)
    missing = [f.name for f in dataclasses.fields(pigeon.Config) if f.name not in stated]
    if missing:
        raise ValueError("selftest/known_good.py CONFIG does not state: " + ", ".join(missing))
    flat, _conflicts = flat_params({"config": stated,
                                    "derived": pigeon.build(pigeon.Config(**stated))})
    return flat


def with_print_file(ctx, flat: dict, name: str, **changes) -> dict:
    """`flat` with its print file replaced by the stand-in (selftest/standin.py) for that design,
    written under the run's output directory; `changes` are a known-bad variant's one change."""
    path = standin.stage(ctx, flat, name, **changes)
    out = dict(flat)
    out["fdm.mesh_path"] = path
    out["cad.meshes"] = {pigeon.MESH_NAME: path}
    return out


def context(ctx, config: dict | None = None, print_file: str = "known-good", **changes):
    """`ctx` with the known-good design in place of whatever the host carried: its params, a ledger
    of CLAIMS and an empty `extra`.  `root`, `out_dir` and `tier` are kept.  The fixtures in
    bad_configs.py call it with their one change (`config`, or a stand-in variant)."""
    ledger = Ledger(claims=[Claim.from_dict(copy.deepcopy(row)) for row in CLAIMS])
    flat = with_print_file(ctx, params(config), print_file, **changes)
    return dataclasses.replace(ctx, params=flat, ledger=ledger, extra={})
