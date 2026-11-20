"""Acoustics of the pigeon whistle (a one-hole vessel flute): the project's single source of pitch physics.

Pure functions on plain numbers and numpy arrays (numpy + scipy only), deterministic, no project imports.
Units: mm, mm^2, mm^3, Hz, Pa; the speed of sound is passed in m/s. Import by file path or as `acoustics`.

Three layers
------------
1. CLOSED FORM (microseconds, for `build()`): the lumped Helmholtz law
       f = c/(2 pi) * sqrt(sum_i G_i / V),     G_i = A_i / (t_i + k_i * r_eq_i),   r_eq = sqrt(A/pi)
   with its exact corollary, the interval rule  f_open^2 - f_closed^2 = (c/2 pi)^2 * G_hole / V  (the window
   model cancels), inverse helpers (hole / vent diameter for a wanted note), the jet numbers (Strouhal,
   Ising, transit, flow) and loss estimates.
2. VOXEL POTENTIAL FLOW (`solve_resonance`, seconds): the quasi-static (Laplace) flow from the chamber to the
   far field through the real 3D openings. It replaces the guessed end corrections k_i by a field solve:
   throat, flare, wall thickness, exterior shading and first-order non-compactness are all in the answer.
3. VALIDATION DATA AND CONTROLS: published instruments for the closed form (`VALIDATION_CASES`), analytic
   cases, grid / truncation studies and tiny synthetic fixtures for the solver (`analytic_cases`,
   `convergence_study`, `truncation_study`, `fixture_box`, `fixture_vessel`). `acoustics_check.py` prints them.

Honest error bands (what each number may be trusted for)
--------------------------------------------------------
Sources are tagged as in the research notes `inputs/references/vessel-flute-acoustics-notes.md` (NOTES):
[SRC] read in a fetched source, [KNOW] textbook knowledge not re-fetched, [CALC] arithmetic, [RUN] measured by
running this file's own checks (`acoustics_check.py`), [JUDGE] the design panel's acoustics review.

* Closed form, absolute pitch of a mouth-blown voiced window, uncalibrated: +-10 % typical, 15-20 % worst case,
  sign not consistent between published instruments (NOTES section 3: -17.5 % ... +3 % on the Csoka alto
  ocarina depending on the end-correction choice; +34 % on a tube-like soprano if non-compactness is ignored).
  Bottles with a real neck: +-3 %. The INTERVAL made by a finger hole: about +-1...3 % in ratio.
* Voxel solve, numerics only [RUN]:
  - staircase bias: against theory G comes out LOW, first order in h: on an 8 mm round hole in a 3 mm wall
    f is -1.1 % at h = 0.8, -0.6 % at 0.6, -0.5 % at 0.5, -0.1 % at 0.25 (`analytic_cases`); a one-voxel-thin
    plate about twice that;
  - aliasing: a boolean voxel model cannot hold a feature to better than about one voxel. Whole-instrument
    models re-voxelised at 0.8 / 0.6 / 0.5 / 0.4 mm scatter by 0.8-2.1 % in f (h = 0.8 reads up to 2 % low);
    a round bore fewer than 8 voxels across is NOT resolved: its voxelised area is off by -43 ... +13 % at
    2-3 voxels across, and even with the area corrected its G is 3-9 % low (see `rescale_opening`);
  - truncation: pad_mm = 30 is within 0.15 % of pad_mm = 120; the iterative tolerance is negligible;
  - cross-implementation: within 0.1 % in f of the acoustics judge's independent solver on three
    whole-instrument models at h = 0.5 (five cases; recorded in `acoustics_check.py`).
  - sharp edges: on the whistle itself (not on the smooth fixtures) every single grid is FLAT, by 1.5 % in f
    at h = 0.4 to 3.5 % at h = 0.8, and still by 0.9 % at h = 0.25 (see CUT-CELL MODELS below);
  So: about +-1.5 % in f at h <= 0.5 and +-3 % at h = 0.8 for a smooth-edged model, as a statement about the
  PASSIVE resonance of the geometry as designed, PROVIDED every opening is at least 8 voxels across or is
  corrected / lumped; for the whistle, +-0.4 % after the extrapolation to h = 0 in model/solve.py.
* Passive resonance vs the pitch a person plays (not in either model):
  - jet / blowing pressure: +-30...60 cents (+-2...3.5 %) over the playable breath range, low notes most
    sensitive (NOTES section 1.4 [SRC] Pure Ocarinas breath curves; Fletcher 1976);
  - lip / face shading of a window near the mouth: -0.2 ... -1.4 % (a face plane 14 ... 2 mm behind the
    window) [JUDGE, potential-flow runs]; a desk under the belly: -1.5 ... -2.8 % (design spec; -2.0 and
    -2.5 % with `bed_z_mm=0.0` on two of the concept models [RUN]) -> read pitch in the playing hold;
  - viscous boundary layer in the window: about -1 to -2 % (`viscous_detune`: -1/(2 Q_visc) with Q_visc ~ 30,
    NOTES section 6 [CALC]);
  - temperature: c = 346 m/s is a warmed instrument; a cold first toot is -13 cents, long play +17 cents
    (NOTES section 1.3 [CALC]);
  - print tolerance: hole diameter +-0.2 mm = +-14...20 cents on the open note; chamber volume -5 % = +44
    cents (NOTES sections 4 and 7 [CALC]).
  Net: played pitch within about +-5 % of the passive resonance, +-10 % once print tolerance is included
  [JUDGE]. Nothing here has been checked against a printed, blown pigeon.

What the voxel solve is (and is not)
------------------------------------
Model: incompressible potential flow, grad^2 phi = -q with q = 1/V uniform in the chamber (the chamber air is
the spring: at the Helmholtz mode it is compressed uniformly to leading order), zero normal velocity on every
plastic face, and a monopole (phi ~ 1/r) radiation condition where the exterior air is cut off. With unit total
source the kinetic energy is (rho/2) * mean_V(phi), so the total conductance is G = 1 / mean_V(phi) and
f = c/(2 pi) sqrt(G/V).
* V = h^3 times the number of voxels flagged `chamber` that are air and face-connected to the main chamber
  body. Nothing else counts: the air in the window / hole / vent passages and the exterior is incompressible
  mass (inertance), not volume.
* Inertance INSIDE the chamber is kept: because the source is spread over the chamber, mean_V(phi) contains the
  internal flow toward each opening. For a tube blown from one end this gives exactly the L/(3A) term, i.e. the
  first-order non-compactness correction f = f_H / sqrt(1 + G L^2/(3V)) of NOTES section 5. The next order is
  reported as `f_rayleigh_hz` (Rayleigh quotient of the same field; 0.05-0.2 % lower for a palm-size chamber).
* The windway is BLOCKED (its voxels are rigid): the player's mouth closes it. A closed opening is solid.
* FREE AIR is the playing condition and the default: everything outside the voxel arrays is air, including the
  space under the bed plane. The exterior is kept within `pad_mm` of each opening's centre; beyond it the field
  is continued as a monopole centred on the nearest opening.
* Not modelled: the jet, viscous and thermal losses, radiation loss, wall compliance, lips and fingers. Only
  the fundamental (Helmholtz) mode; no higher cavity modes.

CUT-CELL MODELS (what `geom.voxel_model(..., cut_cells=True)` adds, and what it does not cure)
----------------------------------------------------------------------------------------------
A boolean voxel model knows a surface only to one voxel, so the cross-section of a 2 mm bore and the chamber
volume jump about as the grid moves (above). A cut-cell model also carries "aperture" (the open fraction of
every cell face, from the geometry's own signed fields) and "chamber_fill" (the chamber fraction of every
cell). The solver then
* keeps the same unknowns as the boolean model, the cells whose CENTRE is air, so a wall can never leak
  through a cell that holds air on both of its sides (a first version that made every partly open cell an
  unknown leaked through the 0.5 mm labium blade and through every wall thinner than two voxels);
* weights each link between two air cells by the open fraction of their common face, and hands the open
  fraction of a face lying between two plastic-centre cells (a sliver of passage along a wall) to the
  neighbouring link (`_node_apertures`); the open area of a round bore then sums to the circle's within
  0.03 % at h = 0.4-0.8 [RUN], against -43 ... +13 % for the boolean model;
* takes V = h^3 * sum(chamber_fill): the true volume (a boolean count of this whistle's chamber is 0.85 %
  low at h = 0.8, where the floor plane falls exactly on a row of voxel centres [RUN]).
What it does NOT cure is the first-order error of the flow itself at sharp edges. Against the same theory,
evaluated for the true circle, the cut-cell box fixture is -1.6 / -1.3 / -0.5 / -0.5 % in f at h = 0.8 /
0.6 / 0.5 / 0.4 and the flanged tube -1.0 ... -0.4 % [RUN, `analytic_cases(h, cut_cells=True)`]: the same
size as the boolean model's error. On the real whistle, whose window has a knife-like labium, G rises by
7-8 % per mm of h in every state all the way down to h = 0.25 (model/solve.py GRID_STUDY), i.e. a single
grid at h = 0.4-0.8 is 1.5-3.5 % flat in f. The velocity is singular at a sharp edge and a finite-volume
grid recovers the missing kinetic energy only in proportion to h. So: extrapolate to h = 0
(`richardson`, or the measured first-order coefficient in model/solve.py), never quote one grid.

Sizing the finger hole and the vent with it (what the numbers above imply)
--------------------------------------------------------------------------
The window (7 x 8 mm, a real 3D passage) is what the field solve is for; a 2 mm vent is what it is worst at.
1. Solve with the hole and vent closed at h <= 0.5 mm: G_window (= "G_mm") and V. Solve at a second h to see
   the aliasing scatter of this geometry before trusting the third digit.
2. The conductance an opening adds is the DIFFERENCE of two solves, G(open) - G(closed): that is exactly the
   quantity in the interval rule ("G_openings_mm" splits one solve by flow share and is within 1-2 % of it).
3. Correct it for the voxelised bore area with `rescale_opening` (areas from `passage_section_mm2` and from
   the design), or calibrate k once with `end_factor` and then size by `hole_diameter_for_open_note` /
   `vent_diameter_for_shift`. A vent under 8 voxels across is better left closed in the voxels and passed as
   `extra_G_mm=conductance(area, t, k)`.
"""
import math
import time

