"""islands.py - slicer-like layer check: does every layer rest on the one below?

The fdm-print gates judge face angles and flat ceilings.  They cannot see material that starts in
mid-air between two sloped faces (a beak tip, a fin above the labium).  This check slices the mesh at
the print's layer height, rasters each layer and flags, with NO minimum-area filter:
  island     a connected piece of a layer that touches nothing in the layer below;
  hanging    new material farther than one line width from the layer below that is NOT held at
             both ends (a cantilevered strand or an unanchored patch).
Material farther than one line width that IS held from both sides is a bridge: allowed, and reported
with its span so a caller can hold it to a limit.
"""
from __future__ import annotations

import math

import numpy as np

PX_MM = 0.1            # raster pitch; a quarter of a 0.45 mm line.  0.2 mm lost: one-line features alias.
TOUCH_PX = 2           # a piece "touches" the layer below if it meets that layer dilated by 2 px (0.2 mm)
SUPPORT_MM = 0.05      # material within this of the layer below counts as resting on it
SURROUND_DEG = 185.0   # anchors are "both ends" when the largest angular gap between them is below this
                       # (the fdm-print pack's own rule for bridge versus cantilever)

_W = {}


def _raster(z):
    """Even-odd scanline raster of the slice at height z (rows = x, columns = y): every contour edge
    toggles the cells to its +x side in each raster column it crosses."""
    nx, ny = _W["shape"]
    polys = [np.asarray(p, float) for p in _W["man"].slice(float(z)).to_polygons()]
    polys = [p for p in polys if len(p) >= 3]
    if not polys:
        return np.zeros((nx, ny), bool)
    a = np.vstack(polys)
    b = np.vstack([np.roll(p, -1, axis=0) for p in polys])
    x0 = (a[:, 0] - _W["lo"][0]) / PX_MM; y0 = (a[:, 1] - _W["lo"][1]) / PX_MM - 0.5
    x1 = (b[:, 0] - _W["lo"][0]) / PX_MM; y1 = (b[:, 1] - _W["lo"][1]) / PX_MM - 0.5
    sw = y0 > y1
    x0, x1, y0, y1 = np.where(sw, x1, x0), np.where(sw, x0, x1), np.where(sw, y1, y0), np.where(sw, y0, y1)
    j0 = np.ceil(y0).astype(np.int64); j1 = np.ceil(y1).astype(np.int64)        # columns j with y0 <= j < y1
    cnt = np.maximum(j1 - j0, 0)
    idx = np.repeat(np.arange(len(a)), cnt)
    j = j0[idx] + (np.arange(int(cnt.sum())) - np.repeat(np.cumsum(cnt) - cnt, cnt))
    t = (j - y0[idx]) / np.maximum(y1[idx] - y0[idx], 1e-12)
    xi = np.ceil(x0[idx] + t * (x1[idx] - x0[idx]) - 0.5).astype(np.int64)
    ok = (j >= 0) & (j < ny)
    m = np.zeros((nx + 1, ny), np.int32)
    np.add.at(m, (np.clip(xi[ok], 0, nx), j[ok]), 1)
    return (np.cumsum(m, axis=0)[:nx] % 2).astype(bool)


