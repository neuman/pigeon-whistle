"""geom.py - the pigeon whistle's geometry: ONE definition, used by everything.

Frame (the print pose IS the desk pose): X from the tail tip (x = 0, the mouthpiece) to the head,
+Y is the bird's LEFT (the window flank), Z up = build direction, bed at z = 0.  Units: mm, degrees.

What lives here
  layout(cfg)        every derived dimension, as plain floats (cheap, pure)
  skin_field(...)    the outer skin as a signed field (negative inside): smooth unions of primitives,
                     then a bottom-up self-support trim and the bed chamfer
  chamber_field(...) the chamber air: the skin primitives shrunk by the shell wall, a flat floor, a
                     planar gable roof at cfg.roof_angle_deg, and the rump lobe behind the window
  cutters            windway, window (haunched lintel, labium ramp notch), finger hole (undercut), vent,
                     dimple, eyes: convex half-space pieces, cylinders and one cone.  The SAME pieces are
                     trimmed into manifold3d solids for the mesh and sampled as fields for the solver.
  voxel_model(...)   rasters for the acoustic solver: booleans at voxel centres and, with cut_cells,
                     the open fraction of every voxel face and the chamber fraction of every voxel
  build_mesh(...)    marching-cubes skin and chamber + exact booleans -> a watertight print-pose mesh
  measure(...)       numbers read back off that mesh
  layer_check(...)   the slicer-like island / hanging-edge check (a project gate calls it)
  derive(cfg)        the fast numbers model/pigeon.py publishes from build()

`cad=True` means "as drawn for the printer" (holes and windway gap enlarged by the Config
compensations); `cad=False` means the acoustic nominal the solver should see.
"""
from __future__ import annotations

import hashlib
import math
import os
import sys
from collections import namedtuple
from types import SimpleNamespace

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:          # loaded by path (a gate, a test): the sibling modules must still import.
    sys.path.append(_HERE)         # Appended, never inserted: nothing here can shadow another module.
import islands  # noqa: E402

GEOM_VERSION = 2
"""Bump when this file changes the solid for an unchanged Config: it is hashed into geometry_hash."""

# ----------------------------------------------------------------------------------------------
# Styling and construction constants.  Inputs that a person would turn are Config fields; these
# are proportions and blends that only matter together (why-this-value on each line).
# ----------------------------------------------------------------------------------------------
BELLY_SKIRT = 0.64      # body and chest ellipsoids are extruded straight down below c_z - 0.64 r_z: the
                        # belly meets the skirt at asin(0.64) = 39.8 deg from vertical, just inside the 40 deg
                        # self-support trim (limit 45).  0.55 lost: a visible band round the breast.
CHEST_SKIRT = BELLY_SKIRT
CHEST_RADII = (0.56, 0.80, 0.72)   # chest radii as fractions of the body radii: a breast that leads the head
CHEST_DZ = 0.10         # chest centre above the body centre, in body r_z: keeps the breast under the head
K_BODY, K_TAIL, K_HEAD, K_BEAK, K_CERE, K_WING, K_FOOT = 6.0, 4.0, 5.0, 1.5, 1.2, 2.5, 1.2
"""Smooth-union radii (mm).  The chamber reuses K_BODY so its crease follows the skin's."""
TAIL_PLAN_R = 1.5       # plan corner radius of the tail tip.  5.0 left a feather-edge inlet rim (judge); 2.5
                        # still left 0.75 mm beside the inlet at x = 0.1 mm (measured); 1.5 leaves >= 1.5 mm
TAIL_TOP_R = 1.2        # top-edge radius of the tail: inlet roof rim = tail_top - 1.2 - windway top >= 1.5 mm
TAIL_TAPER_LEN = 22.0   # the tail narrows toward the tip over this length (mouth comfort)
LIP_STOP_RUN = 1.5      # the lip stop rises over this run (63 deg: a stop, not a ramp)
RUMP_REAR_SLOPE = 1.0   # dz/dx of the rump behind its crest (upward facing, free of print limits)
RUMP_RIDGE_ROUND = 3.5  # rounding length of the rump ridge; 0 would be the thinnest skin but a sharp roof
RUMP_SHOULDER_K = 7.0   # smooth-max radius between the rump flank and its roof
RIDGE_COVER = 2.4       # skin crest above the lobe ridge (vent chimney, >= shell wall at the rounded crest)
RIDGE_MARGIN = 0.3      # body roof ridge this far below the shrunk-skin top: no ceiling cap can survive
RIDGE_NODES = 9         # ridge chord nodes along the body: 10 mm chords sag 0.36 mm under the dome
HIP_START = 0.9         # the ridge ends where the dome's top profile reaches 0.9 x the roof slope; hips beyond
HIP_DROP = 0.8          # each hip plane passes this far below the ridge's end node, so the dome it leaves exposed
                        # starts well past the roof angle (a hip through the node left 44.9 deg facets at 0.5 mm voxels)
DIMPLE_COVER_MM = 2.05  # roof left under the finger dimple at the bore's rim on the ridge line (>= 2.0 shell)
WING_RADII = (0.72, 0.27, 0.46)    # wing ellipsoid radii as fractions of the body radii
WING_DX, WING_DY = -0.16, 0.66     # wing centre from the body centre, in body r_x / r_y
WING_YAW, WING_ROLL = 16.0, 16.0   # deg: tips converge over the rump, the wing leans onto the flank
BAR_AT = (-0.30, -0.52)            # the two wing bars: x behind the body centre, in body r_x
BAR_Z = 0.44                       # bar centre above the body centre, in body r_z: the upper flank, because at the
                                   # equator the body is already at the 68 mm width limit and a proud bar would break it
BAR_LEAN_DEG = 28.0                # bars lean back like a folded wing's coverts
BAR_SHOULDER = 1.0                 # the bar's relief fades over this margin (no end face to overhang)
CERE_R = (3.0, 3.8, 2.3)           # cere bump; 7.6 mm wide survives a 0.4 mm nozzle (judge)
BEAK_ROOT_DEG = -20.0              # the beak leaves the head this far below the head's equator
BIB_R = (8.0, 15.0, 11.0)          # puffed crop under the beak (a cooing pigeon inflates it): the surface the
                                   # beak tip rests in.  A 9 mm ball lost: it read as a goitre in the front view.
K_BIB = 7.0                        # wide blend so the crop is one mass with the breast
BEAK_BURY = 1.2                    # beak tip buried this deep in the bib (>= 1 mm, so no layer starts in air)
FOOT_AT_Y = 8.5                    # foot pad centres either side of the centre line
FOOT_BACK = 2.5                    # foot pad centre behind the chest skirt front
GROOVE_Y = (-6.5, 0.0, 6.5)        # three feather grooves on the rump's rear slope
GROOVE_W, GROOVE_D, GROOVE_LEN = 1.6, 0.5, 9.0   # V groove: 4 lines wide, 4 layers deep
BED_CHAMFER = (0.4, 0.7)           # elephant-foot chamfer, horizontal x vertical (30 deg from vertical)
LIP_BEVEL = (1.0, 1.4)             # lower-lip bevel under the tail tip (36 deg from vertical); leaves 1.6 mm under
                                   # the inlet.  1.2 x 1.4 (41 deg) lost: marching-cubes facets on it read 46-48 deg.
LIP_BEVEL_LEN = 12.0
HAUNCH_DEG = 43.0                  # window haunches and flare: corbel angle from vertical (spec)
LINTEL_FLAT_DEPTH = 1.5            # depth (into the wall) of the flat lintel strip before the roof flares up;
                                   # 3 strands, and the longest is 4.4 mm (the ramp recedes: deeper = longer)
WINDOW_REACH = 2.5                 # window cutters run this far past the flank
EXIT_OVERLAP = 0.05                # windway cutter runs this far into the window so no skin of plastic remains
SEAM_OVERLAP = 0.02                # cutters that share a face overlap by this (measured: exactly abutting
                                   # half-space solids did not always unite: the windway came out in 2 pieces)
CYL_SEGMENTS = 96                  # bores are equal-area 96-gons in the mesh, circles in the voxel model
EYE_TIP_R = 0.3                    # eye dimples are cones: every face of them is steeper than 45 deg
SIMPLIFY_TOL = 0.02                # manifold3d simplify tolerance (mm): every surface stays within it
CAP_MM = 0.02                      # triangles flatter than this (apex to opposite edge) get that edge flipped: same reason
NEEDLE_MM = 0.03                   # edges shorter than this are collapsed after simplify: needle triangles carry
                                   # random normals, and one facing down reads as an unanchored ceiling in fdm.bridge_span
BIG = 1.0e3


# ----------------------------------------------------------------------------------------------
# signed-distance primitives on broadcastable arrays (negative inside)
# ----------------------------------------------------------------------------------------------
def smin(a, b, k):
    """Polynomial smooth union with blend radius k (mm)."""
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * (k * 0.25)


def smax(a, b, k):
    return -smin(-a, -b, k)


def rot_zyx(yaw, pitch, roll):
    y, p, r = np.radians([yaw, pitch, roll])
    rz = np.array([[np.cos(y), -np.sin(y), 0], [np.sin(y), np.cos(y), 0], [0, 0, 1]])
    ry = np.array([[np.cos(p), 0, np.sin(p)], [0, 1, 0], [-np.sin(p), 0, np.cos(p)]])
    rx = np.array([[1, 0, 0], [0, np.cos(r), -np.sin(r)], [0, np.sin(r), np.cos(r)]])
    return rz @ ry @ rx


def _local(X, Y, Z, c, R):
    x, y, z = X - c[0], Y - c[1], Z - c[2]
    return (R[0, 0] * x + R[1, 0] * y + R[2, 0] * z, R[0, 1] * x + R[1, 1] * y + R[2, 1] * z,
            R[0, 2] * x + R[1, 2] * y + R[2, 2] * z)


def sd_ellipsoid(X, Y, Z, c, r, skirt=None, R=None):
    """Ellipsoid bound (exact on the surface, first-order distance near it).  skirt: below
    c_z - skirt*r_z the section is extruded straight down (a vertical skirt to the bed)."""
    if R is not None:
        x, y, z = _local(X, Y, Z, c, R)
    else:
        x, y, z = X - c[0], Y - c[1], Z - c[2]
    if skirt is not None:
        z = np.maximum(z, -skirt * r[2])
    k0 = np.sqrt((x / r[0]) ** 2 + (y / r[1]) ** 2 + (z / r[2]) ** 2)
    k1 = np.sqrt((x / r[0] ** 2) ** 2 + (y / r[1] ** 2) ** 2 + (z / r[2] ** 2) ** 2)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def sd_sphere(X, Y, Z, c, r):
    return np.sqrt((X - c[0]) ** 2 + (Y - c[1]) ** 2 + (Z - c[2]) ** 2) - r


def sd_round_cone(X, Y, Z, a, b, r1, r2):
    """Capsule from a (radius r1) to b (radius r2), radius linear in between."""
    a = np.asarray(a, float); b = np.asarray(b, float); ab = b - a
    t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / max(float(ab @ ab), 1e-9), 0.0, 1.0)
    d = np.sqrt((X - a[0] - t * ab[0]) ** 2 + (Y - a[1] - t * ab[1]) ** 2 + (Z - a[2] - t * ab[2]) ** 2)
    return d - (r1 + (r2 - r1) * t)


def _sstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _round_rect(qx, qy, r):
    return np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - r