import numpy as np
from scipy import ndimage, sparse
from scipy.sparse import csgraph
from scipy.sparse.linalg import splu

NOTES = "inputs/references/vessel-flute-acoustics-notes.md"

# --------------------------------------------------------------------------------------------------------
# Constants (each with why this value, what lost, and where it came from)
# --------------------------------------------------------------------------------------------------------

#: Speed of sound, m/s. Air in a warmed, played instrument is about 25.5 C (Fuks; oboe 25.6 C Meyer, flute
#: 26.8 C Coltman [SRC] speech.kth.se/music/publications/leofuks/IIIbism97co3.html); humidity and CO2 of the
#: breath roughly cancel, so the 25 C dry-air value 331.3*sqrt(1+T/273.15) = 346.1 is used (NOTES 1.3).
#: Lost: 343 (20 C room air: a played instrument is warmer, -13 cents) and 352 (35 C breath: the air in the
#: chamber is not at breath temperature).
C_AIR = 346.0

#: Air density, kg/m^3, at about 25 C (NOTES 2.3 uses 1.18 for every jet number).
RHO_AIR = 1.18

#: Kinematic viscosity of air, m^2/s. Implied by NOTES 2.2: Re = 2500 <=> h*U = 0.0375 m^2/s.
NU_AIR = 1.5e-5

#: Dynamic viscosity (Pa s) and thermal diffusivity (m^2/s) of air, and gamma - 1, as used for the loss
#: estimates of NOTES section 6 [CALC]. Only `radiated_fraction` depends on them.
ETA_AIR = 1.85e-5
THERMAL_DIFFUSIVITY_AIR = 2.1e-5
GAMMA_MINUS_1 = 0.4

# End-correction factors k in  L_eff = t + k * r_eq  (NOTES 1.2).
#: One unflanged pipe end (Levine & Schwinger 1948) [SRC en.wikipedia.org/wiki/End_correction].
K_END_UNFLANGED = 0.6133
#: One flanged end, exact long-pipe value (Nomura / Norris-Sheng) [KNOW]. Used as the theory for the solver's
#: analytic cases. The uniform-piston approximation 8/(3 pi) = 0.849 is the value printed in most sources.
K_END_FLANGED = 0.8217
K_END_FLANGED_PISTON = 8.0 / (3.0 * math.pi)
#: Both sides of a circular aperture in a wall of zero thickness: conductivity 2r exactly, i.e.
#: L_eff = (pi/2) r (Rayleigh, Theory of Sound section 306 [KNOW]; used by Printone via Howe 1998 [SRC]).
K_THIN_APERTURE = math.pi / 2.0
#: Finger hole or vent in a wall, both ends: nominal 1.6; range 1.46 (inner flanged 0.85 + outer unflanged
#: 0.61) to 1.70 (both flanged); the whole range moves the open note only +26/-17 cents (NOTES 1.2, section 7).
K_HOLE = 1.6
K_HOLE_RANGE = (1.46, 1.70)
#: Voiced window, both ends: nominal 1.7, but a CALIBRATION UNKNOWN: one edge is a knife, the other the windway
#: exit, the jet crosses it and the face is near. No source gives a number (NOTES 1.2). Range used for
#: sensitivity: 1.5 (convex exterior) to 2.3 (shaded by lips). Prefer `solve_resonance` over this constant.
K_WINDOW = 1.7
K_WINDOW_RANGE = (1.5, 2.3)
#: Bottle neck, outer end unflanged: L' = L + 1.5 a (Kinsler & Frey via Monteiro et al. arXiv:1805.04014 [SRC]).
K_BOTTLE_NECK = 1.5

#: Position factor p in f = f_H / sqrt(1 + p * G * L^2 / V): opening at the END of a tube-like cavity of
#: length L (1/3) or at its MIDDLE (1/12). Exact to first order for a uniform tube (NOTES section 5 [CALC]).
NONCOMPACT_END = 1.0 / 3.0
NONCOMPACT_MIDDLE = 1.0 / 12.0

#: Jet Strouhal number St = f*W/U (W = cut-up, U = jet speed). A flue instrument has gain for 0.07 < St < 0.27
#: (recorder head, Price et al. arXiv:1502.02170 [SRC]; equivalently U/(W f) > 4, Auvray et al.
#: arXiv:1207.7136 [SRC]); efficiency peaks at 0.14-0.18 (McKinnon thesis re-analysing Verge [SRC]). NOTES 2.2.
STROUHAL_PLAYABLE = (0.07, 0.27)
STROUHAL_BEST = (0.14, 0.18)
#: Ising intonation number I = sqrt(2 P D / (rho H^3)) / f: 2 = maximum efficiency, above about 3 an organ
#: pipe overblows; a vessel flute has no overtone to jump to, so there it means airy / screech (Liljencrants
#: after Ising 1971 [SRC] mmdigest.com/gallery/technical/isingform). NOTES 2.2.
ISING_BEST = 2.0
ISING_OVERBLOWN = 3.0
#: Disturbances travel along the jet at about 0.4 of the jet speed (arXiv:1601.05545 [SRC]); the normal regime
#: has about half a jet wavelength across the mouth (Fletcher 1976 [SRC]). NOTES 2.2.
JET_WAVE_SPEED_RATIO = 0.4
#: The jet must leave the windway laminar: Re = h*U/nu about 500-2500 in recorders (Price slides [SRC]).
JET_REYNOLDS_RANGE = (500.0, 2500.0)

#: Largest chamber dimension / wavelength at which the plain lumped formula is still within about 1.6 %
#: (opening mid-cavity, (kL)^2/24) ... 6.6 % (opening at the end, (kL)^2/6) of the first-order value (NOTES
#: section 5 [CALC]). A judgement, not a published limit. It bounds the CLOSED FORM only: `solve_resonance`
#: carries that first-order term.
LUMPED_RATIO_LIMIT = 0.10

#: Passage keys of a voxel model, in the order used for reporting.
OPENINGS = ("window", "hole", "vent")

#: Cut-cell models: a face open by less than this fraction is treated as closed. A sliver this small carries
#: no flow that matters (its conductance is 0.1 % of a full face) but would put entries 1000 times smaller
#: than its neighbours' on the matrix diagonal of a cell that has no other opening. Lost: 0 (keeps such cells).
APERTURE_MIN = 1.0e-3


# --------------------------------------------------------------------------------------------------------
# 1. Closed form
# --------------------------------------------------------------------------------------------------------

def speed_of_sound(temp_c):
    """Dry-air speed of sound in m/s at `temp_c` degrees C: 331.3*sqrt(1 + T/273.15) (NOTES 1.3)."""
    return 331.3 * math.sqrt(1.0 + temp_c / 273.15)


def circle_area(d_mm):
    return math.pi * d_mm * d_mm / 4.0


def equal_area_radius(area_mm2):
    """Radius of the circle with the same area. The right size measure for a non-circular opening up to about
    2:1 aspect (error in f +0.5 % at 1.5:1, +1.5 % at 2:1, +3.7 % at 3:1; NOTES 1.2 [CALC]). Never the
    hydraulic diameter."""
    return math.sqrt(area_mm2 / math.pi)


def conductance(area_mm2, t_mm, k):
    """Acoustic conductance G = A / (t + k * r_eq) in mm of one opening of area A through a wall of
    thickness t, with end-correction factor k (see the K_* constants)."""
    return area_mm2 / (t_mm + k * equal_area_radius(area_mm2))


def end_factor(conductance_mm, area_mm2, t_mm):
    """Inverse of `conductance` for k: the effective end-correction factor of an opening whose conductance is
    known (from `solve_resonance` or from a measured pitch). This is the calibration step of NOTES section 7."""
    return (area_mm2 / conductance_mm - t_mm) / equal_area_radius(area_mm2)


def helmholtz_hz(volume_mm3, conductance_mm, c=C_AIR):
    """f = c/(2 pi) * sqrt(sum G / V). `conductance_mm` is one conductance or any iterable of them: openings
    are acoustic masses in parallel on one spring, so conductances add (NOTES 1.1: UNSW Helmholtz page,
    Csoka 2018 section 3.2 [SRC])."""
    g = float(np.sum(conductance_mm))
    return c * 1e3 / (2.0 * math.pi) * math.sqrt(g / volume_mm3)


def required_conductance(volume_mm3, f_hz, c=C_AIR):
    """Total conductance a chamber needs to sound `f_hz`: G = V * (2 pi f / c)^2 (mm)."""
    return volume_mm3 * (2.0 * math.pi * f_hz / (c * 1e3)) ** 2


def noncompact_factor(conductance_mm, volume_mm3, cavity_len_mm, position=NONCOMPACT_END):
    """Factor (< 1) on the lumped frequency for an elongated cavity: 1/sqrt(1 + p*G*L^2/V) (NOTES section 5).
    Use the tube value as a bound and about half of its effect as nominal for a fat ellipsoid."""
    return 1.0 / math.sqrt(1.0 + position * conductance_mm * cavity_len_mm ** 2 / volume_mm3)


def interval_conductance(volume_mm3, f_low_hz, f_high_hz, c=C_AIR):
    """Conductance an EXTRA opening must add to raise the note from f_low to f_high:
    G = V * (2 pi / c)^2 * (f_high^2 - f_low^2). Independent of every other opening (NOTES 1.1 corollary)."""
    return volume_mm3 * (2.0 * math.pi / (c * 1e3)) ** 2 * (f_high_hz ** 2 - f_low_hz ** 2)


def raised_note_hz(f_low_hz, added_conductance_mm, volume_mm3, c=C_AIR):
    """The interval rule forwards: the note after an opening of conductance G is added to (or, with a negative
    G, removed from) an instrument sounding f_low."""
    return math.sqrt(f_low_hz ** 2 + (c * 1e3 / (2.0 * math.pi)) ** 2 * added_conductance_mm / volume_mm3)


