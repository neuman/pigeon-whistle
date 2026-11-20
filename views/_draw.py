"""Still pictures of the print mesh: cut-away sections and the labelled inside view.

Used by views/sections.py (image views, through ctx.write_asset) and by the box builders under
site/boxes/.  Everything is drawn by model/render.py (a numpy z-buffer renderer) and Pillow, from the
print mesh alone: same mesh, same bytes.  The leading underscore keeps the view loader off this file.
"""
from __future__ import annotations

import io
import math
import os

import numpy as np

CUT_RGB = (0.86, 0.42, 0.33)
SHELL_RGB = (0.62, 0.66, 0.74)
INK = (38, 42, 52)
BREATH = (26, 107, 219)
PAPER = (247, 247, 245)


class _Png(io.BytesIO):
    """A buffer Pillow saves a PNG into (it reads the format from the name)."""
    name = "picture.png"


def cuts(geom, cfg):
    """The three section planes: name -> (normal, offset, camera azimuth, camera elevation).
    The kept side is the one the normal points to; the camera looks at the cut face."""
    L = geom.layout(cfg)
    jet = L.Ey * L.cs - L.Ex * L.sn                       # the jet plane is -sin x + cos y = jet
    return {
        "side": ((0.0, 1.0, 0.0), 0.0, -90.0, 0.0),
        "jet": ((L.sn, -L.cs, 0.0), -jet, 90.0 + math.degrees(L.sig), 0.0),
        "plan": ((0.0, 0.0, -1.0), -0.5 * (L.z0 + L.z1), -90.0, 89.9),
    }


_DRAWN = {}


def section_png(render, geom, V, F, normal, offset, azim, elev, width=1200, ssaa=2):
    """PNG bytes of the solid cut by a plane, the cut face in CUT_RGB.  Returns (bytes, cut area mm^2).
    One build draws the same cut for a view and for the labelled picture: the second call is served
    from memory (keyed by the mesh's own numbers, so another mesh is another picture)."""
    key = (V.shape, F.shape, float(V.sum()), float(np.abs(V).sum()), tuple(normal), float(offset),
           float(azim), float(elev), int(width), int(ssaa))
    if key not in _DRAWN:
        man = geom._as_manifold(V, F)
        buf = _Png()
        _seconds, area = render.render_section(man, buf, normal=normal, offset=offset, azim=azim, elev=elev,
                                               width=width, ssaa=ssaa, cap_rgb=CUT_RGB, base=SHELL_RGB)
        if len(_DRAWN) > 8:
            _DRAWN.clear()
        _DRAWN[key] = (buf.getvalue(), float(area))
    return _DRAWN[key]


def projector(render, bounds, azim, elev, width, ssaa=2):
    """The mapping model/render.py uses, for labels: returns (to_pixel(x, y, z) -> (px, py), mm per pixel)."""
    R = render.view_matrix(azim, elev)
    b = np.asarray(bounds, float) @ R.T
    mn, mx = b[:, :2].min(0), b[:, :2].max(0)
    W = width * ssaa
    pad = 0.05 * W
    s = (W - 2 * pad) / (mx[0] - mn[0])
    H = int(np.ceil((mx[1] - mn[1]) * s + 2 * pad))
    H += H % ssaa

    def to_pixel(x, y, z):
        p = R @ np.array([x, y, z], float)
        sx = (p[0] - mn[0]) * s + pad
        sy = H - ((p[1] - mn[1]) * s + pad) - (H - 2 * pad - (mx[1] - mn[1]) * s) / 2
        return sx / ssaa, sy / ssaa

    return to_pixel, ssaa / s


def _font(size, bold=False):
    from PIL import ImageFont
    try:
        import matplotlib
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        return ImageFont.truetype(os.path.join(matplotlib.get_data_path(), "fonts", "ttf", name), size)
    except Exception:                                           # noqa: BLE001
        return ImageFont.load_default()


def _label(draw, text, at, target, font, anchor="lm", colour=INK):
    """A label with a leader line from its text to the thing it names, ending in a dot."""
    box = draw.textbbox(at, text, font=font, anchor=anchor)
    pad = 7
    plate = (box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad)
    # the leader starts at the plate's edge nearest the target
    cx = min(max(target[0], plate[0]), plate[2])
    cy = min(max(target[1], plate[1]), plate[3])
    draw.line([(cx, cy), target], fill=colour, width=3)
    r = 6
    draw.ellipse([target[0] - r, target[1] - r, target[0] + r, target[1] + r], fill=colour, outline=(255, 255, 255), width=2)
    draw.rounded_rectangle(plate, radius=8, fill=(255, 255, 255), outline=colour, width=2)
    draw.text(at, text, font=font, fill=colour, anchor=anchor)


def _arrow(draw, a, b, colour, width=6, head=20):
    draw.line([a, b], fill=colour, width=width)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    left = (b[0] - head * math.cos(ang - 0.42), b[1] - head * math.sin(ang - 0.42))
    right = (b[0] - head * math.cos(ang + 0.42), b[1] - head * math.sin(ang + 0.42))
    tip = (b[0] + 0.35 * head * math.cos(ang), b[1] + 0.35 * head * math.sin(ang))
    draw.polygon([tip, left, right], fill=colour)