# ----------------------------------------------------------------------------------------------
# half-space solids: one definition for the mesh (trimmed boxes) and for the rasters (tests)
# ----------------------------------------------------------------------------------------------
def _hs(rows):
    """rows of (ax, ay, az, b) meaning a.p <= b -> (A unit normals (m,3), b (m,))."""
    m = np.asarray(rows, float).reshape(-1, 4)
    n = np.maximum(np.linalg.norm(m[:, :3], axis=1), 1e-12)
    return m[:, :3] / n[:, None], m[:, 3] / n


def hs_field(H, X, Y, Z):
    """max_i(a_i.p - b_i): <= 0 inside the convex solid, the exact distance to the nearest face inside."""
    A, b = H
    f = None
    for (ax, ay, az), bi in zip(A, b):
        g = ax * X + ay * Y + az * Z - bi
        f = g if f is None else np.maximum(f, g)
    return f


def hs_manifold(H, bounds):
    """The convex solid as a manifold3d Manifold: a box (x0,y0,z0,x1,y1,z1) trimmed by every plane."""
    from manifold3d import Manifold
    x0, y0, z0, x1, y1, z1 = bounds
    man = Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))
    for a, b in zip(*H):
        man = man.trim_by_plane(tuple(-a), float(-b))
    return man


# ----------------------------------------------------------------------------------------------
# layout: every derived dimension
# ----------------------------------------------------------------------------------------------
def layout(c):
    """All derived placement numbers for a Config, as plain floats.  Pure; never raises on a
    +-10 % change of any one field (degenerate values are clipped, not refused)."""
    L = SimpleNamespace()
    a = math.radians(min(max(c.roof_angle_deg, 5.0), 80.0))
    L.roof_a, L.cot = a, 1.0 / math.tan(a)
    w = c.shell_wall_mm
    # ---- body group ----
    L.body_c = (c.body_center_x_mm, 0.0, c.body_center_z_mm)
    L.body_r = (c.body_radius_x_mm, c.body_radius_y_mm, c.body_radius_z_mm)
    L.chest_c = (c.body_center_x_mm + c.chest_lead_mm, 0.0, c.body_center_z_mm + CHEST_DZ * c.body_radius_z_mm)
    L.chest_r = tuple(f * r for f, r in zip(CHEST_RADII, L.body_r))
    L.body_ri = tuple(max(r - w, 1.0) for r in L.body_r)        # chamber: the same ellipsoids, shrunk by the wall
    L.chest_ri = tuple(max(r - w, 1.0) for r in L.chest_r)
    hw = c.tail_half_width_mm
    L.hw, L.hw_in = hw, max(hw - w, 1.0)
    L.x_tail_end = c.body_center_x_mm - 0.55 * c.body_radius_x_mm    # tail block and rump end hidden in the body
    L.x_lobe_end = c.body_center_x_mm - 0.62 * L.body_ri[0]          # lobe ends inside the shrunk body
    # ---- voicing frame: u along the jet, v outward (toward +Y), origin at the windway exit ----
    sg = math.radians(c.windway_skew_deg)
    L.sig, L.cs, L.sn = sg, math.cos(sg), math.sin(sg)
    L.v_in = c.labium_offset_mm - 0.5 * c.labium_tip_mm          # chamber-side face of the labium = window inner plane
    L.v_tip = L.v_in + c.labium_tip_mm
    cu = c.cutup_mm
    L.cu = cu
    L.Ex = c.windway_length_mm
    L.Ey = hw - c.window_wall_mm - 0.5 * cu * L.sn - L.v_in * L.cs   # window wall depth is set at mid cut-up
    L.z0 = c.windway_floor_z_mm
    L.z1 = L.z0 + c.windway_height_mm
    L.Th = math.tan(math.radians(HAUNCH_DEG))
    L.hr = max(0.0, 0.5 * (cu - c.lintel_flat_mm))               # haunch run each side
    L.zt = L.z1 + L.hr / L.Th                                    # lintel (flat bridge) height
    L.v_a = L.v_in + LINTEL_FLAT_DEPTH
    L.v_max = L.v_in + c.window_wall_mm + WINDOW_REACH
    L.tr = math.tan(math.radians(min(max(c.labium_ramp_deg, 5.0), 60.0)))
    L.u_far = cu + (L.v_max - L.v_tip) / L.tr + 1.0
    L.win_ceiling = L.zt + (L.v_max - L.v_a) / L.Th              # highest point of the window cutter
    L.ww_len = L.Ex / max(L.cs, 0.5)                             # slot length along its own axis
    # ---- lobe roof (level ridge on the centre line) and the eave it makes on the window wall ----
    L.lobe_ridge = c.lobe_ridge_z_mm
    y_in_lo = L.Ey + L.v_in * L.cs                               # world y of the inner plane at the exit
    y_in_hi = y_in_lo + (cu + 2.0) * L.sn
    L.eave_z = L.lobe_ridge - max(abs(y_in_lo), abs(y_in_hi)) * L.cot
    L.lobe_far_y = min(max(y_in_lo - c.lobe_width_mm, -L.hw_in), y_in_lo - 1.0)   # the lobe's wall away from the window
    # ---- head, beak, bib ----
    L.head_c = (c.head_center_x_mm, 0.0, c.head_center_z_mm)
    L.head_r = c.head_radius_mm
    rt = math.radians(BEAK_ROOT_DEG)
    reach = max(L.head_r - 0.45 * c.beak_base_radius_mm, 1.0)
    L.beak_a = (L.head_c[0] + reach * math.cos(rt), 0.0, L.head_c[2] + reach * math.sin(rt))
    bp = math.radians(c.beak_pitch_deg)
    L.beak_b = (L.beak_a[0] + c.beak_length_mm * math.cos(bp), 0.0, L.beak_a[2] - c.beak_length_mm * math.sin(bp))
    back = 0.6 * BIB_R[0]
    L.bib_c = (L.beak_b[0] - back, 0.0, L.beak_b[2] - c.beak_tip_radius_mm + BEAK_BURY - 0.8 * BIB_R[2])
    L.cere_c = (L.beak_a[0] + 0.6, 0.0, L.beak_a[2] + 0.9 * c.beak_base_radius_mm)
    # ---- wings, feet ----
    L.wing_r = tuple(f * r for f, r in zip(WING_RADII, L.body_r))
    L.wing_c = (c.body_center_x_mm + WING_DX * c.body_radius_x_mm, WING_DY * c.body_radius_y_mm, c.wing_center_z_mm)
    chest_front = L.chest_c[0] + L.chest_r[0] * math.sqrt(1.0 - CHEST_SKIRT ** 2)
    L.foot_c = (chest_front - FOOT_BACK, FOOT_AT_Y, 0.0)
    L.foot_r = (0.5 * c.foot_length_mm, 0.5 * c.foot_width_mm, c.foot_height_mm)
    # ---- rump skin crest over the lobe ----
    L.rump_crest = L.lobe_ridge + RIDGE_COVER
    L.lip_top = c.tail_top_z_mm + c.lip_stop_rise_mm
    # ---- finger dimple: a sphere sunk dimple_depth into the back, along the skin's own normal.  Sunk
    #      vertically it left 1.7 mm of roof on the uphill side of the hole (the back slopes at x = 70).
    L.hole_x, L.vent_x = c.hole_x_mm, c.vent_x_mm
    zt3 = skin_tops(c, L, [L.hole_x - 0.5, L.hole_x, L.hole_x + 0.5], [0.0], L.lip_top - 2.0, L.head_c[2] + L.head_r + 2.0)[:, 0]
    slope = float(zt3[2] - zt3[0])
    nn = math.hypot(slope, 1.0)
    L.dimple_r = max(c.dimple_radius_mm, 1.0)
    L.skin_at_hole = float(zt3[1])
    L.dimple_c = (L.hole_x - slope / nn * (L.dimple_r - c.dimple_depth_mm), 0.0,
                  L.skin_at_hole + (L.dimple_r - c.dimple_depth_mm) / nn)
    # ---- body roof: concave chord ridge under the shrunk dome, hip planes at both ends ----
    L.ridge_x, L.ridge_z = _ridge_nodes(c, L)
    L.roof_H = _roof_planes(L)
    L.hole_ridge = ridge_z_at(L, L.hole_x)
    L.hole_cone_z = L.skin_at_hole - c.dimple_depth_mm - c.hole_chimney_mm    # the bore widens downward below this
    L.vent_ridge = L.lobe_ridge
    return L


def _inner_top(L, x):
    """Top (y = 0) of the shrunk body and chest ellipsoids at station x; -inf outside both."""
    x = np.asarray(x, float)
    out = np.full(x.shape, -np.inf)
    for cc, r in ((L.body_c, L.body_ri), (L.chest_c, L.chest_ri)):
        u = 1.0 - ((x - cc[0]) / r[0]) ** 2
        out = np.maximum(out, np.where(u > 0, cc[2] + r[2] * np.sqrt(np.maximum(u, 0.0)), -np.inf))
    return out


def _ridge_nodes(c, L):
    """Nodes (x, z) of the body roof ridge: on the shrunk dome's back line less RIDGE_MARGIN, held one
    shell wall below the finger dimple, then lowered where needed so the ridge is concave (a concave
    ridge is what makes the roof an intersection of planes: no valley, no flat)."""
    lo = min(L.body_c[0] - L.body_ri[0], L.chest_c[0] - L.chest_ri[0])
    hi = max(L.body_c[0] + L.body_ri[0], L.chest_c[0] + L.chest_ri[0])
    xs = np.linspace(lo + 0.05, hi - 0.05, 801)
    p = _inner_top(L, xs)
    s = np.gradient(p, xs)
    it = int(np.argmax(p))
    lim = HIP_START * L.cot
    rear = np.nonzero(s[: it + 1] > lim)[0]
    front = np.nonzero(s[it:] < -lim)[0]
    ia = int(rear[-1]) + 1 if len(rear) else 0
    ib = it + int(front[0]) - 1 if len(front) else len(xs) - 1
    ia, ib = min(ia, it), max(ib, it)
    rim = 0.5 * (c.hole_d_mm + c.hole_comp_mm) + 0.2               # the bore's rim on the ridge line
    near = [x for x in (L.hole_x - rim, L.hole_x + rim) if xs[ia] < x < xs[ib]]
    nx = np.unique(np.concatenate([np.linspace(xs[ia], xs[ib], RIDGE_NODES), [xs[it]], near]))
    nz = np.interp(nx, xs, p) - RIDGE_MARGIN
    for x in near:                                                # dimple surface above the rim, less the cover
        dz2 = L.dimple_r ** 2 - (x - L.dimple_c[0]) ** 2
        if dz2 > 0:
            i = int(np.argmin(np.abs(nx - x)))
            nz[i] = min(nz[i], L.dimple_c[2] - math.sqrt(dz2) - DIMPLE_COVER_MM)
    k = int(np.argmax(nz))
    for i in range(k + 1, len(nx) - 1):          # forward of the crest: slopes may only fall (a concave ridge)
        s0 = (nz[i] - nz[i - 1]) / (nx[i] - nx[i - 1])
        nz[i + 1] = min(nz[i + 1], nz[i] + s0 * (nx[i + 1] - nx[i]))
    for i in range(k - 1, 0, -1):                # and rearward of it
        s0 = (nz[i] - nz[i + 1]) / (nx[i + 1] - nx[i])
        nz[i - 1] = min(nz[i - 1], nz[i] + s0 * (nx[i] - nx[i - 1]))
    return nx, nz


