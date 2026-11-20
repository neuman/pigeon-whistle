#!/usr/bin/env python3
"""By-hand check of model/acoustics.py. Prints every validation table and exits non-zero if a check fails.

    python3 model/acoustics_check.py                    # about 40 s, needs no project geometry
    python3 model/acoustics_check.py --quick            # h = 0.8 only where a grid is needed (about 5 s)
    python3 model/acoustics_check.py --cross-check ADAPTERS.py

Sections
  1  closed form against published instruments (`acoustics.VALIDATION_CASES`), with the known-bad case
  2  closed form: the design-point numbers it gives for this whistle (information, no pass/fail)
  3  voxel solver against theory (box cavity + hole, flanged tube, thin baffle), at 0.8 / 0.6 / 0.5 mm, as
     boolean models and as cut-cell models
  4  grid convergence and truncation-radius independence
  5  known-good / known-bad control on the built-in fixture (the hole area halved must be heard)
  6  timing on a 120 x 70 x 70 mm body
  7  cross-implementation record: the acoustics judge's independent solver on his three rebuilt concepts

Section 7 prints the numbers RECORDED on 2026-11-19 (`CROSS_CHECK_RECORD`); it is evidence, not a live
check, because the judge's builders are not part of the project. `--cross-check FILE` re-runs it live with an
adapter module that provides `JUDGE_RESULTS` = [(label, model, builder_kwargs, f_judge_hz, G_judge_mm,
lumped_G_mm)], `JUDGE_CENTRES[model]["R"]` (his truncation radius), `build(model, h, **kwargs)` and
`to_vox(build)` -> the voxel dict of `acoustics.solve_resonance`.
"""
import argparse
import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import acoustics as ac  # noqa: E402

#: Largest difference in f (percent) tolerated between this solver and the judge's on the same voxels. Both
#: discretise the same equation on the same grid, so only the truncation centres and the linear-solver
#: tolerance differ; the brief asks for every difference above 1 % to be explained. Recorded worst: 0.08 %.
CROSS_CHECK_TOL_PCT = 1.0

#: Recorded 2026-11-19 at h = 0.5 mm, c = 346 m/s, each model solved with the judge's own truncation radius:
#: (case, judge f Hz, this solver f Hz, judge G mm, this solver G mm, this solver seconds, judge seconds).
#: The character-first case adds the judge's lumped 1.5 mm vent (G = 0.520 mm) to both.
CROSS_CHECK_RECORD = [
    ("print-first closed", 316.58, 316.53, 3.4945, 3.4933, 2.2, 83.6),
    ("print-first open, hole 5.9", 455.09, 455.46, 7.2213, 7.2330, 2.6, 235.9),
    ("acoustics-first closed", 326.16, 326.06, 5.1289, 5.1258, 2.5, 248.2),
    ("acoustics-first open, hole 7.2", 445.39, 445.36, 9.5638, 9.5627, 3.3, 311.1),
    ("character-first closed + 1.5 vent", 330.61, 330.58, 2.8170, 2.8164, 1.8, None),
]

#: Recorded 2026-11-19: the same five models re-voxelised by the judge's builders at other grid sizes (f, Hz).
#: This is the aliasing scatter of a boolean voxel model, not solver error (the solver agrees with the judge's
#: to 0.1 % on identical voxels). Columns: h = 0.8, 0.6, 0.5, 0.4 mm.
GRID_RECORD = [
    ("print-first closed", 310.12, 316.78, 316.53, 315.15),
    ("print-first open, hole 5.9", 447.06, 452.49, 455.46, 455.64),
    ("acoustics-first closed", 325.44, 327.33, 326.06, 324.44),
    ("acoustics-first open, hole 7.2", 443.34, 447.00, 445.36, 443.88),
    ("character-first closed + 1.5 vent", 326.63, 328.29, 330.58, 329.99),
]

#: A halved hole must lower the fixture's pitch by at least this much (percent) for the control to count as
#: 'heard'. Theory and solver both give about -25 %; 10 is far above the solver's 1-2 % error band and far
#: below the effect.
CONTROL_MIN_DROP_PCT = 10.0

#: Time budget from the brief: one solve at h = 0.8 mm on a 120 x 70 x 70 mm body.
TIME_BUDGET_S = 60.0

failures = []


def verdict(ok, what):
    if not ok:
        failures.append(what)
    return "ok" if ok else "FAIL"


def section(title):
    print("\n" + title)
    print("-" * len(title))