def inside_png(render, geom, cfg, V, F, width=1200):
    """The labelled inside view: the mid-plane cut seen from the side over the cut at window height
    seen from above, on one x scale, with every part of the air path named.  PNG bytes."""
    from PIL import Image, ImageDraw
    L = geom.layout(cfg)
    planes = cuts(geom, cfg)
    panels = []
    for name in ("side", "plan"):
        normal, offset, azim, elev = planes[name]
        data, _area = section_png(render, geom, V, F, normal, offset, azim, elev, width=width)
        to_pixel, _mm = projector(render, V, azim, elev, width)
        panels.append((Image.open(io.BytesIO(data)).convert("RGB"), to_pixel))
    (side, side_px), (plan, plan_px) = panels
    head, strip, foot = 92, 54, 64
    H = head + strip + side.height + strip + plan.height + foot
    canvas = Image.new("RGB", (width, H), PAPER)
    draw = ImageDraw.Draw(canvas)
    big, mid, small = _font(40, True), _font(30), _font(24)
    draw.text((36, 26), "Inside the whistle", font=big, fill=INK)
    y_side = head + strip
    y_plan = y_side + side.height + strip
    draw.text((36, head + 10), "Cut through the middle, seen from the bird's right side", font=small, fill=INK)
    draw.text((36, y_side + side.height + 10), "Cut at window height, seen from above (the window is on the bird's left)",
              font=small, fill=INK)
    canvas.paste(side, (0, y_side))
    canvas.paste(plan, (0, y_plan))
    draw.text((36, H - foot + 16), "Drawn from the print file. The red faces are cut plastic. Nothing here is a printed part.",
              font=small, fill=INK)

    def S(x, z):                                           # a point of the mid-plane, on the canvas
        px, py = side_px(x, 0.0, z)
        return (px, py + y_side)

    def P(x, y):                                           # a point of the plan cut, on the canvas
        zc = 0.5 * (L.z0 + L.z1)
        px, py = plan_px(x, y, zc)
        return (px, py + y_plan)

    tan = math.tan(L.sig)
    jet_y = lambda x: L.Ey + (x - L.Ex) * tan              # noqa: E731 - the windway's centre line in plan
    hole_top = L.skin_at_hole - cfg.dimple_depth_mm
    # --- side cut ---
    _label(draw, "finger hole", (S(40.0, 0)[0], y_side + 60), S(L.hole_x, hole_top - 1.2), mid, anchor="lm")
    _label(draw, "chamber", (S(96.0, 0)[0], S(0, 22.0)[1]), S(84.0, 22.0), mid, anchor="mm")
    _label(draw, "vent", (S(12.0, 0)[0], S(0, 40.0)[1]), S(L.vent_x, L.lobe_ridge + 1.2), mid, anchor="mm")
    _label(draw, "lip stop", (S(2.0, 0)[0], S(0, 28.0)[1]), S(cfg.lip_stop_x_mm + 0.6, cfg.tail_top_z_mm + 0.6 * cfg.lip_stop_rise_mm),
           mid, anchor="lm")
    _label(draw, "rump lobe", (S(52.0, 0)[0], S(0, 33.0)[1]), S(L.Ex + 6.0, 15.5), mid, anchor="lm")
    _label(draw, "mouthpiece (the tail)", (S(1.0, 0)[0], y_side + side.height - 34), S(7.0, 0.5 * cfg.tail_top_z_mm + 3.0), mid, anchor="lm")
    _label(draw, "window, seen through the lobe", (S(46.0, 0)[0], y_side + side.height - 34),
           S(L.Ex + 0.5 * L.cu, 0.5 * (L.z0 + L.z1)), mid, anchor="lm")
    # --- plan cut ---
    a = P(-4.5, jet_y(-4.5))
    b = P(L.Ex + L.cu - 1.6, jet_y(L.Ex + L.cu - 1.6))
    _arrow(draw, a, b, BREATH)
    draw.text((24, P(0.0, L.hw + 5.5)[1]), "breath", font=mid, fill=BREATH, anchor="lm")
    _label(draw, "windway", (P(4.0, 0)[0], y_plan + 62), P(14.0, jet_y(14.0) + 0.2), mid, anchor="lm")
    _label(draw, "window", (P(27.0, 0)[0], y_plan + 62), P(L.Ex + 0.45 * L.cu, L.hw - 1.1), mid, anchor="lm")
    _label(draw, "labium (the edge)", (P(47.0, 0)[0], y_plan + 62), P(L.Ex + L.cu + 0.5, jet_y(L.Ex + L.cu) + 0.9), mid, anchor="lm")
    _label(draw, "rump lobe", (P(8.0, 0)[0], y_plan + plan.height - 44), P(L.Ex + 9.0, 0.5 * (jet_y(L.Ex) + L.lobe_far_y)), mid, anchor="lm")
    _label(draw, "chamber", (P(100.0, 0)[0], P(0, -6.0)[1]), P(86.0, -6.0), mid, anchor="mm")
    _label(draw, "mouthpiece", (P(7.0, 0)[0], P(0, -7.0)[1]), P(1.4, -1.5), mid, anchor="lm")
    # a scale bar: 10 mm on this picture's own scale
    _to, mm_per_px = projector(render, V, planes["plan"][2], planes["plan"][3], width)
    bar = 10.0 / mm_per_px
    x1, yb = width - 60, y_plan + plan.height - 40
    draw.line([(x1 - bar, yb), (x1, yb)], fill=INK, width=4)
    for x in (x1 - bar, x1):
        draw.line([(x, yb - 9), (x, yb + 9)], fill=INK, width=4)
    draw.text((x1 - 0.5 * bar, yb - 16), "10 mm", font=small, fill=INK, anchor="mb")
    buf = _Png()
    canvas.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