def _roof_planes(L):
    """Half-spaces of the body chamber roof: a gable pair per ridge chord (each plane leans exactly
    roof_angle from vertical whatever the chord's slope) and a hip plane at each end."""
    sa, ca = math.sin(L.roof_a), math.cos(L.roof_a)
    rows = []
    for i in range(len(L.ridge_x) - 1):
        s = (L.ridge_z[i + 1] - L.ridge_z[i]) / (L.ridge_x[i + 1] - L.ridge_x[i])
        s = float(np.clip(s, -0.95 * L.cot, 0.95 * L.cot))
        ny = math.sqrt(max(ca * ca - (s * sa) ** 2, 1e-9))
        for sy in (1.0, -1.0):
            n = (-s * sa, sy * ny, sa)
            rows.append((*n, n[0] * L.ridge_x[i] + n[2] * L.ridge_z[i]))
    rows.append((-ca, 0.0, sa, -ca * L.ridge_x[0] + sa * (L.ridge_z[0] - HIP_DROP)))        # rear hip
    rows.append((ca, 0.0, sa, ca * L.ridge_x[-1] + sa * (L.ridge_z[-1] - HIP_DROP)))        # front hip
    return _hs(rows)


def ridge_z_at(L, x):
    """Height of the body roof on the centre line at station x."""
    A, b = L.roof_H
    return float(np.min((b - A[:, 0] * x) / A[:, 2]))


def to_local(L, X, Y):
    """World (x, y) -> voicing frame (u along the jet from the exit, v outward)."""
    dx, dy = X - L.Ex, Y - L.Ey
    return dx * L.cs + dy * L.sn, -dx * L.sn + dy * L.cs


def _hs_local(L, rows):
    """Half-spaces written in the voicing frame (alpha u + beta v + gamma z <= delta) -> world."""
    out = []
    for al, be, ga, de in rows:
        ax, ay = al * L.cs - be * L.sn, al * L.sn + be * L.cs
        out.append((ax, ay, ga, de + ax * L.Ex + ay * L.Ey))
    return _hs(out)


# ----------------------------------------------------------------------------------------------
# skin
# ----------------------------------------------------------------------------------------------
class Grid:
    """Axis-aligned sample lattice.  Origins are deliberately off round numbers: a planar feature
    landing exactly on lattice nodes makes marching cubes drop triangles (geometry notes, pitfall 1)."""

    def __init__(self, lo, hi, h):
        n = [int(math.ceil((hi[i] - lo[i]) / h)) + 1 for i in range(3)]
        self._set([(lo[i] + h * np.arange(n[i])).astype(np.float32) for i in range(3)], h)

    @classmethod
    def from_axes(cls, x, y, z):
        """A lattice with arbitrary (sorted) axes, e.g. a few fine columns."""
        g = cls.__new__(cls)
        g._set([np.asarray(a, np.float32) for a in (x, y, z)], float(z[1] - z[0]) if len(z) > 1 else 1.0)
        return g

    def _set(self, axes, h):
        self.x, self.y, self.z = axes
        self.h = float(h)
        self.shape = tuple(len(a) for a in axes)

    def box(self, lo, hi):
        """(slices, X, Y, Z) of the sub-lattice covering [lo, hi] (clipped to the lattice)."""
        sl = []
        for ax, a, b in zip((self.x, self.y, self.z), lo, hi):
            i0 = int(np.searchsorted(ax, a, side="left"))
            sl.append(slice(max(i0 - 1, 0), min(int(np.searchsorted(ax, b, side="right")) + 1, len(ax))))
        return (tuple(sl), self.x[sl[0]][:, None, None], self.y[sl[1]][None, :, None], self.z[sl[2]][None, None, :])


def model_bounds(c, pad=0.0):
    """A box that surely contains the skin (not tight), widened by pad."""
    L = layout(c)
    x1 = max(L.chest_c[0] + L.chest_r[0], L.beak_b[0] + c.beak_tip_radius_mm, L.bib_c[0] + BIB_R[0],
             L.foot_c[0] + L.foot_r[0], L.head_c[0] + L.head_r, L.body_c[0] + L.body_r[0]) + 1.5
    yw = max(L.body_r[1], L.hw, L.wing_c[1] + L.wing_r[1] + 2.0, L.chest_r[1]) + 1.5
    z1 = max(L.head_c[2] + L.head_r, L.body_c[2] + L.body_r[2], L.rump_crest) + 1.5
    return np.array([-1.5 - pad, -yw - pad, -1.5 - pad]), np.array([x1 + pad, yw + pad, z1 + pad])


def _tail_block(c, L, X, Y, Z):
    hw = c.tail_tip_half_width_mm + (L.hw - c.tail_tip_half_width_mm) * _sstep(X / TAIL_TAPER_LEN)
    cx = 0.5 * L.x_tail_end
    d2 = _round_rect(np.abs(X - cx) - (cx - TAIL_PLAN_R), np.abs(Y) - (hw - TAIL_PLAN_R), TAIL_PLAN_R)
    top = c.tail_top_z_mm + c.lip_stop_rise_mm * _sstep((X - c.lip_stop_x_mm + LIP_STOP_RUN) / LIP_STOP_RUN)
    return _round_rect(d2 + TAIL_TOP_R, Z - (top - TAIL_TOP_R), TAIL_TOP_R)


def _rump(c, L, X, Y, Z):
    """Rounded gable over the lobe: flanks at the tail's half width, a roof parallel to the lobe roof,
    a crest RIDGE_COVER above the lobe ridge, falling to the lip stop behind."""
    sa, ca = math.sin(L.roof_a), math.cos(L.roof_a)
    rear = L.lip_top + (X - c.lip_stop_x_mm) * RUMP_REAR_SLOPE
    crest = smin(np.full_like(rear, L.rump_crest), rear, 4.0)
    apex = crest + RUMP_RIDGE_ROUND * L.cot                         # sharp apex; the rounding lowers it to `crest`
    roof = np.sqrt(Y * Y + RUMP_RIDGE_ROUND ** 2) * ca + (Z - apex) * sa
    f = smax(roof, np.abs(Y) - L.hw, RUMP_SHOULDER_K)
    return np.maximum(f, np.maximum(X - L.x_tail_end, c.lip_stop_x_mm - 2.0 - X))


def _wing(c, L, X, Y, Z, side):
    R = rot_zyx(side * WING_YAW, c.wing_pitch_deg, -side * WING_ROLL)
    cc = (L.wing_c[0], side * L.wing_c[1], L.wing_c[2])
    f = sd_ellipsoid(X, Y, Z, cc, L.wing_r, R=R)
    return f


def skin_raw(c, L, g):
    """The skin as designed, before the self-support trim: smooth unions on the lattice g.
    Each primitive is evaluated only in its own padded box (the field is BIG elsewhere)."""
    f = np.full(g.shape, BIG, np.float32)

    def add(fn, lo, hi, k, pad=3.0):
        s, X, Y, Z = g.box(np.asarray(lo, float) - pad - k, np.asarray(hi, float) + pad + k)
        if all(sl.stop > sl.start for sl in s):
            f[s] = smin(f[s], fn(X, Y, Z).astype(np.float32), k)

    def ell_box(cc, r, zlo=None):
        return ((cc[0] - r[0], cc[1] - r[1], cc[2] - r[2] if zlo is None else zlo),
                (cc[0] + r[0], cc[1] + r[1], cc[2] + r[2]))
    zb = float(g.z[0])
    add(lambda X, Y, Z: sd_ellipsoid(X, Y, Z, L.body_c, L.body_r, BELLY_SKIRT), *ell_box(L.body_c, L.body_r, zb), K_BODY)
    add(lambda X, Y, Z: sd_ellipsoid(X, Y, Z, L.chest_c, L.chest_r, CHEST_SKIRT), *ell_box(L.chest_c, L.chest_r, zb), K_BODY)
    add(lambda X, Y, Z: _tail_block(c, L, X, Y, Z), (0, -L.hw, zb), (L.x_tail_end, L.hw, L.lip_top), K_TAIL)
    add(lambda X, Y, Z: _rump(c, L, X, Y, Z), (c.lip_stop_x_mm - 2, -L.hw, zb),
        (L.x_tail_end, L.hw, L.rump_crest + 1), K_TAIL)
    hr = (L.head_r,) * 3
    add(lambda X, Y, Z: sd_sphere(X, Y, Z, L.head_c, L.head_r), *ell_box(L.head_c, hr), K_HEAD)
    add(lambda X, Y, Z: sd_ellipsoid(X, Y, Z, L.bib_c, BIB_R), *ell_box(L.bib_c, BIB_R), K_BIB)
    rb = max(c.beak_base_radius_mm, c.beak_tip_radius_mm)
    add(lambda X, Y, Z: sd_round_cone(X, Y, Z, L.beak_a, L.beak_b, c.beak_base_radius_mm, c.beak_tip_radius_mm),
        np.minimum(L.beak_a, L.beak_b) - rb, np.maximum(L.beak_a, L.beak_b) + rb, K_BEAK)
    add(lambda X, Y, Z: sd_ellipsoid(X, Y, Z, L.cere_c, CERE_R), *ell_box(L.cere_c, CERE_R), K_CERE)
    wr = max(L.wing_r)
    for side in (1.0, -1.0):
        cc = (L.wing_c[0], side * L.wing_c[1], L.wing_c[2])
        add(lambda X, Y, Z, s=side: _wing(c, L, X, Y, Z, s), (cc[0] - wr, cc[1] - 0.6 * wr, cc[2] - 0.7 * wr),
            (cc[0] + wr, cc[1] + 0.6 * wr, cc[2] + 0.7 * wr), K_WING)
        fc = (L.foot_c[0], side * L.foot_c[1], 0.0)
        add(lambda X, Y, Z, fc=fc: sd_ellipsoid(X, Y, Z, fc, L.foot_r, skirt=0.0), *ell_box(fc, L.foot_r, zb), K_FOOT)
    # feather grooves: a V-shaped displacement of the field on the rump's rear slope (forward of the lips)
    x0 = c.lip_stop_x_mm + 1.5
    s, X, Y, Z = g.box((x0, -L.hw, L.lip_top - 3.0), (x0 + GROOVE_LEN, L.hw, L.rump_crest + 2.0))
    win = _sstep((X - x0) / 1.5) * _sstep((x0 + GROOVE_LEN - X) / 1.5)
    for gy in GROOVE_Y:
        f[s] += (GROOVE_D * win * np.maximum(1.0 - np.abs(Y - gy) / (0.5 * GROOVE_W), 0.0)).astype(np.float32)
    # wing bars: a raised band on both flanks, as a displacement of the field inside a leaning footprint
    # drawn in the side (x, z) view.  Nothing but the two flanks lies in that window.
    lean = math.radians(BAR_LEAN_DEG)
    zc = L.body_c[2] + BAR_Z * L.body_r[2]
    half = 0.5 * c.wing_bar_length_mm + 2.0
    for at in BAR_AT:
        xc = L.body_c[0] + at * L.body_r[0]
        s, X, Y, Z = g.box((xc - half, -BIG, zc - half), (xc + half, BIG, zc + half))
        a_ = (X - xc) * math.cos(lean) + (Z - zc) * math.sin(lean)          # across the bar
        b_ = -(X - xc) * math.sin(lean) + (Z - zc) * math.cos(lean)         # along it
        d2 = _round_rect(np.abs(a_) - 0.5 * c.wing_bar_width_mm + 0.8, np.abs(b_) - 0.5 * c.wing_bar_length_mm + 0.8, 0.8)
        f[s] -= (c.wing_bar_proud_mm * _sstep(-d2 / BAR_SHOULDER) * (np.abs(Y) > 6.0)).astype(np.float32)
    return f