def cents(f_hz, ref_hz):
    """Interval from ref to f in cents (100 cents = one semitone)."""
    return 1200.0 * math.log2(f_hz / ref_hz)


def diameter_for_conductance(conductance_mm, t_mm, k=K_HOLE):
    """Diameter of the circular bore through a wall of thickness t whose conductance is G:
    the positive root of pi r^2 = G (t + k r)."""
    gk = conductance_mm * k
    r = (gk + math.sqrt(gk * gk + 4.0 * math.pi * conductance_mm * t_mm)) / (2.0 * math.pi)
    return 2.0 * r


def hole_diameter_for_open_note(volume_mm3, f_closed_hz, f_open_hz, t_mm, k=K_HOLE, c=C_AIR):
    """Finger-hole diameter (mm) that turns the closed note into the open note. Uses the interval rule, so the
    badly known window drops out; k may be calibrated with `end_factor` from a voxel solve or a print.
    Sensitivity: +-0.2 mm = +-14...20 cents on the open note (NOTES section 4)."""
    return diameter_for_conductance(interval_conductance(volume_mm3, f_closed_hz, f_open_hz, c), t_mm, k)


def vent_diameter_for_shift(volume_mm3, f_plugged_hz, f_vented_hz, t_mm, k=K_HOLE, c=C_AIR):
    """Diameter (mm) of an always-open tuning vent that raises the note from f_plugged to f_vented. Same
    physics as the finger hole; a vent raises the closed note about twice as many cents as the open one
    (NOTES section 7)."""
    return hole_diameter_for_open_note(volume_mm3, f_plugged_hz, f_vented_hz, t_mm, k, c)


def jet_speed(p_blow_pa, rho=RHO_AIR):
    """Jet speed (m/s) at the windway exit from the mouth pressure: U = sqrt(2 P / rho) (Bernoulli)."""
    return math.sqrt(2.0 * p_blow_pa / rho)


def strouhal(f_hz, cutup_mm, p_blow_pa, rho=RHO_AIR):
    """St = f * W / U with W the cut-up (windway exit to labium edge). Playable `STROUHAL_PLAYABLE`
    (0.07-0.27), best `STROUHAL_BEST` (0.14-0.18). Sources at the constants."""
    return f_hz * cutup_mm * 1e-3 / jet_speed(p_blow_pa, rho)


def pressure_for_strouhal(f_hz, cutup_mm, st, rho=RHO_AIR):
    """Mouth pressure (Pa) that puts a note at Strouhal number `st`: P = rho/2 * (f W / St)^2."""
    return 0.5 * rho * (f_hz * cutup_mm * 1e-3 / st) ** 2


def ising(f_hz, cutup_mm, windway_height_mm, p_blow_pa, rho=RHO_AIR):
    """Ising intonation number I = sqrt(2 P D / (rho H^3)) / f, D = jet thickness (windway exit height),
    H = cut-up. `ISING_BEST` = 2, overblown above `ISING_OVERBLOWN` = 3. Equals sqrt(D/H) / St."""
    d = windway_height_mm * 1e-3
    hh = cutup_mm * 1e-3
    return math.sqrt(2.0 * p_blow_pa * d / (rho * hh ** 3)) / f_hz


def jet_transit_periods(f_hz, cutup_mm, p_blow_pa, rho=RHO_AIR):
    """Time a jet disturbance takes from the windway exit to the labium, in periods of the note:
    f * W / (0.4 U) = St / 0.4. About 0.5 in the normal regime; the playable Strouhal band maps to 0.18-0.68."""
    return strouhal(f_hz, cutup_mm, p_blow_pa, rho) / JET_WAVE_SPEED_RATIO


def jet_reynolds(windway_height_mm, p_blow_pa, rho=RHO_AIR):
    """Re = h * U / nu at the windway exit; keep inside `JET_REYNOLDS_RANGE` for a laminar jet."""
    return windway_height_mm * 1e-3 * jet_speed(p_blow_pa, rho) / NU_AIR


def windway_flow_l_min(p_blow_pa, exit_width_mm, exit_height_mm, rho=RHO_AIR):
    """Breath flow through the windway exit in L/min: Q = U * W * D (Liljencrants [SRC]; NOTES 2.3: 7.5 L/min
    at 100 Pa through 8 x 1.2 mm). No discharge coefficient: an upper estimate."""
    return jet_speed(p_blow_pa, rho) * exit_width_mm * 1e-3 * exit_height_mm * 1e-3 * 6e4


def lumped_ratio(largest_dimension_mm, f_hz, c=C_AIR):
    """Largest internal chamber dimension divided by the wavelength. Compare with `LUMPED_RATIO_LIMIT`."""
    return largest_dimension_mm * f_hz / (c * 1e3)


def radiation_q(volume_mm3, f_hz, c=C_AIR):
    """Radiation quality factor of an unflanged Helmholtz resonator, Q_rad = 4 pi / (V k^3) (radiation
    resistance rho c k^2 / (4 pi) [KNOW]; NOTES section 6: 534 for 100 cm^3 at 340 Hz)."""
    k = 2.0 * math.pi * f_hz / c
    return 4.0 * math.pi / (volume_mm3 * 1e-9 * k ** 3)


def radiated_fraction(volume_mm3, f_hz, window_area_mm2, window_t_mm, k_window=K_WINDOW, c=C_AIR):
    """Estimate of the share of the oscillation loss that leaves as sound, with the Q factors behind it.

    Losses in parallel (NOTES section 6 [CALC], an Ingard-type estimate, not a measurement):
    radiation `radiation_q`; viscous loss in the window Q_v = omega rho L_eff / R_s with
    R_s = 2 sqrt(2 eta rho omega) (t/d_eq + 1); thermal loss on the chamber wall Q_t = 2 V / ((gamma-1) S delta_t)
    with S the area of the sphere of volume V. Returns {"fraction", "q_rad", "q_visc", "q_therm", "q_passive"}.
    Reproduces the notes' 4.9 % / 6.4 % / 7.7 % for the 100 / 125 / 150 cm^3 worked sets. Real small
    resonators lose more at the neck-cavity junction, so read it as an upper estimate and as a RANKING tool
    (fraction grows as V * f^3)."""
    w = 2.0 * math.pi * f_hz
    q_rad = radiation_q(volume_mm3, f_hz, c)
    r = equal_area_radius(window_area_mm2)
    l_eff = (window_t_mm + k_window * r) * 1e-3
    r_s = 2.0 * math.sqrt(2.0 * ETA_AIR * RHO_AIR * w) * (window_t_mm / (2.0 * r) + 1.0)
    q_visc = w * RHO_AIR * l_eff / r_s
    v = volume_mm3 * 1e-9
    wall_area = (36.0 * math.pi) ** (1.0 / 3.0) * v ** (2.0 / 3.0)
    delta_t = math.sqrt(2.0 * THERMAL_DIFFUSIVITY_AIR / w)
    q_therm = 2.0 * v / (GAMMA_MINUS_1 * wall_area * delta_t)
    q = 1.0 / (1.0 / q_rad + 1.0 / q_visc + 1.0 / q_therm)
    return {"fraction": q / q_rad, "q_rad": q_rad, "q_visc": q_visc, "q_therm": q_therm, "q_passive": q}


def viscous_detune(q_visc):
    """Fractional pitch change caused by the viscous boundary layer in the openings: -1/(2 Q_visc). The
    boundary-layer impedance has equal resistive and mass-like parts (Kirchhoff [KNOW]), so the loss that
    gives Q_visc also adds 1/Q_visc of inertance. Q_visc ~ 30 (NOTES section 6) -> about -1.7 %. This is the
    'viscous losses about -1 to -2 %' line of the module docstring; neither model includes it."""
    return -0.5 / q_visc


# --------------------------------------------------------------------------------------------------------
# 2. Voxel potential-flow solver
# --------------------------------------------------------------------------------------------------------

def _embed(arr, lo, shape, fill):
    """The index box [lo, lo + shape) of `arr`, with `fill` wherever the box sticks out of the array."""
    out = np.full(shape, fill, dtype=arr.dtype)
    src, dst = [], []
    for a in range(3):
        s0 = max(lo[a], 0)
        s1 = min(lo[a] + shape[a], arr.shape[a])
        if s1 <= s0:
            return out
        src.append(slice(s0, s1))
        dst.append(slice(s0 - lo[a], s1 - lo[a]))
    out[tuple(dst)] = arr[tuple(src)]
    return out


class _Level:
    """One multigrid level: the operator, its inverse diagonal, the red/black split and the aggregate map."""
    __slots__ = ("n", "A", "dinv", "red", "black", "A_red", "A_black", "agg", "lu")


#: Coarsest multigrid level is factorised directly below this many unknowns (SuperLU takes milliseconds there).
_COARSE_UNKNOWNS = 1500