def closed_form_cases():
    section("1  Closed form against published instruments (model vs measured)")
    print("%-36s %-9s %9s %9s %8s %7s  %s" % ("case", "kind", "model Hz", "meas. Hz", "error", "band", ""))
    for row in ac.check_validation_cases():
        measured = "%9.1f" % row["measured_hz"] if row["measured_hz"] is not None else "   (calc)"
        band = (">%g %%" if row["kind"] == "known_bad" else "+-%g %%") % row["band_pct"]
        print("%-36s %-9s %9.1f %s %+7.1f%% %7s  %s" % (
            row["id"], row["kind"], row["model_hz"], measured, row["err_pct"], band,
            verdict(row["ok"], "closed form " + row["id"])))
    print("known_bad passes when the lumped model MISSES by more than the band: proof the comparison can fail.")


def design_point():
    section("2  Closed form at this whistle's design point (c = %g m/s; information only)" % ac.C_AIR)
    f_closed, f_open, cutup, windway_h, windway_w = 340.0, 470.0, 7.0, 1.3, 8.0
    for volume in (115e3, 120e3, 125e3):
        g_closed = ac.required_conductance(volume, f_closed)
        d = ac.hole_diameter_for_open_note(volume, f_closed, f_open, 3.0)
        d_vent = ac.vent_diameter_for_shift(volume, 330.0, f_closed, 3.0)
        print("V = %3.0f cm^3: G for %g Hz = %.3f mm; finger hole (t 3.0, k %.1f) d = %.2f mm; "
              "vent that lifts 330 -> 340 Hz d = %.2f mm" % (volume / 1e3, f_closed, g_closed, ac.K_HOLE, d, d_vent))
    for p in (100.0, 200.0, 300.0):
        print("P = %3.0f Pa: U = %4.1f m/s  St(340/470) = %.3f / %.3f  Ising = %.2f / %.2f  transit = %.2f / %.2f "
              "periods  Re = %4.0f  flow = %4.1f L/min" % (
                  p, ac.jet_speed(p), ac.strouhal(f_closed, cutup, p), ac.strouhal(f_open, cutup, p),
                  ac.ising(f_closed, cutup, windway_h, p), ac.ising(f_open, cutup, windway_h, p),
                  ac.jet_transit_periods(f_closed, cutup, p), ac.jet_transit_periods(f_open, cutup, p),
                  ac.jet_reynolds(windway_h, p), ac.windway_flow_l_min(p, windway_w, windway_h)))
    print("playable St %g-%g (best %g-%g); Ising best %g, overblown above %g; Re %g-%g" % (
        *ac.STROUHAL_PLAYABLE, *ac.STROUHAL_BEST, ac.ISING_BEST, ac.ISING_OVERBLOWN, *ac.JET_REYNOLDS_RANGE))
    rad = ac.radiated_fraction(120e3, f_closed, 56.0, 3.5)
    print("V = 120 cm^3 at %g Hz, window 56 mm^2 x 3.5 mm: Q_rad %.0f, Q_visc %.0f, Q_therm %.0f -> passive Q %.0f, "
          "radiated share %.1f %%; viscous detuning %.1f %%; 65 mm chamber / wavelength = %.3f (limit %.2f)" % (
              f_closed, rad["q_rad"], rad["q_visc"], rad["q_therm"], rad["q_passive"], 100 * rad["fraction"],
              100 * ac.viscous_detune(rad["q_visc"]), ac.lumped_ratio(65.0, f_closed), ac.LUMPED_RATIO_LIMIT))


