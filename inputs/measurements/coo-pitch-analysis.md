# Pigeon coo pitch — independent re-measurement (evidence notes)

Independent check, done without reading the earlier analysis outputs (`coo-audio/bursts.json`, `coo-audio/spec.png`, `coo-audio/zoom.png` were NOT opened). All numbers below come from `results.json` produced by my own script unless a URL is given.

Base dir `S = /tmp/claude-1000/-home-neuman-my-thing/cbf22764-116a-4870-bc2f-90231ddadd43/scratchpad`
Work dir `W = S/work/pitch`

## 0. Bottom line

- The coo is a harmonic sound with an arch-shaped F0 of roughly **190-240 Hz at note start/end and 255-300 Hz at the apex** (Paris bird). The 2nd harmonic (H2) therefore runs roughly 380-600 Hz.
- "The loudest partial" is **not a stable property**: for the SAME bird it is H2 at a median 449 Hz in one recording (XC539061) and the fundamental at a median 292 Hz in the other (XC541143). The third recording (Sangli, India, other bird/s) is a pulsed coo at 388 Hz.
- Both Paris recordings agree only on the upper edge: partial level falls to about -10 dB (re note maximum) at 550-600 Hz and -16 to -17 dB at 600-650 Hz. The strongest region is 400-550 Hz in XC539061 (-2 to -4 dB) and 250-350 Hz in XC541143 (-1 to -3 dB). A band of roughly **250-550 Hz**, not two sharp frequencies, is what the evidence supports.
- If two frequencies must be named from the one recording where the loudest partial sweeps low-high-low (XC539061, H2): **low 380 Hz (IQR 363-413), high 511 Hz (IQR 455-533)**; energy-weighted centre 449 Hz (IQR 420-460).
- Project targets 340 / 470 Hz: 470 Hz is supported (33 % of XC539061 loudest-partial energy lies within +/-25 Hz; = pooled P75 472 Hz). **340 Hz is weakly supported**: it sits in the gap between the XC541143 mode (295 Hz) and the XC539061 mode (455 Hz); only 3 % / 11.5 % / 13 % of loudest-partial energy lies within +/-25 Hz of 340 Hz in XC539061 / XC541143 / Sangli. It is 1.9 semitones below my measured H2 start (380 Hz); 470 is 1.4 semitones below my measured H2 peak (511 Hz). The 340->470 interval (5.6 semitones) is close to the measured contour interval (380->511 = 5.1 semitones).
- Evidence is thin: **2 birds at most (1 identified individual in Paris with 40 usable notes over 2 days; >=1 unidentified bird in India with 4 notes)**, sex unknown throughout, hand-held recorder at <50 cm indoors/at a window, and the two same-bird recordings disagree by ~10-12 dB on the level of the fundamental relative to H2 whenever F0 is below ~250 Hz.

## 1. Inputs and licences (from `S/coo-audio/info.json`)

| key | Commons title | author | licence | description URL | format (ffprobe) |
|---|---|---|---|---|---|
| XC539061 | File:Columba livia - Rock Dove XC539061.mp3 | Marie-Lan Taÿ Pamart | CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0) | https://commons.wikimedia.org/wiki/File:Columba_livia_-_Rock_Dove_XC539061.mp3 (xeno-canto https://www.xeno-canto.org/539061) | mp3 320 kb/s, 44.1 kHz mono, 38.71 s |
| XC541143 | File:Columba livia - Rock Dove XC541143.mp3 | Marie-Lan Taÿ Pamart | CC BY-SA 4.0 | https://commons.wikimedia.org/wiki/File:Columba_livia_-_Rock_Dove_XC541143.mp3 (xeno-canto https://www.xeno-canto.org/541143) | mp3 320 kb/s, 44.1 kHz mono, 28.87 s |
| sangli | File:Blue rock pigeon song recorded in May 2012 at Sangli.wav | Sharadapte (Commons user; category "Files uploaded by Sharad Apte") | CC BY-SA 4.0 | https://commons.wikimedia.org/wiki/File:Blue_rock_pigeon_song_recorded_in_May_2012_at_Sangli.wav | pcm_s24le, 44.1 kHz mono, 7.47 s |

