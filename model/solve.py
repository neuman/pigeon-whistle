"""solve.py - the whistle's four notes by potential flow: Config -> voxels -> resonance.

This is the reference the closed form in model/pigeon.py is calibrated against, in a form a gate can
call:

    solve_states(cfg, h) -> {"closed": Hz, "open": Hz, "closed_plugged": Hz, "open_plugged": Hz,
                             "V_mm3": ..., "h": ..., ...}

It rasterises the ACOUSTIC NOMINAL geometry (geom.voxel_model, cut cells) and runs
acoustics.solve_resonance once per state.  Nothing here is fitted to a wanted pitch.

Grid convergence, and why the result is extrapolated
----------------------------------------------------
On this geometry the solved conductance rises steadily as the grid is refined, by the same
fraction in every state: G(h) = G(0) * (1 + GRID_SLOPE_PER_MM * h) within GRID_SCATTER (table in
GRID_STUDY, h = 0.25 ... 0.5 mm).  The flow turns round sharp edges (the labium blade above all),
where the velocity is singular and a finite-volume grid recovers the missing kinetic energy only in
proportion to h; the cut cells already hold every cross-section to second order, so no remaining
part of the error is an area error.  A single grid is therefore 1.5-3 % flat in pitch (h = 0.4-0.8),
and the design centre is defined on the limit h -> 0: least squares through the fine grids for the
record in GRID_STUDY, and for one grid the same first-order law (`extrapolate=True`, the default).

Runtime of solve_states (four states, one process, this machine): 4.3 s at h = 0.8, 11.5 s at 0.6,
20 s at 0.5; per grid of the study see GRID_STUDY["seconds"].
"""
from __future__ import annotations

import math
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:          # loaded by path (a gate, a test): the sibling modules must still import.
    sys.path.append(_HERE)
import acoustics  # noqa: E402
import geom  # noqa: E402

STATES = {                         # name: (finger hole open, tuning vent open)
    "closed": (False, True),
    "open": (True, True),
    "closed_plugged": (False, False),
    "open_plugged": (True, False),
}

PAD_MM = 30.0
"""Exterior air kept round each opening (acoustics.solve_resonance default; 30 vs 120 mm is 0.13 % in f)."""

GRID_SLOPE_PER_MM = -0.0755
"""First-order grid coefficient of the solved conductance on this geometry: G(h) = G(0) (1 + s h).
Measured (GRID_STUDY): -0.083, -0.076, -0.070 and -0.073 per mm in the four states; this is their mean.
With it one grid lands within GRID_SCATTER of the seven-grid limit.  Lost: 0 (a single grid reported
as it is: 2-3 % flat at h = 0.6-0.8) and a two-grid Richardson step inside solve_states (it multiplies
the voxel aliasing of each grid, about 0.4 % in G, by 4 to 5)."""

GRID_SCATTER = 0.004
"""Largest |f(h) / sqrt(1 + s h) / f(0) - 1| over the four states and h = 0.25 ... 0.8 mm in GRID_STUDY
(worst state: 0.37 % at h = 0.8, 0.22 % at 0.6, 0.18 % at 0.5, 0.33 % at 0.35).  A gate that compares solve_states at
one grid with the closed form must allow at least this much."""

GRID_STUDY = {
    "recorded": "2026-11-19, Config as committed with this file (hole 7.05, vent 2.1, window 7.0 x 6.3 mm), "
                "c = 346 m/s, pad 30 mm, cut cells, tol 1e-7; `python3 model/solve.py --study`",
    "h_mm": (0.8, 0.6, 0.5, 0.4, 0.35, 0.3, 0.25),
    "G_mm": {       # total conductance chamber -> far field at each grid
        "closed_plugged": (3.8095, 3.8864, 3.9155, 3.9605, 3.9495, 3.9770, 4.0062),
        "closed": (4.2589, 4.3203, 4.3604, 4.4027, 4.3921, 4.4232, 4.4566),
        "open": (8.1552, 8.2874, 8.3396, 8.4052, 8.4130, 8.4542, 8.5043),
        "open_plugged": (7.6994, 7.8474, 7.8885, 7.9568, 7.9643, 8.0017, 8.0476),
    },
    "V_mm3": 118752.0,          # mean over the grids (118742 ... 118776)
    "G0_mm": {"closed_plugged": 4.0839, "closed": 4.5301, "open": 8.6422, "open_plugged": 8.1898},
    "slope_per_mm": {"closed_plugged": -0.0829, "closed": -0.0757, "open": -0.0700, "open_plugged": -0.0734},
    "f0_hz": {"closed_plugged": 322.93, "closed": 340.12, "open": 469.77, "open_plugged": 457.31},
    "fit_residual": 0.004,      # largest |G - line| / G0 over all points
    "seconds": {    # mean solve time of one state, with 1-4 solves running at once; rasterising adds
        0.8: 1.0, 0.6: 2.6, 0.5: 4.6, 0.4: 8.3, 0.35: 14.6, 0.3: 35.0, 0.25: 46.0},   # 0.3 / 0.9 / 1.6 / 3.7 / 5 / 9 / 17 s
    "peak_memory_gb": {0.8: 0.5, 0.6: 1.1, 0.5: 1.9, 0.4: 3.6, 0.35: 3.4, 0.3: 5.1, 0.25: 8.8},
}
"""The grid study the design centre and the closed form's end factors rest on: least squares of G
against h over the seven grids, read at h = 0.  The five fine grids alone give the same limit within
0.1 % (4.0805 against 4.0839 mm, vent plugged).  The remaining uncertainty of the limit is about
+-0.3 % in f; an unextrapolated solve at h = 0.25 is 0.8-0.9 % flat of it."""


