"""standin.py - the print file the mesh gates' controls read: a box-shaped stand-in.

The known-good design is a Config.  Its own print file (print/pigeon-whistle-<hash>.stl) exists only
while the live design IS that Config: model/mesh.py deletes the files of every other geometry hash.
A control that read it would stop working the day the live design moved.  So the controls of the
five mesh gates read a solid this file builds, each time, into the run's own output directory.

What it is.  A plain block with the known-good bird's overall length, width and height, hollowed by
a gabled chamber of the bird's chamber volume (floor, roof angle and passage sizes taken from the
same known-good params), and opened by four passages: a windway slot through the tail end, a
window through the left side, a vertical finger hole and a vertical vent through the roof ridge.
So the numbers the model publishes about the printed solid (overall_*_mm, shell_wall_min_mm, and
chamber_volume_mm3 to within the 0.29 % of SHORT_MM) are true of it by construction, it has the
same four openings (genus 3), every roof leans roof_angle_deg from vertical, and its two flat
ceilings (windway roof, window lintel) are bridges held at both ends.

What it is not.  It is not a pigeon: no curved skin, no marching-cubes facets, no labium.  A
control on it shows that a gate reads a clean print file as clean and sees its one defect; it says
nothing about how the gate copes with the real surface.  The live check does that.

Each known-bad variant is the stand-in with ONE physical change (see bad_configs.py):
  beak      a drooping beak whose tip is lower than its root: its first layers start in mid-air
  leak      a 1 mm pinhole through the chamber floor: a fifth opening
  short_mm  the chamber built this much shorter than the model says (4 mm; the known-good has 0.3)
  floor_mm  a thinner chamber floor
  keel_mm   both lower long edges cut away at 45 degrees: the block stands on a narrow strip

The sidecar written beside the STL has the keys model/mesh.py writes that a gate reads.  Its
chamber_volume_mm3 and shell_wall_min_mm are those of the solids this file cut, not of the model.
"""
from __future__ import annotations

import json
import math
import os

MESH_STEM = "pigeon-whistle"

END_WALL_MM = 8.0          # plastic at the tail end and the head end of the chamber
HALF_WIDTH_MM = 12.0       # half-width of the chamber: its gable then rises 13.3 mm at 42 deg
WINDOW_X_MM = (30.0, 34.0)  # a 4 mm lintel: a bridge inside max_bridge_mm
BEAK = {"radius": 2.0, "root_in": 3.0, "root_z": 34.0, "reach": 10.0}   # droops 10 mm over 10 mm: 45 deg
LEAK_D_MM = 1.0
LEAK_X_MM = 85.0
SHORT_MM = 0.3
"""The stand-in's chamber is cut this much shorter than the model's volume asks for, on purpose:
it then holds 0.29 % less air than the model publishes, as a real mesh never matches its model
exactly.  That puts the known-good control of whistle.mesh_agrees at 0.29 % against its 0.5 %
limit instead of at a flat 0, which every limit admits."""