def self_support_trim(f, z, deg):
    """Bottom-up sweep: material in a layer is kept only if the layer below reaches within
    dz*tan(deg) of it.  It only removes material, so it cannot create an island."""
    dz = float(z[1] - z[0])
    t = dz * math.tan(math.radians(deg))
    k0 = int(np.searchsorted(z, 0.0))
    for k in range(max(k0, 0) + 1, f.shape[2]):
        np.maximum(f[:, :, k], f[:, :, k - 1] - t, out=f[:, :, k])
    return f


def bed_chamfer(f, g):
    """Elephant-foot chamfer round the whole footprint, widened to the lower-lip bevel under the tail tip."""
    X, Z = g.x[:, None, None], g.z[None, None, :]
    u = _sstep((LIP_BEVEL_LEN + 4.0 - X) / 4.0)
    ch = BED_CHAMFER[0] + (LIP_BEVEL[0] - BED_CHAMFER[0]) * u
    cv = BED_CHAMFER[1] + (LIP_BEVEL[1] - BED_CHAMFER[1]) * u
    f += (ch * np.maximum(1.0 - Z / cv, 0.0)).astype(np.float32)
    return f


def skin_field(c, g, L=None):
    """The printed skin on lattice g (negative inside); the bed plane itself is NOT applied here
    (the mesh trims it exactly; rasters take max(f, -z))."""
    L = L or layout(c)
    f = skin_raw(c, L, g)
    f = self_support_trim(f, g.z, c.self_support_deg)
    return bed_chamfer(f, g)


def skin_tops(c, L, xs, ys, z_lo, z_hi, dz=0.05):
    """Height of the top of the designed skin over each (x, y) of a small lattice: [len(xs), len(ys)]."""
    g = Grid.from_axes(xs, ys, np.arange(z_lo, z_hi, dz))
    f = skin_raw(c, L, g).astype(float)
    ins = f < 0
    k = np.clip(f.shape[2] - 1 - np.argmax(ins[:, :, ::-1], axis=2), 0, f.shape[2] - 2)
    f0 = np.take_along_axis(f, k[:, :, None], 2)[:, :, 0]
    f1 = np.take_along_axis(f, k[:, :, None] + 1, 2)[:, :, 0]
    t = np.where(f1 > f0, f0 / np.where(f1 > f0, f0 - f1, 1.0), 0.0)
    return np.where(ins.any(axis=2), g.z[k] + dz * np.clip(t, 0.0, 1.0), z_lo)


# ----------------------------------------------------------------------------------------------
# chamber
# ----------------------------------------------------------------------------------------------
def lobe_H(c, L):
    """The rump lobe: a gable-roofed box from the windway exit plane forward into the body, bounded
    on the window side by the labium's inner plane.  World half-spaces a.p <= b."""
    sa, ca = math.sin(L.roof_a), math.cos(L.roof_a)
    A1, b1 = _hs_local(L, [(-1, 0, 0, 0.0), (0, 1, 0, L.v_in)])     # u >= 0 ; v <= v_in
    A2, b2 = _hs([(0, 1, 0, L.hw_in), (0, -1, 0, -L.lobe_far_y), (1, 0, 0, L.x_lobe_end), (0, 0, -1, -c.floor_mm),
                  (0, ca, sa, sa * L.lobe_ridge), (0, -ca, sa, sa * L.lobe_ridge)])
    return np.vstack([A1, A2]), np.concatenate([b1, b2])


def body_blob(c, L, X, Y, Z):
    """Shrunk body and chest ellipsoids, smooth-united like the skin (no floor, no roof)."""
    return smin(sd_ellipsoid(X, Y, Z, L.body_c, L.body_ri), sd_ellipsoid(X, Y, Z, L.chest_c, L.chest_ri), K_BODY)


def chamber_bounds(c, L):
    lo = (L.Ex - 12.0 * abs(L.sn) - 1.0, -max(L.body_ri[1], L.chest_ri[1], L.hw_in) - 1.0, c.floor_mm - 1.0)
    hi = (max(L.body_c[0] + L.body_ri[0], L.chest_c[0] + L.chest_ri[0]) + 1.0, -lo[1],
          max(float(np.max(L.ridge_z)), L.lobe_ridge) + 1.0)
    return np.asarray(lo, float), np.asarray(hi, float)


def chamber_field(c, L, X, Y, Z):
    """Chamber air (negative inside): (body blob under its roof) U (lobe), above the floor."""
    body = np.maximum(body_blob(c, L, X, Y, Z), np.maximum(hs_field(L.roof_H, X, Y, Z), c.floor_mm - Z))
    return np.minimum(body, hs_field(lobe_H(c, L), X, Y, Z))


# ----------------------------------------------------------------------------------------------
# cutters
# ----------------------------------------------------------------------------------------------
def windway_pieces(c, L, cad):
    """Vertical slot, gap tapering from inlet to exit, 45 deg chamfers on both exit lips."""
    comp = c.windway_gap_comp_mm if cad else 0.0
    ge, gi = c.windway_gap_exit_mm + comp, c.windway_gap_inlet_mm + comp
    ch = min(c.windway_exit_chamfer_mm, 0.4 * L.ww_len)
    k = 0.5 * (gi - ge) / L.ww_len                       # half-gap growth per mm toward the inlet
    zz = [(0, 0, -1, -L.z0), (0, 0, 1, L.z1)]
    taper = [(-1, 0, 0, L.ww_len + 4.0), (1, 0, 0, -ch + SEAM_OVERLAP), (k, 1, 0, 0.5 * ge), (k, -1, 0, 0.5 * ge)] + zz
    flare = [(-1, 0, 0, ch), (1, 0, 0, EXIT_OVERLAP), (-1, 1, 0, 0.5 * ge + ch), (-1, -1, 0, 0.5 * ge + ch)] + zz
    return [_hs_local(L, taper), _hs_local(L, flare)]


def window_pieces(c, L):
    """(add, keep): the window air is U(add) - U(keep).
    add: the through-cut over the cut-up with a haunch from the windway face and a flat lintel strip
    LINTEL_FLAT_DEPTH deep, then (further out) a roof that flares up at HAUNCH_DEG.
    keep: the labium blade (flat tip, ramp) and, above the jet, the solid that corbels out of the blade
    at HAUNCH_DEG in every direction.  That single corbel is both the labium-side haunch and the roof
    of the ramp notch, so no strand above the window starts in mid-air (print-first's fin)."""
    T, cu = L.Th, L.cu
    base = [(-1, 0, 0, 0.0), (1, 0, 0, L.u_far), (0, 0, -1, -L.z0), (-1, 0, T, T * L.z1)]    # z <= z1 + u/T
    flat = base + [(0, -1, 0, -(L.v_in - SEAM_OVERLAP)), (0, 1, 0, L.v_a), (0, 0, 1, L.zt)]
    flare = base + [(0, -1, 0, -(L.v_a - SEAM_OVERLAP)), (0, 1, 0, L.v_max), (0, -1, T, T * L.zt - L.v_a)]      # z <= zt + (v-v_a)/T
    ra = math.atan(L.tr)
    n_ramp = (-math.sin(ra), math.cos(ra))               # outward normal of the ramp face, in (u, v)
    blade = [(-1, 0, 0, -cu), (1, 0, 0, L.u_far + 2.0), (0, -1, 0, -(L.v_in - 1.0)),
             (n_ramp[0], n_ramp[1], 0, n_ramp[0] * cu + n_ramp[1] * L.v_tip)]
    prism = blade + [(0, 0, 1, L.z1), (0, 0, -1, -(L.z0 - 1.0))]
    cone = [(0, 0, -1, -(L.z1 - SEAM_OVERLAP)), (1, 0, 0, L.u_far + 2.0), (0, -1, 0, -(L.v_in - 1.0))]   # starts inside the prism:
    # the two kept solids must overlap, not abut (abutting, they failed to unite at z1 = 9.3: the corbel's flat underside
    # was left in the mesh as a 42 mm^2 ceiling with 10 non-manifold edges)
    a0, a1 = math.pi, math.pi / 2 + ra                   # tip-face normal -> ramp normal, round the tip corner
    for t in np.linspace(0.0, 1.0, 7):
        ang = a0 + (a1 - a0) * t
        n = (math.cos(ang), math.sin(ang))
        cone.append((n[0], n[1], -T, n[0] * cu + n[1] * L.v_tip - T * L.z1))
    return [_hs_local(L, flat), _hs_local(L, flare)], [_hs_local(L, prism), _hs_local(L, cone)]


def _poly_r(d):
    """Radius of the regular CYL_SEGMENTS-gon whose area equals a circle of diameter d."""
    n = CYL_SEGMENTS
    return 0.5 * d * math.sqrt(2.0 * math.pi / (n * math.sin(2.0 * math.pi / n)))


Bore = namedtuple("Bore", "x y d z_lo z_hi z_cone tan")
"""A vertical bore: axis (x, y), diameter d from z_cone up to z_hi; below z_cone (down to z_lo, inside the
chamber) its radius grows by `tan` per mm of depth.  z_cone = z_lo means a plain cylinder."""


def bores(c, L, cad):
    """Finger hole and vent as Bore tuples, running from inside the chamber to above the skin.
    The finger hole is undercut: hole_chimney_mm below the dimple floor it opens downward at the roof
    angle, so its wall is that long all round instead of following the gable down the sides (a bore
    through a 42 deg gable is 2 mm long on the ridge line and 5.5 mm at the sides)."""
    comp = c.hole_comp_mm if cad else 0.0
    return {"hole": Bore(L.hole_x, 0.0, max(c.hole_d_mm + comp, 0.1), L.hole_ridge - 6.0, L.hole_ridge + 12.0,
                         min(max(L.hole_cone_z, L.hole_ridge - 6.0), L.hole_ridge + 12.0), math.tan(L.roof_a)),
            "vent": Bore(L.vent_x, 0.0, max(c.vent_d_mm + comp, 0.1), L.vent_ridge - 4.0, L.vent_ridge + 10.0,
                         L.vent_ridge - 4.0, 0.0)}


def bore_field(b, X, Y, Z):
    """Signed field of a Bore (negative inside; the distance to its wall near the wall)."""
    rho = np.sqrt((X - b.x) ** 2 + (Y - b.y) ** 2) - 0.5 * b.d
    if b.z_cone > b.z_lo:
        cs = 1.0 / math.hypot(1.0, b.tan)
        rho = np.minimum(rho, rho * cs - (b.z_cone - Z) * (b.tan * cs))     # cylinder U the cone's half-space
    return np.maximum(rho, b.z_lo - Z)


def bore_reach(b):
    """Largest radius of the bore (at its bottom)."""
    return 0.5 * b.d + (b.z_cone - b.z_lo) * b.tan


def dimple_sphere(c, L):
    """Finger dimple: (centre, radius, skin height at the hole)."""
    return L.dimple_c, L.dimple_r, L.skin_at_hole


