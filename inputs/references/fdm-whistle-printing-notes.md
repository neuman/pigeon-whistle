# printing.md — one-piece, support-free FDM vessel whistle (pigeon, 10-12 cm, 0.4 nozzle, PLA/PETG, 0.10-0.16 layers)

Research date 2026-11-19. Nothing in `/home/neuman/my-thing` or `/home/neuman/Documents/work/nopekit` was modified.
Scratch work: `/tmp/claude-1000/-home-neuman-my-thing/cbf22764-116a-4870-bc2f-90231ddadd43/scratchpad/work/printing/`

Provenance tags used below:
- **[S]** sourced, URL given. Most maker pages (Printables, MakerWorld, Thingiverse) returned HTTP 403 to direct fetch, so those lines come from search-result summaries or from All3DP's write-ups of them; treat as secondary.
- **[C]** computed here (script path given).
- **[P]** read from the nopekit `fdm-print` pack source (path given).
- **[K]** my own knowledge / engineering reasoning, NOT verified against a source in this session.
- **[NF]** looked for, not found.

---

## 0. Bottom line (decision)

**Print belly-down, tail lying on the bed, and rotate the voicing 90 degrees about the blow axis: the windway is a VERTICAL slot (thin in Y, tall in Z) and the labium is a VERTICAL blade whose wedge is drawn in the XY layer plane. The window opens on one flank of the tail root, not on top.**

Why (details in section 6):
1. Every voicing-critical surface (both windway walls, windway exit lips, labium edge, window side edges) becomes a vertical wall made of perimeters: no bridge, no overhang, no layer-quantised dimension. Windway gap, cut-up and labium offset are all XY dimensions.
2. Layer lines on the windway walls run ALONG the airflow (X), not across it.
3. Belly + tail on the bed gave a contact patch of about 87 x 35 mm (2082 mm2) in the scratch model versus 11 x 18 mm (198 mm2) standing on the tail [C].
4. Tail and beak have layers parallel to their length, so the bitten mouthpiece is not loaded across layer bonds [P: `packs/fdm-print/references/orientation.md`].
5. In the scratch model belly-down was the only one of three orientations whose outer shell passed the pack's overhang measurement at 45 degrees [C].

What it costs: left/right asymmetry (window on one flank), the chamber roof must be a ridge/tent instead of a dome (loses about 2-21 % of chamber volume depending on how much flat bridged ceiling is accepted, or needs a 10.5 mm dorsal ridge), jet-sheet width limited by tail height (about 6-8 mm in an 11-12 mm tall tail), and two seam-sensitive corners that need a seam rule. Full list in 6.5.

This is consistent with how the loud flat-printed FDM whistles are described ("print on its side for the loudest results", "flat top side face down", "do not rotate it vertically") — see section 1. That those designs are 2D voicing profiles extruded in Z is my inference [K]; their pages could not be fetched.

---

## 1. What successful printable designs actually do