def _work(ks):
    from scipy import ndimage
    st = ndimage.generate_binary_structure(2, 2)
    zs, lw, lo = _W["zs"], _W["line_w"], _W["lo"]
    out = []
    prev = _raster(zs[ks[0] - 1]) if ks[0] > 0 else None
    for k in ks:
        z = float(zs[k]); cur = _raster(z)
        rec = {"k": int(k), "area": float(cur.sum()) * PX_MM ** 2, "isl": [], "hang": [], "bridge": [], "far": 0.0}
        if prev is not None and cur.any():
            new = cur & ~prev
            if new.any():
                d = ndimage.distance_transform_edt(~prev) * PX_MM
                lab, n = ndimage.label(cur, structure=st)
                touched = np.unique(lab[ndimage.binary_dilation(prev, st, iterations=TOUCH_PX) & cur])
                objs = ndimage.find_objects(lab)
                for i in np.setdiff1d(np.arange(1, n + 1), touched):
                    sl = objs[i - 1]; mm = lab[sl] == i
                    cx, cy = ndimage.center_of_mass(mm)
                    rec["isl"].append({"z": round(z, 2), "mm2": round(float(mm.sum()) * PX_MM ** 2, 3),
                                       "at": [round(float((sl[0].start + cx) * PX_MM + lo[0]), 1), round(float((sl[1].start + cy) * PX_MM + lo[1]), 1)]})
                far = cur & (d > lw)
                rec["far"] = float(far.sum()) * PX_MM ** 2
                if far.any():
                    supp = cur & (d <= SUPPORT_MM)
                    lab2, _n2 = ndimage.label(far, structure=st)
                    for i, sl in enumerate(ndimage.find_objects(lab2), 1):
                        mm = lab2[sl] == i
                        dm = np.where(mm, d[sl], 0.0)
                        px, py = np.unravel_index(int(np.argmax(dm)), dm.shape)
                        reach = float(dm[px, py]); gx, gy = sl[0].start + px, sl[1].start + py
                        r = int((reach * 1.35 + 0.3) / PX_MM) + 1
                        x0, y0 = max(gx - r, 0), max(gy - r, 0)
                        sx, sy = np.nonzero(supp[x0:gx + r + 1, y0:gy + r + 1])
                        kind = "unanchored"
                        if len(sx):
                            vx, vy = sx + x0 - gx, sy + y0 - gy
                            keep = vx * vx + vy * vy <= r * r
                            if keep.any():
                                angs = np.sort(np.degrees(np.arctan2(vy[keep], vx[keep])))
                                gaps = np.append(np.diff(angs), angs[0] + 360.0 - angs[-1])
                                kind = "bridge" if gaps.max() <= SURROUND_DEG else "cantilever"
                        item = {"z": round(z, 2), "mm2": round(float(mm.sum()) * PX_MM ** 2, 3), "reach": round(reach, 2),
                                "at": [round(float(gx * PX_MM + lo[0]), 1), round(float(gy * PX_MM + lo[1]), 1)]}
                        if kind == "bridge":
                            item["span"] = round(2.0 * reach, 2); rec["bridge"].append(item)
                        else:
                            item["kind"] = kind; rec["hang"].append(item)
        out.append(rec); prev = cur
    return out


def layer_check(V, F, layer_h, line_w, procs=None):
    """Slice the mesh (vertices V, faces F; print pose, bed at the lowest z) every layer_h and test
    each layer against the one below.  Returns counts and lists of islands, hanging edges and bridges.
    Pass a mesh as (mesh.vertices, mesh.faces)."""
    import multiprocessing as mp
    from manifold3d import Manifold, Mesh
    V = np.asarray(V, float); F = np.asarray(F)
    z_min = float(V[:, 2].min())
    lo = V.min(0)[:2] - 1.0; hi = V.max(0)[:2] + 1.0
    _W.clear()
    _W.update(man=Manifold(Mesh(vert_properties=np.ascontiguousarray(V - [0, 0, z_min], np.float32),
                                tri_verts=np.ascontiguousarray(F, np.uint32))),
              lo=lo, line_w=float(line_w), zs=np.arange(0.5 * layer_h, float(V[:, 2].max()) - z_min, layer_h),
              shape=(int(math.ceil((hi[0] - lo[0]) / PX_MM)), int(math.ceil((hi[1] - lo[1]) / PX_MM))))
    n = len(_W["zs"])
    procs = procs or min(8, mp.cpu_count())
    chunks = [list(map(int, ch)) for ch in np.array_split(np.arange(n), max(procs * 4, 1)) if len(ch)]
    res = None
    if procs > 1:
        try:
            with mp.get_context("fork").Pool(procs) as pool:
                res = pool.map(_work, chunks)
        except Exception:                      # no fork here: do it in this process
            res = None
    if res is None:
        res = [_work(ch) for ch in chunks]
    rows = sorted((r for ch in res for r in ch), key=lambda r: r["k"])
    _W.clear()
    isl = [i for r in rows for i in r["isl"]]
    hang = [i for r in rows for i in r["hang"]]
    bridges = [i for r in rows for i in r["bridge"]]
    worst = sorted(bridges, key=lambda b: -b["span"])[:8]
    return {"layer_height_mm": float(layer_h), "line_width_mm": float(line_w), "raster_mm": PX_MM, "layers": n,
            "islands": len(isl), "hanging": len(hang), "island_list": isl[:40], "hanging_list": hang[:40],
            "bridges": len(bridges), "max_bridge_span_mm": max([b["span"] for b in bridges], default=0.0),
            "worst_bridges": worst, "far_area_mm2": round(float(sum(r["far"] for r in rows)), 2),
            "volume_from_layers_mm3": round(float(sum(r["area"] for r in rows)) * float(layer_h), 1)}
