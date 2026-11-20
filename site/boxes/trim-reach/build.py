#!/usr/bin/env python3
"""Build this box: what the vent trim can and cannot recover.

    python3 site/boxes/trim-reach/build.py

Writes index.html (one self-contained page), thumb.png and box.json beside this file.  Every number
is read from the model: the solver's grid limit (model/solve.py GRID_STUDY), the sensitivity runs
(views/_data.py SENSITIVITY_RUNS), and the closed form of model/pigeon.py for the dashed curve.
Modelled numbers only: no whistle has been printed, and the right-hand panel ASSUMES the trim moves a
mis-printed whistle by as many cents as it moves the model.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

BAND = 0.08          # the tolerance the coo evidence justifies (input coo-pitch-analysis, section 5)
FIRST = 0.10         # typical error of an uncalibrated first print (input vessel-flute-acoustics-notes, section 3)
WORST = (0.15, 0.20)  # its worst case (same input)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def numbers():
    sys.path.append(os.path.join(ROOT, "model"))
    import acoustics
    import pigeon
    import solve
    data = load(os.path.join(ROOT, "views", "_data.py"), "pigeon_views_data")
    cfg, built = pigeon.CONFIG, pigeon.build()
    f0 = solve.GRID_STUDY["f0_hz"]
    sens = {r[0]: r for r in data.SENSITIVITY_RUNS["rows"]}
    cents = lambda f, ref: acoustics.cents(f, ref)                    # noqa: E731
    points = [{"d": 0.0, "name": "plugged", "hz": round(f0["closed_plugged"], 2),
               "cents": round(cents(f0["closed_plugged"], f0["closed"]), 1), "from": "solver, grid limit"},
              {"d": cfg.vent_d_mm, "name": "as printed", "hz": round(f0["closed"], 2), "cents": 0.0,
               "from": "solver, grid limit"}]
    for key, d in (("vent_2_5", 2.5), ("vent_3_0", 3.0), ("vent_3_5", 3.5)):
        shift = sum(sens[key][2]) / 2.0
        points.append({"d": d, "name": "reamed", "hz": round(f0["closed"] * 2.0 ** (shift / 1200.0), 1),
                       "cents": round(shift, 1), "from": "solver, mean of two grids"})
    curve = []
    for i in range(0, 36):
        d = 0.1 * i
        g = [built["g_window_mm"]]
        if d > 0:
            g.append(acoustics.conductance(acoustics.circle_area(d), built["vent_depth_mm"], cfg.k_vent))
        curve.append([round(d, 1), round(acoustics.helmholtz_hz(built["chamber_volume_mm3"], g, cfg.c_air_m_s), 2)])
    # the curve is build()'s own closed form: it must give build()'s three published notes
    assert abs(curve[0][1] - built["f_closed_plugged_hz"]) < 0.01
    assert abs(curve[21][1] - built["f_closed_hz"]) < 0.01 and abs(curve[35][1] - built["f_closed_reamed_hz"]) < 0.01
    down, up = -points[0]["cents"], points[-1]["cents"]
    target = cfg.target_closed_hz
    return {
        "target": target, "band": BAND, "first": FIRST, "worst": list(WORST),
        "points": points, "formula": curve,
        "reach": {"down_cents": down, "up_cents": up,
                  "formula_up_cents": round(built["tune_up_reach_cents"], 1),
                  "formula_short_cents": round(up - built["tune_up_reach_cents"])},
        "recover": {"exact_low": round(target * 2.0 ** (-up / 1200.0), 1), "exact_high": round(target * 2.0 ** (down / 1200.0), 1),
                    "band_low": round(target * (1 - BAND) * 2.0 ** (-up / 1200.0), 1),
                    "band_high": round(target * (1 + BAND) * 2.0 ** (down / 1200.0), 1)},
    }


def thumbnail(D, path):
    """The box as a still (matplotlib, light theme): the same two panels."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    blue, aqua, ink, muted = "#2a78d6", "#1baf7a", "#16191c", "#6b7480"
    t, b = D["target"], D["band"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.8, 7.2), dpi=100)
    fig.patch.set_facecolor("white")
    for ax in (a1, a2):
        ax.axhspan(t * (1 - b), t * (1 + b), color=aqua, alpha=0.16, lw=0)
        ax.axhline(t, color=ink, lw=1.2)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color("#ded9d2")
        ax.tick_params(colors=muted, labelsize=13)
    a1.plot([p[0] for p in D["formula"]], [p[1] for p in D["formula"]], color=muted, lw=1.4, ls=(0, (4, 3)))
    a1.plot([p["d"] for p in D["points"][1:]], [p["hz"] for p in D["points"][1:]], color=blue, lw=2)
    a1.plot([p["d"] for p in D["points"]], [p["hz"] for p in D["points"]], "o", color=blue, ms=10, mec="white", mew=2)
    for p, dy, va in ((D["points"][0], -3.5, "top"), (D["points"][-1], 3.5, "bottom")):
        a1.text(p["d"] + (0.08 if p["d"] == 0 else -0.05), p["hz"] + dy, "%.0f Hz (%+.0f cents)" % (p["hz"], p["cents"]),
                color=ink, fontsize=13, ha="left" if p["d"] == 0 else "right", va=va)
    for edge in (t * (1 - D["first"]), t * (1 + D["first"])):
        a1.axhline(edge, color=muted, lw=1.2, ls=(0, (2, 3)))
    a1.set_xlim(-0.25, 3.75)
    a1.set_ylim(t * 0.87, t * 1.13)
    a1.set_xticks([0, 2.1, 2.5, 3.0, 3.5])
    a1.set_xticklabels(["plugged", "2.1", "2.5", "3.0", "3.5"])
    a1.set_xlabel("vent diameter, mm", color=muted, fontsize=13)
    a1.set_title("The closed note against the vent (Hz)", color=ink, fontsize=16, loc="left", pad=12)
    a1.text(-0.15, t * (1 + b) - 1.5, "8 % band of the coo evidence", color=ink, fontsize=12, va="top")
    a1.text(-0.15, t * (1 + D["first"]) + 1.2, "a first print: 10 % either way", color=ink, fontsize=12, va="bottom")
    lo, hi = t * 0.78, t * 1.22
    xs = [lo + (hi - lo) * i / 400.0 for i in range(401)]
    up, down = D["reach"]["up_cents"], D["reach"]["down_cents"]

    def best(x):
        if x < D["recover"]["exact_low"]:
            return x * 2.0 ** (up / 1200.0)
        if x > D["recover"]["exact_high"]:
            return x * 2.0 ** (-down / 1200.0)
        return t
    a2.plot([lo, hi], [lo, hi], color=muted, lw=1.4, ls=(0, (4, 3)))
    a2.plot(xs, [best(x) for x in xs], color=blue, lw=2.2)
    for x in (D["recover"]["band_low"], D["recover"]["band_high"]):
        a2.plot([x], [best(x)], "o", color=blue, ms=10, mec="white", mew=2)
        a2.text(x, best(x) + (-4 if x < t else 4), "%.0f Hz (%+.1f %%)" % (x, 100 * (x / t - 1)), color=ink, fontsize=13,
                ha="center", va="top" if x < t else "bottom")
    for edge in (t * (1 - D["first"]), t * (1 + D["first"])):
        a2.axvline(edge, color=muted, lw=1.2, ls=(0, (2, 3)))
    a2.set_xlim(lo, hi)
    a2.set_ylim(lo, hi)
    a2.set_xticks([t * (1 + k) for k in (-0.2, -0.1, 0, 0.1, 0.2)])
    a2.set_xticklabels(["-20 %", "-10 %", "340 Hz", "+10 %", "+20 %"])
    a2.set_xlabel("closed note of the first print", color=muted, fontsize=13)
    a2.set_title("After the best trim (Hz)", color=ink, fontsize=16, loc="left", pad=12)
    a2.text(lo + 3, lo + 9, "no trim", color=ink, fontsize=12, rotation=38)
    fig.text(0.012, 0.012, "Modelled, not measured. No whistle is printed yet.", color=muted, fontsize=12)
    fig.subplots_adjust(left=0.06, right=0.985, top=0.9, bottom=0.12, wspace=0.16)
    fig.savefig(path, dpi=100, metadata={"Software": None})
    plt.close(fig)