def solver_vs_theory(hs):
    section("3  Voxel solver against theory (error in f = sqrt(G/G_theory) - 1; tolerance +-%g %%)" % ac.ANALYTIC_TOL_PCT)
    print("%-5s %-20s %9s %11s %8s %8s %6s  %s" % ("h mm", "case", "G mm", "theory mm", "err G", "err f", "s", ""))
    for h in hs:
        for row in ac.analytic_cases(h):
            note = "" if row["bounds_mm"] is None else "  inside Rayleigh's bounds %.2f-%.2f (+tol)" % row["bounds_mm"]
            print("%-5.2f %-20s %9.4f %11.4f %+7.2f%% %+7.2f%% %6.1f  %s%s" % (
                h, row["case"], row["G_mm"], row["G_theory_mm"], row["err_G_pct"], row["err_f_pct"], row["seconds"],
                verdict(row["ok"], "analytic %s h=%.2f" % (row["case"], h)), note))
    print("the same fixtures as CUT-CELL models (face apertures; theory for the true circle):")
    for h in hs:
        for row in ac.analytic_cases(h, cut_cells=True):
            note = "" if row["bounds_mm"] is None else "  inside Rayleigh's bounds %.2f-%.2f (+tol)" % row["bounds_mm"]
            print("%-5.2f %-20s %9.4f %11.4f %+7.2f%% %+7.2f%% %6.1f  %s%s" % (
                h, row["case"], row["G_mm"], row["G_theory_mm"], row["err_G_pct"], row["err_f_pct"], row["seconds"],
                verdict(row["ok"], "analytic cut-cell %s h=%.2f" % (row["case"], h)), note))
    print("theories: box-hole = %s; flanged-tube = %s." % tuple(r["theory"] for r in ac.analytic_cases(hs[0])[:2]))
    if len(hs) >= 2:
        limit = ac.thin_baffle_limit(hs)
        print("thin baffle, plate thickness = h -> 0:  G/(2a) = %s  -> extrapolated %.4f (Rayleigh: 1), f error "
              "%+.2f %%  %s" % (", ".join("%.4f" % r["G_over_2a"] for r in limit["rows"]), limit["limit_G_over_2a"],
                               limit["err_f_pct"], verdict(limit["ok"], "thin-baffle limit")))
        limit = ac.thin_baffle_limit(hs, cut_cells=True)
        print("the same as a cut-cell model:           G/(2a) = %s  -> extrapolated %.4f (Rayleigh: 1), f error "
              "%+.2f %%  %s" % (", ".join("%.4f" % r["G_over_2a"] for r in limit["rows"]), limit["limit_G_over_2a"],
                               limit["err_f_pct"], verdict(limit["ok"], "thin-baffle limit, cut cells")))


def convergence(hs):
    section("4  Grid convergence and truncation-radius independence")
    if len(hs) >= 2:
        study = ac.convergence_study(ac.fixture_box, hs, pad_mm=ac.FIXTURE_PAD_MM)
        print("fixture_box, f / theory at h = %s: %s -> h = 0: %.4f (spread %.2f %%)  %s" % (
            ", ".join("%g" % h for h in hs), ", ".join("%.4f" % r["value"] for r in study["rows"]), study["limit"],
            study["spread_pct"], verdict(abs(study["limit"] - 1.0) * 100 <= ac.ANALYTIC_TOL_PCT, "fixture_box limit")))
        study = ac.convergence_study(ac.fixture_vessel, hs)
        print("fixture_vessel (window + hole + 2.4 mm vent), f Hz: %s -> h = 0: %.1f (spread %.2f %%; the vent is "
              "only %s voxels across: this is the aliasing the module docstring warns about)" % (
                  ", ".join("%.2f" % r["value"] for r in study["rows"]), study["limit"], study["spread_pct"],
                  " / ".join("%.0f" % (2.4 / h) for h in hs)))
        study = ac.convergence_study(lambda h: ac.fixture_vessel(h, vent_open=False), hs)
        print("fixture_vessel, vent closed, f Hz:              %s -> h = 0: %.1f (spread %.2f %%)" % (
            ", ".join("%.2f" % r["value"] for r in study["rows"]), study["limit"], study["spread_pct"]))
    pads = (10.0, 14.0, ac.FIXTURE_PAD_MM)
    study = ac.truncation_study(ac.fixture_box(0.8), pads)
    print("fixture_box h = 0.8, pad_mm %s: f = %s Hz (spread %.2f %%)" % (
        "/".join("%g" % p for p in pads), ", ".join("%.2f" % r["f_hz"] for r in study["rows"]), study["spread_pct"]))
    pads = (15.0, 30.0, 60.0)
    study = ac.truncation_study(ac.fixture_vessel(0.8), pads)
    drift = abs(study["rows"][1]["f_hz"] / study["rows"][2]["f_hz"] - 1.0) * 100
    print("fixture_vessel h = 0.8, pad_mm %s: f = %s Hz; default 30 vs 60: %.2f %%  %s" % (
        "/".join("%g" % p for p in pads), ", ".join("%.2f" % r["f_hz"] for r in study["rows"]), drift,
        verdict(drift <= 0.3, "truncation independence")))