Recording conditions as stated in the Commons descriptions:
- XC539061: "Pedro the friendly feral pigeon waiting for their daily handful of seeds"; Paris, 2020-03-28 08:30; distance <50 cm; Olympus LS-12 internal mics; background "plic-ploc sounds from a nearby water point"; bird seen; type "adult, call, sex uncertain".
- XC541143: "Pedro the friendly feral pigeon begging for food at the window"; Paris, 2020-04-03 10:30; distance ~30 cm; background noise: vacuum cleaner; Olympus LS-12 internal mics; bird NOT seen; "adult, call, sex uncertain".
- sangli: "Blue rock pigeon song recorded in May 2012 at Sangli"; no equipment, distance, sex or number of birds given.
- `info.json` also lists a fourth file (File:Palomar-eva2007-Columba livia.ogg, CC BY-SA 2.5, author field empty, 1715 s dovecote ambience with hens and dogs). It was not among the three files I was given and was not analysed.

## 2. Method (exact)

Files: untrusted downloads, treated as data; decoded with ffmpeg; all Python run as `python3 -I`.

```
W=/tmp/claude-1000/-home-neuman-my-thing/cbf22764-116a-4870-bc2f-90231ddadd43/scratchpad/work/pitch
R=/tmp/claude-1000/-home-neuman-my-thing/cbf22764-116a-4870-bc2f-90231ddadd43/scratchpad/coo-audio/raw
mkdir -p $W/dec
for n in XC539061.mp3 XC541143.mp3 sangli.wav; do
  ffmpeg -nostdin -v error -y -i $R/$n -ac 1 -ar 11025 -f f32le $W/dec/${n%.*}.f32; done
python3 -I $W/scripts/analyze2.py $W        # -> results.json, tracks_*.json, spectrogram_tracks_*.png, loudest_partial_hist.png
python3 -I $W/scripts/filtercheck.py $W     # -> h2_h1_vs_f0_and_background.png, h2h1_by_f0.json
python3 -I $W/scripts/notezoom2.py $W $W/notes_zoom_XC539061.png XC539061:10 XC539061:11 XC539061:15 XC539061:16 XC539061:4 XC539061:18 XC539061:20 XC539061:22
```

Parameters (all in `W/scripts/analyze2.py`):
- Sample rate 11025 Hz; frames Hann 512 samples (46.4 ms), hop 64 samples (5.8 ms), FFT zero-padded to 8192 (1.35 Hz bins), parabolic peak interpolation.
- **Segmentation**: zero-phase 4th-order Butterworth band-pass (150-800 Hz for the Paris files, 250-650 Hz for Sangli), RMS envelope (23 ms; 60 ms for Sangli to bridge the pulses). Noise floor = median of the lowest quartile of the envelope; a segment = envelope > floor + 12 dB, gaps < 60 ms merged (100 ms Sangli). Note bounds reported at -12 dB (`dur12`) and -20 dB (`dur20`) re the note's own peak envelope.
- **F0 method A** (primary): Boersma-style normalised autocorrelation sampled at lags 1/f for f = 170...380 Hz in 1 Hz steps, Viterbi path (penalty 8 per octave of jump), then refinement to the interpolated spectral peak within +/-7 % (re-centred if the maximum is on the window edge). The 170-380 Hz search band is what makes it robust: it excludes both the octave-up error (H2 at 380-650 Hz, which is the stronger partial in XC539061) and the octave-down error (period-doubling subharmonic at 140-165 Hz near the apex).
- **F0 method B** (cross-check): harmonic summation sqrt|S(f)| + sqrt|S(2f)| + 0.5 sqrt|S(3f)| over the same grid, same Viterbi.
- **Stable harmonic run**: longest run of frames with autocorrelation strength >= 0.3 (dips <= 35 ms bridged), frame-to-frame F0 step < 0.08 octave, H1 within 30 dB of the loudest partial. Start/end values = median of the first/last 5 frames (29 ms) of that run; apex = maximum of the 5-point-median-smoothed F0 in the run.
- **Loudest partial**: argmax of the frame spectrum in 150-1500 Hz; harmonic number = round(f_loud/F0) with 1.5 allowed (sub-harmonic regime). Reported at the same start / apex / end instants as F0, plus its own maximum (`lp_max`) and energy-weighted percentiles.
- **Level differences**: dB between interpolated spectral peaks of the same frame.
- **Tonality**: (i) -3 dB and -10 dB width of the loudest partial in a 93 ms Hann frame (window-limited floor is 1.44 bins = 15.5 Hz at -3 dB); (ii) "purity" = fraction of the 100-2000 Hz frame energy lying within +/-45 Hz of the loudest partial; (iii) -3/-10 dB width of the whole-note Welch spectrum (includes the glide).
- **"Used" notes**: Paris files: `clean` = strength >= 0.6, stable run >= 0.15 s and >= 50 % of `dur20`, methods A and B agree (within 0.05 octave) on >= 50 % of frames. Sangli: the 4 segments with `dur12` >= 0.6 s (the long pulsed coos).
- **Sangli is pulsed** (amplitude-modulated at ~19 Hz), so autocorrelation F0 is not meaningful; I report the carrier = strongest component in 250-650 Hz from 93 ms frames (9-point median) and test for a component at half that frequency.