def _build_hierarchy(i, j, w, robin, coords):
    """Aggregation multigrid for A = sum_links w (e_i - e_j)(e_i - e_j)^T + diag(robin).

    Coarsening is geometric (2 x 2 x 2 blocks of the level's integer coordinates) but each block is split into
    its connected pieces, so air on the two sides of a thin wall never lands in one coarse cell: the dominant
    error component is precisely 'chamber high, outside low'. Coarse links carry HALF the summed fine
    conductance (what re-discretising on the 2h grid gives: 4 faces of h -> one face of 2h); Robin terms sum.
    Deterministic: no random numbers, fixed orderings.
    """
    levels = []
    while True:
        n = robin.size
        lev = _Level()
        lev.n = n
        off = sparse.coo_matrix((np.concatenate([-w, -w]), (np.concatenate([i, j]), np.concatenate([j, i]))),
                                shape=(n, n)).tocsr()
        diag = np.bincount(i, weights=w, minlength=n) + np.bincount(j, weights=w, minlength=n) + robin
        lev.A = off + sparse.diags(diag, format="csr")
        lev.dinv = 1.0 / diag
        lev.lu = None
        agg = None
        if n > _COARSE_UNKNOWNS:
            block = [cc >> 1 for cc in coords]
            span1 = int(block[1].max()) + 1
            span2 = int(block[2].max()) + 1
            key = (block[0] * span1 + block[1]) * span2 + block[2]
            same = key[i] == key[j]
            graph = sparse.coo_matrix((np.ones(int(same.sum()), np.int8), (i[same], j[same])), shape=(n, n))
            n_coarse, agg = csgraph.connected_components(graph.tocsr(), directed=False)
            if n_coarse > 0.8 * n:          # coarsening has stalled (a domain of thin sheets): stop here
                agg = None
        if agg is None:
            lev.lu = splu(lev.A.tocsc())
            levels.append(lev)
            return levels
        parity = (coords[0] + coords[1] + coords[2]) & 1
        lev.red = np.flatnonzero(parity == 0)
        lev.black = np.flatnonzero(parity == 1)
        lev.A_red = off[lev.red]
        lev.A_black = off[lev.black]
        lev.agg = agg.astype(np.int64)
        levels.append(lev)
        ci, cj = lev.agg[i], lev.agg[j]
        cross = ci != cj
        coarse = sparse.coo_matrix((0.5 * w[cross], (np.minimum(ci[cross], cj[cross]),
                                                     np.maximum(ci[cross], cj[cross]))),
                                   shape=(n_coarse, n_coarse)).tocsr().tocoo()      # tocsr sums duplicates
        i, j, w = coarse.row.astype(np.int64), coarse.col.astype(np.int64), coarse.data
        robin = np.bincount(lev.agg, weights=robin, minlength=n_coarse)
        member = np.zeros(n_coarse, np.int64)
        member[lev.agg[::-1]] = np.arange(n - 1, -1, -1)
        coords = [b[member] for b in block]


def _vcycle(levels, k, b):
    """One V(1,1) cycle with red-black Gauss-Seidel. Two cells of one colour are never linked (face
    neighbours differ in coordinate parity), so each half-sweep is an exact block solve. Post-smoothing runs
    the colours in reverse, which makes the cycle a symmetric positive-definite preconditioner for CG."""
    lev = levels[k]
    if lev.lu is not None:
        return lev.lu.solve(b)
    x = np.zeros_like(b)
    x[lev.red] = b[lev.red] * lev.dinv[lev.red]
    x[lev.black] = (b[lev.black] - lev.A_black @ x) * lev.dinv[lev.black]
    r = b - lev.A @ x
    x += _vcycle(levels, k + 1, np.bincount(lev.agg, weights=r, minlength=levels[k + 1].n))[lev.agg]
    x[lev.black] = (b[lev.black] - lev.A_black @ x) * lev.dinv[lev.black]
    x[lev.red] = (b[lev.red] - lev.A_red @ x) * lev.dinv[lev.red]
    return x


def _dot(a, b):
    """Inner product by numpy's own pairwise summation instead of BLAS: one thread, and the same bits
    whatever the BLAS thread count (a threaded BLAS dot may regroup the sum)."""
    return float(np.sum(a * b))


def _pcg(levels, b, tol, maxiter):
    """Conjugate gradients preconditioned by one V-cycle, from a zero start. Stops at |r| <= tol * |b|.
    Returns (x, iterations, relative residual)."""
    A = levels[0].A
    x = np.zeros_like(b)
    r = b.copy()
    b_norm = math.sqrt(_dot(b, b))
    z = _vcycle(levels, 0, r)
    p = z.copy()
    rz = _dot(r, z)
    res = 1.0
    for it in range(1, maxiter + 1):
        Ap = A @ p
        alpha = rz / _dot(p, Ap)
        x += alpha * p
        r -= alpha * Ap
        res = math.sqrt(_dot(r, r)) / b_norm
        if res <= tol:
            return x, it, res
        z = _vcycle(levels, 0, r)
        rz_new = _dot(r, z)
        p = z + (rz_new / rz) * p
        rz = rz_new
    return x, maxiter, res


def _face_sides():
    """Index tuples (low_side[a], high_side[a]) selecting the two cells of every face normal to axis a."""
    low_side, high_side = [], []
    for a in range(3):
        low = [slice(None)] * 3
        high = [slice(None)] * 3
        low[a] = slice(0, -1)
        high[a] = slice(1, None)
        low_side.append(tuple(low))
        high_side.append(tuple(high))
    return low_side, high_side


def _node_apertures(aperture, air):
    """Turn geometric face apertures into link weights between AIR-CENTRE cells (`air`), in place.

    Cut-cell rule of this solver (see `CUT-CELL MODELS` in the module docstring): the unknowns are the cells
    whose centre is air, exactly as in a boolean model, so a wall can never leak through a cell that holds
    air on both of its sides. A face between two such cells keeps its open fraction. A face between two
    plastic-centre cells that is partly open is a sliver of the passage running along a wall: its open
    fraction is handed to the neighbouring face (same normal, one cell to the side) between two air cells,
    the most open one of the four. Every other face is closed. So the open area of a passage's cross-section
    is its true area to second order, instead of the staircase's."""
    low_side, high_side = _face_sides()
    for a in range(3):
        ap = aperture[a]
        ap[ap < APERTURE_MIN] = 0.0
        own = ap[low_side[a]]                                         # a view: faces that have both cells
        node = air[low_side[a]] & air[high_side[a]]
        sliver = ~air[low_side[a]] & ~air[high_side[a]] & (own > 0.0)
        others = [b for b in range(3) if b != a]
        pad = [(0, 0)] * 3
        for b in others:
            pad[b] = (1, 1)
        offered = np.pad(np.where(node, own, np.float32(-1.0)), pad, constant_values=-1.0)
        shifts = []
        for b in others:
            for step in (0, 2):                                       # the neighbour one cell down / up axis b
                sel = [slice(None)] * 3
                for other in others:
                    sel[other] = slice(1, -1)
                sel[b] = slice(step, step + own.shape[b])
                shifts.append(tuple(sel))
        best = np.full(own.shape, -1, np.int8)
        best_value = np.zeros(own.shape, np.float32)                  # a closed neighbour (0) takes nothing
        for number, sel in enumerate(shifts):
            better = sliver & (offered[sel] > best_value)
            best[better] = number
            best_value[better] = offered[sel][better]
        merged = np.pad(np.where(node, own, np.float32(0.0)), pad, constant_values=0.0)
        for number, sel in enumerate(shifts):
            merged[sel] += np.where(best == number, own, np.float32(0.0))
        inner = [slice(None)] * 3
        for b in others:
            inner[b] = slice(1, -1)
        ap[low_side[a]] = merged[tuple(inner)]
        last = [slice(None)] * 3
        last[a] = slice(-1, None)
        ap[tuple(last)] = 0.0
    return aperture


