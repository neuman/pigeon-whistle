"""Evaluators that read the print file itself, tier 1: what the fdm-print pack cannot see.

The pack's evaluators (claim C11) judge face angles and flat ceilings.  They do not see a layer
that starts in mid-air between two sloped faces, a fifth opening, a print file built from another
geometry, or how far the thing can be tilted.  These do.

Each reads the STL at ctx.params["fdm.mesh_path"] through ctx.load_file, and two of them the
measurement sidecar model/mesh.py writes beside it (gates/_shared.py print_file).  The path
carries the geometry hash, so after any change to the solid the file is not there until
`python3 model/mesh.py` has run: every evaluator here then FAILS and says so.  None of them skips.

All are `model-only`: the checks were written for this project (two call the model's own
geom.stl_precheck and islands.layer_check).  The limits, and their sources, are in the claims.

Their controls do not read print/: selftest/standin.py builds a stand-in solid for the known-good
design into the run's output directory, and each known-bad fixture is that solid with one defect.

Nothing here slices.  whistle.no_islands rasters the solid layer by layer the way a slicer would
start each layer; it knows nothing of a slicer's line placement, seams or cooling.
"""
from __future__ import annotations

import math
import os

from nopekit.gates import gate, GateContext
from nopekit.modelio import load_path
from nopekit.models import NegativeControl, Tier, Verdict

shared = load_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_shared.py"))

_BAD = "selftest/bad_configs.py:"
_NEEDS_PY = ["numpy", "scipy", "skimage", "trimesh", "manifold3d"]
"""What these evaluators and the model modules behind them import, somewhere: a machine without
one of them reads these evaluators as skipped, not crashed."""


def _no_file(gate_id, acc, units, problem) -> Verdict:
    """The FAIL every print-file evaluator returns when the file cannot be judged: no value, the
    limit it would have been held to, and the remedy in the line."""
    return Verdict(gate=gate_id, passed=False, limit=acc.limit, units=units,
                   comparator=acc.comparator.value, detail=str(problem))


SLICE_AGREEMENT = 0.02
"""whistle.no_islands trusts its layer count only if the layers it rastered add up to the solid's
own volume within this fraction (0.1 % on the whistle).  A mesh the slicer-like check cannot slice
gives no layers and so no islands; without this that would read as a clean print.  A check of the
instrument, not a limit on the design."""


@gate(
    id="whistle.no_islands",
    basis="model-only",
    title="No layer starts in mid-air",
    claims=["no-islands"],
    tier=Tier.BUILD,
    settles="unsupported starts",
    requires_python=_NEEDS_PY,
    negative_control=NegativeControl(
        fixture=_BAD + "drooping_beak",
        note="a beak whose tip hangs 10 mm lower than its root: its first layers rest on nothing, "
             "and every face of it is inside the 45 degree rule the pack judges by",
    ),
)
def no_islands(ctx: GateContext) -> Verdict:
    """Islands plus hanging edges in a layer-by-layer raster of the print file, against C12.

    model/islands.py layer_check at the configured layer height and line width: an island is a
    piece of a layer that touches nothing in the layer below; a hanging edge is new material more
    than one line width out that is not held at both ends.  Material held at both ends is a
    bridge: allowed here, and held to max_bridge_mm by the pack's fdm.bridge_span.
    One process (procs=1): a forked pool would be an input the verdict could not name.
    """
    acc = ctx.acceptance("C12")
    layer_h = float(ctx.params["layer_height_mm"])
    line_w = float(ctx.params["extrusion_width_mm"])
    try:
        mesh, _side, name = shared.print_file(ctx)
    except shared.PrintFileProblem as problem:
        return _no_file("whistle.no_islands", acc, "count", problem)
    volume = float(mesh.volume)
    try:
        report = shared.geom.islands.layer_check(mesh.vertices, mesh.faces, layer_h, line_w, procs=1)
        sliced = float(report["volume_from_layers_mm3"])
    except Exception as exc:        # a surface the slicer-like check cannot take is a failed print file
        return Verdict(gate="whistle.no_islands", passed=False, limit=acc.limit, units="count",
                       comparator=acc.comparator.value,
                       detail=f"{name} could not be sliced ({type(exc).__name__}: {str(exc)[:80]}); no count is "
                              f"given (whistle.mesh_closed says what is wrong with the surface)")
    if not (volume > 0 and abs(sliced / volume - 1.0) <= SLICE_AGREEMENT):
        return Verdict(gate="whistle.no_islands", passed=False, limit=acc.limit, units="count",
                       comparator=acc.comparator.value,
                       detail=f"{name} could not be sliced: {report['layers']} layers add up to {sliced:.0f} mm^3, "
                              f"the solid is {volume:.0f} mm^3; no count is given")
    starts = int(report["islands"]) + int(report["hanging"])
    where = ""
    found = (report["island_list"] + report["hanging_list"])[:1]
    if found:
        where = f"; first at x {found[0]['at'][0]}, y {found[0]['at'][1]}, z {found[0]['z']} mm"
    return Verdict(
        gate="whistle.no_islands", passed=acc.holds(starts), measured=float(starts), limit=acc.limit,
        units="count", comparator=acc.comparator.value,
        detail=f"{name}: {report['islands']} islands and {report['hanging']} hanging edges in {report['layers']} layers of "
               f"{layer_h:g} mm ({line_w:g} mm line){where}; {report['bridges']} bridges, longest "
               f"{report['max_bridge_span_mm']:g} mm; a raster check, not a slice",
    )


