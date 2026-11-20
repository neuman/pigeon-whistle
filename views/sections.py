"""Cut-away pictures of the print mesh: three sections and the labelled inside view.

Each picture is re-rendered from the mesh that build() publishes as fdm.mesh_path, by model/render.py,
and written through ctx.write_asset.  They are drawings of the print file.  Nothing has been printed.
"""
from __future__ import annotations

import importlib.util
import os
import sys

from nopekit.models import View, ViewKind
from nopekit.site import ViewContext, viewgen


def _load(stem):
    name = "pigeon_views_" + stem.lstrip("_")
    if name in sys.modules:
        return sys.modules[name]
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), stem + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


WIDTH = 1200

SECTIONS = {
    # view id: (cut name in _draw.cuts, asset, title, description)
    "section_side": ("side", "section-side.png",
                     "Cut through the middle of the bird",
                     "The print mesh cut on its mid-plane and seen from the bird's right side; cut plastic is "
                     "red. It shows the chamber under its gabled roof, the rump lobe behind it, the finger "
                     "hole with its undercut and the vent. The pale opening low in the lobe is the window, "
                     "seen through. A drawing of the print file, not a photograph."),
    "section_jet": ("jet", "section-jet.png",
                    "Cut along the air jet",
                    "The print mesh cut on the plane of the air jet and seen from the bird's left; cut "
                    "plastic is red. The grey strip in the tail is the far wall of the windway. Where it "
                    "ends, the square opening leads into the rump lobe: the jet crosses this opening and "
                    "meets the labium at its far edge. A drawing of the print file, not a photograph."),
    "section_plan": ("plan", "section-plan.png",
                     "Cut at window height, seen from above",
                     "The print mesh cut level with the middle of the window and seen from above; cut "
                     "plastic is red. The windway narrows from the tail tip to its exit, the window opens "
                     "through the left flank, the labium wedge faces the jet, and the lobe leads into the "
                     "chamber. A drawing of the print file, not a photograph."),
}


def _ready(ctx):
    S = _load("_shared")
    m = S.model_modules(ctx)
    if m is None:
        ctx.log("no model folder: no section is drawn")
        return None
    loaded = S.load_mesh(ctx)
    if loaded is None:
        return None
    return S, m, S.config_of(ctx, m.pigeon), loaded[0], loaded[1]


def _section(ctx, view_id, order):
    name, asset, title, description = SECTIONS[view_id]
    ready = _ready(ctx)
    if ready is None:
        return None
    _S, m, cfg, V, F = ready
    D = _load("_draw")
    normal, offset, azim, elev = D.cuts(m.geom, cfg)[name]
    try:
        data, area = D.section_png(m.render, m.geom, V, F, normal, offset, azim, elev, width=WIDTH)
    except Exception as exc:                                    # noqa: BLE001 - a mesh that will not cut is no picture
        ctx.log("%s: the mesh could not be cut: %s: %s" % (view_id, type(exc).__name__, exc))
        return None
    src = ctx.write_asset(asset, data)
    from PIL import Image
    import io
    w, h = Image.open(io.BytesIO(data)).size
    return View(id=view_id, kind=ViewKind.IMAGE, title=title, description=description, src=src, order=order,
                meta={"width": w, "height": h, "mesh": ctx.param("fdm.mesh_path"),
                      "cut": {"normal": [round(t, 6) + 0.0 for t in normal], "offset_mm": round(offset, 4) + 0.0,
                              "face_mm2": round(area, 0)}})


@viewgen(id="section_side", kind=ViewKind.IMAGE, title=SECTIONS["section_side"][2],
         description=SECTIONS["section_side"][3], requires_python=["trimesh", "numpy", "manifold3d", "PIL"], order=30)
def section_side(ctx: ViewContext) -> View | None:
    """The mid-plane cut."""
    return _section(ctx, "section_side", 30)


@viewgen(id="section_plan", kind=ViewKind.IMAGE, title=SECTIONS["section_plan"][2],
         description=SECTIONS["section_plan"][3], requires_python=["trimesh", "numpy", "manifold3d", "PIL"], order=31)
def section_plan(ctx: ViewContext) -> View | None:
    """The cut at window mid-height."""
    return _section(ctx, "section_plan", 31)


@viewgen(id="section_jet", kind=ViewKind.IMAGE, title=SECTIONS["section_jet"][2],
         description=SECTIONS["section_jet"][3], requires_python=["trimesh", "numpy", "manifold3d", "PIL"], order=32)
def section_jet(ctx: ViewContext) -> View | None:
    """The cut on the jet plane."""
    return _section(ctx, "section_jet", 32)


@viewgen(id="inside", kind=ViewKind.IMAGE, title="Inside the whistle, with its parts named",
         description="Two cuts of the print mesh on one scale: through the middle, and at window height. "
                     "The labels name the mouthpiece, the windway, the window, the labium, the rump lobe, "
                     "the chamber, the finger hole and the vent. A drawing of the print file: nothing here "
                     "is a printed part.",
         requires_python=["trimesh", "numpy", "manifold3d", "PIL"], order=33)
def inside(ctx: ViewContext) -> View | None:
    """The labelled two-cut picture."""
    ready = _ready(ctx)
    if ready is None:
        return None
    _S, m, cfg, V, F = ready
    D = _load("_draw")
    try:
        data = D.inside_png(m.render, m.geom, cfg, V, F, width=WIDTH)
    except Exception as exc:                                    # noqa: BLE001
        ctx.log("inside: the picture could not be drawn: %s: %s" % (type(exc).__name__, exc))
        return None
    src = ctx.write_asset("inside.png", data)
    from PIL import Image
    import io
    w, h = Image.open(io.BytesIO(data)).size
    return View(id="inside", kind=ViewKind.IMAGE, title="Inside the whistle, with its parts named",
                description=inside.view_spec.description, src=src, order=33,
                meta={"width": w, "height": h, "mesh": ctx.param("fdm.mesh_path")})