def solve_resonance(vox, c=C_AIR, pad_mm=30.0, tol=1e-7, *, bed_z_mm=None, extra_G_mm=0.0, maxiter=400,
                    return_field=False):
    """Passive Helmholtz resonance of a voxel model by quasi-static potential flow (see the module docstring
    for the model, for what counts as V and for the error band).

    vox: the dict `geom.voxel_model(cfg, h, hole_open=..., vent_open=...)` returns:
        "origin" (x0, y0, z0) mm: the low corner of voxel [0, 0, 0];  "h": voxel size, mm;
        "solid"  bool[nx, ny, nz], True = plastic;  "chamber" bool, True = chamber air;
        "window" / "hole" / "vent" bool, True = air in that opening's passage (missing, empty or solid = closed);
        "windway" bool, treated as rigid (blocked by the player's mouth). Other keys are ignored.
        Everything outside the arrays is free air.
        CUT CELLS (optional, see `CUT-CELL MODELS` in the module docstring): "aperture", three float arrays
        [nx, ny, nz] with aperture[a][i, j, k] = open fraction (0...1) of the face between voxel [i, j, k] and
        its neighbour one step up axis a (the windway counted as plastic), and "chamber_fill" float
        [nx, ny, nz] = fraction of each voxel that is chamber air. When "aperture" is present the links
        between air cells carry those fractions and V = h^3 * sum(chamber_fill).
    c: speed of sound, m/s.
    pad_mm: exterior air is kept within this distance of each open passage's centroid and continued beyond as
        a monopole. 30 is within 0.15 % of the 120 mm answer; 15 costs about 0.3 % (`truncation_study`).
    tol: relative residual of the linear solve. G is an energy, so its error is of order tol^2.
    bed_z_mm: None = free air (the playing condition). A number puts a rigid plane there (air below it is
        removed): the instrument lying on a desk.
    extra_G_mm: conductance of openings NOT in the voxels (a vent too small for the grid), added in parallel.

    Returns a dict:
        "f_hz"            c/(2 pi) sqrt(G/V)
        "G_mm"            total conductance chamber -> far field (solved + extra_G_mm)
        "V_mm3"           chamber volume used (see module docstring)
        "shares"          {opening: fraction of the volume flow through it} (+ "lumped" if extra_G_mm);
                          sums to 1. Measured as the net flow from chamber voxels into that passage's voxels.
        "G_openings_mm"   {opening: share * G}: each opening's effective conductance in this configuration
        "iterations", "residual", "h"
        "f_rayleigh_hz"   the same field put through a Rayleigh quotient (adds the pressure non-uniformity in
                          the chamber and the passage air's compressibility): the second-order check
        "flux_unassigned" share of the flow that left the chamber NOT through a flagged passage (should be ~0;
                          if above 0.02 the shares fall back to through-flow of each passage, see "shares_by")
        "V_dropped_mm3"   chamber-flagged air not connected to the main chamber (should be 0)
        "cells", "levels", "pad_mm", "centres_mm", "cut_cells", "seconds" {"assemble", "hierarchy", "solve", "total"}
        "field"           only with return_field: {"phi" float32 grid (nan outside the flow domain; 1/mm for
                          unit flow), "origin", "h"}
    Raises ValueError when there is no chamber or no open path to the outside.
    Deterministic (no random numbers, fixed orderings, no BLAS reductions) and single-threaded.
    """
    t_start = time.perf_counter()
    h = float(vox["h"])
    origin = np.asarray(vox["origin"], float)
    cut_cells = vox.get("aperture") is not None
    blocked = np.asarray(vox["solid"], bool).copy()
    if vox.get("windway") is not None:
        blocked |= np.asarray(vox["windway"], bool)
    chamber = np.asarray(vox["chamber"], bool) & ~blocked
    if not chamber.any():
        raise ValueError("the voxel model has no chamber air")
    passages = {}
    for name in OPENINGS:
        if vox.get(name) is None:
            continue
        mask = np.asarray(vox[name], bool) & ~blocked & ~chamber
        if mask.any():
            passages[name] = mask
    if not passages:
        raise ValueError("every opening is closed: a sealed chamber has no Helmholtz resonance")
    centres = {name: origin + (np.array([ax.mean() for ax in np.nonzero(mask)]) + 0.5) * h
               for name, mask in passages.items()}

    # Working box: chamber and passages plus a ball of radius pad_mm round every centre (one spare voxel).
    needed = chamber.copy()
    for mask in passages.values():
        needed |= mask
    lo, shape = [], []
    for a in range(3):
        along = np.flatnonzero(needed.any(axis=tuple(b for b in range(3) if b != a)))
        first, last = int(along[0]), int(along[-1]) + 1
        for cen in centres.values():
            first = min(first, int(math.floor((cen[a] - pad_mm - origin[a]) / h)))
            last = max(last, int(math.ceil((cen[a] + pad_mm - origin[a]) / h)))
        lo.append(first - 2)
        shape.append(last - first + 4)
    shape = tuple(shape)
    fluid = ~_embed(blocked, lo, shape, False)
    n_chamber_given = int(chamber.sum())
    chamber = _embed(chamber, lo, shape, False)
    code = np.zeros(shape, np.int8)                      # 0 = not a passage, n = n-th open passage
    for number, mask in enumerate(passages.values(), start=1):
        code[_embed(mask, lo, shape, False)] = number
    axes = [origin[a] + (lo[a] + np.arange(shape[a]) + 0.5) * h for a in range(3)]
    if bed_z_mm is not None:
        fluid[:, :, axes[2] < bed_z_mm] = False
        chamber &= fluid
        code[~fluid] = 0
    low_side, high_side = _face_sides()
    aperture = None
    if cut_cells:                                        # free air (fully open faces) outside the arrays
        aperture = [_embed(np.asarray(ap, np.float32), lo, shape, np.float32(1.0)) for ap in vox["aperture"]]
        if bed_z_mm is not None:                         # nothing is open below the plane
            below = axes[2] < bed_z_mm
            aperture[0][:, :, below] = 0.0
            aperture[1][:, :, below] = 0.0
            aperture[2][:, :, axes[2] + 0.5 * h < bed_z_mm] = 0.0
        aperture = _node_apertures(aperture, fluid)
    r_near = np.full(shape, np.inf, np.float32)          # distance to the nearest opening centre
    for cen in centres.values():
        r = np.sqrt((axes[0][:, None, None] - cen[0]) ** 2 + (axes[1][None, :, None] - cen[1]) ** 2
                    + (axes[2][None, None, :] - cen[2]) ** 2)
        np.minimum(r_near, r.astype(np.float32), out=r_near)

    # Flow domain: the connected piece of (chamber, passages, air within pad_mm) that holds the chamber.
    domain = fluid & (chamber | (code > 0) | (r_near <= pad_mm))
    if cut_cells:                                        # two air cells may share a closed face: follow the links
        count = int(domain.sum())
        index = np.full(shape, -1, np.int64)
        index[domain] = np.arange(count)
        rows, cols = [], []
        for a in range(3):
            both = (index[low_side[a]] >= 0) & (index[high_side[a]] >= 0) & (aperture[a][low_side[a]] > 0.0)
            rows.append(index[low_side[a]][both])
            cols.append(index[high_side[a]][both])
        graph = sparse.coo_matrix((np.ones(sum(r_.size for r_ in rows), np.int8),
                                   (np.concatenate(rows), np.concatenate(cols))), shape=(count, count))
        _, piece = csgraph.connected_components(graph.tocsr(), directed=False)
        keep = np.zeros(shape, bool)
        keep[domain] = piece == int(np.bincount(piece[index[chamber]]).argmax())
        domain = keep
        del index, rows, cols, graph, piece, keep
    else:
        labels, _ = ndimage.label(domain)
        votes = np.bincount(labels[chamber])
        votes[0] = 0
        domain = labels == int(votes.argmax())
        del labels
    dropped = int((chamber & ~domain).sum())
    chamber &= domain
    n = int(domain.sum())
    index = np.full(shape, -1, np.int32)
    index[domain] = np.arange(n, dtype=np.int32)

    # Links between face neighbours (conductance h each, times the face's open fraction in a cut-cell model;
    # the matrix is kept in units of h) and the monopole condition: an air cell just outside the cut gets
    # phi_cell * r_cell / r_outside, i.e. a link to zero potential of strength 1 - r_cell / r_outside.
    link_i, link_j, link_w = [], [], []
    robin = np.zeros(n)
    for a in range(3):
        low, high = low_side[a], high_side[a]
        both = (index[low] >= 0) & (index[high] >= 0)
        if cut_cells:
            both &= aperture[a][low] > 0.0
            link_w.append(aperture[a][low][both].astype(float))
        link_i.append(index[low][both].astype(np.int64))
        link_j.append(index[high][both].astype(np.int64))
        for me, out in ((low, high), (high, low)):
            cut = (index[me] >= 0) & fluid[out] & ~domain[out] & (r_near[out] > pad_mm)
            if cut.any():
                weight = 1.0 - r_near[me][cut].astype(float) / r_near[out][cut]
                if cut_cells:
                    weight *= aperture[a][low][cut]
                robin += np.bincount(index[me][cut], weights=weight, minlength=n)
    link_i = np.concatenate(link_i)
    link_j = np.concatenate(link_j)
    link_w = np.concatenate(link_w) if cut_cells else np.ones(link_i.size)
    del aperture
    if not robin.any():
        raise ValueError("the chamber has no air path to the outside (openings blocked?)")
    t_assembled = time.perf_counter()
    levels = _build_hierarchy(link_i, link_j, link_w, robin,
                              [ax.astype(np.int64) for ax in np.nonzero(domain)])
    t_hierarchy = time.perf_counter()

    cells_volume = float(chamber.sum()) * h ** 3         # the source is spread over the chamber cells
    volume = cells_volume
    if cut_cells:                                        # the spring is the true chamber volume, cut cells included
        volume = float(np.asarray(vox["chamber_fill"], float).sum()) * h ** 3 * float(chamber.sum()) / n_chamber_given
    source = index[chamber]
    b = np.zeros(n)
    b[source] = h * h / cells_volume                     # (h A) phi = h^3 / V per chamber cell: unit total flow
    phi, iterations, residual = _pcg(levels, b, tol, maxiter)
    t_solved = time.perf_counter()

    g_solved = 1.0 / float(phi[source].mean())
    g_total = g_solved + extra_G_mm
    k_scale = c * 1e3 / (2.0 * math.pi)

    # Flow through each passage: net flow from chamber cells into that passage's cells.
    is_chamber = chamber[domain]
    passage = code[domain]
    flow = (phi[link_i] - phi[link_j]) * link_w * h      # from i to j
    out_i = is_chamber[link_i] & ~is_chamber[link_j]
    out_j = is_chamber[link_j] & ~is_chamber[link_i]
    q = {}
    for number, name in enumerate(passages, start=1):
        q[name] = float(flow[out_i & (passage[link_j] == number)].sum()
                        - flow[out_j & (passage[link_i] == number)].sum())
    unassigned = 1.0 - sum(q.values())
    shares_by = "chamber-face"
    if abs(unassigned) > 0.02:                           # passages do not touch the chamber: use through-flow
        shares_by = "through-flow"
        for number, name in enumerate(passages, start=1):
            edge = (passage[link_i] == number) != (passage[link_j] == number)
            q[name] = 0.5 * float(np.abs(flow[edge]).sum())
    q_sum = sum(q.values())
    solved_part = g_solved / g_total
    shares = {name: solved_part * value / q_sum for name, value in q.items()}
    if extra_G_mm:
        shares["lumped"] = extra_G_mm / g_total

    # Second-order check: Rayleigh quotient with compressible chamber AND passage air, incompressible outside.
    compressible = np.where(is_chamber, volume / cells_volume, (passage > 0).astype(float))
    k2 = (1.0 / g_solved) / (h ** 3 * float((compressible * phi ** 2).sum()))

    out = {
        "f_hz": k_scale * math.sqrt(g_total / volume),
        "G_mm": g_total,
        "V_mm3": volume,
        "shares": shares,
        "G_openings_mm": {name: share * g_total for name, share in shares.items()},
        "iterations": iterations,
        "residual": residual,
        "h": h,
        "f_rayleigh_hz": k_scale * math.sqrt(k2 * g_total / g_solved),
        "flux_unassigned": unassigned,
        "shares_by": shares_by,
        "V_dropped_mm3": dropped * h ** 3,
        "cut_cells": bool(cut_cells),
        "cells": n,
        "levels": [lev.n for lev in levels],
        "pad_mm": float(pad_mm),
        "centres_mm": {name: tuple(float(v) for v in cen) for name, cen in centres.items()},
        "seconds": {"assemble": t_assembled - t_start, "hierarchy": t_hierarchy - t_assembled,
                    "solve": t_solved - t_hierarchy, "total": time.perf_counter() - t_start},
    }
    if return_field:
        field = np.full(shape, np.nan, np.float32)
        field[domain] = phi
        out["field"] = {"phi": field, "origin": tuple(float(v) for v in origin + np.array(lo) * h), "h": h}
    return out


