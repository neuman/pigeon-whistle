"""Helpers the project's viewgens share.  The leading underscore keeps the view loader off this file.

Every viewgen here reads the design the same way: numbers from ctx.params (the model's Config and
build() keys, flattened), geometry from the print mesh that build() publishes as fdm.mesh_path, and
the recorded solver study from model/solve.py.  Nothing in a viewgen runs a solve.
"""
from __future__ import annotations

import os
import sys
from dataclasses import fields
from types import SimpleNamespace

# Display colours (sRGB, 0..1): one cut colour and one air colour on every picture.
CUT_RGB = (0.86, 0.42, 0.33)
AIR_RGB = (0.36, 0.68, 0.95)
BREATH_RGB = (0.10, 0.42, 0.86)


def model_modules(ctx):
    """The model's own modules (geom, render, solve, pigeon), imported from <root>/model.
    Returns None when the folder is not there."""
    model_dir = os.path.join(os.path.abspath(ctx.root or os.curdir), "model")
    if not os.path.isfile(os.path.join(model_dir, "geom.py")):
        return None
    if model_dir not in sys.path:
        sys.path.append(model_dir)          # appended, as model/geom.py does: nothing is shadowed
    import geom
    import pigeon
    import render
    import solve
    return SimpleNamespace(geom=geom, pigeon=pigeon, render=render, solve=solve)


def config_of(ctx, pigeon):
    """The Config the build projected: every Config field read back from ctx.params."""
    kw = {}
    for f in fields(pigeon.Config):
        v = ctx.param(f.name)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            kw[f.name] = type(getattr(pigeon.CONFIG, f.name))(v)
    return pigeon.Config(**kw)


def mesh_file(ctx):
    """Absolute path of the print mesh build() names, or None when it names none or the file is absent."""
    stated = ctx.param("fdm.mesh_path")
    if not isinstance(stated, str) or not stated:
        ctx.log("the model names no fdm.mesh_path: nothing to draw")
        return None
    path = stated if os.path.isabs(stated) else os.path.join(ctx.root or os.curdir, stated)
    if not os.path.isfile(path):
        ctx.log("the print mesh %s is not there: run python3 model/mesh.py" % stated)
        return None
    return path


def load_mesh(ctx):
    """(V, F) of the print mesh (float64 mm, int64), welded, or None."""
    path = mesh_file(ctx)
    if path is None:
        return None
    import numpy as np
    import trimesh
    try:
        mesh = trimesh.load(path, process=True)
    except Exception as exc:                                    # noqa: BLE001 - a broken file is not a crash
        ctx.log("the print mesh could not be read: %s: %s" % (type(exc).__name__, exc))
        return None
    if getattr(mesh, "faces", None) is None or not len(mesh.faces):
        ctx.log("the print mesh holds no faces")
        return None
    return np.asarray(mesh.vertices, np.float64), np.asarray(mesh.faces, np.int64)


def number(ctx, name):
    """A finite model number by name, or None."""
    v = ctx.param(name)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    v = float(v)
    return v if v == v and abs(v) != float("inf") else None
