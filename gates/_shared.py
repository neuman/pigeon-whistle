"""What the whistle's tier-1 evaluators share: the model's code, one potential-flow solve per
design, one print-file reader.

Nothing here judges anything, and no limit lives here: a limit is a claim's acceptance condition,
read by the evaluator with ctx.acceptance().

Only model/solve.py is loaded (by path; it brings acoustics, geom and islands with it).  The
design reaches an evaluator through ctx.params, where each read is recorded, never through a
loaded model/pigeon.py.  pigeon.py is still part of these evaluators' recorded code, because
solve.py imports it for its own command line: an edit of any design value is an edit of pigeon.py,
so it reads as "evaluator code changed" on the eight tier-1 evaluators and they run again at the
next `check --tier 1`.  That errs toward running again, never toward a stale pass.
"""
from __future__ import annotations

import io
import json
import math
import os

from nopekit.modelio import load_path

_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "model")

solve = load_path(os.path.join(_MODEL, "solve.py"))
geom = solve.geom
acoustics = solve.acoustics


# --------------------------------------------------------------------------------------------
# the potential-flow solve
# --------------------------------------------------------------------------------------------
SOLVE_H_MM = 0.6
"""Grid pitch the tier-1 evaluators solve on.  With solve.py's first-order extrapolation one grid
at 0.6 mm is within 0.22 % in frequency of the seven-grid limit (solve.GRID_STUDY), for 11 s of
four states.  Lost: 0.8 mm (4 s, 0.37 %: too close to the 10 cent = 0.58 % the pitch claims
allow) and 0.5 mm (20 s for 0.18 %: nothing gained that a claim reads)."""

SOLVE_SCATTER_PCT = 100.0 * solve.GRID_SCATTER
"""What one grid may be off by against the limit h -> 0, in per cent of frequency (0.4): quoted in
the verdict lines so a reader sees how fine the instrument is beside the limit it is held to."""

SOLVE_SCATTER_CENTS = acoustics.cents(1.0 + solve.GRID_SCATTER, 1.0)
"""The same in cents (7)."""

STATE_WORDS = {"closed": "hole closed", "open": "hole open",
               "closed_plugged": "hole closed and vent plugged", "open_plugged": "hole open and vent plugged"}

CLOSED_FORM_KEY = {"closed": "f_closed_hz", "open": "f_open_hz",
                   "closed_plugged": "f_closed_plugged_hz", "open_plugged": "f_open_plugged_hz"}
"""solve.STATES name -> the build() key that holds the closed form's note for the same state."""


class ParamsConfig:
    """ctx.params seen as the model's Config: `cfg.hole_d_mm` is `ctx.params["hole_d_mm"]`.

    The solve takes a Config and reads attributes off it.  Handing it this view makes every
    choice it touches a recorded read of the evaluator, and nothing it does not touch: 58 of the
    82 fields when this was written (every field that shapes the acoustic geometry, and the speed
    of sound; not the bed, the print settings or the blowing pressure).  So a change of print
    speed leaves these verdicts current, and a field the solve starts to read later is recorded
    the day it does.  *Lost:* pigeon.Config(**every field read from ctx.params): it reads all 82,
    and `nopekit model trace` then solved again for every nudge of the bed size and the blowing
    pressure: 525 s for the five assumption-sourced choices, against 18 s with this view."""

    __slots__ = ("_params", "seen")

    def __init__(self, params):
        self._params = params
        self.seen = {}

    def __getattr__(self, name):
        try:
            value = self._params[name]
        except KeyError:
            raise AttributeError("the model publishes no %r" % name) from None
        self.seen[name] = value
        return value


_SOLVED: dict = {}
"""{state: [(the values that solve read, Hz)]}: one solve per design and state per process."""


def solved(ctx, states) -> dict:
    """{state: Hz} for `states` of the design in ctx.params, by solve.solve_states at SOLVE_H_MM.

    The three solver evaluators of one check run, and their known-good controls while the live
    design is the known-good one, share a solve.  A kept note is served only to a design whose
    value is equal for EVERY choice that solve read, and each of those is compared through
    ctx.params, so an evaluator served from here records the same reads as the one that solved.
    Nothing else can stand behind an entry: the solve opens no file and its result holds no clock
    (reruns are bit-identical, model/solve.py)."""
    out = {}
    for state in states:
        kept = _SOLVED.setdefault(state, [])
        for seen, hz in kept:
            if all(ctx.params[name] == value for name, value in seen.items()):
                out[state] = hz
                break
        else:
            cfg = ParamsConfig(ctx.params)
            hz = float(solve.solve_states(cfg, SOLVE_H_MM, states=[state])[state])
            kept.append((dict(cfg.seen), hz))
            out[state] = hz
    return out


