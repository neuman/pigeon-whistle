"""The whistle opened along its airway, as a model the page can turn and pull apart.

The print mesh (build()'s fdm.mesh_path) is cut by the jet plane: the vertical plane through the
middle of the windway slot, the window and the labium edge.  The cut gives the bird's left flank and
the rest of the bird, each a closed solid with its cut face in its own colour.  Between them sits
the air: the chamber air (the void the mesh encloses once its four openings are plugged) and the
air in the windway (the model's own cutter, ended at the tail tip).  The window is left empty: it is
an opening to the outside, and a body drawn in it would read as a plug on the assembled bird.

The GLB is the model's frame, untransformed: Z up, millimetres, bed at z = 0.  Node names are
"<mover>__<body>"; the movers are `left`, `right` and `air`.
"""
from __future__ import annotations

import importlib.util
import math
import os
import sys

from nopekit.models import View, ViewKind
from nopekit.site import ViewContext, derive_explode, viewgen


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


VIEW_ID = "whistle"
SIMPLIFY_MM = 0.05          # surface tolerance of the drawn shell: 26 000 triangles from the STL's 75 000
AIR_SIMPLIFY_MM = 0.08      # the chamber air is a smooth blob: a coarser tolerance costs nothing a reader sees
CREASE_DEG = 35.0           # shading normals are shared across edges flatter than this (as model/render.py)
OPEN_MM = 42.0              # how far each half travels along the cut's normal at full explode
LIFT_MM = 66.0              # how far the air rises out of the opened bird: clear of both halves
SHELL_3D_RGB = (0.47, 0.52, 0.64)   # the shell in the live viewers, whose lights are brighter than the stills
NODES = ("left__shell", "left__cut", "right__shell", "right__cut", "air__chamber", "air__windway")