def eye_cones(c, L):
    """Side-set eye dimples as cones: (apex point, unit axis pointing out of the head) per side."""
    az, el = math.radians(c.eye_azimuth_deg), math.radians(c.eye_elevation_deg)
    out = []
    for s in (1.0, -1.0):
        n = np.array([math.cos(el) * math.cos(az), s * math.cos(el) * math.sin(az), math.sin(el)])
        out.append((np.asarray(L.head_c) + n * (L.head_r - c.eye_depth_mm), n))
    return out


def _eye_field(c, L, X, Y, Z):
    """< 0 inside either eye cone (radius EYE_TIP_R at the apex, eye_radius at the head surface)."""
    f = None
    k = (c.eye_radius_mm - EYE_TIP_R) / max(c.eye_depth_mm, 0.05)
    for apex, n in eye_cones(c, L):
        x, y, z = X - apex[0], Y - apex[1], Z - apex[2]
        t = x * n[0] + y * n[1] + z * n[2]
        rad = np.sqrt(np.maximum(x * x + y * y + z * z - t * t, 0.0))
        g = np.maximum(rad - (EYE_TIP_R + k * t), -t)
        f = g if f is None else np.minimum(f, g)
    return f


# ----------------------------------------------------------------------------------------------
# voxel model (the acoustic solver's input)
# ----------------------------------------------------------------------------------------------
def _raster_fields(cfg, L, g, hole_open, vent_open, cad):
    """Signed fields (negative inside, in mm near the surface) on any lattice g, each evaluated only in
    its own box and BIG elsewhere: skin (bed plane, finger dimple and eyes applied), chamber, windway,
    window, hole, vent.  A closed bore is absent (BIG everywhere)."""
    X, Y, Z = g.x[:, None, None], g.y[None, :, None], g.z[None, None, :]
    f = skin_field(cfg, g, L)
    np.maximum(f, -Z, out=f)                                           # bed plane
    (dc, dr, _zs) = dimple_sphere(cfg, L)
    s, Xs, Ys, Zs = g.box(np.subtract(dc, dr), np.add(dc, dr))
    f[s] = np.maximum(f[s], -sd_sphere(Xs, Ys, Zs, dc, dr))
    s, Xs, Ys, Zs = g.box(np.subtract(L.head_c, L.head_r + 1), np.add(L.head_c, L.head_r + 1))
    f[s] = np.maximum(f[s], -_eye_field(cfg, L, Xs, Ys, Zs))
    out = {"skin": f}
    for name in ("chamber", "windway", "window", "hole", "vent"):
        out[name] = np.full(g.shape, BIG, np.float32)
    s, Xs, Ys, Zs = g.box(*chamber_bounds(cfg, L))
    out["chamber"][s] = chamber_field(cfg, L, Xs, Ys, Zs)
    # passages: everything near the voicing lives in one box
    vb = ((-5.0, L.Ey - 6.0 - 35.0 * abs(L.sn), L.z0 - 1.0), (L.Ex + L.u_far + 4.0, L.hw + WINDOW_REACH + 3.0, L.win_ceiling + 1.0))
    s, Xs, Ys, Zs = g.box(*vb)

    def union(pieces):
        u = None
        for H in pieces:
            q = hs_field(H, Xs, Ys, Zs)
            u = q if u is None else np.minimum(u, q)
        return u
    out["windway"][s] = union(windway_pieces(cfg, L, cad))
    add, keep = window_pieces(cfg, L)
    out["window"][s] = np.maximum(union(add), -union(keep))
    for name, is_open in (("hole", hole_open), ("vent", vent_open)):
        if is_open:
            b = bores(cfg, L, cad)[name]
            r = bore_reach(b) + 2.0
            s, Xs, Ys, Zs = g.box((b.x - r, b.y - r, b.z_lo), (b.x + r, b.y + r, b.z_hi))
            out[name][s] = bore_field(b, Xs, Ys, Zs)
    return out


def voxel_model(cfg, h, *, hole_open=True, vent_open=True, pad=0.0, cad=False, cut_cells=False):
    """Rasters at voxel centres, pitch h, for acoustics.solve_resonance.  Keys: origin (LOW CORNER of
    voxel [0,0,0]: the centre of voxel [i,j,k] is origin + (i+.5, j+.5, k+.5) h), h, and booleans
    solid (plastic), chamber (air up to the inner mouths of the openings), window / hole / vent /
    windway (air in each passage through the wall; a closed opening is solid), skin (inside the outer
    skin, for the caller's own checks).  cad=False rasterises the acoustic nominal sizes.

    cut_cells=True adds what a boolean raster cannot hold (it only knows a surface to one voxel):
      aperture      three float32 arrays [nx, ny, nz]: aperture[a][i,j,k] is the open (air) fraction of
                    the face between voxel [i,j,k] and its neighbour one step up axis a, from the same
                    fields sampled at the face centres (_face_fraction).  The windway counts as plastic
                    here: the player's mouth closes it.
      chamber_fill  float32 [nx, ny, nz]: the fraction of each voxel that is chamber air, the same
                    partial-volume rule as build()'s chamber_volume_mm3."""
    L = layout(cfg)
    lo, hi = model_bounds(cfg, pad)
    g = Grid(lo + 0.5 * h, hi, h)
    F = _raster_fields(cfg, L, g, hole_open, vent_open, cad)
    skin = F["skin"] < 0
    chamber = (F["chamber"] < 0) & skin
    free = skin & ~chamber
    out = {"origin": tuple(float(a[0]) - 0.5 * h for a in (g.x, g.y, g.z)), "h": float(h), "skin": skin, "chamber": chamber}
    out["windway"] = (F["windway"] < 0) & free
    out["window"] = (F["window"] < 0) & free & ~out["windway"]
    out["hole"] = (F["hole"] < 0) & free
    out["vent"] = (F["vent"] < 0) & free
    out["solid"] = free & ~out["windway"] & ~out["window"] & ~out["hole"] & ~out["vent"]
    if cut_cells:
        out["chamber_fill"] = _pv(F["chamber"], h).astype(np.float32)
        del F
        half = np.float32(0.5 * h)
        ap = []
        for axis in range(3):
            ax = [g.x, g.y, g.z]
            ax[axis] = ax[axis] + half                                 # the lattice of this axis's face centres
            Ff = _raster_fields(cfg, L, Grid.from_axes(*ax), hole_open, vent_open, cad)
            # open = outside the skin, or inside an air region.  The regions abut (window on chamber) or
            # overlap (bores run into the chamber), so their fractions are summed and clipped: the min() of
            # two abutting fields is ~0 on their common face and would read as a half-closed wall.
            opening = 1.0 - _face_fraction(Ff["skin"], h, axis)
            for name in ("chamber", "window", "hole", "vent"):
                opening += _face_fraction(Ff[name], h, axis)
            ap.append(np.clip(opening, 0.0, 1.0, out=opening))
            del Ff
        out["aperture"] = tuple(ap)
    return out


def _face_fraction(F, h, axis):
    """Fraction of each square lattice face (normal to `axis`, side h, centred on F's lattice points)
    that lies inside the region F < 0.  Near the surface the region is taken as the half-space through
    the face centre given by F's value and gradient there, and the area that plane cuts off the square
    is exact: a wall parallel to the face switches it open or shut, a wall across it opens it in
    proportion.  (clip(0.5 - F/h) alone would leave faces INSIDE a wall thinner than 2 h half open.)"""
    out = (F < 0).astype(np.float32)
    band = np.nonzero(np.abs(F) < h)                                   # |distance| < h/sqrt(2) is all that can be cut
    if len(band[0]) == 0:
        return out
    f0 = F[band].astype(np.float64)
    grad = []
    for b in range(3):
        up = list(band); dn = list(band)
        up[b] = np.minimum(band[b] + 1, F.shape[b] - 1)
        dn[b] = np.maximum(band[b] - 1, 0)
        fu, fd = F[tuple(up)].astype(np.float64), F[tuple(dn)].astype(np.float64)
        ok_u, ok_d = (fu < 0.5 * BIG) & (up[b] != band[b]), (fd < 0.5 * BIG) & (dn[b] != band[b])
        fu, fd = np.where(ok_u, fu, f0), np.where(ok_d, fd, f0)         # one-sided at the edge of a field's box
        grad.append((fu - fd) / (h * np.maximum(ok_u.astype(float) + ok_d, 1.0)))
    norm = np.maximum(np.sqrt(grad[0] ** 2 + grad[1] ** 2 + grad[2] ** 2), 1e-6)
    d_in = -f0 / norm                                                  # distance of the face centre inside the region
    b, c = [k for k in range(3) if k != axis]
    p_, q_ = np.abs(grad[b]) / norm * h, np.abs(grad[c]) / norm * h    # the plane's rise across the face, each way
    big, small = np.maximum(p_, q_), np.minimum(p_, q_)
    reach = 0.5 * (big + small)
    corner = np.maximum(reach - np.abs(d_in), 0.0) ** 2 / np.maximum(2.0 * big * small, 1e-12)
    frac = np.where(np.abs(d_in) <= 0.5 * (big - small), 0.5 - np.abs(d_in) / np.maximum(big, 1e-12), corner)
    frac = np.where(np.abs(d_in) >= reach, 0.0, frac)                  # frac: the SMALLER side's share
    out[band] = np.where(d_in > 0, 1.0 - frac, frac)
    return out


# ----------------------------------------------------------------------------------------------
# fast derived numbers for build()
# ----------------------------------------------------------------------------------------------
layer_check = islands.layer_check


def _pv(f, h):
    """Partial-volume weight of each cell from a signed field (exact for a plane through the cell)."""
    return np.clip(0.5 - f / h, 0.0, 1.0)


CHAMBER_H = 0.8
"""Lattice pitch of build()'s chamber-volume integral.  Measured against the 0.35 mm mesh: see derive()."""
SKIN_H = 1.25
"""Lattice pitch of build()'s plastic-volume integral (a mass estimate; +-0.5 % is plenty)."""


def geometry_hash(cfg, fields):
    """sha256 over the geometry-defining fields (name=value at 1e-9) and GEOM_VERSION, 12 hex."""
    txt = ";".join("%s=%s" % (k, repr(round(float(getattr(cfg, k)), 9))) for k in sorted(fields))
    return hashlib.sha256(("v%d;" % GEOM_VERSION + txt).encode()).hexdigest()[:12]