@gate(
    id="whistle.mesh_closed",
    basis="model-only",
    title="The print file is one closed solid with four openings",
    claims=["mesh-closed"],
    tier=Tier.BUILD,
    settles="mesh topology defects",
    requires_python=_NEEDS_PY,
    negative_control=NegativeControl(
        fixture=_BAD + "pinhole",
        note="a 1 mm pinhole through the chamber floor: still closed and one piece, and its genus "
             "is 4 where the four intended openings give 3",
    ),
)
def mesh_closed(ctx: GateContext) -> Verdict:
    """Count of topology defects in the print file, against C13.

    Counted: open edges, edges shared by more than two faces, welds and zero-area faces the
    STL would need (geom.stl_precheck: the file as the cad-solid loader sees it), surface pieces
    beyond one, a signed volume that is not positive, and the distance of the surface's genus from
    geom.expected_genus() (3: windway, window, finger hole, vent).  The genus counts openings; it
    does not say WHICH four they are.  A sealed pocket or a loose piece shows as a second piece.
    """
    acc = ctx.acceptance("C13")
    try:
        mesh, _side, name = shared.print_file(ctx)
    except shared.PrintFileProblem as problem:
        return _no_file("whistle.mesh_closed", acc, "count", problem)
    pre = shared.geom.stl_precheck(mesh.vertices, mesh.faces)
    pieces = int(mesh.body_count)
    volume = float(mesh.volume)
    expected = int(shared.geom.expected_genus())
    closed = pre["open_edges"] == 0 and pre["nonmanifold_edges"] == 0
    # Euler characteristic of a closed orientable surface of `pieces` pieces: 2 * pieces - 2 * genus
    genus = (2 * pieces - int(mesh.euler_number)) // 2 if closed else None
    defects = (pre["open_edges"] + pre["nonmanifold_edges"] + pre["extra_welds"] + pre["dropped_faces"]
               + max(pieces - 1, 0) + (0 if volume > 0 else 1)
               + (abs(genus - expected) if genus is not None else 0))
    return Verdict(
        gate="whistle.mesh_closed", passed=acc.holds(defects), measured=float(defects), limit=acc.limit,
        units="count", comparator=acc.comparator.value,
        detail=f"{name}: {len(mesh.faces)} triangles, {pre['open_edges']} open and {pre['nonmanifold_edges']} "
               f"non-manifold edges, {pre['extra_welds'] + pre['dropped_faces']} repairs needed, {pieces} piece(s), "
               f"genus {'not defined (surface open)' if genus is None else genus} (expected {expected}), "
               f"encloses {volume:.0f} mm^3",
    )