| Design | Orientation / supports | Settings stated | Voicing-relevant notes | Source |
|---|---|---|---|---|
| 12-hole ocarina, RobSoundtrack (after nimaid), Thingiverse 2755765 | "Print it standing vertically"; no internal supports "as long as you stand it vertically, thanks to the angles of the curves" | not stated | 428 makes; sound reported good | [S] https://all3dp.com/2/3d-printed-ocarina-3d-models/ |
| Same family, Prusa "12-hole playable ocarina" (Printables 65399) | one piece, "a bit of support material for the first few layers" | Prusament PLA | "very nicely in tune and plays well" | [S] https://blog.prusa3d.com/3d-print-a-recorder-an-ocarina-or-a-kazoo-3d-pritned-musical-instruments_49390/ |
| Same family, MakerWorld 138835 | not stated | 25 % infill "sufficient for a playable ocarina" | — | [S] search summary of https://makerworld.com/en/models/138835 |
| "Single Print" ocarina, 3E8, Thingiverse 1012353 / Printables 249011 | no supports inside or outside, one piece | min 10 % infill, "the thicker the infill the better the sound will bounce off the walls"; Printables listing shows 0.20 mm layer / 0.4 nozzle, 3 h 53 min, 52 g | 2016 update fixed a "mid-seam issue" seen at layer height <= 0.2 mm | [S] https://all3dp.com/2/3d-printed-ocarina-3d-models/ ; search summary of https://www.printables.com/model/249011-single-print-ocarina |
| Alto C 12-hole (Printables 474058) | "print orientation is on the mouthpiece, no support, only brim if needed" | 0.2 mm, 20 % infill, PLA+; MakerWorld sibling: 0.16 mm, 2 walls, 15 % infill | internal design "helps to reduce airy high notes" | [S] search summaries of https://www.printables.com/model/474058-ocarina-of-time-12-hole-alto-c-ocarina and https://makerworld.com/en/models/429897 |
| Soprano 12-hole, Karuuv (Pinshape) | auto orientation or vertical; EXTERNAL supports only — internal ones "impossible to remove" | "thick walls" | "clean the windway with a small, delicate object" after printing | [S] https://all3dp.com/2/3d-printed-ocarina-3d-models/ |
| Transverse, seggybop, Thingiverse 234512 | two glued halves (no internal support); single-part variant needs external supports, rotated 20 degrees off the bed | — | "You can't re-scale it or the pitch will be off" | [S] same |
| Xun, Licheong, Thingiverse 515147 | vertical, one piece, no supports "because the curve is progressive and the shape is vertical" | "very high resolution" | — | [S] same |
| ECAN3 12-hole soprano C (MakerWorld) | — | 0.4 nozzle, 0.2 mm layer | "Avoid Z-seam on the labium" | [S] search summary of https://makerworld.com/en/models/429890-ocarina-sc |
| Experimental ocarina, Shmoee (Printables 208286) | — | 0.28 mm layer | at 0.28 mm it "did need some sanding of the labium edge" | [S] search summary of https://www.printables.com/model/208286-experimental-ocarina |
| V29 whistle, jzisa, Thingiverse 1179160 | "flat top side face down", raft- and support-free | 0.2 mm, 100 % infill | creator claims "over 118 decibels" (unverified) | [S] https://all3dp.com/2/3d-printed-whistle-3d-models/ |
| Echo 3-tone whistle, LetsMakeThings | "Print on its side for the loudest results" | — | creator claims 129 dB (unverified) | [S] same |
| Customizable whistle, nischi, Thingiverse 46825 | commenters: no supports, keyhole overhang small enough | high infill | — | [S] same |
| Bird water whistle, Nemo_Mk2, Thingiverse 1552526 | one part, no supports | users reported WATER LEAKING below 20 % infill | — | [S] same |
| Baby dragon water whistle, Shira (Printables 12241) | — | PLA, 0.16 mm, 15 % infill, **1.2 mm shell "to help keep it watertight"** | — | [S] same |
| Low-poly chirping bird whistle (Printables 554240) | "default orientation of the STL" | — | — | [S] search summary |
| Warble whistle remix (AdamStag original) | no supports "if you have good part cooling" | 0.4 nozzle, 2 perimeters, 0.2 mm | — | [S] search summary |
| Emergency whistle (Printables 36824) | — | 0 % infill with 3-5 shells | claims ~120 dB (unverified) | [S] search summary |
| Keychain whistle (MakerWorld) | flat | 0.2 mm, 4 walls, 100 % infill; "a hollow whistle absorbs sound, make sure your walls are thick and infill is solid" | — | [S] search summary |
| Tin whistle (MakerWorld 1148967) | supports minimal; a tiny support remains ON THE LABIUM and must be pushed out from the bore side, never pressing on the labium | 0.12 or 0.16 mm; "lower layer height makes the fipple much sharper"; >0.2 mm only if you can finish parts; scarf seam "Contour and Hole" recommended | — | [S] search summary of https://makerworld.com/en/models/1148967-tin-whistle |
| Parametric whistle (MakerWorld) | "optimized for flat FDM printing without internal supports"; another design: "flat on the build plate ... Do not rotate it vertically", overhangs kept <= 45 degrees | — | "global scaling also changes the critical windway and labium dimensions" | [S] search summaries |
| A parametric whistle page | claims a 45-degree-tilted print gives "a significantly sharper labium compared to horizontal or vertical orientations" | — | vendor claim, no independent test found | [S] search summary |
| Labial organ-pipe sections, benjaminwand | most pipes sliced tilted 45 degrees with "support touching build plate" so there is NO support under the labium | — | — | [S] https://github.com/benjaminwand/3d-printed-labial-pipe |
| Pure Ocarinas SLS print (Shapeways) | powder-bed, not FDM | — | windway unplayable until cleared; layer roughness in the windway gave "a noisy, edgy and harsh tone", fixed by polishing with fine sandpaper; holes deliberately undersized then opened to tune | [S] https://pureocarinas.com/playable-3d-printed-ocarina |
| Pures Music guide | "voicing channel runs horizontally", flat voicing channel facing upward "tends to work better than vertical orientations" | layer <= 0.1 mm near the labium; 100 % infill or 4-6 perimeters; sand airway 220 then 400 grit; seams away from the airway; octagonal tone holes for FDM | "Any micro-leak ... bleeds pressure and kills the note entirely" | [S] https://www.puresmusic.com/blogs/ocarinas/3d-print-ocarina-possibility-guide-is-it-playable (a shop blog, no measurements) |
| Chiff & Fipple builders | — | 3D-printed tin-whistle head: windway length 20 mm, windway height 1.3 mm, window length 4 mm | "3D printing alone is not good enough for such a surface finish on the floor [of the windway]" vs another builder: well-tuned prints need little post-processing | [S] https://www.chiffandfipple.com/t/making-a-3d-printed-and-metal-whistle-looking-for-feedback/149553 and search summary of the same forum |

Reading of this evidence:
- Two families appear. **(a) Stand-on-end ocarinas**: the windway is vertical so its cross-section is drawn by perimeters; when the mouthpiece is on the bed the labium edge points down and is the first strand of a bridge across the window [K, geometric inference — the pages do not say this]. They work, with reported labium sanding at coarse layers and windway cleaning. **(b) Flat / on-side whistles**: printed flat or on their side, marketed as loudest; I infer the voicing profile lies in the layer plane with a vertical labium edge [K]. Recommended layout = family (b) applied to the pigeon.
- No source compared windway orientations on one model with measurements [NF]. The Pures Music page and the "45 degree" page disagree with each other and neither shows data.
- Infill advice is contradictory (10 % to 100 %). The only failure reports tied to it are LEAKS (water whistle below 20 % infill), i.e. it is a sealing issue, not "sound bouncing".

---

## 2. Design rules with numbers