def richardson(values, hs, order=1.0):
    """Extrapolate a quantity computed at voxel sizes `hs` to h = 0, assuming error ~ h^order: least-squares
    line through (h^order, value), returned at 0. The solver's error on a staircase boundary is first order.
    Only meaningful when the geometry at each h is the same shape (features that alias on the grid add
    scatter that no extrapolation removes: check the residual scatter yourself)."""
    x = np.asarray(hs, float) ** order
    slope, intercept = np.polyfit(x, np.asarray(values, float), 1)
    return float(intercept)


def convergence_study(make_vox, hs=(0.8, 0.6, 0.5), **solve_kwargs):
    """Solve `make_vox(h)` at each voxel size. Returns {"rows": [{"h", "f_hz", "value", "G_mm", "V_mm3",
    "cells", "seconds"}], "limit": first-order extrapolation of "value" to h = 0, "spread_pct": (max - min) /
    mean of "value", "normalised": bool}.

    "value" is f_hz, or f_hz / theory when the model carries meta["theory_f_hz"] (the synthetic fixtures round
    their dimensions to whole voxels, so their geometry, and with it the theory, differs slightly between
    grids; the ratio is what converges)."""
    rows = []
    normalised = False
    for h in hs:
        vox = make_vox(h)
        r = solve_resonance(vox, **solve_kwargs)
        theory = vox.get("meta", {}).get("theory_f_hz")
        normalised = theory is not None
        rows.append({"h": h, "f_hz": r["f_hz"], "value": r["f_hz"] / theory if normalised else r["f_hz"],
                     "G_mm": r["G_mm"], "V_mm3": r["V_mm3"], "cells": r["cells"],
                     "seconds": r["seconds"]["total"]})
    values = [row["value"] for row in rows]
    return {"rows": rows, "limit": richardson(values, hs), "normalised": normalised,
            "spread_pct": 100.0 * (max(values) - min(values)) / float(np.mean(values))}


def passage_section_mm2(mask, h, axis=2):
    """Voxelised cross-section (mm^2) of a straight passage whose bore runs along grid `axis` (2 = vertical):
    the median number of flagged voxels per slice times h^2. Compare with the designed area: a boolean grid
    holds a 2 mm bore's area only to -43 ... +13 % at h = 0.8-0.4 [RUN]."""
    counts = np.asarray(mask, bool).sum(axis=tuple(a for a in range(3) if a != axis))
    counts = counts[counts > 0]
    if counts.size == 0:
        return 0.0
    return float(np.median(counts)) * h * h


def rescale_opening(conductance_mm, voxel_area_mm2, true_area_mm2, t_mm):
    """Conductance of an opening as DESIGNED, from the conductance the solver found for it as VOXELISED:
    back out the end factor of the voxel opening (`end_factor`, with its voxel area), then re-apply
    G = A/(t + k r_eq) with the true area. Use on `solve_resonance(...)["G_openings_mm"][name]` for the finger
    hole and the vent, then re-total with `helmholtz_hz(V, [G_window, G_hole', G_vent'])`. It removes the area
    aliasing; the staircase bias (-1 ... -5 % in that opening's G, less on finer grids) remains."""
    k = end_factor(conductance_mm, voxel_area_mm2, t_mm)
    return conductance(true_area_mm2, t_mm, k)


def truncation_study(vox, pads=(15.0, 30.0, 60.0), **solve_kwargs):
    """Solve one model at several truncation radii. Returns {"rows": [{"pad_mm", "f_hz", "G_mm", "cells",
    "seconds"}], "spread_pct"}. NOTE: a fixture whose flange is only modelled out to some radius (see
    `fixture_box`) changes its PHYSICS when pad_mm exceeds that radius."""
    rows = []
    for pad in pads:
        r = solve_resonance(vox, pad_mm=pad, **solve_kwargs)
        rows.append({"pad_mm": pad, "f_hz": r["f_hz"], "G_mm": r["G_mm"], "cells": r["cells"],
                     "seconds": r["seconds"]["total"]})
    f = [row["f_hz"] for row in rows]
    return {"rows": rows, "spread_pct": 100.0 * (max(f) - min(f)) / float(np.mean(f))}


# --------------------------------------------------------------------------------------------------------
# 3. Synthetic fixtures and analytic cases for the solver
# --------------------------------------------------------------------------------------------------------

def _grid(lo, counts, h):
    """Cell-centre coordinate arrays (broadcastable) of a grid with low corner `lo`."""
    x = lo[0] + (np.arange(counts[0]) + 0.5) * h
    y = lo[1] + (np.arange(counts[1]) + 0.5) * h
    z = lo[2] + (np.arange(counts[2]) + 0.5) * h
    return x[:, None, None], y[None, :, None], z[None, None, :]


def _bore_cut_cells(vox, radius_mm, first_layer):
    """Add the cut-cell keys to a fixture whose only curved surface is a round vertical bore of `radius_mm` on
    the z axis, present from cell layer `first_layer` to the top of the arrays. Everything else in these
    fixtures lies on cell faces, so the apertures start as the boolean model's (1 between two air cells) and
    only the faces the bore's wall crosses are overwritten: a horizontal face by the share of its square
    inside the circle (16 x 16 sub-samples), a vertical one by the share of its chord inside it (exact)."""
    h = vox["h"]
    air = ~(vox["solid"] | vox["windway"])
    low_side, high_side = _face_sides()
    aperture = []
    for a in range(3):
        ap = np.ones(air.shape, np.float32)
        ap[low_side[a]] = air[low_side[a]] & air[high_side[a]]
        ap[high_side[a]][(slice(None),) * a + (slice(-1, None),)] = air[(slice(None),) * a + (slice(-1, None),)]
        aperture.append(ap)
    nx, ny, nz = air.shape
    x = vox["origin"][0] + (np.arange(nx) + 0.5) * h
    y = vox["origin"][1] + (np.arange(ny) + 0.5) * h
    sub = (np.arange(16) + 0.5) / 16.0 - 0.5
    xs = (x[:, None] + sub[None, :] * h).ravel()
    ys = (y[:, None] + sub[None, :] * h).ravel()
    inside = (xs[:, None] ** 2 + ys[None, :] ** 2 < radius_mm ** 2).reshape(nx, 16, ny, 16)
    disc = inside.mean(axis=(1, 3)).astype(np.float32)                 # share of each horizontal face in the circle
    aperture[2][:, :, max(first_layer - 1, 0):] = disc[:, :, None]

    def chord(face, centre):
        """Share of the segment centre +- h/2 that lies inside the circle, on the line at offset `face`."""
        half = np.sqrt(np.maximum(radius_mm ** 2 - face[:, None] ** 2, 0.0))
        return (np.clip(np.minimum(centre[None, :] + 0.5 * h, half) - np.maximum(centre[None, :] - 0.5 * h, -half),
                        0.0, h) / h).astype(np.float32)
    aperture[0][:, :, first_layer:] = chord(x + 0.5 * h, y)[:, :, None]
    aperture[1][:, :, first_layer:] = chord(y + 0.5 * h, x).T[:, :, None]
    vox["aperture"] = tuple(aperture)
    vox["chamber_fill"] = vox["chamber"].astype(np.float32)
    return vox


def box_hole_theory(hole_area_mm2, t_mm, cavity_section_mm2, cavity_depth_mm):
    """Theory for a prismatic cavity with a round hole in the middle of one end wall of thickness t, the outside
    of that wall being a large flange:

        1/G = [ t + 0.8217 a + 0.8217 a (1 - 1.25 sqrt(A_hole / A_cavity)) ] / A_hole + H / (3 A_cavity)

    outer end: flanged pipe end, `K_END_FLANGED` (Nomura / Norris-Sheng [KNOW]); inner end: the same reduced
    by Ingard's confinement factor (1 - 1.25 xi) for an orifice in a duct, xi = sqrt(area ratio) < 0.4
    (U. Ingard, 'On the theory and design of acoustic resonators', JASA 25, 1953 [KNOW, not re-fetched]);
    last term: the cavity's own axial inertance for a uniform source (exact for plane flow; NOTES section 5).
    The two end corrections are long-pipe values, so for t < a the sum is up to about 4 % of the end length
    too long (thin-wall limit 1.571 a against 1.643 a): the theory itself is good to about 1-2 % in G.
    Returns G in mm."""
    a = equal_area_radius(hole_area_mm2)
    inner = K_END_FLANGED * a * (1.0 - 1.25 * math.sqrt(hole_area_mm2 / cavity_section_mm2))
    return 1.0 / ((t_mm + K_END_FLANGED * a + inner) / hole_area_mm2 + cavity_depth_mm / (3.0 * cavity_section_mm2))


#: Truncation radius the synthetic fixtures are built for: their flange is modelled out to this radius plus
#: two voxels, so solving them with this pad_mm sees an infinite flange (what the theory assumes).
FIXTURE_PAD_MM = 20.0