@gate(
    id="whistle.mesh_agrees",
    basis="model-only",
    title="The print file is the model's solid",
    claims=["mesh-agrees"],
    tier=Tier.BUILD,
    settles="mesh to model disagreement",
    requires_python=_NEEDS_PY,
    negative_control=NegativeControl(
        fixture=_BAD + "short_chamber",
        note="the print file's chamber is 4 mm shorter than the model's: 3.9 % less air, about 34 "
             "cents sharp if printed, with the outside unchanged",
    ),
)
def mesh_agrees(ctx: GateContext) -> Verdict:
    """Largest relative disagreement between the print file and the numbers build() publishes,
    against C14: chamber volume, overall length, width and height.

    The extents are read off the STL here.  The chamber volume is NOT measured here: it is the
    void model/mesh.py measured when it wrote the file (openings plugged with the model's own
    cutters) and recorded in the sidecar, and this evaluator first holds the sidecar to the file
    (geometry hash, triangle and byte counts, plastic volume).  build()'s chamber volume is a
    0.8 mm lattice integral of the same field the mesh was cut from, so this catches a frame,
    unit or staleness error between the two, not an error they share.
    """
    acc = ctx.acceptance("C14")
    model = {"chamber": float(ctx.params["chamber_volume_mm3"]),
             "length": float(ctx.params["overall_length_mm"]),
             "width": float(ctx.params["overall_width_mm"]),
             "height": float(ctx.params["overall_height_mm"])}
    try:
        mesh, side, name = shared.print_file(ctx, sidecar=True)
        void = shared.sidecar_number(side, "chamber_volume_mm3", name)
    except shared.PrintFileProblem as problem:
        return _no_file("whistle.mesh_agrees", acc, "%", problem)
    extent = mesh.bounds[1] - mesh.bounds[0]
    file = {"chamber": void, "length": float(extent[0]), "width": float(extent[1]), "height": float(extent[2])}
    apart = {k: 100.0 * (file[k] / model[k] - 1.0) if model[k] > 0 else float("inf") for k in model}
    worst = max(apart, key=lambda k: abs(apart[k]))
    measured = round(abs(apart[worst]), 3)
    if measured != measured or measured == float("inf"):
        return Verdict(gate="whistle.mesh_agrees", passed=False, limit=acc.limit, units="%",
                       comparator=acc.comparator.value,
                       detail=f"the model publishes no {worst} to compare {name} with")
    return Verdict(
        gate="whistle.mesh_agrees", passed=acc.holds(measured), measured=measured, limit=acc.limit,
        units="%", comparator=acc.comparator.value,
        detail=f"{name}: chamber {void:.0f} mm^3 as measured by model/mesh.py vs {model['chamber']:.0f} in the "
               f"model ({apart['chamber']:+.3f} %); {extent[0]:.2f} x {extent[1]:.2f} x {extent[2]:.2f} mm vs "
               f"{model['length']:.2f} x {model['width']:.2f} x {model['height']:.2f}; worst {worst} "
               f"{apart[worst]:+.3f} % (limit {acc.limit} %)",
    )


@gate(
    id="whistle.wall_as_meshed",
    basis="model-only",
    title="The shell is at least four perimeters thick, in the print file",
    claims=["wall-airtight"],
    tier=Tier.BUILD,
    settles="thinnest shell wall",
    requires_python=_NEEDS_PY,
    negative_control=NegativeControl(
        fixture=_BAD + "thin_floor_printed",
        note="the print file's chamber floor is 1.2 mm where the model says 2.1, and its sidecar "
             "records it",
    ),
)
def wall_as_meshed(ctx: GateContext) -> Verdict:
    """The thinnest shell wall model/mesh.py measured on the print file, against C15.

    This evaluator does NOT measure.  It reads shell_wall_min_mm from the sidecar (the true
    distance from the chamber surface to the skin or the bed, taken before the voicing cuts) after
    holding the sidecar to the file.  It exists so the designed 2.1 mm of whistle.wall_airtight is
    also true of the solid that was meshed.  A wall thinned by the voicing cuts is not in it.
    """
    acc = ctx.acceptance("C15")
    try:
        _mesh, side, name = shared.print_file(ctx, sidecar=True)
        wall = round(shared.sidecar_number(side, "shell_wall_min_mm", name), 2)
    except shared.PrintFileProblem as problem:
        return _no_file("whistle.wall_as_meshed", acc, "mm", problem)
    return Verdict(
        gate="whistle.wall_as_meshed", passed=acc.holds(wall), measured=wall, limit=acc.limit,
        units="mm", comparator=acc.comparator.value,
        detail=f"{name}: thinnest shell wall {wall:.2f} mm as measured by model/mesh.py and recorded beside "
               f"the file (limit {acc.limit} mm); read, not re-measured",
    )