def main():
    D = numbers()
    with open(os.path.join(HERE, "template.html"), "r", encoding="utf-8") as fh:
        page = fh.read()
    page = page.replace("/*__DATA__*/null", json.dumps(D, sort_keys=True, separators=(",", ":")))
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)
    thumbnail(D, os.path.join(HERE, "thumb.png"))
    box = {"schema": 1, "kind": "custom",
           "title": "What the vent trim can and cannot recover",
           "caption": "Left: the modelled closed note with the vent plugged, as printed and reamed. Right: where a "
                      "first print ends after the best trim, if the trim moves it as it moves the model. The band "
                      "is the 8 % each way that the coo evidence tolerates. Nothing here is measured on a print.",
           "src": "index.html", "thumbnail": "thumb.png", "view": "engineering", "section": "implications",
           "about": "C4", "aspect": "16/9"}
    with open(os.path.join(HERE, "box.json"), "w", encoding="utf-8") as fh:
        json.dump(box, fh, indent=1)
        fh.write("\n")
    print(json.dumps({k: D[k] for k in ("points", "reach", "recover")}))
    print("index.html %d bytes, thumb.png %d bytes, caption %d chars" % (
        os.path.getsize(os.path.join(HERE, "index.html")), os.path.getsize(os.path.join(HERE, "thumb.png")), len(box["caption"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
