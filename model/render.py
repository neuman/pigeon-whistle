"""render.py - a small numpy z-buffer renderer (orthographic, crease-aware smooth shading).

No GL, no matplotlib 3D: the mesh previews must render on a headless machine with only numpy,
scipy and Pillow.  render() draws triangles; render_section() cuts the solid with a plane first
(manifold3d caps the cut) and paints the cap.  Angles: azim is the camera's bearing round +Z from
+X (so azim = -90 looks from -Y: the bird's right side, head to the right), elev is its height.
"""
from __future__ import annotations

import time

import numpy as np
from PIL import Image
from scipy import ndimage


def _arrays(man):
    me = man.to_mesh()
    return np.asarray(me.vert_properties[:, :3], np.float64), np.asarray(me.tri_verts, np.int64)


def face_normals_areas(V, F):
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    a = np.linalg.norm(n, axis=1)
    return n / np.maximum(a, 1e-30)[:, None], 0.5 * a


def view_matrix(azim, elev):
    a, e = np.radians(azim), np.radians(elev)
    d = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])   # target -> camera
    right = np.cross([0, 0, 1.0], d); right /= np.linalg.norm(right)
    up = np.cross(d, right)
    return np.stack([right, up, d])


def corner_normals(V, F, crease_deg=35.0):
    """per-corner shading normals = area-weighted mean of the incident face normals that lie
    within crease_deg of the corner's own face (smoothing groups: organic skin shades smooth,
    CSG cuts stay crisp, no light bleeding across the crease)."""
    fn, a = face_normals_areas(V, F)
    wn = fn * a[:, None]
    corner_v = F.ravel()                                    # corner id = 3*face + k
    order = np.argsort(corner_v, kind="stable")
    sv = corner_v[order]; sf = order // 3
    start = np.concatenate([[0], np.nonzero(np.diff(sv))[0] + 1])
    deg = np.diff(np.concatenate([start, [len(sv)]]))
    deg_c = np.repeat(deg, deg); grp = np.repeat(start, deg)
    off = np.cumsum(deg_c) - deg_c
    i = np.repeat(np.arange(len(sv)), deg_c)
    j = np.repeat(grp, deg_c) + (np.arange(int(deg_c.sum())) - np.repeat(off, deg_c))
    fi, fj = sf[i], sf[j]
    keep = np.einsum("ij,ij->i", fn[fi], fn[fj]) > np.cos(np.radians(crease_deg))
    i, fj = i[keep], fj[keep]
    acc = np.stack([np.bincount(i, weights=wn[fj, k], minlength=len(sv)) for k in range(3)], axis=1)
    acc /= np.maximum(np.linalg.norm(acc, axis=1), 1e-30)[:, None]
    cn = np.empty((len(F) * 3, 3)); cn[order] = acc
    return fn, cn.reshape(len(F), 3, 3)