@gate(
    id="whistle.desk_stable",
    basis="model-only",
    title="It sits steady on its belly",
    claims=["desk-stable"],
    tier=Tier.BUILD,
    settles="tipping angle",
    requires_python=_NEEDS_PY,
    negative_control=NegativeControl(
        fixture=_BAD + "narrow_foot",
        note="the same solid standing on a 27.7 mm wide strip: the support under the centre of "
             "mass shrinks to 13.8 mm each side and it tips at 19.3 degrees",
    ),
)
def desk_stable(ctx: GateContext) -> Verdict:
    """Smallest angle the print file can be tilted before it tips, against C20.

    Measured on the STL: the bed patch is the convex hull of the faces lying on the bed, the
    centre of mass is that of the closed solid at ONE density, and the angle is
    atan(distance from the centre of mass to the nearest hull edge, in plan / its height).
    A print is not one density: the head, the tail block and the roof are sparse inside, and this
    does not model that.  The solid head is the highest mass, so one density is more likely to put
    the centre of mass too high than too low.  The desk is taken as flat and rigid.

    The hull is worked out here in numpy (Andrew's monotone chain).  scipy.spatial.ConvexHull was
    tried first: qhull writes a scratch file, an input the verdict cannot name, and the claim read
    Stale on every plain check.
    """
    import numpy as np

    acc = ctx.acceptance("C20")
    try:
        mesh, _side, name = shared.print_file(ctx)
    except shared.PrintFileProblem as problem:
        return _no_file("whistle.desk_stable", acc, "deg", problem)
    if not (mesh.is_watertight and float(mesh.volume) > 0):
        return Verdict(gate="whistle.desk_stable", passed=False, limit=acc.limit, units="deg",
                       comparator=acc.comparator.value,
                       detail=f"{name} is not a closed solid, so it has no centre of mass to measure "
                              f"(whistle.mesh_closed says what is open)")
    verts = np.asarray(mesh.vertices, float)
    tri = verts[np.asarray(mesh.faces)]
    z0 = float(verts[:, 2].min())
    on_bed = (tri[:, :, 2].max(axis=1) - z0 <= shared.BED_TOL_MM) & (np.asarray(mesh.face_normals)[:, 2] < -0.999)
    pts = np.unique(tri[on_bed][:, :, :2].reshape(-1, 2), axis=0) if on_bed.any() else np.zeros((0, 2))
    if len(pts) < 3:
        return Verdict(gate="whistle.desk_stable", passed=False, limit=acc.limit, units="deg",
                       comparator=acc.comparator.value,
                       detail=f"{name} has no flat face on the bed to stand on")
    hull = _convex_hull(pts)
    if len(hull) < 3:
        return Verdict(gate="whistle.desk_stable", passed=False, limit=acc.limit, units="deg",
                       comparator=acc.comparator.value,
                       detail=f"{name} touches the bed along a line only")
    com = np.asarray(mesh.center_mass, float)
    # distance from the centre of mass, in plan, to each hull edge: positive inside (the hull runs
    # counter-clockwise), and the smallest of them is how far the weight is from tipping
    edge = np.roll(hull, -1, axis=0) - hull
    inside = (edge[:, 0] * (com[1] - hull[:, 1]) - edge[:, 1] * (com[0] - hull[:, 0])) / np.hypot(edge[:, 0], edge[:, 1])
    margin = float(inside.min())
    area = 0.5 * float(abs(np.sum(hull[:, 0] * np.roll(hull[:, 1], -1) - np.roll(hull[:, 0], -1) * hull[:, 1])))
    height = float(com[2] - z0)
    angle = round(math.degrees(math.atan2(margin, height)), 1)
    return Verdict(
        gate="whistle.desk_stable", passed=acc.holds(angle), measured=angle, limit=acc.limit,
        units="deg", comparator=acc.comparator.value,
        detail=f"{name}: centre of mass {height:.1f} mm up, {margin:.1f} mm inside the nearest edge of a "
               f"{area:.0f} mm^2 footprint (the hull of the bed patch): tips past {angle:.1f} deg (limit {acc.limit}); one density "
               f"assumed, sparse infill not modelled",
    )


def _convex_hull(points):
    """Convex hull of 2-D points as an (n, 2) array, counter-clockwise, no repeated first point."""
    import numpy as np

    pts = sorted(map(tuple, np.asarray(points, float)))

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out[:-1]
    return np.asarray(half(pts) + half(reversed(pts)), float)