def derive(c):
    """Every geometric number build() publishes, from coarse lattices and closed forms (no mesh).
    chamber_volume_mm3 is a partial-volume integral of chamber_field at CHAMBER_H."""
    L = layout(c)
    d = {}
    # ---- chamber volume, extents ----
    lo, hi = chamber_bounds(c, L)
    g = Grid(lo + 0.137, hi + CHAMBER_H, CHAMBER_H)
    X, Y, Z = g.x[:, None, None], g.y[None, :, None], g.z[None, None, :]
    w = _pv(chamber_field(c, L, X, Y, Z), CHAMBER_H)
    d["chamber_volume_mm3"] = float(w.sum() * CHAMBER_H ** 3)
    x_lo = float(L.Ex + 0.5 * (L.hw_in + L.Ey) * L.sn / max(L.cs, 0.5))        # middle of the (skewed) exit face
    x_hi = float(max(L.body_c[0] + L.body_ri[0], L.chest_c[0] + L.chest_ri[0]))
    d["cavity_length_mm"] = x_hi - x_lo
    # ---- window ----
    d["window_cutup_mm"] = float(L.cu)
    d["window_height_mm"] = float(L.z1 - L.z0)
    d["window_area_mm2"] = float(L.cu * (L.z1 - L.z0))
    uu, zz = np.meshgrid(np.arange(0.01, L.cu, 0.02), np.arange(L.z0 + 0.01, max(L.zt, L.z1) + 0.02, 0.02), indexing="ij")
    ap = (zz < L.z1 + uu / L.Th) & (zz < L.z1 + (L.cu - uu) / L.Th) & (zz < L.zt) & (zz < L.eave_z)
    d["window_aperture_mm2"] = float(ap.sum() * 0.02 * 0.02)
    xm, ym = L.Ex + 0.5 * L.cu * L.cs, L.Ey + 0.5 * L.cu * L.sn          # jet axis at mid cut-up
    d["window_depth_mm"] = float((L.hw - ym) / max(L.cs, 0.5) - L.v_in)   # inner plane -> flank, along v
    d["window_pos_frac"] = float(np.clip((xm - x_lo) / max(x_hi - x_lo, 1e-6), 0.0, 1.0))
    d["window_sill_z_mm"] = float(L.z0)
    d["lip_to_window_mm"] = float(L.Ex - c.lip_stop_x_mm)
    d["lobe_eave_clearance_mm"] = float(L.eave_z - L.zt)
    # ---- lobe cross-section beside the jet: the plane across the jet at mid cut-up ----
    vv, zz = np.meshgrid(np.arange(-2.5 * L.hw, L.v_in, 0.1) + 0.05, np.arange(0.0, L.lobe_ridge + 2.0, 0.1) + 0.05, indexing="ij")
    Xp, Yp = xm - vv * L.sn, ym + vv * L.cs
    d["lobe_area_mm2"] = float((chamber_field(c, L, Xp, Yp, zz) < 0).sum() * 0.01)
    d["lobe_to_window_ratio"] = d["lobe_area_mm2"] / max(d["window_area_mm2"], 1e-9)
    # ---- bores: acoustic area and mean chimney (skin or dimple down to the roof), over the bore disc ----
    dc, dr, _zs = dimple_sphere(c, L)
    for name, ridge in (("hole", L.hole_ridge), ("vent", L.vent_ridge)):
        bore = bores(c, L, False)[name]
        bx, by, dia = bore.x, bore.y, bore.d
        d[name + "_area_mm2"] = float(0.25 * math.pi * dia * dia)
        off = (np.arange(13) - 6) * (0.5 * dia / 6.25)
        zs = np.arange(ridge - 6.0, ridge + 12.0, 0.05)
        px, py = bx + off, by + off
        col = chamber_field(c, L, px[:, None, None], py[None, :, None], zs[None, None, :]) < 0
        z_in = zs[np.maximum(col.shape[2] - 1 - np.argmax(col[:, :, ::-1], axis=2), 0)] + 0.025
        z_out = skin_tops(c, L, px, py, ridge - 2.0, ridge + 12.0)
        r2 = off[:, None] ** 2 + off[None, :] ** 2
        if name == "hole":
            z_out = np.minimum(z_out, dc[2] - np.sqrt(np.maximum(dr * dr - r2, 0.0)))
        disc = r2 <= 0.25 * dia * dia
        d[name + "_depth_mm"] = float(np.maximum(z_out - np.maximum(z_in, bore.z_cone), 0.0)[disc].mean())
    # ---- skin: plastic volume, extents, surface area, solid shell versus sparse core ----
    slo, shi = model_bounds(c)
    gs = Grid(slo + 0.071, shi + SKIN_H, SKIN_H)
    fs = skin_field(c, gs, L)
    Zs = gs.z[None, None, :]
    above = np.clip(0.5 + Zs / SKIN_H, 0.0, 1.0)
    v_skin = float((_pv(fs, SKIN_H) * above).sum() * SKIN_H ** 3)
    d["overall_length_mm"], d["overall_width_mm"], d["overall_height_mm"] = _extents(c, L, gs, fs)
    gap = 0.5 * (c.windway_gap_exit_mm + c.windway_gap_inlet_mm) + c.windway_gap_comp_mm
    v_pass = (gap * (L.z1 - L.z0) * L.ww_len                                  # windway
              + d["window_aperture_mm2"] * d["window_depth_mm"] * 1.3        # window + ramp notch
              + sum(_bore_plastic(c, L, b) for b in bores(c, L, True).values()))
    d["plastic_volume_mm3"] = v_skin - d["chamber_volume_mm3"] - v_pass
    fa = np.full(gs.shape, BIG, np.float32)
    s, Xa, Ya, Za = gs.box(lo, hi)
    fa[s] = chamber_field(c, L, Xa, Ya, Za)
    solid = np.maximum(np.maximum(fs, -fa), -Zs)                             # plastic, with the bed as a surface
    t_shell = c.perimeters * c.extrusion_width_mm
    core = float((_pv(solid + t_shell, SKIN_H)).sum()) / max(float(_pv(solid, SKIN_H).sum()), 1e-9)
    d["core_volume_mm3"] = core * d["plastic_volume_mm3"]                    # deeper than the perimeters: sparse infill
    d["shell_volume_mm3"] = d["plastic_volume_mm3"] - d["core_volume_mm3"]
    d["mass_g"] = c.filament_density_g_cm3 * 1e-3 * (d["shell_volume_mm3"] + c.infill_fraction * d["core_volume_mm3"])
    eps = 1.5 * SKIN_H                                                       # smeared-delta surface integral

    def area(f, wgt):
        dl = np.where(np.abs(f) < eps, (1.0 + np.cos(np.pi * f / eps)) / (2.0 * eps), 0.0)
        return float((dl * wgt).sum() * SKIN_H ** 3)
    k0 = int(np.searchsorted(gs.z, 0.0))
    bed_patch = float(_pv(fs[:, :, k0], SKIN_H).sum() * SKIN_H ** 2)
    d["surface_area_mm2"] = area(fs, above) + area(fa, 1.0) + bed_patch + 2.0 * (L.z1 - L.z0) * L.ww_len
    d["shell_wall_min_mm"] = float(min(c.shell_wall_mm, c.floor_mm))
    return d, L


def _bore_plastic(c, L, b, h=0.3):
    """Plastic a bore removes (mm^3): the part of it between the chamber and the skin, on a small lattice."""
    r = bore_reach(b) + h
    g = Grid((b.x - r + 0.011, b.y - r + 0.013, b.z_lo + 0.017), (b.x + r, b.y + r, b.z_hi), h)
    X, Y, Z = g.x[:, None, None], g.y[None, :, None], g.z[None, None, :]
    skin = skin_raw(c, L, g)
    dc, dr, _zs = dimple_sphere(c, L)
    skin = np.maximum(skin, -sd_sphere(X, Y, Z, dc, dr))
    w = _pv(bore_field(b, X, Y, Z), h) * _pv(skin, h) * (1.0 - _pv(chamber_field(c, L, X, Y, Z), h))
    return float(w.sum() * h ** 3)


def _extents(c, L, g, f):
    """Overall length, width, height of the skin: zero crossings of the coarse field, refined on a
    fine local lattice round each extreme (the beak tip is a 1.5 mm ball)."""
    ins = f < 0
    out = []
    for axis in range(3):
        other = tuple(j for j in range(3) if j != axis)
        ax = (g.x, g.y, g.z)[axis]
        occ = np.nonzero(ins.any(axis=other))[0]
        if len(occ) == 0:
            out.append(0.0); continue
        ends = []
        for idx, sign in ((occ[-1], 1.0), (occ[0], -1.0)):
            if axis == 2 and sign < 0:
                ends.append(0.0); continue                                   # the bed
            sl = [slice(None)] * 3; sl[axis] = idx
            j = np.unravel_index(int(np.argmin(f[tuple(sl)])), f[tuple(sl)].shape)
            p = [0.0, 0.0, 0.0]; p[axis] = float(ax[idx])
            for o, jj in zip(other, j):
                p[o] = float((g.x, g.y, g.z)[o][jj])
            h2 = 0.125
            lo = np.array(p) - 1.5 * g.h; hi = np.array(p) + 1.5 * g.h
            lo[2] = max(lo[2], 0.3)
            g2 = Grid(lo + 0.013, hi, h2)
            f2 = skin_raw(c, L, g2)
            a2 = (g2.x, g2.y, g2.z)[axis]
            m = f2.min(axis=other)
            ii = np.nonzero(m < 0)[0]
            if len(ii) == 0:
                ends.append(float(ax[idx])); continue
            k = int(ii[-1] if sign > 0 else ii[0]); kn = int(np.clip(k + (1 if sign > 0 else -1), 0, len(a2) - 1))
            t = m[k] / (m[k] - m[kn]) if m[kn] > m[k] else 0.0
            ends.append(float(a2[k] + sign * h2 * t))
        out.append(ends[0] - ends[1])
    return out


# ----------------------------------------------------------------------------------------------
# mesh: marching-cubes skin and chamber, exact booleans for everything dimensional
# ----------------------------------------------------------------------------------------------
def _mc_manifold(f, origin, h):
    """Zero level set of a lattice field -> closed manifold3d solid (outward normals)."""
    from manifold3d import Manifold, Mesh, Error
    from skimage import measure
    v, tri, _, _ = measure.marching_cubes(f, level=0.0, spacing=(h, h, h), allow_degenerate=False)
    v = np.ascontiguousarray(v + np.asarray(origin, np.float32), np.float32)
    tri = np.ascontiguousarray(tri, np.uint32)
    man = Manifold(Mesh(vert_properties=v, tri_verts=tri))
    if man.status() != Error.NoError:
        raise RuntimeError("marching-cubes surface is not a closed 2-manifold: %s" % man.status())
    if man.volume() < 0:
        man = Manifold(Mesh(vert_properties=v, tri_verts=np.ascontiguousarray(tri[:, ::-1])))
    return man


def _arrays(man):
    me = man.to_mesh()
    return np.asarray(me.vert_properties[:, :3], np.float64), np.asarray(me.tri_verts, np.int64)


def _as_manifold(V, F):
    from manifold3d import Manifold, Mesh, Error
    man = Manifold(Mesh(vert_properties=np.ascontiguousarray(V, np.float32), tri_verts=np.ascontiguousarray(F, np.uint32)))
    if man.status() != Error.NoError:
        raise RuntimeError("not an oriented closed 2-manifold: %s" % man.status())
    return man


def _bore_manifold(b, grow=0.0):
    """A Bore as a manifold3d solid (equal-area polygons), its radius grown by `grow`."""
    from manifold3d import Manifold
    r = _poly_r(b.d + 2.0 * grow)
    man = Manifold.cylinder(b.z_hi - b.z_lo, r, r, CYL_SEGMENTS).translate((b.x, b.y, b.z_lo))
    if b.z_cone > b.z_lo:
        cone = Manifold.cylinder(b.z_cone - b.z_lo, r + (b.z_cone - b.z_lo) * b.tan, r, CYL_SEGMENTS)
        man = man + cone.translate((b.x, b.y, b.z_lo))
    return man


