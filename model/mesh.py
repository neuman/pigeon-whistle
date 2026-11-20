#!/usr/bin/env python3
"""mesh.py - build the print mesh for CONFIG and everything measured off it.

    python3 model/mesh.py [--voxel 0.35] [--no-previews]

Writes, into print/ at the project root:
    pigeon-whistle-<geometry_hash>.stl    binary STL, print pose (belly down, bed at z = 0)
    pigeon-whistle-<geometry_hash>.json   geom.measure() of that mesh + geometry_hash + triangle count
    preview-*.png                         five views and three cut-away sections
and deletes mesh files left over from other geometry hashes.  model/pigeon.py's build() publishes the
same STL path, so the pack gates read exactly this file.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
import time

import numpy as np

import geom
import pigeon
import render

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRINT_DIR = os.path.join(ROOT, "print")

VIEWS = {                       # name: (azimuth, elevation) of the camera, degrees
    "three-quarter": (35.0, 22.0),
    "side": (-90.0, 4.0),       # the bird's right side, head to the right
    "top": (-90.0, 89.9),
    "front": (0.0, 6.0),
    "rear-left": (148.0, 24.0),  # the window flank
}


def write_previews(cfg, mesh, width=900):
    """Five shaded views and three sections: mid-plane y = 0, the jet plane, window mid-height."""
    V, F = np.asarray(mesh.vertices), np.asarray(mesh.faces)
    L = geom.layout(cfg)
    out = []
    for name, (az, el) in VIEWS.items():
        path = os.path.join(PRINT_DIR, "preview-%s.png" % name)
        render.render(V, F, path, azim=az, elev=el, width=width)
        out.append(path)
    man = geom._as_manifold(V, F)
    jet = L.Ey * L.cs - L.Ex * L.sn                       # the jet plane is v = 0: -sin*x + cos*y = jet
    cuts = {"section-midplane": ((0.0, 1.0, 0.0), 0.0, -90.0, 0.0),
            "section-jet-plane": ((L.sn, -L.cs, 0.0), -jet, 90.0 + math.degrees(L.sig), 0.0),
            "section-window-height": ((0.0, 0.0, -1.0), -0.5 * (L.z0 + L.z1), -90.0, 89.9)}
    for name, (normal, offset, az, el) in cuts.items():
        path = os.path.join(PRINT_DIR, "preview-%s.png" % name)
        render.render_section(man, path, normal=normal, offset=offset, azim=az, elev=el, width=width)
        out.append(path)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--voxel", type=float, default=0.35, help="marching-cubes pitch, mm (default 0.35)")
    ap.add_argument("--no-previews", action="store_true")
    args = ap.parse_args(argv)
    cfg = pigeon.CONFIG
    ghash = geom.geometry_hash(cfg, pigeon.GEOMETRY_FIELDS)
    stem = "%s-%s" % (pigeon.MESH_NAME, ghash)
    os.makedirs(PRINT_DIR, exist_ok=True)
    t0 = time.perf_counter()
    mesh = geom.build_mesh(cfg, args.voxel)
    t_mesh = time.perf_counter() - t0
    stl = os.path.join(PRINT_DIR, stem + ".stl")
    mesh.export(stl)
    t0 = time.perf_counter()
    M = geom.measure(cfg, mesh)
    t_measure = time.perf_counter() - t0
    M.update(geometry_hash=ghash, mesh_file="print/%s.stl" % stem, stl_bytes=os.path.getsize(stl))
    with open(os.path.join(PRINT_DIR, stem + ".json"), "w") as fh:
        json.dump(M, fh, indent=1, sort_keys=True)
        fh.write("\n")
    for old in glob.glob(os.path.join(PRINT_DIR, pigeon.MESH_NAME + "-*")):
        if not os.path.basename(old).startswith(stem + "."):
            os.remove(old)
    previews = [] if args.no_previews else write_previews(cfg, mesh)
    ly = M.get("layers", {})
    print("%s  %d triangles, %.2f MB, genus %d (expected %d), watertight %s" % (
        M["mesh_file"], M["triangles"], M["stl_bytes"] / 1e6, M["genus"], M["genus_expected"], M["watertight"]))
    print("  bbox %s mm; chamber %.1f cm^3; plastic %.1f cm^3; shell wall min %.2f mm" % (
        M["bbox_mm"], M["chamber_volume_mm3"] / 1e3, M["plastic_volume_mm3"] / 1e3, M["shell_wall_min_mm"]))
    print("  overhang past %g deg: %.4f %% of surface; ceilings: %d regions; islands %s, hanging edges %s, longest bridge %s mm" % (
        cfg.overhang_limit_deg, 100.0 * M["overhang"]["frac"], M["ceiling_regions_n"], ly.get("islands"), ly.get("hanging"),
        ly.get("max_bridge_span_mm")))
    print("  mesh %.1f s, measure %.1f s, %d previews" % (t_mesh, t_measure, len(previews)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
