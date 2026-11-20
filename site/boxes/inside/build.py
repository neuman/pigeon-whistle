#!/usr/bin/env python3
"""Build this box: the labelled cut-away of the whistle.

    python3 site/boxes/inside/build.py

Writes inside.png and box.json beside this file (the box of the story section), and the same picture
with its own box.json into ../inside-engineering/ (the box of the engineering view's choices section:
a box sits in one section, and both readers need the picture; the two files are the same bytes).  The
picture is drawn by views/_draw.py from the print mesh that model/pigeon.py publishes: the same bytes
as the page's `inside` image view.  It is its own thumbnail.  A drawing of the print file: nothing has
been printed.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))


def main():
    sys.path.append(os.path.join(ROOT, "model"))
    import numpy as np
    import trimesh
    from PIL import Image
    import geom
    import pigeon
    import render
    spec = importlib.util.spec_from_file_location("pigeon_views_draw", os.path.join(ROOT, "views", "_draw.py"))
    draw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(draw)
    mesh_file = os.path.join(ROOT, pigeon.mesh_path())
    if not os.path.isfile(mesh_file):
        print("no print mesh at %s: run python3 model/mesh.py first" % os.path.relpath(mesh_file, ROOT))
        return 1
    mesh = trimesh.load(mesh_file, process=True)
    V, F = np.asarray(mesh.vertices, np.float64), np.asarray(mesh.faces, np.int64)
    data = draw.inside_png(render, geom, pigeon.CONFIG, V, F, width=1200)
    w, h = Image.open(io.BytesIO(data)).size
    caption = ("Two cuts of the print file on one scale. Breath goes down the windway in the tail, crosses "
               "the window and meets the labium. The chamber and its rump lobe hold the air that sounds. "
               "A drawing of the print file: nothing is printed yet.")
    for folder, view, section in ((HERE, "both", "story"),
                                  (os.path.join(os.path.dirname(HERE), "inside-engineering"), "engineering", "choices")):
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "inside.png"), "wb") as fh:
            fh.write(data)
        box = {"schema": 1, "kind": "image", "title": "Inside the whistle", "caption": caption,
               "src": "inside.png", "thumbnail": "inside.png", "view": view, "section": section, "aspect": "11/16"}
        with open(os.path.join(folder, "box.json"), "w", encoding="utf-8") as fh:
            json.dump(box, fh, indent=1)
            fh.write("\n")
    print("inside.png %d x %d px, %d bytes, in two boxes; caption %d chars" % (w, h, len(data), len(caption)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