# --------------------------------------------------------------------------------------------
# the print file
# --------------------------------------------------------------------------------------------
REMEDY = "run python3 model/mesh.py"

BED_TOL_MM = 0.05
"""A face lies on the bed when all of it is within this of the mesh's lowest point (the fdm-print
pack's own tolerance, and geom.BED_TOL)."""


class PrintFileProblem(Exception):
    """The print file cannot be judged; str() is the one line a person reads, remedy included."""


def read_stl(path: str):
    """(trimesh mesh with its vertices merged, byte count) of the binary STL at `path`.
    A module-level function, so ctx.load_file shares one parse between the evaluators of a sweep."""
    import trimesh
    with open(path, "rb") as fh:
        data = fh.read()
    return trimesh.load_mesh(io.BytesIO(data), file_type="stl", process=True), len(data)


def print_file(ctx, sidecar: bool = False):
    """(mesh, sidecar or None, display name) of the file at ctx.params["fdm.mesh_path"].

    Both files are read through ctx.load_file, so they are inputs of the verdict.  The path carries
    the geometry hash (model/pigeon.py mesh_path), so after any change to the solid the file is
    simply not there: that, an unreadable file, and a sidecar that describes another file all
    raise PrintFileProblem, which the evaluator reports as a FAIL, never as a skip."""
    rel = str(ctx.params["fdm.mesh_path"])
    name = os.path.basename(rel)
    ghash = str(ctx.params["geometry_hash"])
    try:
        mesh, n_bytes = ctx.load_file(rel, read_stl)
    except FileNotFoundError:
        raise PrintFileProblem("no print file %s for the current geometry (%s): %s"
                               % (name, ghash, REMEDY)) from None
    except Exception as exc:       # a truncated or foreign file: say so, as a failure of the file
        raise PrintFileProblem("print file %s cannot be read (%s: %s): %s"
                               % (name, type(exc).__name__, str(exc)[:80], REMEDY)) from None
    if len(mesh.faces) == 0:
        raise PrintFileProblem("print file %s holds no triangles: %s" % (name, REMEDY))
    if not sidecar:
        return mesh, None, name
    side_rel = os.path.splitext(rel)[0] + ".json"
    try:
        side = json.loads(ctx.load_file(side_rel).decode("utf-8"))
    except FileNotFoundError:
        raise PrintFileProblem("%s has no measurement sidecar beside it: %s" % (name, REMEDY)) from None
    except Exception as exc:
        raise PrintFileProblem("the sidecar of %s cannot be read (%s): %s"
                               % (name, type(exc).__name__, REMEDY)) from None
    if not isinstance(side, dict):
        raise PrintFileProblem("the sidecar of %s is not a record: %s" % (name, REMEDY))
    # The sidecar must be the measurement of THIS file for THIS geometry: its hash, its triangle
    # and byte counts and its plastic volume are held to the file itself.  These are identity
    # checks at the sidecar's own rounding, not limits on the design.
    said = []
    if str(side.get("geometry_hash")) != ghash:
        said.append("geometry %s, the model is at %s" % (side.get("geometry_hash"), ghash))
    if side.get("triangles") != len(mesh.faces):
        said.append("%s triangles, the file has %d" % (side.get("triangles"), len(mesh.faces)))
    if side.get("stl_bytes") != n_bytes:
        said.append("%s bytes, the file has %d" % (side.get("stl_bytes"), n_bytes))
    volume = _number(side.get("plastic_volume_mm3"))
    if volume is None or abs(volume - float(mesh.volume)) > 1e-5 * max(abs(volume), 1.0):
        said.append("plastic %s mm^3, the file encloses %.1f" % (side.get("plastic_volume_mm3"), float(mesh.volume)))
    if said:
        raise PrintFileProblem("the sidecar of %s describes another file (it says %s): %s"
                               % (name, "; ".join(said), REMEDY))
    return mesh, side, name


def _number(value):
    """`value` as a finite float, or None."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(float(value)) else None


def sidecar_number(side: dict, key: str, name: str) -> float:
    """A measurement the sidecar must hold; PrintFileProblem when it does not."""
    value = _number(side.get(key))
    if value is None:
        raise PrintFileProblem("the sidecar of %s has no %s: %s" % (name, key, REMEDY))
    return value