def _eye_manifolds(c, L):
    from manifold3d import Manifold
    out = []
    length = c.eye_depth_mm + 2.0
    k = (c.eye_radius_mm - EYE_TIP_R) / max(c.eye_depth_mm, 0.05)
    for apex, n in eye_cones(c, L):
        cone = Manifold.cylinder(length, EYE_TIP_R, EYE_TIP_R + k * length, 48)
        ry = math.degrees(math.acos(float(np.clip(n[2], -1, 1)))); rz = math.degrees(math.atan2(n[1], n[0]))
        out.append(cone.rotate((0, ry, 0)).rotate((0, 0, rz)).translate(tuple(apex)))
    return out


_PARTS = {}


def build_parts(cfg, voxel=0.35, cad=True):
    """Every solid of the build, before simplification: skin (bed-trimmed, with dimple and eyes),
    chamber (the cavity-fill solid), windway, window, hole, vent, air (their union), whistle."""
    key = (repr(cfg), float(voxel), bool(cad), GEOM_VERSION)
    if key in _PARTS:
        return _PARTS[key]
    from manifold3d import Manifold, OpType
    L = layout(cfg)
    h = float(voxel)
    lo, hi = model_bounds(cfg)
    g = Grid(lo - 2.0 * h + 0.0137, hi + 2.0 * h, h)
    f = skin_field(cfg, g, L)
    np.maximum(f, -g.z[None, None, :] - 1.0, out=f)            # close the surface below the bed, inside the lattice
    f[0], f[-1], f[:, 0], f[:, -1], f[:, :, -1] = BIG, BIG, BIG, BIG, BIG
    skin0 = _mc_manifold(f, (g.x[0], g.y[0], g.z[0]), h).trim_by_plane((0.0, 0.0, 1.0), 0.0)   # exact bed plane
    dc, dr, _zs = dimple_sphere(cfg, L)
    dents = [Manifold.sphere(dr, 256).translate(tuple(dc))] + _eye_manifolds(cfg, L)
    skin = skin0 - Manifold.batch_boolean(dents, OpType.Add)
    # chamber: shrunk-ellipsoid blob by marching cubes, floor and roof planes exact, lobe exact
    blo, bhi = chamber_bounds(cfg, L)
    blo = np.minimum(blo, (min(L.body_c[0] - L.body_ri[0], L.chest_c[0] - L.chest_ri[0]), blo[1],
                           min(L.body_c[2] - L.body_ri[2], L.chest_c[2] - L.chest_ri[2])))
    bhi = np.maximum(bhi, (bhi[0], bhi[1], max(L.body_c[2] + L.body_ri[2], L.chest_c[2] + L.chest_ri[2])))
    gb = Grid(blo - 3.0 * h + 0.0171, bhi + 3.0 * h, h)
    fb = body_blob(cfg, L, gb.x[:, None, None], gb.y[None, :, None], gb.z[None, None, :]).astype(np.float32)
    A, b = L.roof_H
    Hb = (np.vstack([A, [[0.0, 0.0, -1.0]]]), np.concatenate([b, [-cfg.floor_mm]]))
    body = _mc_manifold(fb, (gb.x[0], gb.y[0], gb.z[0]), h)
    for a_, b_ in zip(*Hb):
        body = body.trim_by_plane(tuple(-a_), float(-b_))
    big = (lo[0] - 10, lo[1] - 10, lo[2] - 10, hi[0] + 10, hi[1] + 10, hi[2] + 10)
    chamber = body + hs_manifold(lobe_H(cfg, L), big)
    windway = Manifold.batch_boolean([hs_manifold(H, big) for H in windway_pieces(cfg, L, cad)], OpType.Add)
    add, keep = window_pieces(cfg, L)
    window = (Manifold.batch_boolean([hs_manifold(H, big) for H in add], OpType.Add)
              - Manifold.batch_boolean([hs_manifold(H, big) for H in keep], OpType.Add))
    bb = bores(cfg, L, cad)
    hole, vent = _bore_manifold(bb["hole"]), _bore_manifold(bb["vent"])
    air = Manifold.batch_boolean([chamber, windway, window, hole, vent], OpType.Add)
    whistle = skin - air
    whistle.num_tri()                                          # manifold3d is lazy: evaluate here
    P = dict(L=L, voxel=h, skin=skin, chamber=chamber, windway=windway, window=window, hole=hole, vent=vent,
             air=air, whistle=whistle)
    _PARTS.clear()                                             # one build cached: the solids are large
    _PARTS[key] = P
    return P


PLUG_GROW = 0.06
"""measure() closes the openings with the cutters grown by this much, so the 0.02 mm simplification of
the final mesh cannot leave a hairline leak between plug and wall."""


def passage_plug(cfg, L, grow):
    """Windway + window + bores as one solid, every cutter grown by `grow` (mm)."""
    from manifold3d import Manifold, OpType
    lo, hi = model_bounds(cfg, 10.0)
    big = (*lo, *hi)

    def gman(H, dg):
        return hs_manifold((H[0], H[1] + dg), big)
    add, keep = window_pieces(cfg, L)
    parts = [gman(H, grow) for H in windway_pieces(cfg, L, True)]
    parts.append(Manifold.batch_boolean([gman(H, grow) for H in add], OpType.Add)
                 - Manifold.batch_boolean([gman(H, -grow) for H in keep], OpType.Add))
    for b in bores(cfg, L, True).values():
        parts.append(_bore_manifold(b, grow))
    return Manifold.batch_boolean(parts, OpType.Add)


def clean_slivers(V, F, short=1e-3, alt_min=2e-3, max_pass=20):
    """Remove sliver triangles WITHOUT opening the surface: collapse edges shorter than `short`,
    flip the longest edge of caps (triangles whose apex lies within alt_min of the opposite edge).  Where a cutter crosses the marching-cubes skin
    manifold3d leaves a few ~1e-5 mm edges; the cad-solid STL loader welds at 1e-4 mm and counts
    every weld or dropped face as a defect (geometry notes, section 9)."""
    V = np.asarray(V, np.float64).copy(); F = np.asarray(F, np.int64).copy()
    nv = len(V)

    def areas():
        return 0.5 * np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)
    for _ in range(max_pass):
        changed = False
        el = np.linalg.norm(V[F[:, [1, 2, 0]]] - V[F], axis=2)
        fi, kk = np.nonzero(el < short)
        if len(fi):
            parent = np.arange(nv)

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]; x = parent[x]
                return x
            for f_, k in zip(fi, kk):
                a, b = find(F[f_, k]), find(F[f_, (k + 1) % 3])
                if a != b:
                    parent[max(a, b)] = min(a, b)
            used = np.unique(F)
            remap = np.arange(nv); remap[used] = [find(i) for i in used]
            F = remap[F]
            F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
            changed = True
        el = np.linalg.norm(V[F[:, [1, 2, 0]]] - V[F], axis=2)
        caps = np.nonzero(2.0 * areas() < alt_min * el.max(axis=1))[0]
        if len(caps):
            dkey = np.concatenate([F[:, k] * nv + F[:, (k + 1) % 3] for k in range(3)])
            dface = np.tile(np.arange(len(F)), 3); dk = np.repeat(np.arange(3), len(F))
            order = np.argsort(dkey); dkey_s = dkey[order]
            touched = set()
            for f_ in caps:
                if f_ in touched or el[f_].min() < short:
                    continue
                k = int(np.argmax(el[f_])); a, b, cc = F[f_, k], F[f_, (k + 1) % 3], F[f_, (k + 2) % 3]
                pos = np.searchsorted(dkey_s, b * nv + a)
                if pos >= len(dkey_s) or dkey_s[pos] != b * nv + a:
                    continue
                g_ = int(dface[order[pos]]); gk = int(dk[order[pos]])
                if g_ in touched:
                    continue
                dd = F[g_, (gk + 2) % 3]
                F[f_] = (a, dd, cc); F[g_] = (dd, b, cc)
                touched.update((int(f_), g_)); changed = True
        if not changed:
            break
    used = np.unique(F); remap = np.full(nv, -1, np.int64); remap[used] = np.arange(len(used))
    return V[used], remap[F]


def drop_ceiling_slivers(V, F, max_area=0.1, rounds=8):
    """Collapse the shortest edge of every isolated sliver that faces down past 80 deg.
    Such a facet (0.02 mm^2 where a roof plane crosses the marching-cubes dome) has a noise normal,
    yet fdm.bridge_span counts it as a ceiling region and fails the part if it finds no anchor."""
    import trimesh
    for _ in range(rounds):
        ang, area, _n = face_angles(V, F)
        bed = (V[F][:, :, 2].max(axis=1) - V[:, 2].min()) <= BED_TOL
        ceil = (ang >= OVERHANG_CEILING_DEG) & ~bed
        adj = trimesh.Trimesh(V, F, process=False).face_adjacency
        has_ceiling_nbr = np.zeros(len(F), bool)
        both = ceil[adj[:, 0]] & ceil[adj[:, 1]]
        has_ceiling_nbr[adj[both].ravel()] = True
        bad = np.nonzero(ceil & (area < max_area) & ~has_ceiling_nbr)[0]
        if len(bad) == 0:
            break
        done = False
        for f_ in bad:
            el = np.linalg.norm(V[F[f_][[1, 2, 0]]] - V[F[f_]], axis=1)
            k = int(np.argmin(el))
            a, b = int(F[f_, k]), int(F[f_, (k + 1) % 3])
            F2 = np.where(F == max(a, b), min(a, b), F)
            F2 = F2[(F2[:, 0] != F2[:, 1]) & (F2[:, 1] != F2[:, 2]) & (F2[:, 0] != F2[:, 2])]
            try:
                _as_manifold(V, F2)
            except RuntimeError:
                continue
            F = F2; done = True
            break                                               # indices moved: look again
        if not done:
            break
    used = np.unique(F); remap = np.full(len(V), -1, np.int64); remap[used] = np.arange(len(used))
    return V[used], remap[F]


def stl_precheck(V, F, weld_digits=4, zero_area=1e-8):
    """What the cad-solid STL loader will see: float32 triangle soup welded at 1e-4 mm, then open /
    non-manifold edge counts, is_volume, and the welds or dropped faces a further cleanup would need."""
    import trimesh
    V32 = np.asarray(V, np.float32).astype(np.float64)
    soup = trimesh.Trimesh(V32[F].reshape(-1, 3), np.arange(len(F) * 3).reshape(-1, 3), process=False)
    soup.merge_vertices(digits_vertex=weld_digits)
    e = np.sort(np.vstack([soup.faces[:, [0, 1]], soup.faces[:, [1, 2]], soup.faces[:, [2, 0]]]), axis=1)
    _, cnt = np.unique(e, axis=0, return_counts=True)
    work = soup.copy(); welded = dropped = 0
    for _ in range(8):
        before = len(work.vertices); work.merge_vertices(digits_vertex=weld_digits)
        w_ = before - len(work.vertices)
        keep = np.asarray(work.area_faces) > zero_area; d_ = int((~keep).sum())
        if d_:
            work.update_faces(keep); work.remove_unreferenced_vertices()
        welded += w_; dropped += d_
        if w_ == 0 and d_ == 0:
            break
    return {"open_edges": int((cnt == 1).sum()), "nonmanifold_edges": int((cnt > 2).sum()),
            "is_volume": bool(soup.is_volume), "extra_welds": int(welded), "dropped_faces": int(dropped)}


def expected_genus():
    """Independent through-openings of the shell: mouth inlet, window, finger hole, vent -> genus 3."""
    return 3