Visual verification (I rendered and inspected all of these):
- `W/spectrogram_tracks_XC539061.png`, `W/spectrogram_tracks_XC541143.png`, `W/spectrogram_tracks_sangli.png` — full-length spectrograms 0-1 kHz with F0 (A and B), loudest partial, note bounds, rejected segments.
- `W/notes_zoom_XC539061.png`, `W/notes_zoom_XC541143.png` — 8 single notes each at high time resolution with tracks.
- `W/overview_XC539061.png`, `W/overview_XC541143.png`, `W/overview_sangli.png` — 0-2 kHz overviews; `W/zoom_notes.png` — 186 ms vs 23 ms windows plus spectra; `W/sangli_detail.png` — Sangli at three window lengths plus Hilbert envelope.
- `W/loudest_partial_hist.png` — energy-weighted histogram of loudest-partial frequency per recording with 340/470 Hz marked.
- `W/h2_h1_vs_f0_and_background.png` — H2-H1 level vs F0, partial level vs partial frequency, background spectra.

What the pictures show: the cyan F0 track lies on the lowest dark arch in every clean note; method B (green dotted) overlaps it (median per-note agreement 0.955 for XC539061, 0.90 for XC541143; median H2/2 - F0 = -0.42 Hz in both, i.e. H2 is exactly twice F0). Tracking was wrong only in segments that I then excluded (noisy/irregular notes, listed in section 3).

## 3. Results per recording

Format: median (Q1-Q3). All frequencies Hz, durations s, levels dB.

### 3.1 XC539061 (Paris, "Pedro", <50 cm)

Segments found 26; 23 with a stable harmonic run; **18 used** (note ids 2, 4-20 in `results.json["XC539061"]["notes"]`). Not used: #1 (0.54 s, weak, run 0.10 s), #3 (2.27 s, part of a complex vocalisation at 1.85-2.8 s), #21 (21.45 s, run only 0.18 s), #22 and #23 (27.2 s, 28.0 s: noisy coos without harmonic structure, energy peak 340 / 322 Hz), plus 3 rejected segments (4.59 s, 26.75 s, 37.46 s).

| quantity | value |
|---|---|
| notes used | 18 |
| F0 start / apex / end | 192.9 (183.4-207.9) / 255.8 (228.4-277.7) / 200.3 (196.8-206.5); range of apex 209-325 |
| F0 method B start / apex / end | 191.0 (181.5-205.2) / 252.5 (224.5-273.0) / 200.0 (194.0-209.8) |
| F0 apex/start ratio | 1.288 (1.238-1.429) = 4.4 semitones (3.7-6.2) |
| H2 start / apex / end | 381.1 (357.8-412.0) / 507.6 (454.5-554.1) / 386.2 (376.5-423.5) |
| loudest partial start / at F0 apex / own max / end | 380.4 (362.6-412.6) / 455.9 (372.0-514.3) / 510.8 (454.6-532.5) / 381.7 (374.7-414.2) |
| harmonic number of loudest partial | start: H2 in 18/18; apex: H2 in 14, H1 in 4; end: H2 in 17, H1 in 1; by energy: H2 92.0 %, H1 7.8 % |
| loudest partial, energy-weighted per-note median | 449.2 (420.3-459.8) |
| loudest partial, pooled energy-weighted percentiles | P5 306.6, P10 372.0, P25 407.9, P50 441.9, P75 471.6, P90 507.6, P95 523.1; mode bin 450-460 |
| whole-note spectrum peak | 452.2 (417.9-463.6) |
| note duration | -12 dB: 0.380 (0.353-0.429); -20 dB: 0.454 (0.420-0.494); stable harmonic run 0.366 (0.285-0.421) |
| inter-note interval | onset-to-onset 0.941 (0.843-0.982), n=20 intervals < 2 s; silent gap (-12 dB off to on) 0.562 (0.471-0.610) |
| level F0 minus loudest partial | -10.6 (-11.7 to -8.7) median over frames; energy-weighted -10.9 (-11.9 to -9.5) |
| level H2 minus H1 | whole run +10.6 (8.7-11.7); at start +12.4 (9.4-14.6); at apex +6.3 (0.0-8.6); at end +12.4 (10.1-14.2) |
| sub-harmonic at apex | 1.5xF0 component at -9.1 (-12.3 to -6.4) re H1; 0.5xF0 at -39.2 |
| tonality of loudest partial | -3 dB width 22.9 (21.5-25.6) Hz in a 93 ms frame (window floor 15.5 Hz); -10 dB width 48.4 (45.9-52.5); purity 0.81 (0.76-0.86), energy-weighted 0.87 (0.82-0.89) |
| whole-note spectrum width (includes glide) | -3 dB 33.6 (29.6-40.4); -10 dB 92.2 (70.0-132.2) |
| SNR (note peak re noise floor, 150-800 Hz) | 40.2 (38.0-42.1) dB |