def render(V, F, path, azim=-60, elev=22, width=800, height=None, ssaa=2, face_rgb=None,
           base=(0.62, 0.66, 0.74), bg=(0.97, 0.97, 0.96), bounds=None, unlit=None):
    """Render triangles to a PNG (orthographic).  face_rgb: optional (m,3) per-face albedo;
    unlit: optional (m,) bool - faces drawn in flat colour (section caps); bounds: points that
    define the framing (default: the mesh itself).  Returns seconds taken."""
    t0 = time.perf_counter()
    V = np.asarray(V, np.float64); F = np.asarray(F, np.int64)
    R = view_matrix(azim, elev)
    fn, cn = corner_normals(V, F)
    Pc = V @ R.T                                            # camera space, +z toward viewer
    bV = Pc if bounds is None else (np.asarray(bounds, float) @ R.T)
    mn, mx = bV[:, :2].min(0), bV[:, :2].max(0)
    W = width * ssaa
    pad = 0.05 * W
    s = (W - 2 * pad) / (mx[0] - mn[0])
    Hh = int(np.ceil((mx[1] - mn[1]) * s + 2 * pad)) if height is None else height * ssaa
    Hh += Hh % ssaa
    sx = (Pc[:, 0] - mn[0]) * s + pad
    sy = Hh - ((Pc[:, 1] - mn[1]) * s + pad) - (Hh - 2 * pad - (mx[1] - mn[1]) * s) / 2
    sz = Pc[:, 2]
    keep = (fn @ R[2]) > 0                                  # back-face cull (closed solids)
    ids = np.nonzero(keep)[0]
    T = F[ids]
    ax, ay, bx, by, cx, cy = sx[T[:, 0]], sy[T[:, 0]], sx[T[:, 1]], sy[T[:, 1]], sx[T[:, 2]], sy[T[:, 2]]
    den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    ok = np.abs(den) > 1e-12
    x0 = np.clip(np.floor(np.minimum(np.minimum(ax, bx), cx)).astype(np.int64), 0, W - 1)
    x1 = np.clip(np.floor(np.maximum(np.maximum(ax, bx), cx)).astype(np.int64), 0, W - 1)
    y0 = np.clip(np.floor(np.minimum(np.minimum(ay, by), cy)).astype(np.int64), 0, Hh - 1)
    y1 = np.clip(np.floor(np.maximum(np.maximum(ay, by), cy)).astype(np.int64), 0, Hh - 1)
    size = np.maximum(x1 - x0, y1 - y0) + 1
    fr_pix, fr_z, fr_tri, fr_w0, fr_w1 = [], [], [], [], []

    def emit(sel, px, py):
        """barycentric test of pixel centres (px,py) against triangles sel."""
        qx = px + 0.5; qy = py + 0.5
        w0 = ((by[sel] - cy[sel]) * (qx - cx[sel]) + (cx[sel] - bx[sel]) * (qy - cy[sel])) / den[sel]
        w1 = ((cy[sel] - ay[sel]) * (qx - cx[sel]) + (ax[sel] - cx[sel]) * (qy - cy[sel])) / den[sel]
        w2 = 1.0 - w0 - w1
        ins = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not ins.any():
            return
        tsel = sel[ins] if sel.ndim == 1 else np.broadcast_to(sel, ins.shape)[ins]
        w0, w1, w2 = w0[ins], w1[ins], w2[ins]
        z = w0 * sz[T[tsel, 0]] + w1 * sz[T[tsel, 1]] + w2 * sz[T[tsel, 2]]
        fr_pix.append((py[ins] * W + px[ins]).astype(np.int64)); fr_z.append(z)
        fr_tri.append(tsel); fr_w0.append(w0); fr_w1.append(w1)

    lo = 0
    for hi in (2, 4, 8, 16, 32):                            # small triangles: batched by bbox size
        sel = np.nonzero(ok & (size > lo) & (size <= hi))[0]
        lo = hi
        if len(sel) == 0:
            continue
        for dy in range(hi):
            for dx in range(hi):
                m = (x0[sel] + dx <= x1[sel]) & (y0[sel] + dy <= y1[sel])
                if m.any():
                    emit(sel[m], x0[sel[m]] + dx, y0[sel[m]] + dy)
    for t in np.nonzero(ok & (size > 32))[0]:               # few big triangles: one by one
        gy, gx = np.mgrid[y0[t]:y1[t] + 1, x0[t]:x1[t] + 1]
        emit(np.full(gx.size, t), gx.ravel(), gy.ravel())

    img = np.empty((Hh, W, 3), np.float64)
    g = np.linspace(0, 1, Hh)[:, None, None]
    img[:] = np.asarray(bg) * (1 - 0.10 * g)
    depth = np.full(Hh * W, np.nan)
    if fr_pix:
        pix = np.concatenate(fr_pix); z = np.concatenate(fr_z); tri = np.concatenate(fr_tri)
        w0 = np.concatenate(fr_w0); w1 = np.concatenate(fr_w1)
        order = np.lexsort((-z, pix))
        first = order[np.concatenate([[True], pix[order][1:] != pix[order][:-1]])]
        pix, z, tri, w0, w1 = pix[first], z[first], tri[first], w0[first], w1[first]
        gt = ids[tri]                                        # global face index
        nrm = w0[:, None] * cn[gt, 0] + w1[:, None] * cn[gt, 1] + (1 - w0 - w1)[:, None] * cn[gt, 2]
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1), 1e-30)[:, None]
        nc = nrm @ R.T                                       # camera-space normal
        key = np.array([-0.45, 0.60, 0.66]); key /= np.linalg.norm(key)
        fill = np.array([0.70, -0.10, 0.55]); fill /= np.linalg.norm(fill)
        dif = 0.72 * np.clip(nc @ key, 0, 1) + 0.22 * np.clip(nc @ fill, 0, 1)
        hv = key + np.array([0, 0, 1.0]); hv /= np.linalg.norm(hv)
        spec = 0.18 * np.clip(nc @ hv, 0, 1) ** 40
        rim = 0.10 * (1 - np.clip(nc[:, 2], 0, 1)) ** 3
        alb = np.broadcast_to(np.asarray(base), (len(gt), 3)) if face_rgb is None else np.asarray(face_rgb)[gt]
        col = alb * (0.30 + dif)[:, None] + spec[:, None] - rim[:, None]
        flat = np.zeros(len(gt), bool) if unlit is None else np.asarray(unlit)[gt]
        depth[pix] = z
        # cheap screen-space occlusion: pixels lying behind their blurred neighbourhood get darker
        d2 = depth.reshape(Hh, W)
        mask = np.isfinite(d2)
        dfill = np.where(mask, d2, np.nanmin(z))
        sig = 6.0 * ssaa
        blur = ndimage.gaussian_filter(dfill * mask, sig) / np.maximum(ndimage.gaussian_filter(mask.astype(float), sig), 1e-6)
        occ = np.clip((blur - dfill) / 4.0, 0, 1)            # mm of "recess" -> 0..1
        col *= (1 - 0.55 * occ.ravel()[pix])[:, None]
        col[flat] = alb[flat]
        img.reshape(-1, 3)[pix] = np.clip(col, 0, 1)
    img = img.reshape(Hh // ssaa, ssaa, W // ssaa, ssaa, 3).mean(axis=(1, 3))
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(path)
    return time.perf_counter() - t0


def render_section(man, path, normal=(0, 1, 0), offset=0.0, azim=-90, elev=8, width=800,
                   cap_rgb=(0.86, 0.42, 0.33), **kw):
    """cut the solid with a plane (keeps the side the normal points to), paint the cap."""
    cut = man.trim_by_plane(normal, offset)
    V, F = _arrays(cut)
    fn, a = face_normals_areas(V, F)
    nn = np.asarray(normal, float); nn /= np.linalg.norm(nn)
    on_plane = (np.abs(V[F].mean(axis=1) @ nn - offset) < 1e-4) & (fn @ nn < -0.999)
    rgb = np.tile(np.asarray(kw.pop("base", (0.62, 0.66, 0.74))), (len(F), 1))
    rgb[on_plane] = cap_rgb
    Vb, _ = _arrays(man)
    t = render(V, F, path, azim=azim, elev=elev, width=width, face_rgb=rgb, bounds=Vb, unlit=on_plane, **kw)
    return t, float(a[on_plane].sum())
