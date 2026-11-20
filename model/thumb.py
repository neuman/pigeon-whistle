#!/usr/bin/env python3
"""thumb.py - the one still picture of this candidate: site/thumb.png.

    python3 model/thumb.py [--out site/thumb.png] [--width 800] [--height 600]

A three-quarter view of the print mesh (the file build() publishes as fdm.mesh_path) from the bird's
front left, so the head, the finger hole, the window and the mouthpiece are all in sight.  Drawn by
model/render.py at four samples per pixel edge and averaged down, on a plain background with a soft
contact shadow.  Deterministic: the same mesh gives the same bytes.  It is a render of the print file;
nothing has been printed.
"""
from __future__ import annotations

import argparse
import io
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

import pigeon
import render

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AZIM, ELEV = 38.0, 24.0          # camera bearing round +Z from +X, and its height: front left, a little above
SSAA = 4
BODY = (0.60, 0.65, 0.75)        # one filament colour: pigeon blue-grey
PAPER_TOP = (0.965, 0.962, 0.950)
PAPER_BOTTOM = (0.905, 0.902, 0.890)
SHADOW = 0.34                    # darkest the contact shadow gets (share of the paper's brightness removed)


class _Png(io.BytesIO):
    name = "thumb.png"           # Pillow reads the format from the name


def _draw(V, F, bounds, width, height, **kw):
    buf = _Png()
    render.render(V, F, buf, azim=AZIM, elev=ELEV, width=width, height=height, ssaa=SSAA, bounds=bounds, **kw)
    return np.asarray(Image.open(io.BytesIO(buf.getvalue())).convert("RGB"), np.float64) / 255.0


def _coverage(V, F, bounds, width, height):
    """How much of each pixel the triangles cover (0..1): drawn black and unlit on white."""
    img = _draw(V, F, bounds, width, height, face_rgb=np.zeros((len(F), 3)), unlit=np.ones(len(F), bool),
                bg=(1.0, 1.0, 1.0))
    rows = 1.0 - 0.10 * np.linspace(0.0, 1.0, height * SSAA).reshape(height, SSAA).mean(axis=1)   # render's own backdrop
    return np.clip(1.0 - img[:, :, 0] / rows[:, None], 0.0, 1.0)


def make(mesh_file, out, width=800, height=600):
    import trimesh
    mesh = trimesh.load(mesh_file, process=True)
    V, F = np.asarray(mesh.vertices, np.float64), np.asarray(mesh.faces, np.int64)
    # frame: the bird with room round it, so the whole of it and its shadow sit inside width x height
    R = render.view_matrix(AZIM, ELEV)
    P = V @ R.T
    mn, mx = P[:, :2].min(0), P[:, :2].max(0)
    centre = 0.5 * (mn + mx)
    span = max((mx[0] - mn[0]) / 0.86, (mx[1] - mn[1]) / 0.76 * width / height)
    centre[1] -= 0.035 * span * height / width                    # a little more room under the feet
    corners = [centre[0] - 0.5 * span, centre[0] + 0.5 * span]
    bounds = np.array([R.T @ np.array([c, centre[1], 0.0]) for c in corners])
    bounds = np.vstack([bounds, bounds])                           # render pads 5 % each side of these
    bird = _draw(V, F, bounds, width, height, base=BODY, bg=(1.0, 1.0, 1.0))
    cover = _coverage(V, F, bounds, width, height)
    flat = V.copy()
    flat[:, 2] = 0.0
    shade = _coverage(flat, F, bounds, width, height)
    shade = ndimage.gaussian_filter(shade, 0.022 * width)
    shade = SHADOW * np.clip(shade, 0.0, 1.0) ** 1.25
    g = np.linspace(0.0, 1.0, height)[:, None, None]
    paper = np.asarray(PAPER_TOP) * (1.0 - g) + np.asarray(PAPER_BOTTOM) * g
    paper = np.broadcast_to(paper, (height, width, 3)) * (1.0 - shade[:, :, None])
    rows = (1.0 - 0.10 * np.linspace(0.0, 1.0, height * SSAA).reshape(height, SSAA).mean(axis=1))[:, None, None]
    lit = bird - rows * (1.0 - cover[:, :, None])                  # the bird alone (premultiplied by its coverage)
    img = np.clip(lit + paper * (1.0 - cover[:, :, None]), 0.0, 1.0)
    Image.fromarray((img * 255.0 + 0.5).astype(np.uint8)).save(out, format="PNG", optimize=True)
    return img.shape


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, "site", "thumb.png"))
    ap.add_argument("--width", type=int, default=800)
    ap.add_argument("--height", type=int, default=600)
    args = ap.parse_args(argv)
    mesh_file = os.path.join(ROOT, pigeon.mesh_path())
    if not os.path.isfile(mesh_file):
        print("no print mesh at %s: run python3 model/mesh.py first" % os.path.relpath(mesh_file, ROOT))
        return 1
    shape = make(mesh_file, args.out, args.width, args.height)
    print("%s  %d x %d px, %d bytes" % (os.path.relpath(args.out, ROOT), shape[1], shape[0], os.path.getsize(args.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