def controls():
    section("5  Known-good / known-bad control (built-in fixture, h = 0.8 mm)")
    good = ac.fixture_box(0.8)
    bad = ac.fixture_box(0.8, hole_area_scale=0.5)
    r_good = ac.solve_resonance(good, pad_mm=good["meta"]["pad_mm"])
    r_bad = ac.solve_resonance(bad, pad_mm=bad["meta"]["pad_mm"])
    for name, vox, r in (("good", good, r_good), ("bad (hole area halved)", bad, r_bad)):
        print("%-23s hole %.1f mm^2: f = %.1f Hz (theory %.1f, %+.2f %%), %d iterations, residual %.0e, %.2f s" % (
            name, vox["meta"]["hole_area_mm2"], r["f_hz"], vox["meta"]["theory_f_hz"],
            100 * (r["f_hz"] / vox["meta"]["theory_f_hz"] - 1), r["iterations"], r["residual"], r["seconds"]["total"]))
    err = abs(r_good["f_hz"] / good["meta"]["theory_f_hz"] - 1.0) * 100
    drop = (1.0 - r_bad["f_hz"] / r_good["f_hz"]) * 100
    print("known-good within %.1f %% of theory: %s;  known-bad is %.1f %% lower (needs > %g %%): %s" % (
        ac.ANALYTIC_TOL_PCT, verdict(err <= ac.ANALYTIC_TOL_PCT, "control known-good"), drop, CONTROL_MIN_DROP_PCT,
        verdict(drop > CONTROL_MIN_DROP_PCT, "control known-bad")))
    again = ac.solve_resonance(good, pad_mm=good["meta"]["pad_mm"])
    print("deterministic (same input, bit-identical f): %s" % verdict(again["f_hz"] == r_good["f_hz"], "determinism"))


def timing(hs):
    section("6  Timing on a 120 x 70 x 70 mm body (fixture_vessel, three openings, pad_mm 30, one process)")
    for h in hs:
        r = ac.solve_resonance(ac.fixture_vessel(h))
        s = r["seconds"]
        ok = "" if h != 0.8 else "  budget %g s: %s" % (TIME_BUDGET_S, verdict(s["total"] <= TIME_BUDGET_S, "time budget"))
        print("h = %.1f mm: %8d cells, %d levels, %2d iterations, residual %.0e: %5.1f s (assemble %.1f, hierarchy "
              "%.1f, solve %.1f); shares %s%s" % (
                  h, r["cells"], len(r["levels"]), r["iterations"], r["residual"], s["total"], s["assemble"],
                  s["hierarchy"], s["solve"], " ".join("%s %.3f" % kv for kv in r["shares"].items()), ok))


def cross_check_record():
    section("7  Cross-implementation record (acoustics judge's solver, his voxels; RECORDED 2026-11-19, h = 0.5)")
    print("%-34s %9s %9s %8s %9s %9s %7s %8s" % ("case", "judge Hz", "this Hz", "diff", "judge G", "this G", "this s", "judge s"))
    for case, f_judge, f_here, g_judge, g_here, s_here, s_judge in CROSS_CHECK_RECORD:
        print("%-34s %9.2f %9.2f %+7.2f%% %9.4f %9.4f %7.1f %8s" % (
            case, f_judge, f_here, 100 * (f_here / f_judge - 1), g_judge, g_here, s_here,
            "%.0f" % s_judge if s_judge else "-"))
    print("same models re-voxelised (f Hz at h = 0.8 / 0.6 / 0.5 / 0.4): aliasing scatter of the voxel model")
    for case, *fs in GRID_RECORD:
        print("%-34s %s   spread %.1f %%" % (case, "  ".join("%7.2f" % f for f in fs),
                                             100 * (max(fs) - min(fs)) / (sum(fs) / len(fs))))


def cross_check_live(path):
    section("7b Cross-implementation, LIVE (%s)" % path)
    spec = importlib.util.spec_from_file_location("judge_adapters", path)
    adapters = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapters)
    for label, model, kwargs, f_judge, g_judge, lumped in adapters.JUDGE_RESULTS:
        vox = adapters.to_vox(adapters.build(model, h=0.5, **kwargs))
        r = ac.solve_resonance(vox, pad_mm=adapters.JUDGE_CENTRES[model]["R"], extra_G_mm=lumped)
        diff = 100 * (r["f_hz"] / f_judge - 1)
        print("%-44s judge %.2f Hz, here %.2f Hz (%+.2f %%), G %.4f vs %.4f mm, %.1f s  %s" % (
            label, f_judge, r["f_hz"], diff, g_judge, r["G_mm"] - lumped, r["seconds"]["total"],
            verdict(abs(diff) <= CROSS_CHECK_TOL_PCT, "cross-check " + label)))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--quick", action="store_true", help="grid cases at h = 0.8 only")
    parser.add_argument("--cross-check", metavar="ADAPTERS.py", help="re-run section 7 live with this adapter module")
    args = parser.parse_args()
    hs = (0.8,) if args.quick else (0.8, 0.6, 0.5)
    closed_form_cases()
    design_point()
    solver_vs_theory(hs)
    convergence(hs)
    controls()
    timing(hs)
    cross_check_record()
    if args.cross_check:
        cross_check_live(args.cross_check)
    print("\n%s" % ("ALL CHECKS PASSED" if not failures else "FAILED: " + "; ".join(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