### 3.2 XC541143 (Paris, same individual per description, ~30 cm, vacuum cleaner running, bird not seen)

Segments 23; **22 used** (ids 1-22). Not used: #23 (27.64 s, a flat 204-224 Hz note with a 0.2 s noisy onset).

| quantity | value |
|---|---|
| notes used | 22 |
| F0 start / apex / end | 238.1 (230.5-249.2) / 296.1 (292.4-314.4) / 231.1 (228.7-236.1); range of apex 261-339 |
| F0 method B start / apex / end | 239.0 (231.0-248.5) / 292.0 (287.5-311.0) / 231.0 (225.2-237.0) |
| F0 apex/start ratio | 1.270 (1.203-1.343) = 4.1 semitones (3.2-5.1) |
| H2 start / apex / end | 478.8 (462.9-497.5) / 592.5 (583.6-627.4) / 458.9 (449.6-466.8) |
| loudest partial start / at F0 apex / own max / end | 238.1 (233.0-249.2) / 296.1 (292.4-314.4) / 467.1 (420.9-491.5) / 427.5 (268.7-440.5) |
| harmonic number of loudest partial | start: H1 in 22/22; apex: H1 in 22/22; end: H2 in 13, H1 in 8, 1.5 in 1; by energy: H1 92.4 %, H2 7.5 % |
| loudest partial, energy-weighted per-note median | 291.6 (283.8-305.9) |
| loudest partial, pooled energy-weighted percentiles | P5 241.4, P10 251.2, P25 273.2, P50 290.2, P75 308.5, P90 331.0, P95 468.8; mode bin 290-300 |
| whole-note spectrum peak | 292.0 (286.0-309.5) |
| note duration | -12 dB: 0.419 (0.402-0.453); -20 dB: 0.504 (0.472-0.532); stable harmonic run 0.360 (0.318-0.398) |
| inter-note interval | onset-to-onset 1.131 (1.094-1.211), n=21; silent gap 0.706 (0.674-0.766) |
| level F0 minus loudest partial | 0.0 (0.0-0.0) (F0 is the loudest partial); energy-weighted -0.05 |
| level H2 minus H1 | whole run -6.9 (-8.6 to -4.8); at start -4.1 (-5.5 to -2.7); at apex -10.7 (-16.1 to -9.1); at end +0.15 (-1.3 to +1.1) |
| sub-harmonic at apex | 1.5xF0 at -12.8 (-13.4 to -12.3) re H1; 0.5xF0 at -30.9 |
| tonality of loudest partial | -3 dB width 21.5 (21.0-21.5) Hz; -10 dB 42.8 (40.5-45.8); purity 0.66 (0.63-0.71), energy-weighted 0.74 (0.70-0.80) |
| whole-note spectrum width | -3 dB 26.2 (23.2-28.3); -10 dB 75.4 (65.3-78.1) |
| SNR | 40.5 (39.7-42.6) dB |

Caveat on "start": many XC541143 notes begin with 50-120 ms of breathy, non-harmonic sound containing an up-gliding component (roughly 250->400 Hz); the harmonic arch starts after it. The start value above is the start of the harmonic arch. Measured instead at the -12 dB envelope onset without the stability gate (an earlier pass of my own script), F0 "start" was 199 (176-234) Hz and the loudest partial there 337 (281-355) Hz, so the start figure moves by ~40 Hz with the definition. Apex and energy-weighted values do not depend on it.

