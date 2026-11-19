# Acoustics + voicing notes: one-hole pigeon vessel flute (340 Hz closed / 470 Hz open)

Scope: quantitative design rules, sources, validation cases, worked numbers. Research date 2026-11-19.
Scratch (all mine, nothing written to the project or to nopekit):

- Evaluator + all arithmetic below: `/tmp/claude-1000/-home-neuman-my-thing/cbf22764-116a-4870-bc2f-90231ddadd43/scratchpad/work/acoustics/vessel_flute.py`
  (run: `python3 /tmp/claude-1000/-home-neuman-my-thing/cbf22764-116a-4870-bc2f-90231ddadd43/scratchpad/work/acoustics/vessel_flute.py`, pure stdlib, prints every number quoted in sections 3, 7, 8)
- Fingering reverse-engineering of the thesis ocarina: `/tmp/claude-1000/-home-neuman-my-thing/cbf22764-116a-4870-bc2f-90231ddadd43/scratchpad/work/acoustics/csoka_fit.py`
- Downloaded source PDFs/text (untrusted, read-only): `/tmp/claude-1000/-home-neuman-my-thing/cbf22764-116a-4870-bc2f-90231ddadd43/scratchpad/work/acoustics/dl/`
  (`csoka.pdf`, `isma2019.pdf`, `arxiv0911.pdf`, `printone.pdf`, `tea.pdf`, `price_arxiv.pdf`, `price2014.pdf`, `auvray.pdf`, `fletcher1976.pdf`, `mckinnon.pdf`, `bridges.pdf`, `francis.pdf`)

Tags: [SRC] = read in a fetched source this session; [CALC] = my arithmetic (script above); [KNOW] = textbook knowledge NOT re-fetched this session (treat as lower confidence); [NOT FOUND] = searched, nothing citable.

---

## 0. Bottom line (read this first)

1. Pitch law (lumped): `f = c/(2*pi) * sqrt( sum_i G_i / V )`, `G_i = A_i / (t_i + k_i * r_eq_i)`, `r_eq = sqrt(A/pi)`. Use equal-area radius for non-circular openings, not hydraulic diameter (section 1.2).
2. **The finger hole is the well-predicted part; the voiced window is the badly-predicted part.**
   `f_open^2 - f_closed^2 = (c/2pi)^2 * G_hole / V` — independent of the window model. So: get the closed note right by measurement/trim, size the hole from this rule.