def build(params: dict, *, beak: bool = False, leak: bool = False, short_mm: float = SHORT_MM,
          floor_mm: float | None = None, keel_mm: float = 0.0):
    """(manifold3d solid, facts) of the stand-in for the design `params` describes."""
    from manifold3d import CrossSection, Manifold

    length = float(params["overall_length_mm"])
    width = float(params["overall_width_mm"])
    height = float(params["overall_height_mm"])
    volume = float(params["chamber_volume_mm3"])
    floor_model = float(params["floor_mm"])
    floor = floor_model if floor_mm is None else float(floor_mm)
    tan_roof = math.tan(math.radians(float(params["roof_angle_deg"])))
    b = HALF_WIDTH_MM
    rise = b / tan_roof
    cavity_len = length - 2.0 * END_WALL_MM
    # the wall height that gives the MODEL's chamber volume on the model's floor: section = V / length
    wall_h = (volume / cavity_len - b * rise) / (2.0 * b)
    eave = floor_model + wall_h
    ridge = eave + rise
    if wall_h <= 0 or ridge > height - 2.0:
        raise ValueError("stand-in chamber does not fit this envelope: wall %.1f mm, ridge %.1f of %.1f mm"
                         % (wall_h, ridge, height))
    cavity_len -= float(short_mm)

    body = Manifold.cube((length, width, height)).translate((0.0, -0.5 * width, 0.0))
    if keel_mm > 0:
        k, y = float(keel_mm), 0.5 * width
        # a 45 degree cut along each lower long edge, leaving a strip width - 2 k wide on the bed
        tri = CrossSection([[(y - k - 1.0, -1.0), (y + 1.0, -1.0), (y + 1.0, k + 1.0)]])
        cut = tri.extrude(length + 2.0).rotate((90.0, 0.0, 90.0)).translate((-1.0, 0.0, 0.0))
        body = body - cut - cut.mirror((0.0, 1.0, 0.0))
    section = CrossSection([[(-b, floor), (b, floor), (b, eave), (0.0, ridge), (-b, eave)]])
    # extrude runs along +z: map the section's (x, y) to the solid's (y, z) and the extrusion to x
    cavity = section.extrude(cavity_len).rotate((90.0, 0.0, 90.0)).translate((END_WALL_MM, 0.0, 0.0))
    z0 = float(params["windway_floor_z_mm"])
    z1 = z0 + float(params["windway_height_mm"])
    gap = float(params["windway_exit_gap_cad_mm"])
    windway = Manifold.cube((END_WALL_MM + 2.0, gap, z1 - z0)).translate((-1.0, -0.5 * gap, z0))
    window = Manifold.cube((WINDOW_X_MM[1] - WINDOW_X_MM[0], 0.5 * width - b + 2.0, z1 - z0)) \
        .translate((WINDOW_X_MM[0], b - 1.0, z0))
    bores = []
    for x_key, d_key in (("hole_x_mm", "hole_cad_d_mm"), ("vent_x_mm", "vent_cad_d_mm")):
        r = 0.5 * float(params[d_key])
        bores.append(Manifold.cylinder(height - ridge + 6.0, r, r, 64)
                     .translate((float(params[x_key]), 0.0, ridge - 5.0)))
    solid = body - cavity - windway - window - bores[0] - bores[1]
    if leak:
        solid = solid - Manifold.cylinder(floor + 2.0, 0.5 * LEAK_D_MM, 0.5 * LEAK_D_MM, 24) \
            .translate((LEAK_X_MM, 0.0, -1.0))
    if beak:
        r, reach = BEAK["radius"], BEAK["reach"]
        span = math.hypot(reach + BEAK["root_in"], reach + BEAK["root_in"])
        rod = Manifold.cylinder(span, r, r, 32).rotate((0.0, 135.0, 0.0)) \
            .translate((length - BEAK["root_in"], 0.0, BEAK["root_z"]))
        solid = solid + rod
    facts = {
        "chamber_volume_mm3": round(float(cavity.volume()), 1),
        # the thinnest plastic between the chamber and the outside, from the sizes cut above
        "shell_wall_min_mm": round(min(floor, END_WALL_MM, 0.5 * width - b, height - ridge), 3),
    }
    return solid, facts


def stage(ctx, params: dict, name: str, **changes) -> str:
    """Write the stand-in (with `changes`) and its sidecar under the run's output directory; return
    the STL's absolute path.  The file name carries the design's geometry hash, as the real one does."""
    import numpy as np
    import trimesh

    solid, facts = build(params, **changes)
    me = solid.to_mesh()
    mesh = trimesh.Trimesh(vertices=np.asarray(me.vert_properties)[:, :3], faces=np.asarray(me.tri_verts),
                           process=False)
    ghash = str(params["geometry_hash"])
    path = ctx.out_path("selftest", name, "%s-%s.stl" % (MESH_STEM, ghash))
    mesh.export(path)
    lo, hi = mesh.bounds
    sidecar = dict(facts)
    sidecar.update({
        "geometry_hash": ghash,
        "stand_in": name,
        "triangles": int(len(mesh.faces)),
        "stl_bytes": os.path.getsize(path),
        "bbox_mm": [round(float(v), 3) for v in hi - lo],
        "plastic_volume_mm3": round(float(solid.volume()), 1),
    })
    with open(os.path.splitext(path)[0] + ".json", "w", encoding="utf-8") as fh:
        json.dump(sidecar, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return path