### 3.3 sangli (India, unidentified bird/s; pulsed "rolling" coo)

Segments 6; **4 used** (ids 1, 2, 4, 6: the long pulsed coos at 0.26, 1.43, 3.70, 6.42 s). Not used: #3 (2.93 s, 0.16 s long, a harmonic pair 272 / 543 Hz with the upper 14 dB stronger) and #5 (5.21 s, down-sweeps 600->300 Hz); I cannot tell whether those come from the same bird.

| quantity | value |
|---|---|
| notes used | 4 |
| F0 | not separable from the loudest partial: there is no component at half the carrier frequency (level at carrier/2 = -27.5 dB re carrier, background in 140-260 Hz = -29.5 dB). So either F0 = the carrier (~388 Hz) or a 194 Hz fundamental is suppressed by more than ~27 dB. A 100 Hz hum line is present throughout. |
| carrier (loudest partial) start / middle / end | 470.6 (449.3-473.5) / 372.9 (367.5-380.1) / 453.4 (427.1-477.1) — start and end are noisy single-frame-cluster estimates; 3 of 4 notes open with a ~470-480 Hz element lasting ~0.1-0.2 s |
| carrier in the loud core (frames within 6 dB of note max) | 388.0 (383.1-390.6) |
| loudest partial, energy-weighted per-note median | 390.3 (386.4-391.7) |
| pooled energy-weighted percentiles | P5 348.7, P10 360.1, P25 375.3, P50 388.6, P75 401.2, P90 458.4, P95 479.6; mode bin 380-390 |
| whole-note spectrum peak | 382.2 (377.9-387.6) |
| note duration | -12 dB: 0.835 (0.818-0.853); -20 dB: 0.843 (0.827-0.884) |
| inter-note interval | onset-to-onset 1.175, 2.265, 2.728 s (n=3; median 2.265) |
| level F0 minus loudest partial | not measurable (see F0 row) |
| pulse (AM) rate | 18.9 (18.4-23.0) Hz; per note 17.2, 18.8, 35.0, 19.0 (the 35.0 is probably the 2nd harmonic of the pulse rate) |
| tonality | -3 dB width 23.5 (22.9-25.2) Hz in a 93 ms frame; -10 dB 65.9 (62.9-67.4); purity 0.61 (0.59-0.63), energy-weighted 0.73; whole-note spectrum -3 dB 37.6 (26.9-49.4), -10 dB 181.7 (150.8-199.2) — broadened by the pulsing |
| SNR | 26.9 (26.6-27.2) dB; envelope is flat-topped near full scale (peak 0.706), and energy at ~1100-1300 Hz (3x carrier) with little at 2x suggests limiting/clipping in the file |

## 4. Why the two same-bird recordings disagree (`W/h2_h1_vs_f0_and_background.png`, `W/h2h1_by_f0.json`)

H2 minus H1 (dB), median over frames, binned by F0:

| F0 bin (Hz) | XC539061 | XC541143 | difference |
|---|---|---|---|
| 180-200 | +11.8 | (n<15) | |
| 200-220 | +12.0 | -0.2 | 12.2 |
| 220-240 | +12.2 | -0.5 | 12.7 |
| 240-260 | +8.3 | -2.3 | 10.6 |
| 260-280 | +3.4 | -5.2 | 8.6 |
| 280-300 | -5.6 | -8.8 | 3.2 |
| 300-320 | -11.4 | -13.4 | 2.0 |
| 320-340 | (n<15) | -17.7 | |

- Above F0 ~280 Hz the two recordings agree within 2-3 dB; below ~250 Hz XC539061 has ~10-12 dB less fundamental relative to H2. The size of the gap shrinks steadily as F0 rises through 240-300 Hz, which is the pattern a high-pass effect acting below ~300 Hz would give.
- So at the same F0 the two recordings give a different H1/H2 balance: the flip of the loudest partial is not explained by the higher F0 in XC541143 alone. Which recording is closer to what the bird emits is unknown (XC539061 may have attenuated lows, or XC541143 boosted ones). Causes I cannot separate: recorder low-cut filter, microphone placement/room, or the bird's own vocal-tract setting. The Olympus LS-12 has a switchable 100 Hz / 300 Hz low-cut (https://www.soundonsound.com/reviews/olympus-ls12-ls14, https://www.manualsdir.com/manuals/482718/olympus-ls-12-ls-14.html?page=67); whether it was engaged is not stated anywhere — not found. The XC539061 background spectrum is roughly flat from 50 to 500 Hz (-78.7, -82.5, -81.9, -78.7 dB/Hz in 50-100, 100-200, 200-300, 300-500 Hz), which neither proves nor excludes a filter.
- Also different between the days: F0 itself is higher in XC541143 (apex 296 vs 256 Hz; energy-weighted F0 285 vs 229 Hz).
- Median partial level re note maximum, by partial frequency (H1 and H2 pooled, stable runs of used notes; confounded with position in the note because note edges are quieter):