def solve_states(cfg, h, extrapolate=True, states=None):
    """Passive resonance of the four states of `cfg` on a grid of pitch h (mm).

    Returns {"closed": Hz, "open": Hz, "closed_plugged": Hz, "open_plugged": Hz (hole closed / open,
    vent open unless "plugged"), "V_mm3", "h", "extrapolated", "G_mm": {state: conductance, as
    reported}, "raw_hz": {state: f on the grid itself}, "seconds"}.
    extrapolate=True (default) divides each solved conductance by (1 + GRID_SLOPE_PER_MM * h): the
    first-order limit h -> 0, good to GRID_SCATTER in f for h <= 0.8.  False reports the grid's own
    numbers.  Deterministic and single-threaded; 4.3 s at h = 0.8, 11.5 s at 0.6, 20 s at 0.5 (measured)."""
    t0 = time.perf_counter()
    speed = float(cfg.c_air_m_s)
    out = {"h": float(h), "extrapolated": bool(extrapolate), "G_mm": {}, "raw_hz": {}}
    for name in (states or STATES):
        hole_open, vent_open = STATES[name]
        vox = geom.voxel_model(cfg, h, hole_open=hole_open, vent_open=vent_open, cut_cells=True)
        r = acoustics.solve_resonance(vox, c=speed, pad_mm=PAD_MM)
        g = r["G_mm"] / (1.0 + GRID_SLOPE_PER_MM * h) if extrapolate else r["G_mm"]
        out["G_mm"][name] = g
        out["raw_hz"][name] = r["f_hz"]
        out["V_mm3"] = r["V_mm3"]
        out[name] = acoustics.helmholtz_hz(r["V_mm3"], g, speed)
    out["seconds"] = time.perf_counter() - t0
    return out


def grid_study(cfg, hs=GRID_STUDY["h_mm"]):
    """Re-run the study behind GRID_STUDY: solve every state on every grid (no extrapolation) and fit
    G against h.  Returns {"h_mm", "G_mm", "V_mm3", "G0_mm", "slope_per_mm", "f0_hz", "fit_residual"}.
    About 12 minutes and 9 GB with the default grids (h = 0.25 is three quarters of both)."""
    import numpy as np
    speed = float(cfg.c_air_m_s)
    runs = [solve_states(cfg, h, extrapolate=False) for h in hs]
    volume = float(np.mean([r["V_mm3"] for r in runs]))
    out = {"h_mm": tuple(hs), "G_mm": {}, "V_mm3": volume, "G0_mm": {}, "slope_per_mm": {}, "f0_hz": {}}
    worst = 0.0
    for name in STATES:
        g = np.array([r["G_mm"][name] for r in runs])
        slope, g0 = np.polyfit(np.asarray(hs, float), g, 1)
        out["G_mm"][name] = tuple(float(v) for v in g)
        out["G0_mm"][name] = float(g0)
        out["slope_per_mm"][name] = float(slope / g0)
        out["f0_hz"][name] = acoustics.helmholtz_hz(volume, float(g0), speed)
        worst = max(worst, float(np.max(np.abs(g - (g0 + slope * np.asarray(hs, float)))) / g0))
    out["fit_residual"] = worst
    return out


def main(argv=None):
    import argparse
    import pigeon
    ap = argparse.ArgumentParser(description="The four notes of the committed Config by potential flow.")
    ap.add_argument("--h", type=float, default=0.6, help="grid pitch, mm (default 0.6)")
    ap.add_argument("--study", action="store_true", help="the full grid study (about 12 min, 9 GB)")
    args = ap.parse_args(argv)
    cfg = pigeon.CONFIG
    if args.study:
        s = grid_study(cfg)
        print("h mm            " + "".join("%9.2f" % h for h in s["h_mm"]) + "      h->0  slope/mm    f0 Hz")
        for name in STATES:
            print("%-16s" % name + "".join("%9.4f" % g for g in s["G_mm"][name])
                  + "%10.4f %+9.4f %8.2f" % (s["G0_mm"][name], s["slope_per_mm"][name], s["f0_hz"][name]))
        print("V = %.0f mm^3, largest fit residual %.4f of G0" % (s["V_mm3"], s["fit_residual"]))
        return 0
    r = solve_states(cfg, args.h)
    built = pigeon.build(cfg)
    keys = {"closed": "f_closed_hz", "open": "f_open_hz", "closed_plugged": "f_closed_plugged_hz",
            "open_plugged": "f_open_plugged_hz"}
    print("h = %g mm, V = %.0f mm^3, %.1f s" % (r["h"], r["V_mm3"], r["seconds"]))
    for name in STATES:
        print("%-15s solve %7.2f Hz (on the grid %7.2f)   closed form %7.2f Hz   %+.2f %%" % (
            name, r[name], r["raw_hz"][name], built[keys[name]], 100.0 * (built[keys[name]] / r[name] - 1.0)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