def fixture_box(h=0.8, hole_area_scale=1.0, side_mm=40.0, depth_mm=32.0, wall_mm=3.2, hole_d_mm=8.0, cut_cells=False):
    """Tiny synthetic voxel model: a box cavity under a thick lid with one round hole (flagged "window"), set in
    a block wide enough to act as an infinite flange for pad_mm = `FIXTURE_PAD_MM`. About 0.1 s at h = 0.8.

    `hole_area_scale` scales the hole AREA (0.5 = the known-bad twin for a gate's controls: it sounds about
    25 % lower, by theory and by the solver; the as-voxelised area ratio is 0.45 at h = 0.8). Dimensions are rounded to whole voxels; "meta" carries the as-voxelised
    geometry and the theory for exactly that geometry:
        {"side_mm", "depth_mm", "wall_mm", "hole_area_mm2", "pad_mm", "theory_G_mm", "theory_f_hz" (at C_AIR)}.
    cut_cells=True adds "aperture" and "chamber_fill" for the round hole (`_bore_cut_cells`); the hole area in
    the theory is then the true circle's, not the voxelised one.
    """
    n_side = 2 * int(round(side_mm / (2.0 * h)))
    n_depth = int(round(depth_mm / h))
    n_wall = max(1, int(round(wall_mm / h)))
    n_margin = int(math.ceil((FIXTURE_PAD_MM - n_side * h / 2.0) / h)) + 2
    n_margin = max(n_margin, 2)
    n_lat = n_side + 2 * n_margin
    counts = (n_lat, n_lat, 1 + n_depth + n_wall)
    lo = (-n_lat * h / 2.0, -n_lat * h / 2.0, -(1 + n_depth) * h)
    X, Y, Z = _grid(lo, counts, h)
    half = n_side * h / 2.0
    chamber = (np.abs(X) < half) & (np.abs(Y) < half) & (Z > -n_depth * h) & (Z < 0.0)
    radius = 0.5 * hole_d_mm * math.sqrt(hole_area_scale)
    hole = (X * X + Y * Y < radius * radius) & (Z > 0.0)
    solid = ~(chamber | hole)
    empty = np.zeros(counts, bool)
    area = math.pi * radius * radius if cut_cells else float(hole[:, :, -1].sum()) * h * h
    g = box_hole_theory(area, n_wall * h, (n_side * h) ** 2, n_depth * h)
    volume = float(chamber.sum()) * h ** 3
    vox = {"origin": lo, "h": float(h), "solid": solid, "chamber": chamber, "window": hole,
           "hole": empty, "vent": empty, "windway": empty,
           "meta": {"side_mm": n_side * h, "depth_mm": n_depth * h, "wall_mm": n_wall * h,
                    "hole_area_mm2": area, "pad_mm": FIXTURE_PAD_MM, "theory_G_mm": g,
                    "theory_f_hz": helmholtz_hz(volume, g)}}
    return _bore_cut_cells(vox, radius, 1 + n_depth) if cut_cells else vox


def fixture_flanged_tube(h=0.8, radius_mm=5.0, length_mm=20.0, cut_cells=False):
    """A blind round bore in a flanged block; the top voxel layer of the bore is the "window" passage and the
    rest is the chamber. The flow in the bore is exactly one-dimensional, so

        1/G = [ (L - p)/3 + p + 0.8217 a ] / A        (p = passage length = one voxel)

    is exact up to the flanged end correction `K_END_FLANGED` itself: the sharpest test of the exterior
    treatment. "meta": {"area_mm2", "length_mm", "pad_mm", "theory_G_mm"}."""
    n_len = int(round(length_mm / h))
    n_half = int(math.ceil(FIXTURE_PAD_MM / h)) + 2
    counts = (2 * n_half, 2 * n_half, 1 + n_len)
    lo = (-n_half * h, -n_half * h, -(1 + n_len) * h)
    X, Y, Z = _grid(lo, counts, h)
    bore = (X * X + Y * Y < radius_mm * radius_mm) & (Z > -n_len * h)
    passage = bore & (Z > -h)
    chamber = bore & ~passage
    empty = np.zeros(counts, bool)
    area = math.pi * radius_mm ** 2 if cut_cells else float(passage[:, :, -1].sum()) * h * h
    a = equal_area_radius(area)
    g = area / ((n_len - 1) * h / 3.0 + h + K_END_FLANGED * a)
    vox = {"origin": lo, "h": float(h), "solid": ~bore, "chamber": chamber,
           "window": passage, "hole": empty, "vent": empty, "windway": empty,
           "meta": {"area_mm2": area, "length_mm": n_len * h, "pad_mm": FIXTURE_PAD_MM, "theory_G_mm": g}}
    return _bore_cut_cells(vox, radius_mm, 1) if cut_cells else vox


def fixture_thin_baffle(h=0.8, radius_mm=6.0, shell_inner_mm=18.0, shell_outer_mm=24.0, cut_cells=False):
    """A round hole in a plate ONE voxel thick, open half-space on the outside, and on the inside a rigid
    hemispherical bowl whose outer shell (shell_inner < r < shell_outer) is the uniform source ("chamber").

    Inside the shell the flow is the aperture's half-space flow to within (a/r)^2, so the conductance of the
    aperture alone, between the two infinities, follows from the solved G as

        1/G_aperture = 1/G - S + 1/(2 pi R1),   S = mean over the shell of [phi(r) - phi(R1)] for radial flow

    (the shell term S and the missing inner far field 1/(2 pi R1) are closed-form: `meta["shell_term_per_mm"]`,
    `meta["inner_far_per_mm"]`). Rayleigh: G_aperture -> 2a = d as the plate thickness -> 0 and, for thickness
    t, A/(t + 16a/(3 pi)) < G_aperture < A/(t + pi a/2) (Theory of Sound section 306 [KNOW]).
    Solve with pad_mm = meta["pad_mm"]. "meta": {"area_mm2", "t_mm", "pad_mm", "shell_term_per_mm",
    "inner_far_per_mm", "G_lower_mm", "G_upper_mm", "G_thin_mm"}."""
    pad = shell_inner_mm + 4.0
    n_half = int(math.ceil(max(pad, shell_outer_mm) / h)) + 2
    n_below = int(math.ceil(shell_outer_mm / h)) + 1
    counts = (2 * n_half, 2 * n_half, n_below + 1)
    lo = (-n_half * h, -n_half * h, -n_below * h)
    X, Y, Z = _grid(lo, counts, h)
    r = np.sqrt(X * X + Y * Y + Z * Z)
    inside = Z < 0.0
    bowl = inside & (r < shell_outer_mm)
    chamber = bowl & (r >= shell_inner_mm)
    hole = (X * X + Y * Y < radius_mm * radius_mm) & ~inside
    empty = np.zeros(counts, bool)
    area = math.pi * radius_mm ** 2 if cut_cells else float(hole[:, :, -1].sum()) * h * h
    a = equal_area_radius(area)
    r1, r2 = shell_inner_mm, shell_outer_mm
    # phi(r) - phi(R1) = [R2^3 (1/R1 - 1/r) - (r^2 - R1^2)/2] / (2 pi (R2^3 - R1^3)); its r^2-weighted mean:
    d3 = r2 ** 3 - r1 ** 3
    weighted = ((r2 ** 3 / r1 + r1 * r1 / 2.0) * d3 / 3.0 - r2 ** 3 * (r2 * r2 - r1 * r1) / 2.0
                - (r2 ** 5 - r1 ** 5) / 10.0)
    shell_term = weighted / (2.0 * math.pi * d3) / (d3 / 3.0)
    vox = {"origin": lo, "h": float(h), "solid": ~(bowl | hole), "chamber": chamber, "window": hole,
           "hole": empty, "vent": empty, "windway": empty,
           "meta": {"area_mm2": area, "t_mm": float(h), "pad_mm": pad, "shell_term_per_mm": shell_term,
                    "inner_far_per_mm": 1.0 / (2.0 * math.pi * r1),
                    "G_lower_mm": area / (h + 2.0 * K_END_FLANGED_PISTON * a),
                    "G_upper_mm": area / (h + K_THIN_APERTURE * a), "G_thin_mm": 2.0 * a}}
    return _bore_cut_cells(vox, radius_mm, n_below) if cut_cells else vox


def thin_baffle_conductance(h, cut_cells=False, **solve_kwargs):
    """Conductance (mm) of the one-voxel-thick baffle aperture at voxel size h, corrected to 'between two
    infinities' as described in `fixture_thin_baffle`, together with the fixture's meta."""
    vox = fixture_thin_baffle(h, cut_cells=cut_cells)
    meta = vox["meta"]
    r = solve_resonance(vox, pad_mm=meta["pad_mm"], **solve_kwargs)
    inv = 1.0 / r["G_mm"] - meta["shell_term_per_mm"] + meta["inner_far_per_mm"]
    return 1.0 / inv, meta


def fixture_vessel(h=0.8, hole_open=True, vent_open=True):
    """A body-sized stand-in for the pigeon that needs no project geometry: an ellipsoidal shell
    120 x 70 x 70 mm with a 2.4 mm wall (chamber about 250 cm^3), a 7 x 8 mm window in the +Y flank, a 7 mm
    finger hole and a 2.4 mm vent bored vertically through the top. For timing, flux shares and the
    open/closed logic; there is no theory value for it."""
    semi = np.array([60.0, 35.0, 35.0])
    wall = 2.4
    counts = tuple(int(math.ceil(2.0 * s / h)) + 2 for s in semi)
    lo = tuple(-c_ * h / 2.0 for c_ in counts)
    X, Y, Z = _grid(lo, counts, h)
    outer = (X / semi[0]) ** 2 + (Y / semi[1]) ** 2 + (Z / semi[2]) ** 2 < 1.0
    inner_semi = semi - wall
    chamber = (X / inner_semi[0]) ** 2 + (Y / inner_semi[1]) ** 2 + (Z / inner_semi[2]) ** 2 < 1.0
    shell = outer & ~chamber
    window = shell & (np.abs(X + 30.0) < 3.5) & (np.abs(Z) < 4.0) & (Y > 0.0)
    hole = shell & ((X - 15.0) ** 2 + Y * Y < 3.5 ** 2) & (Z > 0.0)
    vent = shell & ((X + 20.0) ** 2 + Y * Y < 1.2 ** 2) & (Z > 0.0)
    if not hole_open:
        hole = np.zeros(counts, bool)
    if not vent_open:
        vent = np.zeros(counts, bool)
    return {"origin": lo, "h": float(h), "solid": shell & ~(window | hole | vent), "chamber": chamber,
            "window": window, "hole": hole, "vent": vent, "windway": np.zeros(counts, bool)}


#: Tolerance (percent, on FREQUENCY) the analytic cases must meet at h <= 0.8 mm. Measured [RUN]: box-hole
#: -1.1 % (h = 0.8) ... -0.5 % (0.5); flanged tube -0.6 ... -0.3 %; thin-baffle limit -0.8 %. The box theory is
#: itself only good to about 1 % in f. 2.5 leaves a margin over the measured errors; lost: 1.0 (fails at
#: h = 0.8 on the staircase bias alone, which is a known property, not a fault) and 5.0 (a 10 % error in the
#: hole area moves f by about 3.5 % [CALC]: it would pass).
ANALYTIC_TOL_PCT = 2.5