| partial frequency (Hz) | XC539061 | XC541143 |
|---|---|---|
| 150-200 | -19.6 | |
| 200-250 | -15.2 | -6.0 |
| 250-300 | -8.7 | -2.7 |
| 300-350 | -6.2 | -1.2 |
| 350-400 | -6.5 | (n<20) |
| 400-450 | -3.7 | -12.0 (n=47) |
| 450-500 | -2.3 | -7.0 |
| 500-550 | -4.1 | -7.4 |
| 550-600 | -10.4 | -10.4 |
| 600-650 | -17.3 | -15.8 |
| 650-700 | | -19.9 |

- Common to both: level falls steeply above ~550 Hz. They differ in where the maximum is (400-550 Hz vs 250-350 Hz).
- Near the apex of the higher notes (F0 above ~280 Hz) a component at 1.5xF0 appears (period doubling): 9-13 dB below H1. A pure-tone whistle cannot reproduce this roughness.

## 5. What two whistle frequencies does this support?

Candidates from the data, by rule used:

| rule | low (closed) | high (open) | interval | source |
|---|---|---|---|---|
| extremes of the loudest partial within a note, XC539061 (H2) | 380 (363-413) | 511 (455-533) | 5.1 semitones | 18 notes, 1 bird |
| same rule, XC541143 (loudest = F0) | 238 (231-249) | 296 (292-314) | 3.8 semitones | 22 notes, same bird |
| H2 extremes, XC541143 (not the loudest there) | 479 / 459 (start / end) | 593 (584-627) | 3.7-4.4 semitones | 22 notes |
| Sangli pulsed coo | 388 (383-391) body | ~470 opening element (449-474) | 3.3 semitones, falling not rising | 4 notes, weak |
| energy-weighted centre only | 292 (XC541143), 388 (Sangli), 449 (XC539061); geometric mean 371 | | | 3 recordings |
| project targets | 340 | 470 | 5.6 semitones | |

Energy of the loudest partial within +/-25 Hz of a candidate frequency (fraction of the pooled, per-note-normalised energy):

| centre Hz | XC539061 | XC541143 | sangli |
|---|---|---|---|
| 240 | 0.000 | 0.186 | 0.000 |
| 290 | 0.062 | 0.622 | 0.011 |
| 340 | 0.030 | 0.115 | 0.130 |
| 380 | 0.140 | 0.001 | 0.732 |
| 390 | 0.243 | 0.002 | 0.709 |
| 450 | 0.372 | 0.027 | 0.078 |
| 470 | 0.333 | 0.040 | 0.096 |
| 500 | 0.186 | 0.046 | 0.053 |
| 510 | 0.167 | 0.037 | 0.032 |
| whole 300-500 band | 0.83 | 0.31 | 0.976 |

Reading:
- From my measurements alone the best-supported pair for "loudest partial, low then high" is **about 380 Hz and about 500-510 Hz** (XC539061), with within-recording IQR of about +/-7 % on each; if "high" is taken as where the energy concentrates rather than the momentary peak, **450-470 Hz**.
- 470 Hz is consistent with the data. 340 Hz is a compromise value between recordings rather than a measured mode; 380-390 Hz has more direct support (XC539061 H2 start/end 380/382; Sangli body 388).
- Between-recording spread is far larger than within-recording spread: the energy-weighted loudest partial is 292, 388 and 449 Hz in the three files (a factor 1.54). A tuning tolerance tighter than roughly +/-8 % (1.3 semitones) on either note is not justified by this evidence.
- The interval is the more repeatable feature: F0 apex/start ratio 1.29 (XC539061) and 1.27 (XC541143), i.e. 4.1-4.4 semitones; the loudest-partial extremes in XC539061 give 5.1 semitones. 340->470 is 5.6 semitones (ratio 1.38), 380->510 is 5.1 (ratio 1.34), 380->470 is 3.7 (ratio 1.24).