3. Honest uncalibrated error band of the closed-form model on real, mouth-blown ocarinas: **about +-10 % in frequency typical (+-170 cents), 15-20 % worst case**, and the sign is NOT consistent between published instruments (section 3). Interval/ratio error is much smaller (about +-1...3 % in ratio). After ONE calibration print (measure closed pitch, back out the window's effective length) expect +-3 % (+-50 cents). Blowing pressure alone moves pitch by +-30...60 cents.
4. 340 Hz in a palm-size chamber is at the small-chamber limit: `G_closed = V*(2*pi*f/c)^2` = 3.81 mm at 100 cm3, 5.72 mm at 150 cm3. A playable window (cut-up 6-8 mm, area >= ~36-60 mm2) then needs V ~ 110-150 cm3 with a plain 2-3 mm wall, or a deliberately deep window chimney ("voicing neck", 4.5-6 mm) at 100-125 cm3. Below ~80 cm3 it needs a 6-10 mm neck and will be quiet/breathy (section 6).
5. Finger hole for 340->470 Hz: d = 5.5 mm (V=100 cm3, wall 2.5), 6.5 mm (125 cm3, 2.5), 7.8 mm (150 cm3, 3.0). All sealable by adult and child fingers. +-0.2 mm in hole diameter = +-14...20 cents on the open note.
6. Voicing start values for 340/470 Hz: cut-up (windway exit to labium edge) 7-7.5 mm, window width = windway width 7-8 mm, windway exit height 1.2-1.5 mm (inlet ~2x), windway length >= 20-35 mm, 45 deg x 0.5-0.7 mm chamfers at the exit, labium edge on the windway mid-plane (offset 0...+0.1 mm), ramp 15-30 deg, edge <= 0.5 mm. Blowing 100-300 Pa, 7-16 L/min, about 60-75 dB SPL at 1 m (estimate).
7. Geometry warnings: keep the longest internal dimension short and do not put the window at the far end of a long cavity (non-compactness flattens the open note more than the closed one: ratio drops 1.38 -> 1.33 for an 80-90 mm cavity blown from the end). A head lobe joined by a narrow passage is a second resonator (616 Hz for a 4 mm x 10 mm passage) — make the head solid or join it with a wide throat.

---

## 1. Helmholtz model for a vessel with several openings

### 1.1 Formula
- `f = c/(2*pi) * sqrt(S/(V*L))` single neck — UNSW Helmholtz page [SRC] https://phys.unsw.edu.au/jw/Helmholtz.html ; Okada et al. ISMA 2019 eq. (2) [SRC] https://pub.dega-akustik.de/ISMA2019/data/articles/000010.pdf ; Wikipedia Helmholtz resonance [SRC] https://en.wikipedia.org/wiki/Helmholtz_resonance
- Several openings: the openings are acoustic masses in parallel on one compliance, so conductances add: `f = c/(2*pi)*sqrt(sum_i(A_i/Leff_i)/V)`. This is the model used (lumped circuit: cavity = capacitance `V/(rho c^2)`, each hole = inductance `rho*L/A + 8*rho*a/(3*pi*A)`, holes in parallel) in Csoka's BME thesis on a real 12-hole ocarina [SRC] https://last.hit.bme.hu/download/rucz/onlab/fuvos_hangszerek/Csoka_Bence_-_Okarina_Szakdolgozat_2018.pdf (section 3.2). Simplified forms `f ∝ sqrt(A_total/V)`: Paley, Bridges 2015 eq. (1) [SRC] https://archive.bridgesmathart.org/2015/bridges2015-559.pdf ; Wikipedia Vessel flute [SRC] https://en.wikipedia.org/wiki/Vessel_flute (cites Benade, Fundamentals of Musical Acoustics pp. 473-476).
- Consequences confirmed by sources: pitch depends on the total open-hole conductance, hole position is (to first order) irrelevant (Pure Ocarinas [SRC] https://pureocarinas.com/how-ocarinas-work ; Kobayashi et al. arXiv:0911.3567 [SRC] https://arxiv.org/pdf/0911.3567); each further hole of equal area gives a smaller interval, `f_h/f_0 = sqrt((A0+Ah)/A0)` (Paley eq. 2 [SRC]).
- Useful exact corollary [CALC]: `f_open^2 = f_closed^2 + (c/2pi)^2 * G_h/V`.

### 1.2 End corrections (the `k` in `Leff = t + k*r`)
| case | value | source |
|---|---|---|
| unflanged pipe end | 0.6133 r (Levine & Schwinger 1948) | [SRC] https://en.wikipedia.org/wiki/End_correction |
| flanged (infinite baffle) end | "0.85 times the radius" | [SRC] UNSW Helmholtz page |
| flanged, piston approximation | 8/(3*pi) r = 0.849 r per end; hole in a wall `L = d + 2*8a/(3*pi)` = d + 1.698 a | [SRC] Okada 2019 (uses it with wall d = 1.5 mm); Kobayashi 2009 eq. (7) |
| neck of a bottle | "0.6 r at the outside end and one radius at the inside end" (sum 1.6 r); guitar sound hole (hole in a plate) "about 1.7 times the radius" | [SRC] UNSW Helmholtz page |
| neck, outer end unflanged | `L' = L + 1.5 a` | [SRC] Monteiro et al. arXiv:1805.04014 (Kinsler & Frey) https://arxiv.org/pdf/1805.04014 |
| Helmholtz neck (flue-pipe mouth rule) | `Leq = Ln + 0.3 D`, D = hydraulic diameter (= 0.6 r for a circle, i.e. ONE unflanged end only) | [SRC] Wikipedia Helmholtz resonance, citing Liljencrants (fonema.se, site dead: not fetched) |
| zero-thickness circular aperture (Rayleigh) | conductivity 2r, i.e. `Leff = (pi/2) r = 1.571 r` | [KNOW] Rayleigh, Theory of Sound §306; used by Printone "Rayleigh's end corrections for a circular aperture on a thin wall [Howe 1998]" [SRC] |
| exact flanged end | 0.8217 r (Nomura / Norris-Sheng) | [KNOW], not fetched |

Design values:
- **Finger hole in a wall of thickness t**: `Leff = t + k_h*r`, `k_h = 1.6` nominal, range 1.46 (inner flanged 0.85 + outer unflanged 0.61) to 1.70 (both flanged). Thin-wall limit 1.571. This is the "t + 1.5...1.7 r" asked about; the spread k_h = 1.46...1.70 moves the open note only +26/-17 cents in the worked sets (section 7).
- **Non-circular openings**: use the equal-area radius `r_eq = sqrt(A/pi)`. Rayleigh's ellipse conductivity is `pi*a/K(e)` [KNOW]; evaluated in my script [CALC]: G_ellipse/G_equal-area-circle = 1.010 (aspect 1.5:1), 1.030 (2:1), 1.076 (3:1), 1.12 (4:1) -> f error of the equal-area rule +0.5 %, +1.5 %, +3.7 %, +5.9 % (real pitch higher than predicted for long slots). So equal-area is fine up to 2:1; do not use hydraulic diameter for a hole in a wall (hydraulic diameter appears only in the single-end 0.3 D rule above). For elongated slots conductance grows toward a perimeter law (Nia et al., Proc. R. Soc. A 2015, sound-hole conductance — seen only as a search hit, not read: [NOT VERIFIED]).
- **Voiced window**: `Leff = t_eff + k_w*r_eq` with `k_w = 1.7` nominal, but treat `t_eff` and `k_w` as calibration unknowns: one edge is a knife (t -> 0), the opposite edge is the windway exit face, the jet crosses the opening, and the player's lips/face are nearby. Sources state the problem but give no number: "the theoretical calculation ... contains various uncertain factors on the open-end correction around the edge hole" and "the open end correction can be affected by the blow velocity (jet) on the aperture" (Kobayashi 2009 [SRC]); "With organ pipes, the end correction due to the fipple is very much larger than that required for the open end" (J. Campin, forum, qualitative [SRC] https://theocarinanetwork.com/testing-the-helmholtz-formula-t13419.html); "proximity of solid surfaces (such as the face or sheltering)" listed as a pitch/tone parameter (W. Hicks [SRC] https://emi.wesleyhicks.art/ocarina_characteristics); a finger a few mm above an open hole lowers its pitch (Pure Ocarinas [SRC] https://pureocarinas.com/why-ocarina-airy-high-notes). Quantified lip/ramp shading of the window: [NOT FOUND].

### 1.3 Speed of sound to use
- `c = 331.3*sqrt(1+T/273.15)`: 343.2 (20 C), 346.1 (25 C), 349.0 (30 C), 351.9 (35 C) m/s [CALC].
- The air in a played instrument is not at 35 C. Warmed-up instrument equilibrium: 25.5 C assumed by Fuks, "in good agreement with ... the oboe 25.6 C (Meyer) and the flute 26.8 C (Coltman)" [SRC] https://www.speech.kth.se/music/publications/leofuks/IIIbism97co3.html . Breath is "nearly saturated at 37 C"; a 1 % frequency rise needs +3 % water vapour or -6 % CO2 (UNSW [SRC] https://www.phys.unsw.edu.au/jw/warming.html). Exhaled CO2 2.5 % rising to 8.5 % after a minute of playing gives a 15-20 cent dip (Fuks [SRC]). Humidity 0->100 % RH changes pitch less than a 2 C change (Wikipedia Vessel flute [SRC]).
- Temperature coefficient measured on an ocarina: about 0.9 cents/C (Pure Ocarinas study, 2.5 C -> -39 c ... 22 C -> -3 c [SRC] https://pureocarinas.com/study-ocarina-breath-curves-temperature); ideal-gas value is ~3 cents/C.
- **Use c = 346 m/s (25 C dry-equivalent; humidity and CO2 roughly cancel).** Cold first toot at 20 C: -13 cents; long warm play: up to +17 cents [CALC].

### 1.4 Blowing pressure -> pitch
- Pitch rises monotonically with blowing pressure (Fletcher 1976 conclusion (iv) [SRC] https://www.phys.unsw.edu.au/music/people/publications/Fletcher1976.pdf ; Kobayashi 2009 Fig. 3; Printone: "higher speed produces higher frequencies" [SRC]).
- Measured on one alto ocarina (uncalibrated pressure units, Pure Ocarinas study [SRC]): lowest note -40 / -20 / 0 / +20 cents at 30 / 34 / 36 / 39 units, i.e. **+60 cents for +30 % pressure** -> f ∝ P^0.13 [CALC]; highest note 56 / 68 / 83 / 121 units, +60 cents for x2.16 pressure -> f ∝ P^0.045 [CALC]. "The low notes are much more sensitive to pressure changes" [SRC] https://pureocarinas.com/ocarina-breath-curves .
- Usable bend: "about a third of a semitone / 30 cents", 5-10 cents for fast music; total range "several semitones" before the note breaks (Wikipedia Vessel flute [SRC]). Tenor recorder for comparison: each note stays stable over about +-40 cents of pressure-driven pitch (Price et al. arXiv:1502.02170 Fig. 12 [SRC] https://arxiv.org/pdf/1502.02170).
- Makers tune each higher note ~20 cents flat at constant pressure so that the player blows progressively harder (Pure Ocarinas [SRC] https://pureocarinas.com/measure-ocarina-breath-curve). For our 2-note toy: design both notes for the same pressure (section 2.3).
- Absolute ocarina blowing pressures in Pa: [NOT FOUND] (Hickman explicitly did not calibrate; one uncalibrated U-tube peak of 19 cm H2O is mentioned as a trial observation, not a result).

---

## 2. Voicing geometry for a LOW vessel flute (300-500 Hz)

### 2.1 Published dimensions (real instruments)
| instrument | cut-up W (exit->edge) | window / jet width | windway exit height h | windway length | other | source |
|---|---|---|---|---|---|---|
| 12-hole ABS alto C ocarina (V = 90 ml, plays C5 = 530 Hz, nominal low A4) | 8.5 mm | window area 62.2 mm2 (=> ~7.3 mm wide if rectangular) | inlet 3.3 x 6.9 mm (exit not given) | 36.6 mm | jet-labium offset y0 = 0.1 mm, wall 6.8 mm | Csoka 2018 Table 5.1 [SRC] |
| Night by Noble plastic soprano C ocarina (low A5 = 880 Hz) | 5 or 6 mm (opening 6 x 5 mm2) | 5-6 mm | flue exit = half the 3 mm inlet => 1.5 mm | — | wall 1.5 mm; jet 20 m/s in the simulation; cavity pressure amplitude ~300 Pa | Okada 2019 [SRC] |
| Yamaha YRT-304B tenor recorder (low C4 = 262 Hz) | 4.83 mm | 14.7 mm | 1.09 mm (1.95 mm at inlet) | 72.0 mm | two 45 deg chamfers 0.7 mm deep; lip aligned with duct centre | Price 2015 [SRC] |
| Zen-On Bressan alto recorder | 4 mm | 12 mm | 1 mm | — | y0 = 0.1 mm | arXiv:1601.05545 [SRC] |
| Fletcher's experimental organ pipe, 330 Hz (E4), 4 x 4 x 46 cm | "normal speech with a cut-up near 1 cm" (5/10/15 mm tested) | 40 mm | flue 0.25 and 1.0 mm | — | languid bevel ~60 deg; jet divergence ~5 deg; jet centre-line directed slightly outside the lip | Fletcher 1976 [SRC] |
| alto C ocarina maker rule | voicing "approx 9-10 mm long" | 8-9 mm | "1.2 mm high"; "no taller than 1.5 mm if an Alto C and above" | — | square/rectangular voicing limits range | OberonOcarinas, forum [SRC] https://theocarinanetwork.com/problems-with-ocarina-t22983.html |
| printable whistle (OpenSCAD) | window_size 4 mm (measured commercial whistle 4.76 mm) | 7 mm (7.14) | 1.4 mm | 40 mm (25.4) | lip angle 15 deg (20 deg measured) | ephetic/whistle main.scad [SRC] https://github.com/ephetic/whistle |
| clay workshop ocarina | — | = windway stick | — | — | "chisel a ~45 deg bevel"; aperture starts just past the windway end | Paley 2015 [SRC] |

Ratios: recorders/organ W/h ~ 4 ("it can reach 12 in flue organ pipes") (Auvray et al. arXiv:1207.7136 [SRC]; Price slides [SRC] https://spot.colorado.edu/~pricej/downloads/JPriceASAOct2014.pdf). Ocarinas run W/h ~ 5-7 and window roughly square.

### 2.2 Jet / Strouhal rules
- Dimensionless jet velocity `theta = Uj/(W f)`; "theta is expected to be larger than 4" for the normal regime; below 4 only weak aeolian regimes (Auvray [SRC]). Equivalent: `St = f W / Uj < 0.25`.
- Recorder head gain region measured: St = f*W~/U0 from 0.07 to ~0.27-0.29 (W~ = W + chamfer depth); "the observed |Sh| = 1 boundary at St = 0.27 agrees closely with the low-blowing-pressure boundary" (Price [SRC]). Efficiency peak at St ~ 0.14-0.18 (McKinnon thesis re-analysis of Verge; "typical recorders have a power efficiency of about 1 %") [SRC] https://spot.colorado.edu/~pricej/downloads/DanielMcKinnonHonorsThesis.pdf . Jet wave phase velocity ~0.4 U, growth ~0.3/h (arXiv:1601.05545 [SRC]); normal regime has about half a jet wavelength across the mouth (Fletcher 1976 [SRC]).
- Ising intonation number: `I = sqrt(2 P D/(rho H^3))/F`, D = jet thickness (flue height), H = cut-up; "I = 2 gives maximum efficiency", above ~3 the pipe overblows; W (width) does not enter, it sets power and air use; `V = sqrt(2P/rho)`, `Q = V*W*D` (Liljencrants [SRC] https://www.mmdigest.com/gallery/technical/isingform , https://www.mmdigest.com/gallery/technical/isint ; original: Ising, Walcker Hausmitteilung 42, 1971). Note I = sqrt(D/H)/St, so I = 2...3 <=> St = 0.13...0.22 for D/H ~ 0.17 [CALC] — the two rules agree. An ocarina has no usable overtone, so "overblow" there = airy/screech.
- Jet must be laminar: Re = h*U0/nu ~ 500-2500 in recorders (Price slides [SRC]) => h*U <= 0.0375 m2/s: at 300 Pa (22.5 m/s) h <= 1.67 mm [CALC].
- Chamfers: 45 deg chamfers at the windway exit roughly halve jet sensitivity vs a square exit and move the oscillation threshold to lower jet velocity (Price 2015 citing Segoufin et al., Acustica 86, 649-661 (2000), "Windway Length and Chamfers" — primary not fetched).
- Labium offset: the offset between labium and channel exit "controls the ratio between even and odd harmonics" (Auvray [SRC]); ocarina-maker check: looking down the windway the labium edge is visible, "half in shadow ... half lit" (forum [SRC]) = edge on the windway mid-plane. Published offsets: 0.1 mm (two instruments above).
- Other maker rules [SRC, forum https://theocarinanetwork.com/i-ve-created-a-program-that-generates-dimensions-f-t24268-s10.html]: voicing hole no wider than the airway exit; airway edge tangent to the voicing-hole edge; windway about 2x larger at the entrance than at the exit; too-short windway causes turbulence; a finger hole close to the voicing ruins tone (no distance given: [NOT FOUND]). Wikipedia Vessel flute: holes/fingers too close to the labium disrupt the airstream [SRC].
- Surface finish: a laser-sintered ocarina was "noisy, harsh" until the windway was polished with fine sandpaper (Pure Ocarinas [SRC] https://pureocarinas.com/playable-3d-printed-ocarina). Printone printed PLA/FDM vessel flutes with 4 mm shells and un-smoothed interiors: "surface roughness has only a small effect on the dominant frequency" (chamber, not windway) [SRC] https://research.autodesk.com/app/uploads/2023/03/printone-interactive-resonance-simulation.pdf_rech9KdWpXEj8vpN9.pdf .
- Labium angle / edge thickness for low ocarinas: no measured rule found beyond the table (15-20 deg whistles, ~45 deg clay, 60 deg organ languid bevel); "labium too blunt" is a listed cause of weak tone (search summary of ceramicartsnetwork.org; page not read: [NOT VERIFIED]).

### 2.3 What this gives for 340 / 470 Hz [CALC, script]
`U = f*W/St`, `P = rho U^2/2` (rho = 1.18):

| cut-up W | note | U_min (St 0.27) | U_opt (St 0.16) | U_max (St 0.07) |
|---|---|---|---|---|
| 7.0 mm | 340 Hz | 8.8 m/s (46 Pa) | 14.9 m/s (131 Pa) | 34 m/s (682 Pa) |
| 7.0 mm | 470 Hz | 12.2 m/s (88 Pa) | 20.6 m/s (249 Pa) | 47 m/s (1303 Pa) |
| 7.5 mm | 340 Hz | 9.4 m/s (53 Pa) | 15.9 m/s (150 Pa) | 36 m/s (783 Pa) |
| 7.5 mm | 470 Hz | 13.1 m/s (101 Pa) | 22.0 m/s (286 Pa) | 50 m/s (1496 Pa) |

- Both notes speak at one breath pressure anywhere from ~100 to ~650 Pa; best common point ~150-250 Pa. W = 6-8 mm is the usable band: W > 9.5 mm would not speak the 470 Hz note below ~160 Pa; W < 5 mm pushes the 340 Hz optimum below 70 Pa (weak).
- Ising check, windway 1.2 mm, W = 7 mm: I(340) = 2.26 / 3.20 / 3.92 and I(470) = 1.64 / 2.32 / 2.84 at 100 / 200 / 300 Pa. With W = 7.5: I(340) = 2.04 / 2.89 / 3.54. => 100-200 Pa is the sweet spot; 1.5 mm windway shifts everything ~12 % toward "overblown".
- Flow and level (windway 8 mm wide): 1.2 mm high -> 7.5 / 10.6 / 13.0 L/min at 100 / 200 / 300 Pa; 1.5 mm -> 9.4 / 13.3 / 16.2 L/min. Jet power P*Q = 12.5 / 35 / 65 mW (1.2 mm). With the flue-pipe efficiency of "order 1 %" (Fletcher 1976 [SRC]) and an assumed 0.1-1 % band: about 60-70 dB at 100 Pa, 64-74 dB at 200 Pa, 67-77 dB SPL at 1 m [CALC, monopole, Lp = Lw - 11]. Fletcher's upper bound: `Lmax = 107 + 10 log10(D*W0/R^2) + 15 log10 P` dB (SI units, 100 % efficiency, half radiated) [SRC]. Measured ocarina SPL: [NOT FOUND].
- Start geometry: windway exit 1.2-1.5 mm x 7-8 mm, inlet ~2.5-3 mm tall (2:1 convergence), length >= 20 mm (ocarina 36.6 mm, recorder 72 mm), chamfers 45 deg x 0.5-0.7 mm on the exit, cut-up 7-7.5 mm, labium edge on the windway mid-plane (0 to +0.1 mm toward the outside), ramp 15-30 deg, edge <= 0.5 mm, window width = windway width.

---

## 3. Measured validation cases (known-good inputs for a closed-form evaluator)

All reproduced by `vessel_flute.py` [CALC]. c as stated per case.

| id | object | inputs | measured | model | error |
|---|---|---|---|---|---|
| V1 | tea bottle, Monteiro et al. (arXiv:1805.04014) | V = 435 cm3 (and lower, water-filled), neck d = 29.0(2) mm, L = 70(1) mm, k = 1.5, 22.3 C | fit of f^2 vs 1/V gives c = 345(5) m/s vs 344 expected => implied f(435 cm3) = 223.4 Hz +-1.5 % | 222.7 Hz (c = 344) | -0.3 % (+-1.5 %) |
| V2 | 750 ml wine bottle, J. D. Cook https://www.johndcook.com/blog/2022/07/20/helmholtz-resonator/ | V = 750 cm3, d = 20 mm, L = 90 mm | 106 Hz (phone app) | 117.8 (k=0), 109.0 (k=1.5), 108.0 (k=1.7), c = 343 | +11 %, +2.9 %, +1.9 % |
| V2b | three more Cook bottles https://www.johndcook.com/blog/2021/02/08/pitch-of-a-big-wine-bottle/ | 750 ml d 19.05 L 88.9; 1.5 L d 19.05 L 177.8; 355 ml beer d 19.05 L 76.2 | 114, 63, 191 Hz | k=1.5: 104.8, 54.3, 162.6 | -8 %, -14 %, -15 % (eyeballed necks, tapered shoulders: shows what sloppy geometry costs) |
| V3 | UNSW spherical resonator (calculation on the page, regression only) | V = 2920 cm3, S = 8.3 cm2, L = 80 mm, Leff = 105 mm (k = 1.54), c = 343 | page: 90 Hz (calculated) | 89.8 Hz | -0.2 % |
| V4 | **12-hole ABS alto C ocarina, Csoka 2018 (BME thesis), mouth-blown, measured spectrum** | V = 90 ml (water fill), window A13 = 62.21 mm2, wall 6.8 mm, subholes A4 = 7.55 and A9 = 5.73 mm2; note C5 = window + both subholes (standard 12-hole fingering; inferred, the thesis prints no fingering chart) | **529.76 Hz** (scale: C 529.759, D 600.855, E 659.334, F 699.214, G 786.476, A 880.679, B 999.884, C 1063.544) | see below | see below |
| V5 | **Night by Noble soprano C ocarina, Okada et al. ISMA 2019** | inner V = 9.425 cm3, mouth opening 6 x 5 mm2, wall d = 1.5 mm, cavity length 86 mm, c = 340 | lowest note A5 = 880 Hz (nominal); compressible LES of the scanned geometry 850 +- 50 Hz | lumped: 1175 Hz (paper's own number, reproduced) | **+33.6 %** |
| V6 | Kobayashi 2009 3D LES ocarina model (simulation, not a measurement) | V = 9.425 cm3, 5 x 5 mm aperture, zero wall, jet 10 m/s | LES 880 Hz | 1273 Hz | +45 % |

V4 model variants (c = 343) [CALC]:

| window t, k | holes t, k | all-closed (nominal A4 = 440) | C5 (measured 529.76) | D5/C5 ratio (meas. 1.1342, D = +A1 17.35 mm2, inferred) |
|---|---|---|---|---|
| 6.8, 1.698 (flanged both ends) | 6.8, 1.698 | 378.8 (-13.9 %) | 436.9 (**-17.5 %**) | 1.1309 |
| 6.8, 0.849 (thesis model) | 6.8, 0.849 | 441.3 (+0.3 %) | 499.4 (-5.7 %) | 1.1233 |
| 3.4 (= wall/2), 1.7 | 6.8, 1.6 | 433.4 (-1.5 %) | 485.8 (-8.3 %) | 1.1093 |
| 3.4, 1.5 | 6.8, 1.5 | 452.2 (+2.8 %) | 503.3 (-5.0 %) | 1.1044 |
| 3.0, 1.698 | 3.0, 1.698 | 441.7 (+0.4 %) | 524.8 (-0.9 %) | 1.1395 |

The thesis' own lumped simulation gave 522.56 / 576.61 / 647.87 / 685.62 / 779.53 / 886.01 / 1002.64 / 1093.92 Hz against the measured scale above: -1.4 %, -4.0 %, -1.7 %, -1.9 %, -0.9 %, +0.6 %, +0.3 %, +2.9 % [SRC Table 5.2]. Caveats: the tabulated 6.8 mm "wall thickness" is suspiciously thick for moulded ABS; if the true hole depth is ~3 mm the plain flanged model is within 1 %.

V5 explained [CALC]: that cavity is 86 mm long with a mean cross-section of only 1.1 cm2 — a stopped pipe, not a compact vessel (quarter wave at 880 Hz = 97 mm). With the non-compactness term of section 5 (opening at the end of a tube-like cavity) the same inputs give 799 Hz (-9.2 %); the exact closed-tube + lumped-neck solution `x*tan(x) = G*L^2/V` gives 775 Hz (-12 %). So V5 is the known-BAD case for a purely lumped evaluator and a good test of the correction term.

Also relevant:
- Printone (Umetani et al., SIGGRAPH Asia 2016 [SRC]): 16 PLA FDM free-form vessel flutes, shell h = 0.4 cm; BEM passive resonance vs speaker-measured resonance "up to 10 Hz deviation" (CUBE, 4 cm edge, 3 holes 8/10/12 mm, notes ~860-1175 Hz); 100 of 104 target notes playable; failures "at most 3 % lower than the target" at the highest notes because accuracy degrades "when the total area of the finger holes becomes large". They state the plain Helmholtz model with Rayleigh end corrections is "inapplicable for free-form wind instruments with multiple finger holes" (STAR shape, many holes; figure only, no numbers). Fipple modelled "as holes with a sharp edge"; scaling the HEN (5 x 5 x 7 cm) by 1.5x/2x/3x gave 2/3, 1/2, 1/3 frequency. Window dimensions not published => not usable as a numeric case.
- Gemshorn (Charnley, Perrin, Stone, Proc. IoA 9(3), 1987): Helmholtz behaviour, V ~ 97 ml "roughly as predicted", plots of frequency vs pressure and vs hole diameter — PDF returned 404, numbers [NOT FOUND].
- Hickman forum data (alto D: measured V = 45 cm3 incl. finger holes, ~40 cm3 without; voicing ~7 mm circle) https://theocarinanetwork.com/helmholtz-calculation-t20435.html — no measured pitch posted, his arithmetic has unit errors: not usable.
- Koop "Alto C: 130 cm3, window 9 x 5 mm, wall 4 mm, A4" https://tonykoop.github.io/ocarina/design.md is an unvalidated spreadsheet target (plain model gives ~314 Hz for those numbers [CALC]); do not use.
- Scaling sanity check [CALC]: V ∝ f^-3 from V4 (90 ml @ 440) predicts 11.3 ml @ 880 (V5 has 9.4) and 195 ml @ 340 Hz for a full-range 12-hole-style voicing. Our one-hole instrument can use a relatively smaller window, hence 100-150 cm3.

### Honest error band
- Bottle with a real cylindrical neck, measured dimensions: +-3 % (V1, V2).
- Compact vessel, finger holes only changing: interval errors about +-1...3 % in ratio (V4 D5/C5 within -2.6...+0.5 % across model variants; thesis scale within +-4 % absolute).
- **Voiced window, absolute pitch, no calibration: -17 % ... +3 % on V4 depending on which defensible end-correction choice is made, and +34 % on V5 if non-compactness is ignored. State +-10 % typical / +-15-20 % worst case (+-1.5 to +-3 semitones).** A +-5 % or +-1 semitone claim is not supported by the published data for an uncalibrated voiced window; +-5 % is defensible only for the hole-induced change and after calibrating the window on a print.
- Direction: not consistent. Thick-walled alto: real pitch HIGHER than the flanged-both-ends formula; thin, long soprano: real pitch much LOWER than lumped. For our geometry the down-pulling effects are non-compactness (-17...-85 cents closed), lip/face shading and a soft breath; the up-pulling ones are the knife-edge labium (t_eff < wall), convex exterior (k < 1.7) and hard blowing.

---

## 4. Finger hole sizing

- Size from `G_h = V*(2*pi/c)^2*(f_open^2 - f_closed^2)` and `pi r^2 = G_h*(t + k_h r)` [CALC]. With c = 346, 340 -> 470 Hz: G_h/V = 34.72 m^-2, i.e. G_h = 3.47 mm per 100 cm3. Equivalent statement: G_h = 0.911 * G_closed (ratio^2 - 1 = 0.911).
- Results (k_h = 1.6): V = 100 cm3, wall 2.5 -> d = 5.53 mm; 125 cm3, 2.5 -> 6.54 mm; 150 cm3, 3.0 -> 7.84 mm.
- Sensitivity: +-0.2 mm in d = +-20 / +-17 / +-14 cents on the open note (sets A/B/C); +-0.5 mm = +-50 / +-42 / +-35 cents. k_h 1.46...1.70 = +26 / -17 cents. Print the hole 0.5-1 mm undersize and ream to pitch ("holes were deliberately undersized ... tuned by opening out the holes", Pure Ocarinas 3D print [SRC]; "print ... drill holes out, match to a tuner", forum [SRC]). Paint/roughness narrowing a hole lowers pitch (Kerr blog [SRC] https://cameronkerrnz.github.io/posts/2024/3d-print-and-paint-ocarina).
- Upper limits, real instruments: the ABS alto C ocarina has finger holes of 5.73-75.43 mm2 = 2.7-9.8 mm diameter and thumb holes 109-113 mm2 = 11.8-12.0 mm (Csoka Table 5.1 [SRC], diameters [CALC]). Printone's playable CUBE used 10.2 / 11.4 / 13.2 mm holes [SRC]. "The size of a finger hole can never exceed the internal diameter of the chamber" (Pure Ocarinas [SRC] https://pureocarinas.com/ocarina-chamber-shape-range-chamber-volume-bypassing). Anthropometric fingertip-width data and a published "maximum sealable hole" number: [NOT FOUND]. Working limits from the instruments above: <= 10 mm for an adult finger, 12 mm thumb; for a child keep <= 7-8 mm [KNOW/judgement]. Our 5.5-7.8 mm is inside all of these. Lower limit: 2.7 mm holes exist on the ABS ocarina; "too small ... rough, muffled" (Flutopedia, flutes [SRC] https://www.flutopedia.com/finger_hole_size.htm).
- Partial covering (the coo glide) [CALC, G scaled with open area and its equal-area radius]: 10 % open area -> 366-368 Hz, 25 % -> 393-394, 50 % -> 425-426, 75 % -> 449-450, 100 % -> 470 Hz. The first quarter of the opening gives ~40 % of the rise, so a rocking finger gives a smooth, front-loaded glide. A finger hovering a few mm above the hole still flattens it (shading, Pure Ocarinas [SRC]); lift clear by roughly a hole diameter [KNOW].
- Hole placement: pitch-neutral to first order, but keep it away from the window/labium (tone, section 2.2) and prefer mid-body over the far end (section 5).

---

## 5. Chamber shape

- If all internal dimensions << wavelength the shape does not matter: "the pitch of fundamental only depends on the volume of the cavity but irrespective to its shape" (Kobayashi 2009 [SRC]); pitch "insensitive to mouthpiece location for the round cavity shapes" though it "changes up to 20 Hz" with mouthpiece location in general (Printone [SRC]). Hickman (maker) reports shape does matter in practice for range, and proposes that open holes "bypass" part of an elongated chamber [SRC].
- Wavelengths (c = 346): 1018 mm at 340 Hz, 736 mm at 470 Hz. An 80-90 mm cavity has kL = 0.49-0.56 (340) and 0.68-0.77 (470): not negligible.
- First-order non-compactness correction [CALC, derived from the closed-tube input impedance; exact for a uniform tube]: an opening at the END of a cavity of length L adds inertance equal to a neck-length increase `dLeff = A*L^2/(3V)`; at the MIDDLE `A*L^2/(12V)`. Equivalent: `f = f_H / sqrt(1 + p*G*L^2/V)`, p = 1/3 (end), 1/12 (middle); small-argument form `f ≈ f_H*(1 - (kL)^2/6)` (end) or `(1 - (kL)^2/24)` (middle). A fat ellipsoid is less severe than a uniform tube (use the tube value as the bound, about half of it as nominal: judgement). Validated against V5 (1175 -> 799 Hz vs 880 nominal).
- Effect on the worked sets (L = 80-90 mm): window at the end: closed -68...-85 cents, open -125...-155 cents, ratio 1.327-1.337 instead of 1.382. Window at mid-length: closed -17...-22, open -33...-42 cents, ratio 1.367-1.370. => put the window (and hole) near the middle of the long axis if the layout allows, or compensate with a ~4-8 % larger hole conductance. This also means "blown through the tail" with the window at the tail end is the acoustically worst position; a window on the back/belly just in front of the tail root is better.
- First higher cavity mode: sphere `f = 2.0816*c/(2*pi*R)` -> 3.8 kHz for R = 30 mm [KNOW formula, CALC]; tube-like `c/(2L)` -> 2.0 kHz for L = 85 mm. Both >= 4x the open note and inharmonic, so the tone stays nearly sinusoidal: "the overtone peaks are quite smaller than the main resonance peak" (Okada 2019 [SRC]); harmonics "very small and almost undetectable" on two clay ocarinas (Francis, UIUC P406 report [SRC] https://courses.physics.illinois.edu/phys406/sp2017/Student_Projects/Spring12/Gregory_Francis_P406_Project_Report_Sp12.pdf , which also saw a fixed body resonance near 1100 Hz on a large ocarina).
- Head lobe = second Helmholtz system: `f2 = c/(2pi)*sqrt(G_neck*(1/V_head + 1/V_body))` [KNOW, CALC]. V_head = 8 cm3, V_body = 120 cm3: a throat of 150 mm2 x 10 mm gives 1670 Hz (harmless, head simply adds to V); a 4 mm dia x 10 mm passage gives **616 Hz** (too close to 470: detunes and adds loss). Rule: throat conductance >= ~650 m^-2 * V_head (f2 >= 1.4 kHz), i.e. >= 5.2 mm for 8 cm3 — or make the head solid/sealed off and count only the body volume.

---

## 6. Why low notes in small chambers are breathy; minimum window

- Fixed by the pitch: `G_closed = V*(2*pi*f/c)^2`. At 340 Hz: 2.29 mm (60 cm3), 3.05 (80), 3.81 (100), 4.57 (120), 5.72 (150) [CALC].
- With a plain wall the window that fits is small [CALC, k = 1.7]: t_eff = 3 mm -> 15.5 mm2 (60 cm3), 23.3 (80), 32.2 (100), 42.2 (120), 59.4 mm2 (150 cm3); t_eff = 1.5 mm -> 10.6, 16.4, 23.4, 31.5, 45.6 mm2. A 60 cm3 chamber would need a ~3.9 mm square window: its cut-up would put the 340 Hz optimum jet at ~8 m/s (~40 Pa) — almost no drive power, and the broadband jet hiss is not reduced with it. That is the breathiness.
- Radiation: `Q_rad = 4*pi/(k*G) = 4*pi/(V k^3)` (unflanged; half that if flanged) [KNOW: radiation resistance rho c k^2/(4 pi); LibreTexts form Q = 2 pi sqrt(V (L'/S)^3) [SRC, search summary]]. At 340 Hz: 890 (60 cm3), 667 (80), 534 (100), 427 (125), 356 (150). Viscous loss in the window (Ingard-type estimate, Q_v ~ 30) and wall thermal loss (Q ~ 350-390) give a passive Q of only ~26-27, so merely 4.9 % (100 cm3), 6.4 % (125), 7.7 % (150) of the oscillation loss is radiated [CALC]. Radiated fraction ∝ V*f^3: small chamber + low note = little sound per unit of jet power. Real small resonators lose even more at the neck/cavity junction (Starecki 2007, search summary only [NOT VERIFIED]). Rough FDM layers (0.1-0.2 mm) are comparable to the viscous boundary layer (0.12 mm at 340 Hz [CALC]) — keep the window walls and windway smooth.
- Source strength is window area x acoustic velocity, and velocity saturates relative to jet speed, so loudness goes roughly with window area squared. Maker statements that match: larger chamber and hole "play with a higher pressure and are louder"; large voicings are louder but airier; bass ocarinas need a voicing neck — a neck "traps a plug of air which slows down the oscillations", letting a low note come from a smaller chamber; "as instruments get larger and lower, more neck is required"; a bass-size chamber "will be problematic" (Pure Ocarinas / forum [SRC]). If the sound hole is too large for the chamber the instrument gets airy (Pure Ocarinas, search summary).
- **Minimum practical window (derived, no published rule: [NOT FOUND])**: cut-up >= 6 mm (section 2.3) and width >= 6 mm => >= ~36 mm2; preferred 49-60 mm2 (7 x 7 to 8 x 7.5). Needed window depth t_eff for a 6 x 6 window at 340 Hz: 10.0 mm (60 cm3), 6.0 (80), 3.7 (100), 2.1 (120), 0.5 mm (150 cm3). So: 60 cm3 is only possible with a 10 mm neck (lossy, quiet); 80 cm3 marginal; **>= 100 cm3 recommended, 125-150 cm3 comfortable**.

---

## 7. Three worked parameter sets (c = 346 m/s, k_w = 1.7, k_h = 1.6) [CALC]

`window_t_eff` is the acoustic depth of the window opening (local wall thickening / chimney around the window; the labium ramp is cut into it). It is the calibration parameter.

| | Set A (compact) | Set B (mid) | Set C (large, plain wall) |
|---|---|---|---|
| chamber volume V | 100 cm3 | 125 cm3 | 150 cm3 |
| wall at finger hole | 2.5 mm | 2.5 mm | 3.0 mm |
| window width x cut-up | 7.0 x 7.0 mm (49 mm2, r_eq 3.95) | 8.0 x 7.0 mm (56 mm2, r_eq 4.22) | 8.0 x 7.5 mm (60 mm2, r_eq 4.37) |
| required G_closed | 3.812 mm | 4.765 mm | 5.718 mm |
| window t_eff needed for 340 Hz | 6.14 mm | 4.57 mm | 3.06 mm (= the wall) |
| finger hole diameter (G_h) | 5.53 mm (3.472 mm) | 6.54 mm (4.341 mm) | 7.84 mm (5.209 mm) |
| nominal closed / open | 340.0 / 470.0 Hz | 340.0 / 470.0 Hz | 340.0 / 470.0 Hz |
| k_w = 1.5 instead of 1.7 | 351.0 / 478.0 (+55 / +29 c) | 352.9 / 479.4 (+65 / +34 c) | 355.1 / 481.0 (+75 / +40 c) |
| k_w = 2.3 (shaded window) | 312.4 / 450.5 (-146 / -74 c) | 308.4 / 447.7 (-169 / -84 c) | 304.1 / 444.7 (-193 / -96 c) |
| t_eff -1 mm / +1 mm (closed) | 354.1 / 327.5 Hz (+70 / -65 c) | 355.5 / 326.4 (+77 / -71 c) | 357.5 / 324.9 (+87 / -79 c) |
| non-compact, window at end (L = 80/85/90 mm) | 327.0 / 437.3, ratio 1.337 | 325.4 / 433.5, ratio 1.332 | 323.7 / 429.6, ratio 1.327 |
| non-compact, window mid-body | 336.6 / 461.1, ratio 1.370 | 336.2 / 460.0, ratio 1.368 | 335.7 / 458.9, ratio 1.367 |
| V -5 % | closed +44 c | +44 c | +44 c |
| always-open tuning vent 2 mm dia | 372.6 / 494.1 (+159 / +87 c) | 366.3 / 489.4 (+129 / +70 c) | 359.7 / 484.5 (+98 / +52 c) |
| passive Q / radiated fraction | 26 / 4.9 % | 27 / 6.4 % | 27 / 7.7 % |
| flow at 200 Pa, windway 1.2 mm | 9.3 L/min | 10.6 L/min | 10.6 L/min |

Reading the table:
- Any window-model error moves the closed note about twice as many cents as the open note (the hole's conductance is unaffected), so the ratio drifts 1.33-1.46 across the plausible band. The interval must be closed by trimming, not by trusting the model.
- Set C needs no special window chimney and radiates best; Set A needs a 6 mm deep window surround. If the pigeon body can hold ~125-150 cm3 (e.g. inner ellipsoid 80 x 60 x 60 mm = 151 cm3; 75 x 57 x 57 = 128 cm3 [CALC]) prefer B/C.
- Trim strategy that only ever needs material removed: design the closed note 80-120 cents FLAT on the nominal model (window t_eff +1.5 mm gives -96 / -104 / -115 c for A / B / C; V +10 % gives -82 c), print the finger hole ~1 mm undersize, then (1) raise the closed note with a small always-open vent (drill 1.5 / 2.0 / 2.5 mm: closed +102 / +159 / +218 c in set A, +83 / +129 / +179 c in B, +62 / +98 / +137 c in C; open note about half that; an eye or nostril is a natural place) or by lengthening the window by filing the labium back, (2) ream the finger hole until the open note is 470 Hz. A vent raises the closed note about twice as much as the open note, so do step (1) first. Lowering pitch after printing is only possible by adding wax/tape (shading the window, shrinking a hole) — hence start flat.
- Alternative, cleaner for a gated workflow: print one calibration body, measure f_closed and f_open with a tuner at a comfortable breath, compute `t_eff_measured = A_w/(V*(2*pi*f_closed/c)^2) - 1.7*r_eq` and `k_h_measured` likewise, feed them back, reprint. Expect +-50 cents after that.

---

## 8. Templates

### 8.1 Python evaluator (stdlib; same code as in vessel_flute.py)
```python
import math

def r_eq(area_mm2):
    return math.sqrt(area_mm2 / math.pi)

def conductance_mm(area_mm2, t_mm, k_end):
    """G = A / (t + k*r_eq)  [mm]"""
    return area_mm2 / (t_mm + k_end * r_eq(area_mm2))

def helmholtz_hz(volume_mm3, openings, c=346.0, cavity_len_mm=0.0, pos_factor=0.0):
    """openings = [(area_mm2, t_mm, k_end), ...]; c in m/s.
    pos_factor: 0 lumped, 1/3 opening at the end of a tube-like cavity, 1/12 at its middle."""
    G = sum(conductance_mm(a, t, k) for a, t, k in openings)
    f = c * 1000.0 / (2 * math.pi) * math.sqrt(G / volume_mm3)
    if cavity_len_mm and pos_factor:
        f /= math.sqrt(1.0 + pos_factor * G * cavity_len_mm ** 2 / volume_mm3)
    return f

def cents(f, ref):
    return 1200 * math.log2(f / ref)

def hole_d_for(volume_mm3, f_closed, f_open, t_mm, k_end=1.6, c=346.0):
    Gh = volume_mm3 * (2 * math.pi / (c * 1000.0)) ** 2 * (f_open ** 2 - f_closed ** 2)
    r = (Gh * k_end + math.sqrt((Gh * k_end) ** 2 + 4 * math.pi * Gh * t_mm)) / (2 * math.pi)
    return 2 * r

def strouhal(f_hz, cutup_mm, p_blow_pa, rho=1.18):          # playable 0.07..0.27, best ~0.16
    return f_hz * cutup_mm * 1e-3 / math.sqrt(2 * p_blow_pa / rho)

def ising(f_hz, cutup_mm, windway_h_mm, p_blow_pa, rho=1.18):  # best 2..3
    return math.sqrt(2 * p_blow_pa * windway_h_mm * 1e-3 / (rho * (cutup_mm * 1e-3) ** 3)) / f_hz
```

### 8.2 Candidate parameter sets (JSON)
```json
{
  "A_compact": {"chamber_volume_mm3": 100000, "wall_mm": 2.5, "window_width_mm": 7.0, "window_cutup_mm": 7.0, "window_t_eff_mm": 6.14, "window_k_end": 1.7, "hole_d_mm": 5.53, "hole_k_end": 1.6, "speed_of_sound_m_s": 346.0, "windway_exit_h_mm": 1.2, "pred_closed_hz": 340.0, "pred_open_hz": 470.0},
  "B_mid":     {"chamber_volume_mm3": 125000, "wall_mm": 2.5, "window_width_mm": 8.0, "window_cutup_mm": 7.0, "window_t_eff_mm": 4.57, "window_k_end": 1.7, "hole_d_mm": 6.54, "hole_k_end": 1.6, "speed_of_sound_m_s": 346.0, "windway_exit_h_mm": 1.2, "pred_closed_hz": 340.0, "pred_open_hz": 470.0},
  "C_large":   {"chamber_volume_mm3": 150000, "wall_mm": 3.0, "window_width_mm": 8.0, "window_cutup_mm": 7.5, "window_t_eff_mm": 3.06, "window_k_end": 1.7, "hole_d_mm": 7.84, "hole_k_end": 1.6, "speed_of_sound_m_s": 346.0, "windway_exit_h_mm": 1.2, "pred_closed_hz": 340.0, "pred_open_hz": 470.0}
}
```

### 8.3 Validation cases (JSON; expected = what the evaluator must return, measured = what reality did)
```json
[
  {"id": "V1_tea_bottle", "volume_mm3": 435000, "openings": [[660.52, 70.0, 1.5]], "c": 344.0, "expected_hz": 222.7, "measured_hz": 223.4, "measured_tol_pct": 1.5, "source": "https://arxiv.org/pdf/1805.04014"},
  {"id": "V2_wine_750", "volume_mm3": 750000, "openings": [[314.16, 90.0, 1.5]], "c": 343.0, "expected_hz": 109.0, "measured_hz": 106.0, "source": "https://www.johndcook.com/blog/2022/07/20/helmholtz-resonator/"},
  {"id": "V3_unsw_sphere_calc_only", "volume_mm3": 2920000, "openings": [[830.0, 80.0, 1.538]], "c": 343.0, "expected_hz": 89.8, "page_calc_hz": 90.0, "source": "https://phys.unsw.edu.au/jw/Helmholtz.html"},
  {"id": "V4_abs_alto_C5_thesis_model", "volume_mm3": 90000, "openings": [[62.21, 6.8, 0.849], [7.55, 6.8, 0.849], [5.73, 6.8, 0.849]], "c": 343.0, "expected_hz": 499.4, "measured_hz": 529.76, "note": "fingering inferred; plain flanged model (k=1.698) returns 436.9", "source": "https://last.hit.bme.hu/download/rucz/onlab/fuvos_hangszerek/Csoka_Bence_-_Okarina_Szakdolgozat_2018.pdf"},
  {"id": "V5_night_soprano_lumped_KNOWN_BAD", "volume_mm3": 9425, "openings": [[30.0, 1.5, 1.698]], "c": 340.0, "expected_hz": 1175, "measured_hz": 880, "source": "https://pub.dega-akustik.de/ISMA2019/data/articles/000010.pdf"},
  {"id": "V5_night_soprano_noncompact", "volume_mm3": 9425, "openings": [[30.0, 1.5, 1.698]], "c": 340.0, "cavity_len_mm": 86.0, "pos_factor": 0.3333, "expected_hz": 799, "measured_hz": 880}
]
```

---

## 9. Not found / open
- Hoekje "ocarina physics" page: not located (his Baldwin Wallace site lists flute tone-hole spreadsheets only). ocarinaforest.com physics page: 404, Wayback not reachable from this tool.
- Fletcher & Rossing vessel-flute section, Benade pp. 473-476: not accessible; only cited through secondary sources.
- Robert Hickman's making guide with voicing dimensions: no numeric windway/labium dimensions exist on pureocarinas.com pages read (all qualitative).
- A Thingiverse/Printables parametric ocarina with acoustic formulas in source: none found (only ephetic/whistle, a pipe whistle; Mikolas Zuza's Printables 12-hole ocarina prints support-free in PLA at 100 % infill per the Kerr blog, dimensions not published).
- Measured ocarina blowing pressures in Pa, flow in L/min, SPL in dB; quantified lip/ramp shading of the window; fingertip anthropometry; a published minimum window area: none found. Values given for these are derived (flagged [CALC]) from recorder/organ-pipe data.
- Liljencrants' flue-mouth end-correction page (fonema.se): domain dead.
