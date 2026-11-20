"""The numbers behind the whistle, as tables and charts the page can quote.

Every table here is read from one of four places, and each row says which:

* ctx.params: the model's Config fields and build() keys (the closed form);
* model/solve.py GRID_STUDY: the recorded potential-flow grid study (the reference notes);
* the print mesh's measurement file (print/<mesh>.json, written by model/mesh.py);
* two data literals in views/_data.py: the solver's sensitivity runs and the measured coo evidence.

No viewgen here runs a solve.  Nothing has been printed or blown: every pitch is a modelled passive
resonance, and the coo numbers are measurements of recordings of real birds.

A row with one number carries its unit in the column `in` (text), so a number written in prose in
any spelling of that unit can be found on the page.
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import sys

from nopekit.models import View, ViewKind
from nopekit.site import ViewContext, viewgen


def _shared():
    name = "pigeon_views_shared"
    if name in sys.modules:
        return sys.modules[name]
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_shared.py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


DATA = None                      # views/_data.py, loaded once: the sensitivity runs and the coo evidence


def _data():
    global DATA
    if DATA is None:
        name = "pigeon_views_data"
        if name not in sys.modules:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_data.py")
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        DATA = sys.modules[name]
    return DATA


# ------------------------------------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------------------------------------
def _r(value, digits):
    """Rounded, and never a negative zero."""
    out = round(float(value), digits)
    return 0.0 if out == 0 else out


def _cents(f, ref):
    return 1200.0 * math.log2(f / ref)


def _shift(f, cents):
    return f * 2.0 ** (cents / 1200.0)


def _mean(values):
    return sum(values) / float(len(values))


def _table(view_id, title, description, columns, rows, order, meta=None):
    return View(id=view_id, kind=ViewKind.TABLE, title=title, description=description,
                data={"columns": columns, "rows": rows}, meta=dict(meta or {}), order=order)


LONG = [{"key": "what", "label": "What"},
        {"key": "value", "label": "Value", "align": "right"},
        {"key": "in", "label": "Unit"},
        {"key": "from", "label": "Read from"}]


def _row(row_id, what, value, unit, source, digits=None):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and digits is not None:
        value = _r(value, digits)
    return {"id": row_id, "what": what, "value": value, "in": unit, "from": source}


def _study(ctx):
    """(solve module, GRID_STUDY) or (None, None)."""
    S = _shared()
    m = S.model_modules(ctx)
    study = getattr(getattr(m, "solve", None), "GRID_STUDY", None) if m else None
    if not isinstance(study, dict) or "f0_hz" not in study:
        ctx.log("model/solve.py holds no GRID_STUDY: the solver tables are left out")
        return None, None
    return m.solve, study


def _sidecar(ctx):
    """The mesh's measurement file as a dict, or {}."""
    S = _shared()
    path = S.mesh_file(ctx)
    if path is None:
        return {}
    side = os.path.splitext(path)[0] + ".json"
    try:
        with open(side, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        ctx.log("the mesh has no measurement file beside it")
        return {}
    if doc.get("geometry_hash") != ctx.param("geometry_hash"):
        ctx.log("the mesh's measurement file is of another geometry: left out")
        return {}
    return doc


def _have(ctx, *names):
    S = _shared()
    got = {n: S.number(ctx, n) for n in names}
    missing = [n for n, v in got.items() if v is None]
    if missing:
        ctx.log("the model does not give %s" % ", ".join(missing))
        return None
    return got


STATE_WORDS = {
    "closed": "finger hole closed, vent as printed",
    "open": "finger hole open, vent as printed",
    "closed_plugged": "finger hole closed, vent plugged",
    "open_plugged": "finger hole open, vent plugged",
}
STATE_KEYS = {"closed": "f_closed_hz", "open": "f_open_hz",
              "closed_plugged": "f_closed_plugged_hz", "open_plugged": "f_open_plugged_hz"}


def _trim_rows(ctx):
    """The closed and open note at each vent state, from the grid limit and the sensitivity runs.
    Returns (rows, f0) or None."""
    _solve, study = _study(ctx)
    p = _have(ctx, "vent_d_mm", "target_closed_hz", "target_open_hz")
    if study is None or p is None:
        return None
    f0 = study["f0_hz"]
    sens = {r[0]: r for r in _data().SENSITIVITY_RUNS["rows"]}
    rows = [{"id": "plugged", "vent": "plugged", "vent_mm": 0.0,
             "closed_hz": _r(f0["closed_plugged"], 2),
             "closed_cents": _r(_cents(f0["closed_plugged"], f0["closed"]), 1),
             "open_hz": _r(f0["open_plugged"], 2),
             "open_cents": _r(_cents(f0["open_plugged"], f0["open"]), 1)},
            {"id": "printed", "vent": "as printed", "vent_mm": _r(p["vent_d_mm"], 2),
             "closed_hz": _r(f0["closed"], 2), "closed_cents": 0.0,
             "open_hz": _r(f0["open"], 2), "open_cents": 0.0}]
    for key, d in (("vent_2_5", 2.5), ("vent_3_0", 3.0), ("vent_3_5", 3.5)):
        closed, opened = _mean(sens[key][2]), _mean(sens[key][3])
        rows.append({"id": key, "vent": "reamed", "vent_mm": d,
                     "closed_hz": _r(_shift(f0["closed"], closed), 1), "closed_cents": _r(closed, 1),
                     "open_hz": _r(_shift(f0["open"], opened), 1), "open_cents": _r(opened, 1)})
    for row in rows:
        row["closed_off_target_pct"] = _r(100.0 * (row["closed_hz"] / p["target_closed_hz"] - 1.0), 1)
        row["open_off_target_pct"] = _r(100.0 * (row["open_hz"] / p["target_open_hz"] - 1.0), 1)
    return rows, f0


# ------------------------------------------------------------------------------------------------
# the two notes
# ------------------------------------------------------------------------------------------------
@viewgen(id="notes", kind=ViewKind.TABLE, order=40,
         title="The two notes in the model",
         description="Each state of the whistle, by the closed form in build() and by the potential-flow "
                     "solve at its grid limit. Passive resonances at 346 m/s: no jet, no player, no print.")
def notes(ctx: ViewContext) -> View | None:
    """The four solved states against the two targets."""
    _solve, study = _study(ctx)
    p = _have(ctx, "target_closed_hz", "target_open_hz", "closed_error_cents", "open_error_cents",
              "interval_ratio", *STATE_KEYS.values())
    if study is None or p is None:
        return None
    f0 = study["f0_hz"]
    rows = []
    for state in ("closed", "open", "closed_plugged", "open_plugged"):
        target = p["target_closed_hz"] if state.startswith("closed") else p["target_open_hz"]
        formula = p[STATE_KEYS[state]]
        rows.append({
            "id": state, "state": STATE_WORDS[state],
            "closed_form_hz": _r(formula, 2), "solver_hz": _r(f0[state], 2), "target_hz": _r(target, 0),
            "closed_form_off_target_cents": _r(_cents(formula, target), 2),
            "solver_off_target_cents": _r(_cents(f0[state], target), 2),
            "solver_off_target_pct": _r(100.0 * (f0[state] / target - 1.0), 2),
            "forms_differ_pct": _r(100.0 * (formula / f0[state] - 1.0), 2),
        })
    columns = [
        {"key": "state", "label": "State"},
        {"key": "closed_form_hz", "label": "Closed form", "units": "Hz", "align": "right"},
        {"key": "solver_hz", "label": "Solver, grid limit", "units": "Hz", "align": "right"},
        {"key": "target_hz", "label": "Target", "units": "Hz", "align": "right"},
        {"key": "closed_form_off_target_cents", "label": "Closed form off target", "units": "cents", "align": "right"},
        {"key": "solver_off_target_cents", "label": "Solver off target", "units": "cents", "align": "right"},
        {"key": "solver_off_target_pct", "label": "Solver off target", "units": "%", "align": "right"},
        {"key": "forms_differ_pct", "label": "Closed form against solver", "units": "%", "align": "right"},
    ]
    ratio = p[STATE_KEYS["open"]] / p[STATE_KEYS["closed"]]
    meta = {
        "interval": {"ratio": _r(ratio, 2), "semitones": _r(12.0 * math.log2(ratio), 1),
                     "cents": _r(_cents(p[STATE_KEYS["open"]], p[STATE_KEYS["closed"]]), 0),
                     "target_ratio": _r(p["target_open_hz"] / p["target_closed_hz"], 2),
                     "target_semitones": _r(12.0 * math.log2(p["target_open_hz"] / p["target_closed_hz"]), 1)},
        "reads": "ctx.params (build() keys f_*_hz, targets) and model/solve.py GRID_STUDY f0_hz",
    }
    return _table("notes", "The two notes in the model", notes.view_spec.description, columns, rows, 40, meta)


@viewgen(id="trim", kind=ViewKind.TABLE, order=41,
         title="What the vent does to both notes",
         description="The tuning vent plugged, as printed, and reamed to three drill sizes. Solver values: "
                     "the grid limit for plugged and printed, the mean of two grids for the reamed sizes. "
                     "Modelled, not measured on a print.")
def trim(ctx: ViewContext) -> View | None:
    """Both notes against the vent's state."""
    got = _trim_rows(ctx)
    if got is None:
        return None
    rows, _f0 = got
    columns = [
        {"key": "vent", "label": "Vent"},
        {"key": "vent_mm", "label": "Vent diameter", "units": "mm", "align": "right"},
        {"key": "closed_hz", "label": "Hole closed", "units": "Hz", "align": "right"},
        {"key": "closed_cents", "label": "Hole closed, shift", "units": "cents", "align": "right"},
        {"key": "closed_off_target_pct", "label": "Hole closed, off target", "units": "%", "align": "right"},
        {"key": "open_hz", "label": "Hole open", "units": "Hz", "align": "right"},
        {"key": "open_cents", "label": "Hole open, shift", "units": "cents", "align": "right"},
        {"key": "open_off_target_pct", "label": "Hole open, off target", "units": "%", "align": "right"},
    ]
    return _table("trim", "What the vent does to both notes", trim.view_spec.description, columns, rows, 41,
                  {"reads": "model/solve.py GRID_STUDY f0_hz and views/_data.py SENSITIVITY_RUNS",
                   "runs": _data().SENSITIVITY_RUNS["recorded"]})


@viewgen(id="tuning_bands", kind=ViewKind.TABLE, order=42,
         title="How far off a first print may be, and what the trim recovers",
         description="The bands round each target, and the first-print pitch the vent trim can still bring "
                     "back, if the trim moves a real whistle by as many cents as it moves the model. "
                     "Arithmetic on modelled numbers: no whistle has been printed.")
def tuning_bands(ctx: ViewContext) -> View | None:
    """Bands in Hz and cents, and the reach of the trim against them."""
    got = _trim_rows(ctx)
    p = _have(ctx, "target_closed_hz", "target_open_hz", "tune_down_reach_cents", "tune_up_reach_cents",
              "f_closed_reamed_hz", "vent_ream_max_mm")
    if got is None or p is None:
        return None
    trim_rows, _f0 = got
    by = {r["id"]: r for r in trim_rows}
    lo, hi = p["target_closed_hz"], p["target_open_hz"]
    down = -by["plugged"]["closed_cents"]                   # cents the plug lowers the closed note
    up = by["vent_3_5"]["closed_cents"]                     # cents the largest ream raises it
    rows = []
    for pct, why, src in ((8.0, "the coo evidence tolerates", "input %s, section 5" % _data().COO_INPUT),
                          (10.0, "a first print may be off by",
                           "input vessel-flute-acoustics-notes, section 3; model/acoustics.py, its error budget"),
                          (5.0, "a played note may sit from the passive resonance by",
                           "model/acoustics.py, its error budget")):
        tag = "pct%d" % int(pct)
        rows += [
            _row(tag, "band %s, each way" % why, pct, "%", src, 0),
            _row(tag + "_cents", "the same in cents", 1200.0 * math.log2(1.0 + pct / 100.0), "cents", "arithmetic", 0),
            _row(tag + "_closed_low", "hole closed, low edge", lo * (1.0 - pct / 100.0), "Hz", "arithmetic on the target", 1),
            _row(tag + "_closed_high", "hole closed, high edge", lo * (1.0 + pct / 100.0), "Hz", "arithmetic on the target", 1),
            _row(tag + "_open_low", "hole open, low edge", hi * (1.0 - pct / 100.0), "Hz", "arithmetic on the target", 1),
            _row(tag + "_open_high", "hole open, high edge", hi * (1.0 + pct / 100.0), "Hz", "arithmetic on the target", 1),
        ]
    rows += [
        _row("down", "plugging the vent lowers the closed note by", down, "cents", "solver, grid limit", 1),
        _row("down_pct", "the same in percent", 100.0 * (1.0 - 2.0 ** (-down / 1200.0)), "%", "arithmetic", 1),
        _row("down_formula", "the same by the closed form", p["tune_down_reach_cents"], "cents", "build(): tune_down_reach_cents", 1),
        _row("up", "reaming the vent to %.1f mm raises the closed note by" % p["vent_ream_max_mm"], up, "cents",
             "solver, mean of two grids", 1),
        _row("up_pct", "the same in percent", 100.0 * (2.0 ** (up / 1200.0) - 1.0), "%", "arithmetic", 1),
        _row("up_formula", "the same by the closed form", p["tune_up_reach_cents"], "cents", "build(): tune_up_reach_cents", 1),
        _row("up_formula_hz", "closed note with the vent reamed, closed form", p["f_closed_reamed_hz"], "Hz",
             "build(): f_closed_reamed_hz", 1),
        _row("up_formula_short", "the closed form falls short of the solver by", up - p["tune_up_reach_cents"], "cents",
             "arithmetic", 0),
    ]
    # the first-print pitch that the trim brings exactly to target, and into the 8 % band
    exact_low, exact_high = lo * 2.0 ** (-up / 1200.0), lo * 2.0 ** (down / 1200.0)
    band_low, band_high = lo * 0.92 * 2.0 ** (-up / 1200.0), lo * 1.08 * 2.0 ** (down / 1200.0)
    rows += [
        _row("exact_low", "flattest first print the ream brings to target", exact_low, "Hz", "arithmetic", 1),
        _row("exact_low_pct", "that is under target by", 100.0 * (1.0 - exact_low / lo), "%", "arithmetic", 1),
        _row("exact_high", "sharpest first print the plug brings to target", exact_high, "Hz", "arithmetic", 1),
        _row("exact_high_pct", "that is over target by", 100.0 * (exact_high / lo - 1.0), "%", "arithmetic", 1),
        _row("band_low", "flattest first print the ream brings inside the 8 % band", band_low, "Hz", "arithmetic", 1),
        _row("band_low_pct", "that is under target by", 100.0 * (1.0 - band_low / lo), "%", "arithmetic", 1),
        _row("band_high", "sharpest first print the plug brings inside the 8 % band", band_high, "Hz", "arithmetic", 1),
        _row("band_high_pct", "that is over target by", 100.0 * (band_high / lo - 1.0), "%", "arithmetic", 1),
    ]
    for miss in (15.0, 20.0):
        flat, sharp = lo * (1.0 - miss / 100.0), lo * (1.0 + miss / 100.0)
        flat_fixed, sharp_fixed = flat * 2.0 ** (up / 1200.0), sharp * 2.0 ** (-down / 1200.0)
        tag = "miss%d" % int(miss)
        rows += [
            _row(tag, "a first print that misses by", miss, "%", "a case, not a prediction", 0),
            _row(tag + "_flat", "printed flat by that much", flat, "Hz", "arithmetic", 0),
            _row(tag + "_flat_fixed", "after the largest ream", flat_fixed, "Hz", "arithmetic", 0),
            _row(tag + "_flat_left", "still under target by", 100.0 * (1.0 - flat_fixed / lo), "%", "arithmetic", 1),
            _row(tag + "_sharp", "printed sharp by that much", sharp, "Hz", "arithmetic", 0),
            _row(tag + "_sharp_fixed", "after the plug", sharp_fixed, "Hz", "arithmetic", 0),
            _row(tag + "_sharp_left", "still over target by", 100.0 * (sharp_fixed / lo - 1.0), "%", "arithmetic", 1),
        ]
    return _table("tuning_bands", "How far off a first print may be, and what the trim recovers",
                  tuning_bands.view_spec.description, LONG, rows, 42)


@viewgen(id="trim_chart", kind=ViewKind.CHART, order=60,
         title="Closed note against vent diameter",
         description="Solver values of the closed note as the vent goes from plugged (drawn at 0 mm) to "
                     "reamed, with the target and the band the coo evidence tolerates. Modelled.")
def trim_chart(ctx: ViewContext) -> View | None:
    """The closed note over the vent's diameter, with the target and the 8 % band."""
    got = _trim_rows(ctx)
    p = _have(ctx, "target_closed_hz")
    if got is None or p is None:
        return None
    rows, _f0 = got
    target = p["target_closed_hz"]
    data = {
        "series": [{"key": "closed", "label": "finger hole closed",
                    "points": [[r["vent_mm"], r["closed_hz"]] for r in rows]}],
        "x": {"label": "vent diameter (0 = plugged)", "units": "mm"},
        "y": {"label": "closed note", "units": "Hz", "zero": False},
        "rule": [{"value": _r(target, 0), "label": "target"},
                 {"value": _r(target * 1.08, 1), "label": "target + 8 %"},
                 {"value": _r(target * 0.92, 1), "label": "target - 8 %"}],
    }
    return View(id="trim_chart", kind=ViewKind.CHART, title="Closed note against vent diameter",
                description=trim_chart.view_spec.description, data=data, order=60)


# ------------------------------------------------------------------------------------------------
# dimensions
# ------------------------------------------------------------------------------------------------
@viewgen(id="airway", kind=ViewKind.TABLE, order=43,
         title="Chamber, window, finger hole and vent: the sizes",
         description="Acoustic sizes are what the pitch model uses. Print sizes are what the mesh holds: "
                     "holes drawn 0.2 mm larger and the windway gap 0.1 mm wider, because printed holes "
                     "and slots come out small.")
def airway(ctx: ViewContext) -> View | None:
    """Every dimension of the air path, acoustic and as drawn for print."""
    names = ("chamber_volume_mm3", "cavity_length_mm", "lumped_ratio", "window_cutup_mm", "window_height_mm",
             "window_area_mm2", "window_depth_mm", "window_aperture_mm2", "window_sill_z_mm", "g_window_mm",
             "windway_length_mm", "windway_height_mm", "windway_gap_inlet_mm", "windway_gap_exit_mm",
             "windway_exit_gap_cad_mm", "windway_gap_comp_mm", "windway_skew_deg", "windway_floor_z_mm",
             "windway_exit_chamfer_mm", "labium_tip_mm", "labium_ramp_deg", "labium_offset_mm", "lintel_flat_mm",
             "lobe_area_mm2", "lobe_to_window_ratio", "lobe_width_mm", "lobe_ridge_z_mm", "lobe_eave_clearance_mm",
             "hole_d_mm", "hole_cad_d_mm", "hole_comp_mm", "hole_depth_mm", "hole_chimney_mm", "hole_area_mm2",
             "hole_x_mm", "g_hole_mm", "dimple_radius_mm", "dimple_depth_mm", "vent_d_mm", "vent_cad_d_mm",
             "vent_depth_mm", "vent_area_mm2", "vent_x_mm", "g_vent_mm", "vent_ream_max_mm", "lip_to_window_mm",
             "lip_stop_rise_mm", "shell_wall_mm", "floor_mm", "shell_wall_min_mm", "roof_angle_deg",
             "k_window", "k_hole", "k_vent")
    p = _have(ctx, *names)
    if p is None:
        return None
    side = _sidecar(ctx)
    cfg, built = "Config: %s", "build(): %s"
    rows = [
        _row("chamber_cm3", "chamber volume", p["chamber_volume_mm3"] / 1000.0, "cm^3", built % "chamber_volume_mm3", 1),
        _row("chamber_mm3", "chamber volume", p["chamber_volume_mm3"], "mm^3", built % "chamber_volume_mm3", 0),
    ]
    if isinstance(side.get("chamber_volume_mm3"), (int, float)):
        measured = float(side["chamber_volume_mm3"])
        rows += [
            _row("chamber_mesh_cm3", "chamber volume measured in the print mesh", measured / 1000.0, "cm^3", "mesh measurement file", 1),
            _row("chamber_mesh_pct", "model against mesh", 100.0 * (p["chamber_volume_mm3"] / measured - 1.0), "%", "arithmetic", 2),
        ]
    rows += [
        _row("cavity_length", "longest dimension of the chamber", p["cavity_length_mm"], "mm", built % "cavity_length_mm", 1),
        _row("lumped_ratio", "that length over the wavelength of the open note", p["lumped_ratio"], "ratio", built % "lumped_ratio", 3),
        _row("cutup", "window: cut-up (windway exit to labium edge)", p["window_cutup_mm"], "mm", built % "window_cutup_mm", 1),
        _row("window_height", "window: height (the jet's width)", p["window_height_mm"], "mm", built % "window_height_mm", 1),
        _row("window_area", "window: area", p["window_area_mm2"], "mm^2", built % "window_area_mm2", 1),
        _row("window_depth", "window: wall depth", p["window_depth_mm"], "mm", built % "window_depth_mm", 2),
        _row("window_aperture", "window: aperture with its haunches", p["window_aperture_mm2"], "mm^2", built % "window_aperture_mm2", 1),
        _row("window_sill", "window: sill above the bed", p["window_sill_z_mm"], "mm", built % "window_sill_z_mm", 1),
        _row("lintel", "window: flat bridge over it", p["lintel_flat_mm"], "mm", cfg % "lintel_flat_mm", 1),
        _row("g_window", "window: acoustic conductance", p["g_window_mm"], "mm", built % "g_window_mm", 2),
        _row("k_window", "window: end factor, calibrated to the solve", p["k_window"], "ratio", cfg % "k_window", 3),
        _row("windway_length", "windway: length", p["windway_length_mm"], "mm", cfg % "windway_length_mm", 0),
        _row("windway_height", "windway: height", p["windway_height_mm"], "mm", cfg % "windway_height_mm", 1),
        _row("gap_inlet", "windway: gap at the lips", p["windway_gap_inlet_mm"], "mm", cfg % "windway_gap_inlet_mm", 1),
        _row("gap_exit", "windway: gap at the exit, acoustic", p["windway_gap_exit_mm"], "mm", cfg % "windway_gap_exit_mm", 1),
        _row("gap_exit_cad", "windway: gap at the exit, as drawn for print", p["windway_exit_gap_cad_mm"], "mm", built % "windway_exit_gap_cad_mm", 1),
        _row("gap_comp", "windway: gap allowance for print", p["windway_gap_comp_mm"], "mm", cfg % "windway_gap_comp_mm", 1),
        _row("skew", "windway: turned outward in plan", p["windway_skew_deg"], "deg", cfg % "windway_skew_deg", 1),
        _row("windway_floor", "windway: floor above the bed", p["windway_floor_z_mm"], "mm", cfg % "windway_floor_z_mm", 1),
        _row("exit_chamfer", "windway: chamfer on both exit lips", p["windway_exit_chamfer_mm"], "mm", cfg % "windway_exit_chamfer_mm", 1),
        _row("lip_to_window", "lip stop to window", p["lip_to_window_mm"], "mm", built % "lip_to_window_mm", 0),
        _row("lip_stop_rise", "lip stop: rise", p["lip_stop_rise_mm"], "mm", cfg % "lip_stop_rise_mm", 0),
        _row("labium_tip", "labium: flat on the tip", p["labium_tip_mm"], "mm", cfg % "labium_tip_mm", 1),
        _row("labium_ramp", "labium: ramp angle", p["labium_ramp_deg"], "deg", cfg % "labium_ramp_deg", 0),
        _row("labium_offset", "labium: tip outside the jet's mid-plane", p["labium_offset_mm"], "mm", cfg % "labium_offset_mm", 2),
        _row("lobe_area", "rump lobe: section beside the jet", p["lobe_area_mm2"], "mm^2", built % "lobe_area_mm2", 0),
        _row("lobe_ratio", "rump lobe: that section over the window area", p["lobe_to_window_ratio"], "ratio", built % "lobe_to_window_ratio", 1),
        _row("lobe_width", "rump lobe: width", p["lobe_width_mm"], "mm", cfg % "lobe_width_mm", 0),
        _row("lobe_ridge", "rump lobe: ridge above the bed", p["lobe_ridge_z_mm"], "mm", cfg % "lobe_ridge_z_mm", 2),
        _row("lobe_eave", "rump lobe: roof eave above the window lintel", p["lobe_eave_clearance_mm"], "mm", built % "lobe_eave_clearance_mm", 2),
        _row("hole_d", "finger hole: diameter, acoustic", p["hole_d_mm"], "mm", cfg % "hole_d_mm", 2),
        _row("hole_cad_d", "finger hole: diameter, as drawn for print", p["hole_cad_d_mm"], "mm", built % "hole_cad_d_mm", 2),
        _row("hole_comp", "both holes: diameter allowance for print", p["hole_comp_mm"], "mm", cfg % "hole_comp_mm", 1),
        _row("hole_depth", "finger hole: mean wall length", p["hole_depth_mm"], "mm", built % "hole_depth_mm", 1),
        _row("hole_chimney", "finger hole: straight bore before the undercut", p["hole_chimney_mm"], "mm", cfg % "hole_chimney_mm", 1),
        _row("hole_area", "finger hole: area", p["hole_area_mm2"], "mm^2", built % "hole_area_mm2", 1),
        _row("hole_x", "finger hole: distance from the tail tip", p["hole_x_mm"], "mm", cfg % "hole_x_mm", 0),
        _row("g_hole", "finger hole: acoustic conductance", p["g_hole_mm"], "mm", built % "g_hole_mm", 2),
        _row("k_hole", "finger hole: end factor, calibrated to the solve", p["k_hole"], "ratio", cfg % "k_hole", 3),
        _row("dimple_r", "finger dimple: sphere radius", p["dimple_radius_mm"], "mm", cfg % "dimple_radius_mm", 0),
        _row("dimple_depth", "finger dimple: depth", p["dimple_depth_mm"], "mm", cfg % "dimple_depth_mm", 1),
        _row("vent_d", "vent: diameter, acoustic", p["vent_d_mm"], "mm", cfg % "vent_d_mm", 1),
        _row("vent_cad_d", "vent: diameter, as drawn for print", p["vent_cad_d_mm"], "mm", built % "vent_cad_d_mm", 1),
        _row("vent_depth", "vent: chimney length", p["vent_depth_mm"], "mm", built % "vent_depth_mm", 2),
        _row("vent_area", "vent: area", p["vent_area_mm2"], "mm^2", built % "vent_area_mm2", 2),
        _row("vent_x", "vent: distance from the tail tip", p["vent_x_mm"], "mm", cfg % "vent_x_mm", 1),
        _row("vent_to_lips", "vent: distance in front of the lip stop", p["vent_x_mm"] - (ctx.param("lip_stop_x_mm") or 0.0), "mm", "arithmetic on Config", 1),
        _row("g_vent", "vent: acoustic conductance", p["g_vent_mm"], "mm", built % "g_vent_mm", 3),
        _row("k_vent", "vent: end factor, calibrated to the solve", p["k_vent"], "ratio", cfg % "k_vent", 2),
        _row("vent_ream", "vent: largest ream that was solved", p["vent_ream_max_mm"], "mm", cfg % "vent_ream_max_mm", 1),
        _row("wall", "shell wall", p["shell_wall_mm"], "mm", cfg % "shell_wall_mm", 1),
        _row("floor", "chamber floor", p["floor_mm"], "mm", cfg % "floor_mm", 1),
        _row("wall_min", "thinnest shell wall", p["shell_wall_min_mm"], "mm", built % "shell_wall_min_mm", 1),
        _row("roof", "chamber roof planes, from vertical", p["roof_angle_deg"], "deg", cfg % "roof_angle_deg", 0),
    ]
    return _table("airway", "Chamber, window, finger hole and vent: the sizes", airway.view_spec.description,
                  LONG, rows, 43)


@viewgen(id="size_print", kind=ViewKind.TABLE, order=44,
         title="Overall size, mass and print settings",
         description="Size and mass from the model, the slicer settings the design assumes, and what was "
                     "measured on the print mesh. The mass is the model's estimate: nothing has been sliced "
                     "or printed.")
def size_print(ctx: ViewContext) -> View | None:
    """Envelope, mass, slicer settings and the mesh's own measurements."""
    names = ("overall_length_mm", "overall_width_mm", "overall_height_mm", "max_length_mm", "max_width_mm",
             "max_height_mm", "mass_g", "plastic_volume_mm3", "filament_density_g_cm3", "nozzle_d_mm",
             "extrusion_width_mm", "layer_height_mm", "perimeters", "infill_fraction", "print_speed_mm_s",
             "bed_x_mm", "bed_y_mm", "bed_z_mm", "brim_mm", "overhang_limit_deg", "self_support_deg",
             "max_bridge_mm", "shell_wall_mm", "head_radius_mm", "body_radius_y_mm", "tail_half_width_mm",
             "tail_tip_half_width_mm", "tail_top_z_mm", "beak_length_mm", "foot_height_mm", "wing_bar_proud_mm")
    p = _have(ctx, *names)
    if p is None:
        return None
    side = _sidecar(ctx)
    cfg, built, mesh = "Config: %s", "build(): %s", "mesh measurement file: %s"
    rows = [
        _row("length", "length, tail tip to breast", p["overall_length_mm"], "mm", built % "overall_length_mm", 1),
        _row("width", "width", p["overall_width_mm"], "mm", built % "overall_width_mm", 1),
        _row("height", "height", p["overall_height_mm"], "mm", built % "overall_height_mm", 1),
        _row("max_length", "length allowed", p["max_length_mm"], "mm", cfg % "max_length_mm", 0),
        _row("max_width", "width allowed", p["max_width_mm"], "mm", cfg % "max_width_mm", 0),
        _row("max_height", "height allowed", p["max_height_mm"], "mm", cfg % "max_height_mm", 0),
        _row("mass", "mass in PLA, model estimate", p["mass_g"], "g", built % "mass_g", 0),
        _row("plastic", "plastic volume, solid", p["plastic_volume_mm3"] / 1000.0, "cm^3", built % "plastic_volume_mm3", 1),
        _row("density", "filament density (PLA)", p["filament_density_g_cm3"], "g/cm^3", cfg % "filament_density_g_cm3", 2),
        _row("head", "head diameter", 2.0 * p["head_radius_mm"], "mm", "arithmetic on Config: head_radius_mm", 0),
        _row("head_ratio", "head diameter over body width", p["head_radius_mm"] / p["body_radius_y_mm"], "ratio", "arithmetic on Config", 2),
        _row("tail_width", "tail width at its root", 2.0 * p["tail_half_width_mm"], "mm", "arithmetic on Config: tail_half_width_mm", 0),
        _row("mouthpiece_width", "mouthpiece width at the tail tip", 2.0 * p["tail_tip_half_width_mm"], "mm", "arithmetic on Config: tail_tip_half_width_mm", 1),
        _row("mouthpiece_height", "mouthpiece height", p["tail_top_z_mm"], "mm", cfg % "tail_top_z_mm", 0),
        _row("nozzle", "nozzle", p["nozzle_d_mm"], "mm", cfg % "nozzle_d_mm", 1),
        _row("line", "line width", p["extrusion_width_mm"], "mm", cfg % "extrusion_width_mm", 2),
        _row("layer", "layer height", p["layer_height_mm"], "mm", cfg % "layer_height_mm", 2),
        _row("perimeters", "perimeters (walls)", p["perimeters"], "lines", cfg % "perimeters", 0),
        _row("wall", "shell wall they make", p["shell_wall_mm"], "mm", cfg % "shell_wall_mm", 1),
        _row("infill", "infill in the solid parts", 100.0 * p["infill_fraction"], "%", cfg % "infill_fraction", 0),
        _row("speed", "print speed assumed", p["print_speed_mm_s"], "mm/s", cfg % "print_speed_mm_s", 0),
        _row("bed_x", "printer bed assumed, x", p["bed_x_mm"], "mm", cfg % "bed_x_mm", 0),
        _row("bed_y", "printer bed assumed, y", p["bed_y_mm"], "mm", cfg % "bed_y_mm", 0),
        _row("bed_z", "printer height assumed", p["bed_z_mm"], "mm", cfg % "bed_z_mm", 0),
        _row("brim", "brim allowance", p["brim_mm"], "mm", cfg % "brim_mm", 0),
        _row("overhang_limit", "overhang limit, from vertical", p["overhang_limit_deg"], "deg", cfg % "overhang_limit_deg", 0),
        _row("self_support", "steepest lean of the skin, from vertical", p["self_support_deg"], "deg", cfg % "self_support_deg", 0),
        _row("bridge_limit", "longest flat bridge allowed", p["max_bridge_mm"], "mm", cfg % "max_bridge_mm", 0),
    ]
    layers = side.get("layers") if isinstance(side.get("layers"), dict) else {}
    overhang = side.get("overhang") if isinstance(side.get("overhang"), dict) else {}
    com = side.get("center_of_mass_mm") if isinstance(side.get("center_of_mass_mm"), list) else None

    def add(row_id, what, value, unit, key, digits):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            rows.append(_row(row_id, what, value, unit, mesh % key, digits))

    add("mesh_triangles", "print mesh: triangles", side.get("triangles"), "triangles", "triangles", 0)
    add("mesh_mb", "print mesh: file size", (side.get("stl_bytes") or 0) / 1.0e6 or None, "MB", "stl_bytes", 2)
    add("mesh_voxel", "print mesh: marching-cubes pitch", side.get("voxel_mm"), "mm", "voxel_mm", 2)
    add("mesh_pieces", "print mesh: solid pieces", side.get("solid_pieces"), "pieces", "solid_pieces", 0)
    add("mesh_genus", "print mesh: through-openings (genus)", side.get("genus"), "openings", "genus", 0)
    add("mesh_plastic", "print mesh: plastic volume", (side.get("plastic_volume_mm3") or 0) / 1000.0 or None, "cm^3", "plastic_volume_mm3", 1)
    add("mesh_wall_min", "print mesh: thinnest shell wall (the floor)", side.get("shell_wall_min_mm"), "mm", "shell_wall_min_mm", 2)
    add("mesh_wall_above", "print mesh: thinnest wall above the floor", side.get("shell_wall_min_above_floor_mm"), "mm", "shell_wall_min_above_floor_mm", 2)
    add("layers", "layers at this layer height", layers.get("layers"), "layers", "layers.layers", 0)
    add("islands", "layers that start in mid-air (islands)", layers.get("islands"), "islands", "layers.islands", 0)
    add("hanging", "hanging edges", layers.get("hanging"), "edges", "layers.hanging", 0)
    add("bridges", "flat bridges", layers.get("bridges"), "bridges", "layers.bridges", 0)
    add("bridge_longest", "longest bridge (the window lintel)", layers.get("max_bridge_span_mm"), "mm", "layers.max_bridge_span_mm", 1)
    add("overhang_worst", "steepest face that is not a ceiling, from vertical",
        (overhang.get("chamber") or {}).get("steepest_non_ceiling_deg"), "deg", "overhang.chamber.steepest_non_ceiling_deg", 0)
    add("overhang_share", "surface past the overhang limit", 100.0 * overhang["frac"] if isinstance(overhang.get("frac"), (int, float)) else None,
        "%", "overhang.frac", 4)
    add("bed_patch", "area resting on the bed", side.get("bed_patch_mm2"), "mm^2", "bed_patch_mm2", 0)
    add("tipping", "tips over past", side.get("tipping_angle_deg"), "deg", "tipping_angle_deg", 1)
    if com and len(com) == 3:
        add("com_x", "centre of mass from the tail tip", com[0], "mm", "center_of_mass_mm", 1)
        add("com_z", "centre of mass above the bed", com[2], "mm", "center_of_mass_mm", 1)
    add("com_edge", "centre of mass inside the bed patch by", side.get("com_to_patch_edge_mm"), "mm", "com_to_patch_edge_mm", 1)
    return _table("size_print", "Overall size, mass and print settings", size_print.view_spec.description,
                  LONG, rows, 44)


# ------------------------------------------------------------------------------------------------
# the solver
# ------------------------------------------------------------------------------------------------
@viewgen(id="grid_study", kind=ViewKind.TABLE, order=45,
         title="The solver's grid study",
         description="The four states solved on seven grids, and the straight-line fit read at zero grid "
                     "pitch. Every single grid reads flat; the design centre is the limit. Recorded in "
                     "model/solve.py, not re-run here.")
def grid_study(ctx: ViewContext) -> View | None:
    """Each state's note on each grid, the limit, and how far below it each grid reads."""
    solve, study = _study(ctx)
    c = _shared().number(ctx, "c_air_m_s")
    if study is None or c is None:
        return None
    import acoustics
    hs, volume = study["h_mm"], study["V_mm3"]
    rows = []
    for state in ("closed", "open", "closed_plugged", "open_plugged"):
        row = {"id": state, "state": STATE_WORDS[state]}
        for h, g in zip(hs, study["G_mm"][state]):
            row["hz_at_%s" % str(h).replace(".", "_")] = _r(acoustics.helmholtz_hz(volume, g, c), 1)
        row["limit_hz"] = _r(study["f0_hz"][state], 2)
        row["limit_g_mm"] = _r(study["G0_mm"][state], 3)
        row["slope_per_mm"] = _r(study["slope_per_mm"][state], 4)
        row["coarsest_below_pct"] = _r(100.0 * (1.0 - acoustics.helmholtz_hz(volume, study["G_mm"][state][0], c) / study["f0_hz"][state]), 1)
        row["finest_below_pct"] = _r(100.0 * (1.0 - acoustics.helmholtz_hz(volume, study["G_mm"][state][-1], c) / study["f0_hz"][state]), 1)
        rows.append(row)
    columns = [{"key": "state", "label": "State"}]
    columns += [{"key": "hz_at_%s" % str(h).replace(".", "_"), "label": "h = %g mm" % h, "units": "Hz", "align": "right"} for h in hs]
    columns += [
        {"key": "limit_hz", "label": "Limit, h to 0", "units": "Hz", "align": "right"},
        {"key": "limit_g_mm", "label": "Conductance at the limit", "units": "mm", "align": "right"},
        {"key": "slope_per_mm", "label": "Slope of conductance", "units": "per mm", "align": "right"},
        {"key": "coarsest_below_pct", "label": "Coarsest grid below the limit", "units": "%", "align": "right"},
        {"key": "finest_below_pct", "label": "Finest grid below the limit", "units": "%", "align": "right"},
    ]
    closed = [acoustics.helmholtz_hz(volume, g, c) for g in study["G_mm"]["closed"]]
    meta = {
        "grids": {"coarsest_mm": _r(max(hs), 2), "finest_mm": _r(min(hs), 2), "solved": len(hs)},
        "closed_below_limit_pct": {("h_%g" % h).replace(".", "_"): _r(100.0 * (1.0 - f / study["f0_hz"]["closed"]), 1)
                                   for h, f in zip(hs, closed)},
        "chamber_mm3": _r(volume, 0),
        "fit_residual_pct": _r(100.0 * study["fit_residual"], 1),
        "one_grid_scatter_pct": _r(100.0 * solve.GRID_SCATTER, 1),
        "limit_uncertain_pct": 0.3,
        "slope_used_per_mm": _r(solve.GRID_SLOPE_PER_MM, 4),
        "pad_mm": _r(solve.PAD_MM, 0),
        "speed_of_sound_m_s": _r(c, 0),
        "peak_memory_gb": _r(max(study["peak_memory_gb"].values()), 1),
        "recorded": study.get("recorded", ""),
        "limit_note": "the limit is good to about 0.3 % in pitch (model/solve.py)",
    }
    return _table("grid_study", "The solver's grid study", grid_study.view_spec.description, columns, rows, 45, meta)


@viewgen(id="grid_chart", kind=ViewKind.CHART, order=61,
         title="How the solved notes approach the grid limit",
         description="Each state's solved pitch as a share below its own limit, against grid pitch. The "
                     "points fall on a line: the convergence is first order and not finished at 0.25 mm.")
def grid_chart(ctx: ViewContext) -> View | None:
    """Percent below the limit against grid pitch, one series per state."""
    _solve, study = _study(ctx)
    c = _shared().number(ctx, "c_air_m_s")
    if study is None or c is None:
        return None
    import acoustics
    volume = study["V_mm3"]
    series = []
    for state in ("closed", "open", "closed_plugged", "open_plugged"):
        pts = [[_r(h, 2), _r(100.0 * (1.0 - acoustics.helmholtz_hz(volume, g, c) / study["f0_hz"][state]), 2)]
               for h, g in zip(study["h_mm"], study["G_mm"][state])]
        series.append({"key": state, "label": STATE_WORDS[state], "points": sorted(pts)})
    data = {"series": series,
            "x": {"label": "grid pitch h", "units": "mm"},
            "y": {"label": "solved pitch below the grid limit", "units": "%"}}
    return View(id="grid_chart", kind=ViewKind.CHART, title="How the solved notes approach the grid limit",
                description=grid_chart.view_spec.description, data=data, order=61)


@viewgen(id="sensitivities", kind=ViewKind.TABLE, order=46,
         title="What moves the pitch, and by how much",
         description="Solver runs with one thing changed, on two grids, each against the unchanged design "
                     "on the same grid. Cents: 100 cents is one semitone. Modelled: a printed whistle may "
                     "answer differently.")
def sensitivities(ctx: ViewContext) -> View | None:
    """The shift of both notes for each change that was solved."""
    rows = []
    for key, what, closed, opened in _data().SENSITIVITY_RUNS["rows"]:
        row = {"id": key, "change": what}
        for name, pair in (("closed", closed), ("open", opened)):
            if pair is None:
                continue
            row[name + "_h05_cents"] = _r(pair[0], 1)
            row[name + "_h04_cents"] = _r(pair[1], 1)
            row[name + "_mean_cents"] = _r(_mean(pair), 1)
            row[name + "_mean_pct"] = _r(100.0 * (2.0 ** (_mean(pair) / 1200.0) - 1.0), 2)
        rows.append(row)
    columns = [{"key": "change", "label": "Change"}]
    for name, word in (("closed", "Hole closed"), ("open", "Hole open")):
        columns += [
            {"key": name + "_h05_cents", "label": word + ", h = 0.5 mm", "units": "cents", "align": "right"},
            {"key": name + "_h04_cents", "label": word + ", h = 0.4 mm", "units": "cents", "align": "right"},
            {"key": name + "_mean_cents", "label": word + ", mean", "units": "cents", "align": "right"},
            {"key": name + "_mean_pct", "label": word + ", mean", "units": "%", "align": "right"},
        ]
    return _table("sensitivities", "What moves the pitch, and by how much", sensitivities.view_spec.description,
                  columns, rows, 46, {"runs": _data().SENSITIVITY_RUNS["recorded"]})


@viewgen(id="pitch_per_tenth", kind=ViewKind.TABLE, order=47,
         title="Pitch per 0.1 mm, the desk, and a fingertip near the window",
         description="The sensitivity runs reduced to what a maker needs: cents per 0.1 mm of each printed "
                     "size, the shift from resting on a desk, and the shift from a fingertip near the "
                     "window. Modelled.")
def pitch_per_tenth(ctx: ViewContext) -> View | None:
    """Cents per 0.1 mm, the desk plane and the fingertip, with the notes they lead to."""
    _solve, study = _study(ctx)
    if study is None:
        return None
    f0 = study["f0_hz"]
    sens = {r[0]: r for r in _data().SENSITIVITY_RUNS["rows"]}
    src = "sensitivity runs, mean of two grids"

    def per_tenth(minus, plus, which, step_mm):
        values = [abs(v) for key in (minus, plus) for v in sens[key][which]]
        return _mean(values) / (step_mm / 0.1)

    rows = [
        _row("hole_open", "finger hole diameter, open note, per 0.1 mm", per_tenth("hole_minus", "hole_plus", 3, 0.2), "cents", src, 1),
        _row("hole_open_02", "finger hole diameter, open note, per 0.2 mm", 2.0 * per_tenth("hole_minus", "hole_plus", 3, 0.2), "cents", src, 1),
        _row("cutup_closed", "cut-up, closed note, per 0.1 mm", per_tenth("cutup_minus", "cutup_plus", 2, 0.5), "cents", src, 1),
        _row("cutup_open", "cut-up, open note, per 0.1 mm", per_tenth("cutup_minus", "cutup_plus", 3, 0.5), "cents", src, 1),
        _row("height_closed", "window height, closed note, per 0.1 mm", per_tenth("height_minus", "height_plus", 2, 0.5), "cents", src, 1),
        _row("height_open", "window height, open note, per 0.1 mm", per_tenth("height_minus", "height_plus", 3, 0.5), "cents", src, 1),
        _row("step_holes", "step used for the finger hole", 0.2, "mm", "sensitivity runs", 1),
        _row("step_window", "step used for the cut-up and the window height", 0.5, "mm", "sensitivity runs", 1),
    ]
    for key, word in (("desk", "on a desk or a flat palm"), ("pad_3", "fingertip 3 mm off the window"),
                      ("pad_0", "fingertip flat on the window")):
        closed, opened = _mean(sens[key][2]), _mean(sens[key][3])
        rows += [
            _row(key + "_closed", "%s: closed note" % word, closed, "cents", src, 1),
            _row(key + "_closed_pct", "the same in percent", 100.0 * (2.0 ** (closed / 1200.0) - 1.0), "%", "arithmetic", 2),
            _row(key + "_closed_hz", "closed note then, from the grid limit", _shift(f0["closed"], closed), "Hz", "arithmetic on the grid limit", 0),
            _row(key + "_open", "%s: open note" % word, opened, "cents", src, 1),
            _row(key + "_open_pct", "the same in percent", 100.0 * (2.0 ** (opened / 1200.0) - 1.0), "%", "arithmetic", 2),
            _row(key + "_open_hz", "open note then, from the grid limit", _shift(f0["open"], opened), "Hz", "arithmetic on the grid limit", 0),
        ]
    on_grid = _data().SENSITIVITY_RUNS["pad_0_on_grid_hz"]
    rows += [
        _row("pad_0_closed_grid_hz", "fingertip flat on the window: closed note on the solver's own two grids, mean",
             _mean(on_grid["closed"]), "Hz", "sensitivity runs, not carried to the grid limit", 0),
        _row("pad_0_open_grid_hz", "fingertip flat on the window: open note on the solver's own two grids, mean",
             _mean(on_grid["open"]), "Hz", "sensitivity runs, not carried to the grid limit", 0),
    ]
    pad = _data().SENSITIVITY_RUNS["pad"]
    share = _data().SENSITIVITY_RUNS["flow_share"]
    rows += [
        _row("pad_across", "the fingertip in the model: a rigid disc, across", pad["across_mm"], "mm", "sensitivity runs", 0),
        _row("pad_thick", "the same disc, thick", pad["thick_mm"], "mm", "sensitivity runs", 0),
        _row("pad_off", "the same disc, away from the window in the second fingertip run", pad["off_mm"], "mm", "sensitivity runs", 0),
        _row("share_closed_window", "hole closed: share of the flow through the window", 100.0 * share["closed"]["window"], "%", "solver, h = 0.6 mm", 0),
        _row("share_closed_vent", "hole closed: share through the vent", 100.0 * share["closed"]["vent"], "%", "solver, h = 0.6 mm", 0),
        _row("share_open_window", "hole open: share through the window", 100.0 * share["open"]["window"], "%", "solver, h = 0.6 mm", 0),
        _row("share_open_hole", "hole open: share through the finger hole", 100.0 * share["open"]["hole"], "%", "solver, h = 0.6 mm", 0),
        _row("share_open_vent", "hole open: share through the vent", 100.0 * share["open"]["vent"], "%", "solver, h = 0.6 mm", 0),
    ]
    return _table("pitch_per_tenth", "Pitch per 0.1 mm, the desk, and a fingertip near the window",
                  pitch_per_tenth.view_spec.description, LONG, rows, 47, {"runs": _data().SENSITIVITY_RUNS["recorded"]})


@viewgen(id="playing", kind=ViewKind.TABLE, order=48,
         title="The breath the model assumes",
         description="Jet numbers at one assumed blowing pressure. The pressure is an assumption, and no "
                     "player has been measured.")
def playing(ctx: ViewContext) -> View | None:
    """Blowing pressure, jet speed, flow and the Strouhal numbers of both notes."""
    p = _have(ctx, "blow_pressure_pa", "jet_speed_m_s", "flow_l_min", "strouhal_closed", "strouhal_open",
              "radiated_fraction", "c_air_m_s", "lumped_ratio", "windway_gap_exit_mm", "window_cutup_mm")
    S = _shared()
    m = S.model_modules(ctx)
    if p is None or m is None:
        return None
    import acoustics
    cfg, built = "Config: %s", "build(): %s"
    rows = [
        _row("pressure", "blowing pressure assumed", p["blow_pressure_pa"], "Pa", cfg % "blow_pressure_pa", 0),
        _row("jet_speed", "jet speed at the windway exit", p["jet_speed_m_s"], "m/s", built % "jet_speed_m_s", 1),
        _row("flow", "air flow", p["flow_l_min"], "L/min", built % "flow_l_min", 1),
        _row("strouhal_closed", "Strouhal number, closed note", p["strouhal_closed"], "ratio", built % "strouhal_closed", 2),
        _row("strouhal_open", "Strouhal number, open note", p["strouhal_open"], "ratio", built % "strouhal_open", 2),
        _row("strouhal_low", "playable band, low edge", acoustics.STROUHAL_PLAYABLE[0], "ratio", "model/acoustics.py STROUHAL_PLAYABLE", 2),
        _row("strouhal_high", "playable band, high edge", acoustics.STROUHAL_PLAYABLE[1], "ratio", "model/acoustics.py STROUHAL_PLAYABLE", 2),
        _row("strouhal_best_low", "best band, low edge", acoustics.STROUHAL_BEST[0], "ratio", "model/acoustics.py STROUHAL_BEST", 2),
        _row("strouhal_best_high", "best band, high edge", acoustics.STROUHAL_BEST[1], "ratio", "model/acoustics.py STROUHAL_BEST", 2),
        _row("jet_thickness", "jet thickness (windway exit gap)", p["windway_gap_exit_mm"], "mm", cfg % "windway_gap_exit_mm", 1),
        _row("jet_travel", "jet travel (cut-up)", p["window_cutup_mm"], "mm", built % "window_cutup_mm", 1),
        _row("radiated", "share of the jet's power radiated as sound, estimate", 100.0 * p["radiated_fraction"], "%", built % "radiated_fraction", 1),
        _row("speed_of_sound", "speed of sound assumed", p["c_air_m_s"], "m/s", cfg % "c_air_m_s", 0),
        _row("lumped_ratio", "chamber length over the open note's wavelength", p["lumped_ratio"], "ratio", built % "lumped_ratio", 3),
        _row("lumped_limit", "where the uncalibrated lumped law is trusted to about 2 %", acoustics.LUMPED_RATIO_LIMIT, "ratio",
             "model/acoustics.py LUMPED_RATIO_LIMIT", 2),
    ]
    return _table("playing", "The breath the model assumes", playing.view_spec.description, LONG, rows, 48)


# ------------------------------------------------------------------------------------------------
# the measured coo
# ------------------------------------------------------------------------------------------------
@viewgen(id="coo_evidence", kind=ViewKind.TABLE, order=49,
         title="The measured coo, recording by recording",
         description="Medians over the used notes of each recording, from the pitch analysis of the three "
                     "coo recordings (input coo-pitch-analysis). Measured on recordings of real birds; the "
                     "whistle's notes are not in this table.")
def coo_evidence(ctx: ViewContext) -> View | None:
    """Per recording: fundamental and loudest partial at the start, the top and the end of a note."""
    rows = []
    for rec in _data().COO_EVIDENCE["recordings"]:
        row = {"id": rec["id"], "recording": rec["id"], "where": rec["where"], "input": rec["input"],
               "length_s": rec["length_s"], "notes_used": rec["notes_used"],
               "loudest_start_hz": rec["loudest"][0], "loudest_top_hz": rec["loudest"][1],
               "loudest_end_hz": rec["loudest"][2], "loudest_is": rec["loudest_is"],
               "loudest_weighted_hz": rec["loudest_weighted"],
               "note_s": rec["note_s"], "onset_to_onset_s": rec["onset_s"],
               "near_340_pct": _r(100.0 * rec["near_340"], 1), "near_470_pct": _r(100.0 * rec["near_470"], 1)}
        if rec["f0"] is not None:
            row.update(f0_start_hz=rec["f0"][0], f0_top_hz=rec["f0"][1], f0_end_hz=rec["f0"][2])
        if rec["h2_minus_h1_db"] is not None:
            row["h2_minus_h1_db"] = rec["h2_minus_h1_db"]
        if rec["gap_s"] is not None:
            row["gap_s"] = rec["gap_s"]
        rows.append(row)
    columns = [
        {"key": "recording", "label": "Recording"},
        {"key": "where", "label": "Where"},
        {"key": "notes_used", "label": "Notes used", "align": "right"},
        {"key": "f0_start_hz", "label": "Fundamental, start", "units": "Hz", "align": "right"},
        {"key": "f0_top_hz", "label": "Fundamental, top", "units": "Hz", "align": "right"},
        {"key": "f0_end_hz", "label": "Fundamental, end", "units": "Hz", "align": "right"},
        {"key": "loudest_start_hz", "label": "Loudest partial, start", "units": "Hz", "align": "right"},
        {"key": "loudest_top_hz", "label": "Loudest partial, highest (Sangli: loud core)", "units": "Hz", "align": "right"},
        {"key": "loudest_end_hz", "label": "Loudest partial, end", "units": "Hz", "align": "right"},
        {"key": "loudest_is", "label": "Which partial is loudest"},
        {"key": "loudest_weighted_hz", "label": "Loudest partial, energy-weighted", "units": "Hz", "align": "right"},
        {"key": "h2_minus_h1_db", "label": "Second harmonic over fundamental", "units": "dB", "align": "right"},
        {"key": "note_s", "label": "Note length", "units": "s", "align": "right"},
        {"key": "onset_to_onset_s", "label": "Onset to onset", "units": "s", "align": "right"},
        {"key": "gap_s", "label": "Silence between notes", "units": "s", "align": "right"},
        {"key": "near_340_pct", "label": "Loudest-partial energy within 25 Hz of 340 Hz", "units": "%", "align": "right"},
        {"key": "near_470_pct", "label": "Loudest-partial energy within 25 Hz of 470 Hz", "units": "%", "align": "right"},
        {"key": "length_s", "label": "Recording length", "units": "s", "align": "right"},
        {"key": "input", "label": "Input record"},
    ]
    return _table("coo_evidence", "The measured coo, recording by recording", coo_evidence.view_spec.description,
                  columns, rows, 49, {"input": _data().COO_INPUT,
                                      "method": "medians over the used notes; note length at 12 dB under the note's peak"})


@viewgen(id="coo_summary", kind=ViewKind.TABLE, order=50,
         title="What the coo evidence supports, and how thin it is",
         description="The analysis's own reading of the three recordings (input coo-pitch-analysis), beside "
                     "the whistle's two targets. The recordings disagree on which partial is loudest.")
def coo_summary(ctx: ViewContext) -> View | None:
    """Candidate note pairs, the spread between recordings and the tolerance that follows."""
    p = _have(ctx, "target_closed_hz", "target_open_hz")
    if p is None:
        return None
    rows = [_row(key, what, value, unit, "input %s, section %s" % (_data().COO_INPUT, section))
            for key, what, value, unit, section in _data().COO_EVIDENCE["summary"]]
    lo, hi = p["target_closed_hz"], p["target_open_hz"]
    rows += [
        _row("target_closed", "the whistle's target, finger hole closed", lo, "Hz", "Config: target_closed_hz", 0),
        _row("target_open", "the whistle's target, finger hole open", hi, "Hz", "Config: target_open_hz", 0),
        _row("target_ratio", "the targets' ratio", hi / lo, "ratio", "arithmetic", 2),
        _row("target_semitones", "the targets' interval", 12.0 * math.log2(hi / lo), "semitones", "arithmetic", 1),
        _row("closed_below_start", "closed target below the measured start of the loudest partial",
             12.0 * math.log2(380.0 / lo), "semitones", "arithmetic on the row above", 1),
        _row("open_below_top", "open target below the measured top of the loudest partial",
             12.0 * math.log2(511.0 / hi), "semitones", "arithmetic on the row above", 1),
    ]
    return _table("coo_summary", "What the coo evidence supports, and how thin it is",
                  coo_summary.view_spec.description, LONG, rows, 50, {"input": _data().COO_INPUT})


@viewgen(id="coo_chart", kind=ViewKind.CHART, order=62,
         title="The loudest partial through one note, against the two modelled notes",
         description="Median loudest partial at the start, the highest point and the end of a note in the "
                     "two Paris recordings (input coo-pitch-analysis), with the whistle's two modelled "
                     "notes as lines. In XC539061 the loudest partial is the second harmonic; in XC541143 "
                     "it is the fundamental until late in the note. The bird's values are measured; the "
                     "lines are modelled.")
def coo_chart(ctx: ViewContext) -> View | None:
    """Start, top and end of the loudest partial per recording, with the modelled notes as rules."""
    p = _have(ctx, "f_closed_hz", "f_open_hz")
    if p is None:
        return None
    series = []
    for rec in _data().COO_EVIDENCE["recordings"][:2]:
        series.append({"key": rec["id"], "label": rec["id"],
                       "points": [[0.0, rec["loudest"][0]], [0.5, rec["loudest"][1]], [1.0, rec["loudest"][2]]]})
    data = {"series": series,
            "x": {"label": "place in the note (0 start, 0.5 highest, 1 end)", "units": ""},
            "y": {"label": "frequency", "units": "Hz", "zero": False},
            "rule": [{"value": _r(p["f_closed_hz"], 0), "label": "model, hole closed"},
                     {"value": _r(p["f_open_hz"], 0), "label": "model, hole open"}]}
    return View(id="coo_chart", kind=ViewKind.CHART, title="The loudest partial through one note, against the two modelled notes",
                description=coo_chart.view_spec.description, data=data, order=62, meta={"input": _data().COO_INPUT})