How thin:
- Birds: 1 identified individual (Paris, 2 recordings 6 days apart, 18 + 22 used notes) plus an unknown number (>=1) at Sangli with 4 notes. Effective n for between-bird variation is 2.
- Sex, age class beyond "adult", and call type are not established. The Paris notes are single moaning coos repeated about once per second by a hand-fed bird waiting for food; the Sangli notes are pulsed coos. Whether these are the same call type is my reading of the spectrograms, not something the metadata states.
- Recording chain: hand-held recorder with internal mics at <50 cm indoors/at a window (Paris), MP3 320 kb/s; unknown equipment and apparent limiting plus 100 Hz hum (Sangli). No calibrated level, no free-field recording, no control of low-cut settings.
- The ranking of H1 vs H2 flips between the two same-bird recordings, so "which partial is loudest at the bird" is unresolved.

## 6. Published measurements (quick web search)

- A published numeric fundamental or dominant frequency for the *Columba livia* coo: **not found** in this search.
- Baptista & Abs 1983, "Vocalizations", in Abs (ed.) *Physiology and Behaviour of the Pigeon*, Academic Press, pp. 3-18: citation confirmed via papers citing it (e.g. https://sora.unm.edu/sites/default/files/journals/auk/v116n03/p0737-p0748.pdf), but the chapter text and any Hz values in it: not found (not online).
- Goller & Larsen 1997, J Exp Biol 200:2165-2176, "In situ biomechanics of the syrinx and sound generation in pigeons" (doi 10.1242/jeb.200.16.2165): PDF returned HTTP 403 (https://cob.silverchair.com/jeb/article-pdf/3405852/jexbio_200_16_2165.pdf); numbers not retrieved.
- Elemans et al. 2015, Nat Commun 6:8978 (https://pmc.ncbi.nlm.nih.gov/articles/PMC4674827/): Fig. 6 shows spectrograms of spontaneous *Columba livia* vocalisations and ex vivo syrinx F0; the text gives no numeric pigeon F0 (only "iso-F0 contours at fixed intervals (Columba, 10 Hz)").
- Beckers, Suthers & ten Cate 2003, PNAS (https://pmc.ncbi.nlm.nih.gov/articles/PMC165882): different genus. "The f0 of coo vocalizations in Eurasian collared doves is ≈500 Hz"; in the trachea the 2nd and 3rd harmonics are "on average, -11 and -20 dB" re the fundamental and "the relative intensity of 2f0 measured in the trachea is on average 32 dB higher than in the emitted coo"; conclusion "the pure-tone quality of turtledove song originates by a source-filtering mechanism". Relevance: in *Streptopelia* the emitted coo is a near-pure tone at F0; my Paris recordings of *C. livia* are not like that (H2 within about +/-11 dB of H1).
- xeno-canto remark on XC637685 (https://xeno-canto.org/637685), a recordist's annotation not a measurement: "the low frequency song (less than 800Hz)" of a feral pigeon. Consistent with my spectra (almost no energy above ~700 Hz).
- Goodwin (*Pigeons and Doves of the World*): not searched online; no numbers found.
- Wikipedia "Rock dove" (https://en.wikipedia.org/wiki/Rock_dove): qualitative description only, no Hz.
- Not a vocalisation, for disambiguation only: rock pigeon wing tones "700±50 Hz" (https://journals.biologists.com/jeb/article/219/14/2173/15376/Specialized-primary-feathers-produce-tonal-sounds).

## 7. Files and data templates

Outputs in `W = /tmp/claude-1000/-home-neuman-my-thing/cbf22764-116a-4870-bc2f-90231ddadd43/scratchpad/work/pitch`:
- `W/results.json` — everything in the tables above.
- `W/tracks_XC539061.json`, `W/tracks_XC541143.json`, `W/tracks_sangli.json` — per-note frame tracks.
- `W/analyze2.log` — console summary of the final run.
- `W/h2h1_by_f0.json` — table in section 4.
- PNGs listed in section 2.
- Scripts: `W/scripts/analyze2.py` (main), `W/scripts/filtercheck.py`, `W/scripts/notezoom2.py`, `W/scripts/overview.py`, `W/scripts/zoom.py`, `W/scripts/sangli_look.py`, `W/scripts/peaks.py` (per-frame peak dump used for exploration).
- Decoded audio: `W/dec/XC539061.f32`, `W/dec/XC541143.f32`, `W/dec/sangli.f32` (float32 LE mono 11025 Hz).

`results.json` structure:

```json
{
  "XC539061": {
    "meta": {"floor_db": -54.3, "thr_db": -42.3, "duration_s": 38.68},
    "n_segments": 26, "n_notes_all": 23, "n_notes_used": 18,
    "summary_used": {"f0_start": {"n": 18, "median": 192.9, "q1": 183.4, "q3": 207.9, "min": 150.7, "max": 222.3}, "...": "same shape for every key"},
    "pooled_loudest_partial_energy_weighted": {"p5": 306.6, "p10": 372.0, "p25": 407.9, "p50": 441.9, "p75": 471.6, "p90": 507.6, "p95": 523.1, "mode_10Hz_bin_centre": 455.0},
    "notes": [{"t_on": 1.31, "t_off": 1.67, "dur12": 0.36, "dur20": 0.45, "kind": "tonal", "clean": true, "f0_start": 169, "f0_apex": 209, "f0_end": 203, "lp_start": 341, "lp_at_apex": 353, "lp_max": 413, "lp_end": 375, "lp_hn_start": 2.0, "...": "..."}],
    "rejected": [{"t_on": 4.592, "t_off": 4.858, "dur12": 0.265, "reject": "no stable harmonic run >=100 ms"}],
    "summary_all_tonal_segments": {"...": "same keys, all 23 tonal segments"}
  },
  "XC541143": {"...": "same"},
  "sangli": {"...": "summary_used keys: carrier_start, carrier_mid, carrier_end, carrier_core_median, half_carrier_level_re_carrier_db, bg_140_260_median_re_carrier_db, am_rate_hz, lp_ew_*, note_spectrum_*"}
}
```

Read-back template:

```python
# python3 -I thisfile.py
import json
W = "/tmp/claude-1000/-home-neuman-my-thing/cbf22764-116a-4870-bc2f-90231ddadd43/scratchpad/work/pitch"
R = json.load(open(f"{W}/results.json"))
for rec in ("XC539061", "XC541143"):
    s = R[rec]["summary_used"]
    for k in ("f0_start", "f0_apex", "f0_end", "lp_start", "lp_max", "lp_end", "lp_ew_median", "dur12", "onset_to_onset_lt2s", "dL_h2_minus_h1_med", "bw3_med", "purity_med"):
        print(rec, k, s[k]["median"], s[k]["q1"], s[k]["q3"], s[k]["n"])
tracks = json.load(open(f"{W}/tracks_XC539061.json"))   # list aligned with R["XC539061"]["notes"]
tr = tracks[9]                                            # note #10
a, b = tr["run"]                                          # stable harmonic run, frame indices
t, f0, loud = tr["t"][a:b], tr["f0"][a:b], tr["fl"][a:b]  # seconds, Hz, Hz
```

Headline numbers as a block for downstream use:

```json
{
  "XC539061": {"n_notes": 18, "f0_start_apex_end_hz": [192.9, 255.8, 200.3], "loudest_start_max_end_hz": [380.4, 510.8, 381.7], "loudest_harmonic": 2, "loudest_energy_weighted_median_hz": 449.2, "h2_minus_h1_db": 10.6, "dur12_s": 0.380, "onset_to_onset_s": 0.941},
  "XC541143": {"n_notes": 22, "f0_start_apex_end_hz": [238.1, 296.1, 231.1], "loudest_start_max_end_hz": [238.1, 467.1, 427.5], "loudest_harmonic": 1, "loudest_energy_weighted_median_hz": 291.6, "h2_minus_h1_db": -6.9, "dur12_s": 0.419, "onset_to_onset_s": 1.131},
  "sangli":   {"n_notes": 4,  "f0_hz": null, "carrier_core_hz": 388.0, "loudest_energy_weighted_median_hz": 390.3, "pulse_rate_hz": 18.9, "dur12_s": 0.835, "onset_to_onset_s": [1.175, 2.265, 2.728]}
}
```

## 8. Limits of this analysis

- F0 search band fixed at 170-380 Hz; a note with F0 outside it would be mis-tracked (none seen in the spectrograms).
- Start/end values depend on the onset definition by up to ~40 Hz (section 3.2 caveat).
- Sangli numbers rest on 4 noisy notes; carrier start/end there are indicative only.
- Levels are relative within a frame; no absolute SPL and no correction for microphone or room response.
- Nothing in `/home/neuman/my-thing` or `/home/neuman/Documents/work/nopekit` was read or modified.