def analytic_cases(h=0.8, cut_cells=False, **solve_kwargs):
    """Run the solver against theory at voxel size h (cut_cells=True: the same fixtures as cut-cell models,
    the theory then evaluated for the true circle). Returns a list of rows
        {"case", "theory", "G_mm", "G_theory_mm", "err_G_pct", "err_f_pct", "tol_f_pct", "bounds_mm", "ok",
         "seconds"}
    (frequency goes as sqrt(G), so err_f = sqrt(G/G_theory) - 1). Cases:
      box-hole       `fixture_box` against `box_hole_theory`
      flanged-tube   `fixture_flanged_tube` (exact but for the 0.8217 a flanged end correction)
      thin-baffle    `fixture_thin_baffle`, one-voxel plate: compared with Rayleigh's UPPER bound
                     A/(t + pi a/2) (to which a thin plate tends) and required to lie inside both bounds
                     widened by the tolerance; `thin_baffle_limit` does the t -> 0 extrapolation to G = 2a.
    """
    rows = []

    def add(case, theory, g, g_theory, seconds, bounds=None):
        err_f = 100.0 * (math.sqrt(g / g_theory) - 1.0)
        ok = abs(err_f) <= ANALYTIC_TOL_PCT if bounds is None else bounds[0] <= g <= bounds[1]
        rows.append({"case": case, "theory": theory, "G_mm": g, "G_theory_mm": g_theory,
                     "err_G_pct": 100.0 * (g / g_theory - 1.0), "err_f_pct": err_f,
                     "tol_f_pct": ANALYTIC_TOL_PCT, "bounds_mm": bounds, "seconds": seconds, "ok": bool(ok)})

    vox = fixture_box(h, cut_cells=cut_cells)
    r = solve_resonance(vox, pad_mm=vox["meta"]["pad_mm"], **solve_kwargs)
    add("box-hole", "t + 0.8217a + 0.8217a(1 - 1.25 xi), + H/(3 A_cav)", r["G_mm"], vox["meta"]["theory_G_mm"],
        r["seconds"]["total"])
    vox = fixture_flanged_tube(h, cut_cells=cut_cells)
    r = solve_resonance(vox, pad_mm=vox["meta"]["pad_mm"], **solve_kwargs)
    add("flanged-tube", "(L - p)/3 + p + 0.8217a", r["G_mm"], vox["meta"]["theory_G_mm"], r["seconds"]["total"])
    t0 = time.perf_counter()
    g, meta = thin_baffle_conductance(h, cut_cells, **solve_kwargs)
    slack = (1.0 + ANALYTIC_TOL_PCT / 100.0) ** 2
    add("thin-baffle (t = h)", "Rayleigh: A/(t + 16a/3pi) < G < A/(t + pi a/2)", g, meta["G_upper_mm"],
        time.perf_counter() - t0, bounds=(meta["G_lower_mm"] / slack, meta["G_upper_mm"] * slack))
    return rows


def thin_baffle_limit(hs=(0.8, 0.6, 0.5), cut_cells=False, **solve_kwargs):
    """The thin-baffle result G = 2a = d: solve the one-voxel plate at each h (so thickness and voxel size go to
    zero together), normalise by 2 * a_eq of the voxelised hole and extrapolate linearly to h = 0.
    Returns {"rows": [{"h", "G_mm", "G_over_2a"}], "limit_G_over_2a", "err_f_pct", "tol_f_pct", "ok"}."""
    rows = []
    for h in hs:
        g, meta = thin_baffle_conductance(h, cut_cells, **solve_kwargs)
        rows.append({"h": h, "G_mm": g, "G_over_2a": g / meta["G_thin_mm"]})
    limit = richardson([row["G_over_2a"] for row in rows], hs)
    err_f = 100.0 * (math.sqrt(limit) - 1.0)
    return {"rows": rows, "limit_G_over_2a": limit, "err_f_pct": err_f, "tol_f_pct": ANALYTIC_TOL_PCT,
            "ok": bool(abs(err_f) <= ANALYTIC_TOL_PCT)}


# --------------------------------------------------------------------------------------------------------
# 4. Published instruments for the closed form
# --------------------------------------------------------------------------------------------------------

#: Published cases for the CLOSED FORM (NOTES sections 3 and 8.3). `openings` are (area_mm2, t_mm, k).
#: `expected_hz` is what `validation_case_hz` must return (a regression on the formula); `measured_hz` is what
#: the real object did (None when the source only calculated); `band_pct` is the honest error band for that
#: kind of object. kind: "good" (model must be inside the band), "honest" (a voiced window: inside the wide
#: uncalibrated band, error shown as it is), "known_bad" (the lumped model MUST miss by more than the band:
#: a gate's proof that the comparison can fail).
VALIDATION_CASES = [
    {"id": "V1_tea_bottle", "kind": "good", "volume_mm3": 435000.0, "openings": [(660.52, 70.0, K_BOTTLE_NECK)],
     "c": 344.0, "expected_hz": 222.7, "measured_hz": 223.4, "band_pct": 3.0,
     "source": "Monteiro et al., arXiv:1805.04014 (neck d 29.0, L 70; fit of f^2 vs 1/V, +-1.5 %)"},
    {"id": "V2_wine_750", "kind": "good", "volume_mm3": 750000.0, "openings": [(314.16, 90.0, K_BOTTLE_NECK)],
     "c": 343.0, "expected_hz": 109.0, "measured_hz": 106.0, "band_pct": 3.0,
     "source": "J. D. Cook, johndcook.com/blog/2022/07/20/helmholtz-resonator/ (phone app)"},
    {"id": "V3_unsw_sphere", "kind": "good", "volume_mm3": 2920000.0, "openings": [(830.0, 80.0, 1.538)],
     "c": 343.0, "expected_hz": 89.8, "measured_hz": None, "reference_hz": 90.0, "band_pct": 0.5,
     "source": "phys.unsw.edu.au/jw/Helmholtz.html (the page's own calculation: regression only)"},
    {"id": "V4_abs_alto_C5_thesis_model", "kind": "honest", "volume_mm3": 90000.0,
     "openings": [(62.21, 6.8, K_END_FLANGED_PISTON), (7.55, 6.8, K_END_FLANGED_PISTON),
                  (5.73, 6.8, K_END_FLANGED_PISTON)],
     "c": 343.0, "expected_hz": 499.4, "measured_hz": 529.76, "band_pct": 10.0,
     "source": "Csoka 2018, BME thesis, 12-hole ABS alto C ocarina, mouth-blown spectrum; fingering inferred"},
    {"id": "V4_abs_alto_C5_flanged_both_ends", "kind": "honest", "volume_mm3": 90000.0,
     "openings": [(62.21, 6.8, 2.0 * K_END_FLANGED_PISTON), (7.55, 6.8, 2.0 * K_END_FLANGED_PISTON),
                  (5.73, 6.8, 2.0 * K_END_FLANGED_PISTON)],
     "c": 343.0, "expected_hz": 436.9, "measured_hz": 529.76, "band_pct": 20.0,
     "source": "same instrument, the plain 'flanged both ends' choice: the worst defensible end correction"},
    {"id": "V5_night_soprano_noncompact", "kind": "honest", "volume_mm3": 9425.0,
     "openings": [(30.0, 1.5, 2.0 * K_END_FLANGED_PISTON)], "c": 340.0, "cavity_len_mm": 86.0,
     "position": NONCOMPACT_END, "expected_hz": 799.0, "measured_hz": 880.0, "band_pct": 10.0,
     "source": "Okada et al., ISMA 2019 (Night by Noble soprano C, lowest note A5), with the tube correction"},
    {"id": "V5_night_soprano_lumped_KNOWN_BAD", "kind": "known_bad", "volume_mm3": 9425.0,
     "openings": [(30.0, 1.5, 2.0 * K_END_FLANGED_PISTON)], "c": 340.0, "expected_hz": 1175.0,
     "measured_hz": 880.0, "band_pct": 10.0,
     "source": "same instrument, purely lumped: an 86 mm cavity of 1.1 cm^2 section is a stopped pipe"},
]

#: How closely `validation_case_hz` must reproduce `expected_hz` (percent). The expected values are quoted to
#: 4 significant figures in NOTES, so 0.1 % is rounding, not physics.
REGRESSION_TOL_PCT = 0.1


def validation_case_hz(case):
    """Closed-form frequency of one `VALIDATION_CASES` entry."""
    g = sum(conductance(a, t, k) for a, t, k in case["openings"])
    f = helmholtz_hz(case["volume_mm3"], g, case["c"])
    if case.get("cavity_len_mm"):
        f *= noncompact_factor(g, case["volume_mm3"], case["cavity_len_mm"], case["position"])
    return f


def check_validation_cases():
    """Evaluate every published case. Returns rows {"id", "kind", "model_hz", "expected_hz", "measured_hz",
    "err_pct" (model vs measured, or vs the source's own calculation), "band_pct", "regression_ok", "ok"}.
    ok = the formula still returns the recorded value AND the error is inside the band (outside it for the
    known-bad case)."""
    rows = []
    for case in VALIDATION_CASES:
        f = validation_case_hz(case)
        reference = case["measured_hz"] if case["measured_hz"] is not None else case["reference_hz"]
        err = 100.0 * (f / reference - 1.0)
        regression_ok = abs(f / case["expected_hz"] - 1.0) * 100.0 <= REGRESSION_TOL_PCT
        inside = abs(err) <= case["band_pct"]
        rows.append({"id": case["id"], "kind": case["kind"], "model_hz": f, "expected_hz": case["expected_hz"],
                     "measured_hz": case["measured_hz"], "err_pct": err, "band_pct": case["band_pct"],
                     "regression_ok": bool(regression_ok),
                     "ok": bool(regression_ok and (inside != (case["kind"] == "known_bad")))})
    return rows