### 2.1 Voicing geometry as printed (recommended sideways layout)
- **Windway gap (the thin dimension, now along Y): model 1.2-1.5 mm; do not go below about 1.0 mm.** Basis: printed whistle head with 1.3 mm windway height works [S chiffandfipple]; slots between two perimeter walls close up by roughly 0.1-0.3 mm total [P geometry_rules.md: vertical holes print 0.1-0.4 mm undersize; S Bambu forum: holes ~0.23 mm small]; 1.0 mm is > 2 extrusion widths so the slicer never merges the walls [K]. Add +0.10 to +0.15 mm to the modelled gap or use slicer XY hole compensation, then measure with feeler gauges / drill shanks on a coupon.
- **Windway length**: 15-25 mm is what the tail gives; forum guidance is that too short a windway causes turbulence, exact minimum [NF]. Printed example: 20 mm [S].
- **Windway top**: a 1.2-1.5 mm bridge — negligible. **Window top**: a bridge equal to the cut-up length (3-5 mm). Hubs: sag is "to some extent always present unless the bridge is less than 5 mm" [S https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/]. Keep it under 5 mm or chamfer it at <= 43 degrees.
- **Labium tip thickness: model an explicit flat tip 0.45-0.50 mm thick (one extrusion width). Never model a zero-thickness knife.** A slicer drops whatever is thinner than its minimum feature, so a modelled knife prints truncated and the cut-up grows by d = t_min / (2 tan(alpha/2)) [C `calc_numbers.py`]:

  | wedge angle alpha | t_min 0.2 | 0.3 | 0.45 | 0.6 mm |
  |---|---|---|---|---|
  | 15 deg | 0.76 | 1.14 | 1.71 | 2.28 mm |
  | 20 deg | 0.57 | 0.85 | 1.28 | 1.70 |
  | 25 deg | 0.45 | 0.68 | 1.01 | 1.35 |
  | 30 deg | 0.37 | 0.56 | 0.84 | 1.12 |
  | 40 deg | 0.27 | 0.41 | 0.62 | 0.82 |

  On a 3-5 mm cut-up that is a 10-40 % error. PrusaSlicer Arachne: "Features thinner than this value [minimum feature size] will not be printed. Feature thicker than the minimum will be widened to the minimum perimeter width" [S https://help.prusa3d.com/article/arachne-perimeter-generator_352769]; default percentages [NF — the commonly quoted 25 % / 85 % of nozzle were not confirmed]. Whether a 0.45 mm blunt edge voices as well as a sharper one is [K]/untested here; one parametric ocarina project uses a teardrop tip radius of 1.0 mm and labium offset -0.2 mm but has printed nothing yet [S https://github.com/aleckmadrid/Parametric_alto_C_Ocarina].
- **Labium wedge angle and offset are free in this layout** (they are XY geometry); values belong to the acoustics notes.
- **Windway exit lips**: keep square and seam-free; a small chamfer is suggested by one designer "to allow the windsheet to expand" [S search summary]; size [NF].
- **Elephant foot**: bottom 0.2-0.4 mm of the part bulges 0.1-0.3 mm [P geometry_rules.md]; Prusa compensation "around 0.2 mm usually works well for the default 0.4 mm nozzle" [S https://help.prusa3d.com/article/elephant-foot-compensation_114487]. Rule: windway floor (bottom end of the slot) and window bottom edge >= 2.5 mm above the bed; 0.5 mm x 45 degree chamfer round the whole bed outline including the tail tip [P; S Hubs recommends a 45 degree chamfer on edges touching the plate].

### 2.2 If the classic horizontal windway is used instead (fallback, not recommended)
- Roof is a bridge across the windway width (8-12 mm). Expect the first bridge layer to sag and be rough; a 1.2 mm windway is 10 layers at 0.12 mm so every dimension in Z is quantised to the layer height, including the labium offset [K]. Bridge strands necessarily run across the windway, i.e. ACROSS the airflow [K]; one design tells users to adjust "external bridge infill direction" in OrcaSlicer [S search summary].
- The labium edge is a single bridged strand. Reported consequences: sanding the labium at 0.28 mm layers; "lower layer height makes the fipple much sharper" [S].
- The pack will not catch this: see 7.3.

### 2.3 Overhangs and the chamber roof
- Design rule 45 degrees from vertical; 45-60 "usually acceptable but rough"; past 60 needs support [P geometry_rules.md]. Hubs: "can usually be printed up to 45 degrees" [S].
- Fine layers help geometrically. Fraction of each bead resting on the layer below = 1 - h tan(theta) / w [C; stair-step model per S https://www.padtinc.com/2017/07/12/towards-self-supporting-design-for-additive-manufacturing-part-1-standard-guidelines/]:

  | w = 0.45 mm | 45 deg | 50 | 55 | 60 | 65 | angle at 50 % support |
  |---|---|---|---|---|---|---|
  | h = 0.10 | 0.78 | 0.74 | 0.68 | 0.62 | 0.52 | 66.0 deg |
  | h = 0.12 | 0.73 | 0.68 | 0.62 | 0.54 | 0.43 | 61.9 |
  | h = 0.16 | 0.64 | 0.58 | 0.49 | 0.38 | 0.24 | 54.6 |
  | h = 0.20 | 0.56 | 0.47 | 0.37 | 0.23 | 0.05 | 48.4 |

  So 60 degrees at 0.12 mm has the same overlap as 45 degrees at 0.20 mm. Caveats: one test author warns too low a layer height "causes more upwards curling on difficult overhangs", and Polymaker says best overhang surfaces come from HIGH layer height [S search summary; https://wiki.polymaker.com/printing-tips/material-science/overhangs]. No measured 0.1-vs-0.2 mm comparison at 55-65 degrees was found [NF]. Treat anything above 45 degrees as needing a coupon.
- **A round dome roof fails.** Scratch model, belly-down, round ellipsoid cavity: 6.4 % of total surface past 45 degrees, worst 79.9 degrees (limit is 0.5 %) [C].
- Roof options measured on the scratch body (outer 105 x 50 x 46 mm, round back left unmodified, wall >= 2.0 mm everywhere, cavity semi-axes 27.8 x 22.8 x 21.8 mm) [C `orient_study.py`, results in `orient_study_results.json`]:

  | Roof | flat bridged ceiling strip | cavity volume | vs round | pack overhang result |
  |---|---|---|---|---|
  | round dome (reference) | 8.9 mm cap | 52.8 cm3 | 100 % | FAIL 6.4 % |
  | 43.5 deg ridge tent from the widest section | 4.0 mm | 41.6 | 78.9 % | pass 0.10 % @45 |
  | tent starting where the dome reaches 10 deg | 10.3 mm | 46.7 | 88.5 % | pass @45 |
  | ... 20 deg | 16.0 mm | 50.1 | 95.0 % | pass @45 |
  | ... 30 deg | 21.5 mm | 51.8 | 98.2 % | pass @45 |
  | tangent "teardrop" 43.5 deg, capped | 27.7 mm | 51.5 | 97.7 % | pass @45 |
  | tangent 53.5 deg, capped | 19.7 mm | 52.7 | 100 % | pass only if limit set to 55 |
  | tangent 58.5 deg, capped | 15.6 mm | 52.9 | 100 % | pass only if limit set to 60 |
  | uncapped 43.5 deg teardrop | none | — | — | needs the back raised 10.5 mm as a ridge |

  Trade: every option that keeps > 90 % of the volume inside a round back needs a flat bridged ceiling 10-28 mm wide. Suggested starting point: tent from the 10-degree line with a ~10 mm bridged strip (88.5 %), or give the pigeon a slightly peaked back. The chamber volume used for pitch must be the volume of the roof actually modelled.
- Outer shell: the body must leave the bed at <= 45 degrees. In the scratch model a belly plane 0.708 x (body semi-height) below the body centre plus a 45 degree chamfer round the patch brought the shell from 8.65 % past limit (naive: small flat, undercut chin, horizontal beak, tail held off the bed, 28.5 mm cantilever) to 0.15 % [C].
- Head/beak/tail: no chin undercut (blend head into chest), beak stubby and tilted down so its underside is steeper than 45 degrees, tail underside ON the bed. A tail held horizontal above the bed is a cantilever; pack allowance is 2 mm [P `gates/mesh.py` MAX_CANTILEVER_MM_DEFAULT].

### 2.4 Bridges
- Under 20 mm reliable, to 30 mm with visible sag, default pack limit 30 mm for a ceiling anchored on opposite sides [P geometry_rules.md, `gates/mesh.py`]. Other sources: 10-20 mm, "< 10 mm", "> 5 mm may need support" [S search summary of several design guides] — the spread is real.
- Inside the chamber a sagging ceiling is acoustically harmless but loose strands can break off in a toy that is put in the mouth: keep internal bridges <= ~10-15 mm and blow/rinse the part out before first use [K].
- Do not put the finger hole through a flat bridged ceiling: its first-layer rim is printed in mid-air (All3DP: mid-air holes fail because "their perimeters have nothing under them") [S https://all3dp.com/2/3d-printing-holes-screw-guide/]. Put it through a sloped part of the roof with a VERTICAL axis.

### 2.5 Walls, perimeters, labium blade
- Pack minimum for a wall: 3 perimeters = 1.20 mm at a 0.4 nozzle, or 3 x `extrusion_width_mm` if stated (1.26 at 0.42, 1.35 at 0.45) [P `gates/printability.py` PERIMETERS_MIN, NOZZLE_MIN_WALL_MM].
- Wall thickness that is exactly n perimeters (spacing = w - h(1 - pi/4)) [C]:

  | | n=3 | n=4 | n=5 | n=6 |
  |---|---|---|---|---|
  | h 0.12, w 0.42 | 1.21 | 1.60 | 2.00 | 2.39 mm |
  | h 0.12, w 0.45 | 1.30 | 1.72 | 2.15 | 2.57 |
  | h 0.16, w 0.45 | 1.28 | 1.70 | 2.11 | 2.53 |

  Recommended shell: 2.0-2.2 mm = 5 perimeters, no sparse infill inside the wall.

### 2.6 Seams
- A seam on the labium or windway exit is a known defect: "Avoid Z-seam on the labium" [S]; Prusa names layer seams as a main leak source [S https://blog.prusa3d.com/watertight-3d-printing-pt1-vases-cups-and-other-open-models_48949/].
- In the sideways layout the layers that contain the windway split the tail into two islands, and the sharpest convex corners in those layers are exactly the labium tip and the windway exit lip [K — verify in slicer preview].
- Proposed deterministic rule [K]: place the bird with the window flank toward +Y, seam position "Rear", and give the tail flank a slight outward bulge so the rear-most point of each loop is mid-flank, away from both corners. Otherwise use seam painting (block within ~5 mm of labium and windway exit). Scarf seam is recommended by one whistle designer for interior finish [S].

---

## 3. Air-tightness

| Lever | Number | Source |
|---|---|---|
| Perimeters | "at least 3-4 perimeters for a single wall", 5-6 rarely needed | [S] https://help.prusa3d.com/en/article/watertight-prints_112324 |
| Perimeters by material (water test, cylinders) | PETG, PLA: 4 minimum; ABS/ASA/PC/PP: 2; "the most important" factor; most parts worked with 4-6 perimeters (2-3 mm walls) | [S] Prusa blog (URL above) |
| Layer height | "best to print with 0.15 mm"; 0.05 mm best, 0.3 mm worst; help article: 0.15 mm most durable, do not exceed 60-65 % of nozzle width | [S] both Prusa pages |
| Flow | +5-10 % extrusion multiplier (105-110 %), or line width +5-10 % (0.40 -> 0.44); more stringing, especially PETG | [S] both |
| Nozzle temperature | +5-10 C | [S] both |
| Top/bottom solid layers | 2-7 bottom layers were all waterproof; set 5 or more "just to be sure" | [S] Prusa blog |
| Infill/perimeter overlap | default 10 % of nozzle; raise to 25-35 % if leaks persist | [S] Prusa help |
| Linear/pressure advance | one forum guide: watertight with only 2 perimeters at 0.4 nozzle by raising PLA to 220 C and turning linear advance OFF (single user, anecdotal) | [S] https://forum.prusa3d.com/forum/original-prusa-i3-mk3s-mk3-general-discussion-announcements-and-releases/guide-how-to-get-water-and-airtight-prints-on-the-first-try-with-just-2-perimeters-and-the-default-0-4mm-nozzle |
| Sealing afterwards | acrylic varnish sprayed in and out a few times (not for food use); food-grade epoxy (days to cure); nail polish | [S] Prusa blog |
| Maker practice | 1.2 mm shell for a water whistle; leaks reported below 20 % infill; Mod Podge (Hard) over paint on an ocarina | [S] All3DP whistle list; https://cameronkerrnz.github.io/posts/2024/3d-print-and-paint-ocarina |

Rules for this part:
- Shell 2.0-2.2 mm, 5 perimeters, 0.12-0.15 mm layers, PLA at +5 C, flow 100-103 % for the first article (higher flow shrinks the windway gap and holes; raise only if the leak test fails).
- Sparse infill next to the airway is a leak plenum linking windway, chamber and outside if any perimeter is porous [K]. Either 100 % infill in the thick regions (head, tent crown, tail block) or >= 5 perimeters plus >= 0.8 mm of solid top/bottom. Pack estimate at 100 % solid: 59-72 g, 9-14.5 h (47-58 cm3 of plastic, 0.12-0.16 mm layers, 40 mm/s) [C using P `gates/_process_model.py`; pack says +-30 %].
- Leak test before judging the voicing [K]: plug window and finger hole, submerge, blow through the tail, look for bubbles; or fill with water and watch the outside.
- If a sealant is used it must be accounted for: paint in finger holes "lowers the pitch, since it makes the holes smaller" [S cameronkerrnz], and any wash on the inside reduces chamber volume (raises pitch) and can clog a 1.2 mm windway [K].

---

## 4. Closed cavities, supports, roughness

- The chamber is not sealed (window + finger hole), so there is no trapped-air or drain-hole issue [K].
- Supports inside the chamber cannot be removed: the pack says so explicitly ("A steep face inside a closed pocket passes `fdm.overhang` and traps its support permanently" — it does not check removability) [P `PACK.md`], and Karuuv notes internal supports are "impossible to remove" [S]. Print with supports OFF; the geometry must pass at the chosen overhang limit on its own.
- Roughness: on the windway it matters a lot (SLS ocarina: "noisy, edgy and harsh tone" until polished [S]; "remove layer ridges inside the voicing duct" [S Pures Music]). On the chamber wall no source reported an audible effect [NF]; the user's "high quality for smoother air chambers" (R3) is cheap insurance, not a demonstrated need.
- A vertical-slot windway cannot be sanded on its walls except with a folded strip of 400-grit or a feeler gauge; design it so it does not need sanding [K].
- PETG strings (pack `sourcing.md` rates PETG stringing "high", PLA "low") [P]; strings across a 1.2 mm windway or the window are a voicing defect. **PLA for the first article**; PETG only if heat resistance is needed (PLA softens at 55-60 C, PETG 75-80 C [P `sourcing.md`]).

---

## 5. Dimensional accuracy, pitch sensitivity, tuning

### 5.1 What prints off-size
- Vertical-axis holes: 0.1-0.4 mm undersize, polygonal when small [P geometry_rules.md]. Causes: cooling shrinkage, layer squish bulging into the hole, polygon faceting [S https://all3dp.com/2/3d-printing-holes-screw-guide/]. One user: ~0.23 mm small; another reports holes OVERSIZE on a different machine [S search summary of Bambu/Prusa forums] — measure, do not assume the sign.
- Hubs gives no fixed number: it "depends on the printer, slicing software, hole size and material" [S].
- Compensation: OrcaSlicer/Bambu "X-Y hole compensation" (per-side value, only affects holes fully contained in the XY plane, outer dimensions untouched) [S https://www.orcaslicer.com/wiki/print_settings/quality/quality_settings_precision]. PrusaSlicer: forum posts say there is no separate hole compensation, only XY size compensation for contours [S forum, not verified against current version].
- General tolerance: PLA +-0.15 mm, PETG +-0.2 mm on a 50 mm feature [P `sourcing.md`]; the pack "says nothing about dimensional accuracy ... that is a physical claim settled with calipers on a real print" [P `PACK.md`].
- Horizontal-axis holes: crown sags; teardrop above ~8 mm [P]. Use vertical axes for the finger hole.

### 5.2 Sensitivity (Helmholtz: f proportional to sqrt(sum of opening conductances / V)) [C, simple model G = A/(t + 1.7 r); approximate]
- 340 -> 470 Hz fixes G_hole / G_window = (470/340)^2 - 1 = 0.911; the hole carries 47.7 % of total conductance with the hole open.
- Total window conductance needed at 340 Hz, c = 343 m/s: V 40 cm3 -> 1.55 mm; 45 -> 1.75; 52 -> 2.02; 60 -> 2.33; 80 -> 3.10; 100 -> 3.88 mm (G_hole = 0.911 x that). Palm-size chambers (40-60 cm3) therefore need a SMALL window and a SMALL finger hole (order 3.5-5 mm), which makes print error proportionally larger. (Sizing itself belongs to the acoustics notes.)
- Finger hole printed small (open note goes flat):

  | hole d, wall t | -0.1 mm | -0.2 mm | -0.3 mm |
  |---|---|---|---|
  | 3.5 mm, 2.2 | 17 cents | 34 | 51 |
  | 4 mm, 2.2 | 14 | 29 | 44 |
  | 5 mm, 2.2 | 11 | 22 | 34 |
  | 6 mm, 2.2 | 9 | 18 | 27 |

- Window printed small on each side (closed note goes flat), assuming d ln G / d ln A = 0.75: 5 x 2.5 mm: 39 cents per 0.1 mm, 80 per 0.2; 6 x 3: 33 / 66; 7 x 3.5: 28 / 57; 8 x 4: 25 / 49.
- Chamber volume: +1 % V = -0.5 % f = -8.6 cents. A 0.1 mm over-thick inner skin on a 52 cm3 chamber removes ~1.7 % V = +0.87 % f (+15 cents).
- Temperature: +1 K = +0.17 % = +3 cents. Blowing pressure also moves an ocarina's pitch [S cameronkerrnz: "you can't expect any model to be pitch perfect"; one user's print only in tune "if you blow fairly hard"].
- Conclusion: untuned first prints land within roughly +-1/4 to +-1/2 semitone of target. For R6 ("does not have to fool a bird") that may already be acceptable; if not, tune.

### 5.3 Tuning after printing
- Enlarging a hole raises the pitch; start with the smallest hole and enlarge gradually; a hole made too large "probably can't be fixed"; work from the lowest hole up [S https://instruments-du-monde.com/en/blogs/ocarina/how-to-tune-ocarina via search summary]. Pure Ocarinas deliberately undersized, opened the holes, then fed the measured sizes back into the model [S].
- Order for this instrument [K]: (1) leak test; (2) closed note first — it depends on window and volume only; (3) then the finger hole.
- Bias the model so both corrections go the easy way [K]: finger hole modelled 0.2-0.3 mm under nominal (ream up with a drill bit turned by hand); closed note aimed 10-20 cents flat, since raising it is easy (open the window slightly, or reduce volume with a small pour of epoxy/wax on the floor) and lowering it is not (only by shading the window or blowing softer).
- To lower the open note: wax, nail varnish or UV resin on the hole wall; paint does this unintentionally [S cameronkerrnz].
- Never scale the STL in the slicer: pitch and the windway/labium dimensions all change [S seggybop, parametric whistle page].

---

## 6. Orientation study for the 11 cm bird [C]

Script: `.../work/printing/orient_study.py` (run with `env PYTHONPATH=/home/neuman/Documents/work/nopekit/src python3 orient_study.py`). It builds a simplified pigeon (body ellipsoid 72 x 50 x 48, head sphere r 14, beak, tail 38 x 18 x 11) and measures it with the pack's own `_overhang_measure` / `_bridge_measure` from `/home/neuman/Documents/work/nopekit/packs/fdm-print/gates/mesh.py` (imported read-only). The voicing is NOT in these meshes. STLs of the roof variants: `study_*_bellydown.stl` in the same folder.

### 6.1 Outer shell only

| Case | bed patch | past 45 deg (limit 0.5 %) | worst | bridge/cantilever |
|---|---|---|---|---|
| naive cute bird, belly-down (4 mm sliced off a round belly, undercut chin, level beak, tail held 13 mm up) | 40 x 28 mm, 860 mm2 | 8.65 % FAIL | 67.7 deg | 28.5 mm CANTILEVER FAIL (the tail) |
| fixed shell, belly-down (belly plane + 45 deg chamfer, chin blended, beak drooped, tail on the bed) | 87 x 35 mm, 2082 mm2 | 0.15 % pass | 52.5 deg (18 mm2 of slivers at the bed edge) | none |
| same shell standing on the tail tip | 11 x 18 mm, 198 mm2 | 4.32 % FAIL | 77.1 deg (rump flaring out from the tail) | 9.4 mm UNANCHORED FAIL |
| same shell standing on the head | ~1 mm2 | 6.03 % FAIL | 78.7 deg | — |

A shell could be redesigned to pass tail-down (a rump that widens at <= 45 degrees, i.e. a teardrop bird), but it would still stand 105 mm tall on a patch under 2 cm2 and need a brim.

### 6.2 Where the voicing ends up in each orientation [K, geometric reasoning]

| Orientation | Windway | Labium edge | Verdict |
|---|---|---|---|
| Belly-down, classic layout (window on top of tail) | horizontal slot; roof is an 8-12 mm bridge; height quantised in layers; ridges across the flow | horizontal edge = first strand of a bridge, or the lip of a 45 degree overhang | prints, rough; what most flat whistles with top windows accept |
| **Belly-down, sideways layout (recommended)** | vertical slot between two perimeter walls; top is a 1.2-1.5 mm bridge; layer lines along the flow | vertical blade, tip drawn by perimeters in every layer | crisp without supports |
| Tail-down | cross-section drawn by perimeters (good), but it starts at the bed (elephant foot at the mouth) and layer ridges cross the flow | points DOWN: bridged first strand across the window | labium is the weak point; tiny patch; mouthpiece loaded across layers |
| Head-down (tail up) | as tail-down; windway exit face is a ceiling over the window | points UP: clean | no usable contact patch; windway exit lips are bridged |

### 6.3 Recommended layout, concretely
- Frame: X = length (tail at -X), Y = width, Z = build direction, bed at z = 0.
- Belly plane and tail underside coplanar on the bed; 0.5 mm x 45 degree chamfer round the outline; body leaves the bed at <= 43.5 degrees.
- Tail about 18-20 mm wide x 11-13 mm tall. Windway: slot 1.2-1.5 mm thick in Y, 6-8 mm tall in Z, from z >= 2.5 mm, running along X near one flank.
- Window: rectangular opening through that flank at the tail root, Z extent = slot height, X extent = cut-up; top closed by a <= 5 mm bridge or a 43 degree chamfer.
- Labium: upstream edge of the chamber's flank wall, vertical, 0.45-0.5 mm flat tip, outer ramp in XY.
- Chamber: flat floor (>= 2 mm), ridge-tent roof per 2.3, no supports.
- Finger hole: on the back, vertical axis, through a sloped part of the roof. With a tent roof from the widest section inside a round back the wall is about 11 mm thick (measured vertically) halfway out from the ridge [K arithmetic: outer sphere R 24 gives 20.8 mm height at r = 12; tent of base radius 21.8 gives 9.8 mm], which lengthens the hole chimney and lowers its conductance — thin it locally with an external fingertip dimple so the chimney is <= 3 mm, and use the real chimney length in the pitch model.
- Layer height 0.12 mm (0.10-0.16), PLA, 5 perimeters, supports off, seam rule from 2.6.

### 6.4 Drainage
- Condensation in a windway is normal [S https://flute-a-bec.com/condensationgb.html]; water beads in the corners and resists blowing out; remedy offered there is a 1:1 water/washing-up-liquid mix.
- With the window on the flank near floor level, tipping the bird tail-down lets the chamber drain through the window [K]. Put the window's lower edge within ~1 mm of the chamber floor.

### 6.5 What is lost
1. Symmetry: one flank carries the window; the other is plain.
2. Chamber volume: about 2-21 % versus a dome, or a 10.5 mm dorsal ridge (table in 2.3).
3. Jet width is capped by tail height (6-8 mm).
4. The windway walls cannot be reached with sandpaper.
5. Two seam-sensitive corners need a seam rule or painting.
6. Extra plastic and time where the tent roof thickens the back (58 vs 47 cm3 of plastic in the scratch model).
7. The roof is not a dome, so "smooth air chamber" is a faceted ridge inside (invisible).

---

## 7. nopekit `fdm-print` pack: exact facts for the model

Pack root: `/home/neuman/Documents/work/nopekit/packs/fdm-print/` — read `PACK.md`, `selftest/baseline.json` (every key with units), `references/geometry_rules.md`, `references/orientation.md`, `lenses.md`, `sourcing.md`, `gates/mesh.py`, `gates/printability.py`.

### 7.1 Gates and defaults [P]
| Gate | Fails when | Default |
|---|---|---|
| `fdm.process_model_valid` | units / ratios off; prerequisite of all others; SKIPS (and so skips everything) if no `part_bbox_mm` | layer/nozzle 0.10-0.75 (0.12/0.4 = 0.30 ok), width/nozzle 0.8-2.0 |
| `fdm.bed_fit` | footprint > bed - 2 x brim | `brim_mm` 5.0 |
| `fdm.min_wall` | `part_min_wall_mm` < 3 x `extrusion_width_mm` (else 1.20 at 0.4 nozzle) | 1.26 mm at 0.42, 1.35 at 0.45 |
| `fdm.overhang` | area with `angle > overhang_limit_deg` (strict), excluding bed faces and faces >= `bridge_ceiling_deg`, exceeds `overhang_area_allow_frac` of TOTAL surface (inner + outer) | 45 deg, 0.005, 80 deg |
| `fdm.bridge_span` | ceiling region (>= 80 deg) span > `max_bridge_mm` if anchored on opposite sides, > `max_cantilever_mm` if one side, any span if unanchored | 30 mm, 2 mm |
| `fdm.layer_alignment` | needs `load_axis` + `utilisation`; skips otherwise | 0.5 strength ratio |
| `fdm.print_time_est` | > `max_print_time_h` or > `max_filament_g` | 24 h, 1000 g |

Mesh must be exported IN PRINT ORIENTATION with the bed at z = 0, watertight, positive volume; `trimesh` + `numpy` required (present here: trimesh 5.1.1, numpy 2.0.0, manifold3d available; shapely/rtree missing).

### 7.2 Projection template (keys verified against `selftest/baseline.json`; values are placeholders to be replaced by model outputs)
```json
{
  "fdm.part_bbox_mm": [110.0, 50.0, 46.0],
  "fdm.part_volume_mm3": 50000.0,
  "fdm.surface_area_mm2": 21000.0,
  "fdm.part_min_wall_mm": 2.0,
  "fdm.mesh_path": "build/print/pigeon_bellydown.stl",
  "bed_x_mm": 220.0, "bed_y_mm": 220.0, "bed_z_mm": 250.0, "brim_mm": 0.0,
  "nozzle_d_mm": 0.4, "extrusion_width_mm": 0.45, "layer_height_mm": 0.12,
  "perimeters": 5, "infill_fraction": 1.0, "print_speed_mm_s": 40.0,
  "filament_density_g_cm3": 1.24,
  "max_print_time_h": 24.0, "max_filament_g": 1000.0,
  "build_axis": [0.0, 0.0, 1.0],
  "overhang_limit_deg": 45.0, "overhang_area_allow_frac": 0.005,
  "bridge_ceiling_deg": 80.0, "max_bridge_mm": 30.0, "max_cantilever_mm": 2.0
}
```
Bed size is the user's printer — unknown, placeholder. `brim_mm` 0 is defensible only because the patch is ~2000 mm2 in PLA; record it as a choice.

### 7.3 Gotchas found
1. **Exact-45-degree faces are a coin flip.** The test is `angles > limit`. A roof modelled at exactly 45.000 degrees measured 307 mm2 "past the limit" in memory and 18 mm2 after an STL round-trip (float32) [C]. Model self-supporting faces at 43-44 degrees, or set the limit with margin.
2. **`fdm.min_wall` will fail on the labium tip** if the 0.45-0.5 mm tip is published as `part_min_wall_mm` (limit 1.20-1.35 mm). The gate's docstring: it "cannot tell them apart, and a project that wants that distinction should carry two parameters". Publish the thinnest SHELL wall there and carry the labium tip as its own parameter and claim.
3. **The pack passes a bridged labium or windway roof.** An 8-12 mm ceiling anchored both sides is far inside 30 mm. "It is not a slicer"; crispness of the voicing is a physical claim, not something a green sweep shows.
4. **A dome apex is reported as a small BRIDGE and passes; it is the 45-80 degree band around it that fails `fdm.overhang`** (round cavity: bridge 8.9 mm pass, overhang 6.4 % fail) [C].
5. **Raising `overhang_limit_deg` to 55-60 is allowed but must carry provenance** (machine, material, layer height) per the constant's docstring; the default was deliberately not set to 60.
6. Overhang area is a fraction of the whole surface, so a small bad region on a large part passes (the naive bird's whole tail underside was only part of 8.65 %). Read `worst_deg` and the face file, not only pass/fail.
7. Supports trapped in the cavity are not detected (2nd lens in `lenses.md`).

### 7.4 Roof construction recipe (from `orient_study.py`, trimesh + manifold)
```python
# cavity = (ellipsoid below the ring plane) UNION hull(ring ellipse + ridge segment), optionally flat-capped
slope = 1.0 / math.tan(math.radians(43.5))          # roof rise per horizontal run
ring  = ellipse(a_in*f, b_in*f) at height z_r       # f = sqrt(1-(z_r/c)^2); z_r = 0 for the widest section
apex  = z_r + min(a_in, b_in)*f*slope
ridge = segment of half-length (max(a_in,b_in)-min(a_in,b_in))*f along the long axis at height apex
tent  = trimesh.convex.convex_hull(vstack([ring_pts, ridge_end_1, ridge_end_2]))
cavity = union(intersection(ellipsoid, halfspace(z <= z_r)), intersection(tent, halfspace(z <= cap)))
```
All hull facets are at least as steep as `slope` because every ring point lies within min(a,b)*f of the ridge.

---

## 8. Mouth safety (toy)

### 8.1 Materials
- Prusa: PETG and sometimes PLA are regarded as chemically neutral, but "Natural/pure PETG-filament without any color, would be your best bet"; "Another issue is color-pigment and unknown additives"; "The grooves in between those layers are a seedbed for bacteria as they are almost impossible to clean properly"; "The standard brass nozzle is not considered food-safe, as it wears out" (stainless or titanium advised); food-safe certified epoxy coatings exist; "We do not recommend using 3d-prints as food-containers" [S https://help.prusa3d.com/en/article/food-safe-fdm-printing_112313/]. "Watertight does not mean food safe" [S Prusa watertight article].
- Brass lead: vendor blog cites 2.5-3.7 % lead by weight in standard brass, and a university study that could not detect lead transfer to filament (vendor source, not verified) [S search summary of qidi3d.com].
- A 2021 Frontiers in Microbiology study is cited for biofilm accumulating between layers (via the same vendor blog; primary paper not read) [S secondary].
- Practical rule [K]: natural or known-pigment PLA/PETG from a vendor with a food-contact statement, stainless nozzle if available, single user, rinse and dry after use, not dishwasher (PLA softens at 55-60 C [P]). A whistle is brief lip contact, not food storage, but the chamber stays damp.

### 8.2 Small parts / mechanical
- Small parts cylinder: 31.7 mm diameter, depth 25.4 to 57.1 mm (same in EN 71-1 8.2 and ASTM F963 Fig. 3 / 16 CFR 1501) [S https://law.resource.org/pub/eu/toys/en.71.1.2014.html ; https://law.resource.org/pub/us/cfr/ibr/003/astm.f963.2011.html]. A one-piece 105-110 mm bird cannot fit; nothing is detachable; no pea, no plug.
- EN 71-1 4.11 (mouth-actuated toys): mouthpieces and removable components must not fit the cylinder, including after soaking (8.9: 4 min immersion at 20 C, 10 min dry, four cycles), torque (8.3: 0.34 N m) and tension (8.4: 50 N if accessible dimension <= 6 mm, 90 N if larger); toys with loose internal parts must not release anything that fits the cylinder under 8.17.2 [S EN 71-1:2014 text at law.resource.org; clause 4.11 paraphrased by the fetch tool, numbers for 8.2-8.9 quoted]. Drop test 8.5: 850 mm, five drops. EN 71-1 8.17 blow/suck parameters [NF in the retrieved text].
- ASTM F963-11 4.6.2 / 8.13: mouth-actuated toys must not release an object fitting the cylinder after 10 alternating blow-and-suck cycles of at least 295 cm3 each, delivered in under 3 s, relief valve at 2 psig [S ASTM F963-11 at law.resource.org]. The edition now mandatory in the US is F963-23 (effective 2024-04-20) [S CPSC via search summary]; its text was not read.
- Consequences for the design [K]: beak and tail must survive a drop and a 90 N pull without snapping along a layer line (belly-down orientation helps); no loose bridge strands or support crumbs inside; all edges at the mouth rounded.
- Minimum mouthpiece size: no numeric minimum found beyond "must not fit the small parts cylinder" [NF].

### 8.3 Sound limits
- **EN 71-1:2014 4.20.2.10, wind toys** ("toy clearly designed to emit sound when actuated by the blowing action of the child or another person"; examples "toy trumpets and toy whistles"): time-averaged A-weighted emission level measured at 50 cm "shall not exceed 85 dB for exposure category 2 toys and 90 dB for exposure category 3 toys"; C-weighted peak at 50 cm "shall not exceed 110 dB". Category 2 includes wind toys that imitate musical instruments; category 3 includes wind toys such as whistles. Assumed use distance 25 cm (A-weighted) and 2.5 cm worst case (peak) [S https://law.resource.org/pub/eu/toys/en.71.1.2014.html ; cross-checked against STC table "EN 71-1:2014+A1:2018 Wind toy: cat 2 85, cat 3 90, LpC peak 110" https://stc.group/getfile/index/action/images/slug/tcd-infosheet-sound-level-requirements-2016nov-01].
- How the wind toy is blown in the EN test (8.28.2.9) [NF].
- **ASTM F963**: section 4.5 does not apply to "sounds produced by mouth-actuated toys where the sound pressure level is determined by the blowing action of the child" [S F963-11 text]; STC's table lists wind toys as "Not applicable" under ASTM F963-17 [S]. For reference its other limits (F963-17 per STC): close-to-the-ear LAeq 65 dB / LCpeak 110 dB; hand-held, table-top, floor LAeq 85 dB / LCpeak 115 dB.
- Expected level of this toy: not measured, no source [NF]. A-weighting is -6.0 dB at 340 Hz and -3.6 dB at 470 Hz [C], and the high figures quoted for printed whistles (118-130 dB) are creators' claims for multi-kHz pealess whistles, not comparable. Check with a sound-level meter at 50 cm against 85 dB(A) (the stricter category).

---

## 9. Print profile to start from (to be confirmed on the user's machine)

```json
{
  "material": "PLA (first article); PETG only if heat resistance is needed",
  "nozzle_mm": 0.4, "layer_height_mm": 0.12, "first_layer_height_mm": 0.2,
  "line_width_mm": 0.45, "wall_loops": 5,
  "top_solid_layers": 7, "bottom_solid_layers": 6,
  "infill": "100 % (or >= 5 walls with solid top/bottom; no sparse infill touching the airway)",
  "supports": "OFF",
  "brim": "none (patch ~2000 mm2); add if PETG lifts",
  "seam": "Rear, window flank facing +Y; verify in preview that no seam sits on the labium or windway exit",
  "nozzle_temp": "+5 C over the filament preset",
  "flow": "100-103 %; raise toward 105 % only if the leak test fails",
  "elephant_foot_compensation_mm": 0.2,
  "xy_hole_compensation_mm": "calibrate on the coupon (expect +0.05 to +0.15 per side)",
  "outer_wall_speed_mm_s": 30, "cooling": "100 % after layer 3",
  "scale": "never scale in the slicer"
}
```
Values other than those cited in sections 2-3 are [K] starting points.

## 10. Coupons to print before the bird [K]
1. **Voicing coupon** (30 min): the tail block alone with the vertical-slot windway, window and labium, glued or taped onto a jar/tube of known volume. Measure gap with feeler gauges, cut-up with calipers, listen. Print three gaps (1.1 / 1.3 / 1.5 mm) side by side.
2. **Roof coupon**: a 45 mm wide strip of the chosen roof section (43.5 degree tent and, if wanted, 55 degrees) plus the intended flat bridged strip, at 0.12 mm, to justify any `overhang_limit_deg` above 45.
3. **Hole coupon**: vertical holes 3.0-6.0 mm in 0.5 mm steps through the real wall thickness; record printed diameters for the hole compensation.
4. **Leak coupon**: a closed 5-perimeter cup of the wall section, water test.

## 11. Not found
- Any measured comparison of windway/labium print orientation on one whistle model.
- EN 71-1 8.17 (blow/suck durability) and 8.28.2.9 (wind-toy measurement procedure) parameters.
- ASTM F963-23 section 4.5 text (exemption confirmed only for -11 text and by a 2020 lab table for -17).
- A numeric minimum mouthpiece size.
- Measured SPL of any low-pitched (300-500 Hz) printed vessel flute.
- Slicer default values for Arachne minimum feature size / minimum wall width.
- A source quantifying chamber-wall roughness effects on a vessel flute.
- Direct text of Printables/MakerWorld/Thingiverse pages (HTTP 403); an API query to Printables was blocked by the session's permission policy and not retried.
- A minimum windway length for stable voicing.

## 12. Files produced
- `/tmp/claude-1000/-home-neuman-my-thing/cbf22764-116a-4870-bc2f-90231ddadd43/scratchpad/work/printing/orient_study.py` — orientation and roof study
- `/tmp/claude-1000/-home-neuman-my-thing/cbf22764-116a-4870-bc2f-90231ddadd43/scratchpad/work/printing/orient_study_results.json` — its numbers
- `/tmp/claude-1000/-home-neuman-my-thing/cbf22764-116a-4870-bc2f-90231ddadd43/scratchpad/work/printing/calc_numbers.py` — overlap, wall, labium-tip, A-weighting, sensitivity, print-time tables
- `/tmp/claude-1000/-home-neuman-my-thing/cbf22764-116a-4870-bc2f-90231ddadd43/scratchpad/work/printing/study_*_bellydown.stl` — five roof-variant solids (no voicing)
- `/tmp/claude-1000/-home-neuman-my-thing/cbf22764-116a-4870-bc2f-90231ddadd43/scratchpad/work/printing/dl/stc_sound.pdf` — STC sound-limit table (downloaded reference)