def build_mesh(cfg, voxel=0.35):
    """The printable solid in PRINT pose as a trimesh.Trimesh (watertight, bed at z = 0).
    Skin and chamber dome come from marching cubes at `voxel`; bed, floor, roof planes, lobe, windway,
    window, labium, lintel, bores, dimple and eyes are exact manifold3d booleans (CAD-compensated sizes)."""
    import trimesh
    P = build_parts(cfg, voxel, cad=True)
    V0, F0 = _arrays(P["whistle"].simplify(SIMPLIFY_TOL))
    try:
        man = _as_manifold(*clean_slivers(V0, F0, short=NEEDLE_MM, alt_min=CAP_MM))
    except RuntimeError:                                       # a collapse pinched the surface: weld only what the
        man = _as_manifold(*clean_slivers(V0, F0))             # STL loader would weld (raises if THAT breaks it)
    V, F = drop_ceiling_slivers(*_arrays(man))
    man = _as_manifold(V, F)
    V, F = _arrays(man)
    mesh = trimesh.Trimesh(vertices=V, faces=F, process=False)
    mesh.metadata.update(voxel=float(voxel), genus=int(man.genus()), stl_precheck=stl_precheck(V, F))
    return mesh


# ----------------------------------------------------------------------------------------------
# measurement off the mesh
# ----------------------------------------------------------------------------------------------
OVERHANG_CEILING_DEG = 80.0     # the pack's own split: steeper than the limit and below this = overhang, above = ceiling
BED_TOL = 0.05                  # the pack's bed-face tolerance (mm above the lowest point)


def face_angles(V, F):
    """(angle, area, normal) per face; angle = asin(-n_z): 0 vertical wall, 90 flat ceiling (pack convention)."""
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    a2 = np.linalg.norm(n, axis=1)
    n = n / np.maximum(a2, 1e-30)[:, None]
    return np.degrees(np.arcsin(np.clip(-n[:, 2], -1, 1))), 0.5 * a2, n


def classify_faces(cfg, V, F, L=None):
    """0 skin, 1 chamber, 2 voicing (windway, window, bores, dimple, eyes) per face, by which
    defining surface the face centroid lies on."""
    L = L or layout(cfg)
    C = V[F].mean(axis=1)
    X, Y, Z = C[:, 0], C[:, 1], C[:, 2]
    tol = 0.12
    cls = np.zeros(len(F), np.int8)
    cls[np.abs(chamber_field(cfg, L, X, Y, Z)) < tol] = 1
    near = np.zeros(len(F), bool)
    for H in windway_pieces(cfg, L, True):
        near |= np.abs(hs_field(H, X, Y, Z)) < tol
    add, keep = window_pieces(cfg, L)
    inside_any = np.minimum(hs_field(add[0], X, Y, Z), hs_field(add[1], X, Y, Z)) < tol
    for H in add + keep:
        near |= (np.abs(hs_field(H, X, Y, Z)) < tol) & inside_any
    u, v = to_local(L, X, Y)
    near &= ~((v < L.v_in - tol) & (u > 0.3))                    # the lobe wall behind the labium is chamber
    for b in bores(cfg, L, True).values():
        near |= (np.abs(bore_field(b, X, Y, Z)) < tol) & (Z > b.z_lo + tol)
    dc, dr, _zs = dimple_sphere(cfg, L)
    near |= np.abs(sd_sphere(X, Y, Z, dc, dr)) < 0.05
    near |= np.abs(_eye_field(cfg, L, X, Y, Z)) < 0.05
    cls[near] = 2
    return cls


def overhang_report(V, F, cls, limit_deg):
    """Pack convention: area of non-bed faces with limit < angle < 80 deg over the TOTAL area."""
    ang, area, _n = face_angles(V, F)
    bed = (V[F][:, :, 2].max(axis=1) - V[:, 2].min()) <= BED_TOL
    past = (ang > limit_deg) & (ang < OVERHANG_CEILING_DEG) & ~bed
    tot = float(area.sum())
    out = {"total_area_mm2": round(tot, 1), "past_mm2": round(float(area[past].sum()), 3),
           "frac": float(area[past].sum() / tot), "worst_deg": round(float(ang[past].max()), 2) if past.any() else 0.0}
    for i, nm in enumerate(("skin", "chamber", "voicing")):
        m = cls == i
        nb = m & ~bed & (ang < OVERHANG_CEILING_DEG) & (area > 1e-9)
        out[nm] = {"area_mm2": round(float(area[m].sum()), 1), "past_mm2": round(float(area[m & past].sum()), 3),
                   "frac_of_total": float(area[m & past].sum() / tot),
                   "steepest_non_ceiling_deg": round(float(ang[nb].max()), 2) if nb.any() else 0.0,
                   "ceiling_mm2": round(float(area[m & (ang >= OVERHANG_CEILING_DEG) & ~bed].sum()), 3)}
    return out, ang, area, bed


def ceiling_regions(V, F, cls, ang, area, bed):
    """Edge-connected groups of faces at >= 80 deg (the pack's 'ceilings'): where, how big, whose."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    sel = np.nonzero((ang >= OVERHANG_CEILING_DEG) & ~bed)[0]
    if len(sel) == 0:
        return []
    loc = -np.ones(len(F), np.int64); loc[sel] = np.arange(len(sel))
    e = np.sort(np.vstack([F[sel][:, [0, 1]], F[sel][:, [1, 2]], F[sel][:, [2, 0]]]), axis=1)
    owner = np.tile(np.arange(len(sel)), 3)
    order = np.lexsort((e[:, 1], e[:, 0])); e = e[order]; owner = owner[order]
    same = np.all(e[1:] == e[:-1], axis=1)
    gph = coo_matrix((np.ones(int(same.sum())), (owner[:-1][same], owner[1:][same])), shape=(len(sel), len(sel)))
    ncomp, lab = connected_components(gph, directed=False)
    out = []
    for i in range(ncomp):
        fs = sel[lab == i]
        pts = V[np.unique(F[fs])]
        ext = pts.max(0) - pts.min(0)
        out.append({"mm2": round(float(area[fs].sum()), 3), "z": round(float(pts[:, 2].mean()), 2),
                    "at": [round(float(t), 1) for t in pts.mean(0)], "extent_xy": [round(float(ext[0]), 2), round(float(ext[1]), 2)],
                    "class": ("skin", "chamber", "voicing")[int(np.bincount(cls[fs], minlength=3).argmax())]})
    return sorted(out, key=lambda r: -r["mm2"])


def measure(cfg, mesh, layers=True):
    """Numbers read off the built mesh (print pose).  Rebuilds the pre-cut solids for the Config at
    the mesh's voxel size (cached) to close the openings and to measure the shell wall before the cuts."""
    from scipy.spatial import cKDTree, ConvexHull
    from manifold3d import Manifold, OpType
    voxel = float(mesh.metadata.get("voxel", 0.35))
    P = build_parts(cfg, voxel, cad=True)
    L = P["L"]
    V, F = np.asarray(mesh.vertices, float), np.asarray(mesh.faces, np.int64)
    man = _as_manifold(V, F)
    M = {"voxel_mm": voxel, "triangles": int(len(F)), "watertight": bool(mesh.is_watertight),
         "winding_consistent": bool(mesh.is_winding_consistent), "genus": int(man.genus()),
         "genus_expected": expected_genus(), "solid_pieces": len(man.decompose()),
         "stl_precheck": stl_precheck(V, F)}
    lo, hi = V.min(0), V.max(0)
    M["bbox_min_mm"] = [round(float(t), 3) for t in lo]; M["bbox_max_mm"] = [round(float(t), 3) for t in hi]
    M["bbox_mm"] = [round(float(t), 3) for t in hi - lo]
    M["plastic_volume_mm3"] = round(float(man.volume()), 1)
    M["surface_area_mm2"] = round(float(man.surface_area()), 1)
    # chamber air: fill every passage (cutters minus the cavity-fill solid) and read the one void that is left
    closed = man + (passage_plug(cfg, L, PLUG_GROW) - P["chamber"])
    Vc, Fc = _arrays(closed)
    import trimesh
    comps = trimesh.Trimesh(Vc, Fc, process=False).split(only_watertight=False)
    vols = sorted(float(m_.volume) for m_ in comps)
    M["closed_shell_surfaces"] = len(comps)
    M["chamber_volume_mm3"] = round(-vols[0], 1) if len(vols) >= 2 and vols[0] < 0 else 0.0
    M["chamber_fill_solid_mm3"] = round(float(P["chamber"].volume()), 1)
    M["chamber_pieces"] = len(P["chamber"].decompose())
    # window aperture: the passage plug sliced just outside the labium's inner plane
    wplug = (P["window"] - P["chamber"]).translate((-L.Ex, -L.Ey, 0.0)).rotate((0.0, 0.0, -math.degrees(L.sig)))
    M["window_aperture_mm2"] = round(float(wplug.rotate((-90.0, 0.0, 0.0)).slice(L.v_in + 0.02).area()), 3)   # y -> z
    # shell wall before the voicing cuts: true distance chamber surface -> skin (or the bed)
    Vs, _Fs = _arrays(P["skin"])
    Vch, _Fch = _arrays(P["chamber"].refine_to_length(0.6))
    dist, _ = cKDTree(Vs).query(Vch, workers=-1)
    dist = np.minimum(dist, Vch[:, 2])                                 # the bed face has no vertices of its own
    for b in bores(cfg, L, True).values():                             # the bores themselves are not wall
        dist[bore_field(b, Vch[:, 0], Vch[:, 1], Vch[:, 2]) < 0.0] = np.inf
    M["shell_wall_min_above_floor_mm"] = round(float(dist[Vch[:, 2] > cfg.floor_mm + 0.05].min()), 3)
    j = int(np.argmin(dist))
    M["shell_wall_min_mm"] = round(float(dist[j]), 3)
    M["shell_wall_min_at"] = [round(float(t), 1) for t in Vch[j]]
    M["shell_wall_p01_mm"] = round(float(np.percentile(dist, 1)), 3)
    M["floor_mm"] = round(float(Vch[:, 2].min()), 3)
    # overhang, ceilings
    cls = classify_faces(cfg, V, F, L)
    ov, ang, area, bed = overhang_report(V, F, cls, cfg.overhang_limit_deg)
    M["overhang"] = ov
    regs = ceiling_regions(V, F, cls, ang, area, bed)
    M["ceiling_regions"] = regs[:12]
    M["ceiling_regions_n"] = len(regs)
    M["chamber_ceiling_mm2"] = ov["chamber"]["ceiling_mm2"]
    # bed patch, centre of mass, tipping
    down = bed & (ang > 89.0)
    M["bed_patch_mm2"] = round(float(area[down].sum()), 1)
    pts = V[np.unique(F[down])][:, :2]
    com = np.asarray(mesh.center_mass, float)
    M["center_of_mass_mm"] = [round(float(t), 2) for t in com]
    if len(pts) >= 3:
        hull = ConvexHull(pts)
        margin = float(-(hull.equations[:, :2] @ com[:2] + hull.equations[:, 2]).max())
        M["bed_patch_extent_mm"] = [round(float(np.ptp(pts[:, 0])), 1), round(float(np.ptp(pts[:, 1])), 1)]
        M["com_to_patch_edge_mm"] = round(margin, 2)
        M["tipping_angle_deg"] = round(math.degrees(math.atan2(margin, com[2])), 1)
    if layers:
        M["layers"] = layer_check(V, F, cfg.layer_height_mm, cfg.extrusion_width_mm)
    return M