def _linear(rgb):
    """sRGB display colour -> the linear factors glTF stores."""
    return [round(((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92, 4) for c in rgb]


def _split_normals(np, V, F, crease_deg):
    """Vertices split along creases so each carries one shading normal: (V', N', F')."""
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    area = np.linalg.norm(n, axis=1)
    fn = n / np.maximum(area, 1e-30)[:, None]
    corner_v = F.ravel()
    order = np.argsort(corner_v, kind="stable")
    sv = corner_v[order]
    sf = order // 3
    start = np.concatenate([[0], np.nonzero(np.diff(sv))[0] + 1])
    deg = np.diff(np.concatenate([start, [len(sv)]]))
    deg_c = np.repeat(deg, deg)
    grp = np.repeat(start, deg)
    off = np.cumsum(deg_c) - deg_c
    i = np.repeat(np.arange(len(sv)), deg_c)
    j = np.repeat(grp, deg_c) + (np.arange(int(deg_c.sum())) - np.repeat(off, deg_c))
    fi, fj = sf[i], sf[j]
    keep = np.einsum("ij,ij->i", fn[fi], fn[fj]) > math.cos(math.radians(crease_deg))
    i, fj = i[keep], fj[keep]
    acc = np.stack([np.bincount(i, weights=n[fj, k], minlength=len(sv)) for k in range(3)], axis=1)
    acc /= np.maximum(np.linalg.norm(acc, axis=1), 1e-30)[:, None]
    cn = np.empty((len(F) * 3, 3))
    cn[order] = acc
    # weld corners that share a vertex and (to 1e-3) a normal
    key = np.concatenate([corner_v[:, None].astype(np.float64), np.round(cn, 3)], axis=1)
    _uniq, first, inverse = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inverse = np.asarray(inverse).reshape(-1)
    return V[corner_v[first]], cn[first], inverse.reshape(-1, 3)


def _body(trimesh, np, V, F, rgb, alpha=1.0, crease=CREASE_DEG, normal=None):
    """A trimesh.Trimesh with shading normals and one plain material."""
    V = np.asarray(V, np.float64)
    F = np.asarray(F, np.int64)
    if normal is None:
        Vs, Ns, Fs = _split_normals(np, V, F, crease)
    else:                                                       # a flat face: one normal for all of it
        used, inverse = np.unique(F.ravel(), return_inverse=True)
        Vs, Fs = V[used], np.asarray(inverse).reshape(-1, 3)
        Ns = np.tile(np.asarray(normal, np.float64), (len(Vs), 1))
    material = trimesh.visual.material.PBRMaterial(
        baseColorFactor=_linear(rgb) + [float(alpha)], metallicFactor=0.0, roughnessFactor=0.75,
        alphaMode="BLEND" if alpha < 1.0 else "OPAQUE", doubleSided=False)
    mesh = trimesh.Trimesh(vertices=np.round(Vs, 3).astype(np.float32), faces=Fs,
                           vertex_normals=np.round(Ns, 3).astype(np.float32), process=False)
    mesh.visual = trimesh.visual.TextureVisuals(material=material)
    return mesh


def build_bodies(S, m, cfg, V, F):
    """{node name: trimesh.Trimesh} of the opened whistle, plus the cut plane's (normal, offset).
    Deterministic: manifold3d booleans and numpy only."""
    import numpy as np
    import trimesh
    geom = m.geom
    L = geom.layout(cfg)
    arrays, as_manifold = geom._arrays, geom._as_manifold
    whole = as_manifold(V, F)
    shell = whole.simplify(SIMPLIFY_MM)
    # the jet plane: v = 0 in the voicing frame, -sin x + cos y = d; its normal points to the bird's left
    nrm = (-L.sn, L.cs, 0.0)
    d = L.Ey * L.cs - L.Ex * L.sn
    out = {}
    for name, n, off in (("left", nrm, d), ("right", tuple(-t for t in nrm), -d)):
        Vh, Fh = arrays(shell.trim_by_plane(n, off))
        a = np.cross(Vh[Fh[:, 1]] - Vh[Fh[:, 0]], Vh[Fh[:, 2]] - Vh[Fh[:, 0]])
        fn = a / np.maximum(np.linalg.norm(a, axis=1), 1e-30)[:, None]
        nn = np.asarray(n, np.float64)
        cap = (np.abs(Vh[Fh].mean(axis=1) @ nn - off) < 1e-3) & (fn @ nn < -0.999)
        out[name + "__shell"] = _body(trimesh, np, Vh, Fh[~cap], SHELL_3D_RGB)
        out[name + "__cut"] = _body(trimesh, np, Vh, Fh[cap], S.CUT_RGB, normal=-nn)
    # chamber air: plug the windway, window and both bores; the one void left inside is the air
    closed = whole + geom.passage_plug(cfg, L, geom.PLUG_GROW)
    Vc, Fc = arrays(closed)
    shells = trimesh.Trimesh(Vc, Fc, process=False).split(only_watertight=False)
    voids = sorted((float(s.volume), k) for k, s in enumerate(shells))
    if len(voids) >= 2 and voids[0][0] < 0.0:
        void = shells[voids[0][1]]
        air = as_manifold(np.asarray(void.vertices), np.asarray(void.faces)[:, ::-1]).simplify(AIR_SIMPLIFY_MM)
        Va, Fa = arrays(air)
        out["air__chamber"] = _body(trimesh, np, Va, Fa, S.AIR_RGB, alpha=0.5, crease=50.0)
    # the breath's way in: the windway slot as the model cuts it (print sizes), ended at the tail tip
    from manifold3d import Manifold, OpType
    lo, hi = V.min(0) - 10.0, V.max(0) + 10.0
    big = (*lo, *hi)
    windway = Manifold.batch_boolean([geom.hs_manifold(H, big) for H in geom.windway_pieces(cfg, L, True)], OpType.Add)
    windway = windway.trim_by_plane((1.0, 0.0, 0.0), float(V[:, 0].min()))
    Vw, Fw = arrays(windway)
    if len(Fw):
        out["air__windway"] = _body(trimesh, np, Vw, Fw, S.BREATH_RGB, crease=20.0)
    return out, nrm, d


@viewgen(
    id=VIEW_ID,
    kind=ViewKind.MODEL3D,
    title="The whistle, opened along its airway",
    description="The print mesh cut by the plane of the air jet. The left flank and the rest of the "
                "bird come apart; the air they enclose stays between them: the chamber air in light "
                "blue, the air in the windway in dark blue. Modelled geometry: nothing here is a "
                "printed part.",
    requires_python=["trimesh", "numpy", "manifold3d"],
    order=5,
)
def whistle(ctx: ViewContext) -> View | None:
    """The opened whistle as a GLB: two halves, their cut faces, and the air."""
    S = _shared()
    m = S.model_modules(ctx)
    if m is None:
        ctx.log("whistle: no model folder, nothing to draw")
        return None
    loaded = S.load_mesh(ctx)
    if loaded is None:
        return None
    V, F = loaded
    try:
        cfg = S.config_of(ctx, m.pigeon)
        bodies, nrm, d = build_bodies(S, m, cfg, V, F)
    except Exception as exc:                                    # noqa: BLE001 - a mesh that will not cut is no view
        ctx.log("whistle: the mesh could not be opened: %s: %s" % (type(exc).__name__, exc))
        return None
    import trimesh
    scene = trimesh.Scene()
    bounds = {}
    for name in NODES:
        mesh = bodies.get(name)
        if mesh is None or not len(mesh.faces):
            continue
        scene.add_geometry(mesh, node_name=name, geom_name=name)
        low, high = mesh.bounds
        bounds[name] = ([float(v) for v in low], [float(v) for v in high])
    if "left__shell" not in bounds or "right__shell" not in bounds:
        ctx.log("whistle: the cut left one side empty")
        return None
    src = ctx.write_asset("whistle.glb", scene.export(file_type="glb", include_normals=True))
    # The halves part along the cut's own normal and the air rises out between them.  Stated, because
    # the bird is as wide as it is tall to 0.02 mm and the derived stacking axis would turn on that.
    opened = {"movers": {
        "left": {"offset": [round(OPEN_MM * t, 3) + 0.0 for t in nrm]},
        "right": {"offset": [round(-OPEN_MM * t, 3) + 0.0 for t in nrm]},
        "air": {"offset": [0.0, 0.0, LIFT_MM]},
    }}
    parts = {
        "left_flank": [n for n in ("left__shell", "left__cut") if n in bounds],
        "body_and_head": [n for n in ("right__shell", "right__cut") if n in bounds],
        "chamber_air": [n for n in ("air__chamber",) if n in bounds],
        "windway_air": [n for n in ("air__windway",) if n in bounds],
    }
    meta = {
        "nodes": sorted(bounds),
        "explode": derive_explode(bounds, overrides=opened),
        "parts": {k: v for k, v in parts.items() if v},
        "units": "mm",
        "mesh": ctx.param("fdm.mesh_path"),
        "frame": "the model's frame, untransformed: x from the tail tip to the head, +y the bird's "
                 "left, z up, bed at z = 0",
        "cut_plane": {"normal": [round(t, 6) for t in nrm], "offset_mm": round(d, 4),
                      "what": "the jet plane: through the middle of the windway slot and the labium edge"},
    }
    return View(id=VIEW_ID, kind=ViewKind.MODEL3D, title="The whistle, opened along its airway",
                description=whistle.view_spec.description, src=src, meta=meta, order=5)
