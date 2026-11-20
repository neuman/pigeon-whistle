"""The two data literals the views and the boxes share.  The leading underscore keeps the view loader
off this file, and it imports nothing: a box builder can load it by path.

SENSITIVITY_RUNS: the tuning step's solver runs with one thing changed.  model/solve.py records the
grid study (GRID_STUDY) and nothing else, so these runs have their one home here.
COO_EVIDENCE: the headline numbers of the pitch analysis of the three coo recordings, copied from
the input coo-pitch-analysis (inputs/measurements/coo-pitch-analysis.md), each with its section.
Nothing here is a measurement of a printed whistle: none exists.
"""
from __future__ import annotations

SENSITIVITY_RUNS = {
    "recorded": "2026-11-19, the tuning step's solver runs: model/acoustics.py solve_resonance on cut-cell "
                "grids h = 0.5 and 0.4 mm, c = 346 m/s, pad 30 mm; each shift is against the unchanged "
                "design on the SAME grid. model/solve.py records the grid study only, so these runs "
                "are held here.",
    "grids_mm": (0.5, 0.4),
    # id: (what changed, closed note cents at h = 0.5 / 0.4, open note cents at h = 0.5 / 0.4)
    "rows": (
        ("vent_2_5", "vent reamed to 2.5 mm", (21.6, 26.5), (11.6, 14.2)),
        ("vent_3_0", "vent reamed to 3.0 mm", (57.6, 54.8), (31.1, 29.6)),
        ("vent_3_5", "vent reamed to 3.5 mm", (87.2, 90.1), (47.5, 49.2)),
        ("hole_minus", "finger hole 0.2 mm smaller", None, (-15.4, -13.8)),
        ("hole_plus", "finger hole 0.2 mm larger", None, (12.8, 15.5)),
        ("cutup_minus", "cut-up 0.5 mm shorter", (-43.3, -38.0), (-22.9, -20.2)),
        ("cutup_plus", "cut-up 0.5 mm longer", (34.5, 34.7), (18.6, 18.8)),
        ("height_minus", "window 0.5 mm lower", (-28.5, -27.5), (-15.2, -14.7)),
        ("height_plus", "window 0.5 mm higher", (26.3, 24.3), (14.2, 13.1)),
        ("desk", "rigid plane under the belly (desk or palm)", (-33.8, -34.8), (-18.2, -18.7)),
        ("pad_0", "fingertip pad flat on the window", (-678.0, -649.0), (-298.0, -289.0)),
        ("pad_3", "fingertip pad 3 mm off the design plane of the window (about 2 mm off the built flank)", (-71.5, -70.7), (-37.7, -37.3)),
    ),
    "pad": {"across_mm": 16.0, "thick_mm": 8.0,             # the rigid disc that stands for a fingertip
            "off_mm": 3.0},                                # its distance from the window in the run pad_3
    # the stopped notes as the two grids themselves gave them, Hz (each grid reads 1.4 to 1.9 % flat)
    "pad_0_on_grid_hz": {"closed": (225.5, 230.5), "open": (388.5, 392.2)},
    "flow_share_grid_mm": 0.6,                               # where the flow goes, on one grid
    "flow_share": {"closed": {"window": 0.877, "vent": 0.123},
                   "open": {"window": 0.463, "hole": 0.472, "vent": 0.065}},
}

COO_INPUT = "coo-pitch-analysis"
COO_EVIDENCE = {
    # input coo-pitch-analysis (inputs/measurements/coo-pitch-analysis.md), sections 3.1 to 3.3 and 5.
    # Medians over the used notes; Hz, seconds, dB.  Each recording is its own input record.
    "recordings": (
        {"id": "XC539061", "input": "coo-xc539061-paris-feral-pigeon", "where": "Paris, feral pigeon, under 50 cm",
         "length_s": 38.71, "notes_used": 18,
         "f0": (192.9, 255.8, 200.3), "loudest": (380.4, 510.8, 381.7), "loudest_is": "second harmonic",
         "loudest_weighted": 449.2, "h2_minus_h1_db": 10.6, "note_s": 0.380, "onset_s": 0.941, "gap_s": 0.562,
         "near_340": 0.030, "near_470": 0.333},
        {"id": "XC541143", "input": "coo-xc541143-paris-feral-pigeon", "where": "Paris, the same bird, about 30 cm",
         "length_s": 28.87, "notes_used": 22,
         "f0": (238.1, 296.1, 231.1), "loudest": (238.1, 467.1, 427.5), "loudest_is": "fundamental",
         "loudest_weighted": 291.6, "h2_minus_h1_db": -6.9, "note_s": 0.419, "onset_s": 1.131, "gap_s": 0.706,
         "near_340": 0.115, "near_470": 0.040},
        {"id": "sangli", "input": "coo-sangli-blue-rock-pigeon", "where": "Sangli, India, bird not identified",
         "length_s": 7.47, "notes_used": 4,
         "f0": None, "loudest": (470.6, 388.0, 453.4), "loudest_is": "pulsed carrier",
         "loudest_weighted": 390.3, "h2_minus_h1_db": None, "note_s": 0.835, "onset_s": 2.265, "gap_s": None,
         "near_340": 0.130, "near_470": 0.096},
    ),
    "summary": (
        # id, what, value, unit, section of the input
        ("pair_low", "loudest partial at the start of a note, XC539061", 380.0, "Hz", "0, 5"),
        ("pair_low_q1", "its lower quartile", 363.0, "Hz", "0, 5"),
        ("pair_low_q3", "its upper quartile", 413.0, "Hz", "0, 5"),
        ("pair_high", "loudest partial at its highest, XC539061", 511.0, "Hz", "0, 5"),
        ("pair_high_q1", "its lower quartile", 455.0, "Hz", "0, 5"),
        ("pair_high_q3", "its upper quartile", 533.0, "Hz", "0, 5"),
        ("pair_interval", "that rise", 5.1, "semitones", "5"),
        ("p75", "upper quartile of the loudest-partial energy, XC539061", 471.6, "Hz", "3.1"),
        ("centre_low", "energy-weighted loudest partial, lowest recording", 292.0, "Hz", "5"),
        ("centre_mid", "energy-weighted loudest partial, middle recording", 388.0, "Hz", "5"),
        ("centre_high", "energy-weighted loudest partial, highest recording", 449.0, "Hz", "5"),
        ("centre_mean", "geometric mean of the three", 371.0, "Hz", "5"),
        ("spread", "highest over lowest of the three", 1.54, "ratio", "5"),
        ("band_low", "band the evidence supports, low edge", 250.0, "Hz", "0"),
        ("band_high", "band the evidence supports, high edge", 550.0, "Hz", "0"),
        ("tolerance", "tightest tuning tolerance the evidence justifies, each way", 8.0, "%", "5"),
        ("tolerance_semitones", "the same in semitones", 1.3, "semitones", "5"),
        ("f0_ratio_a", "fundamental, apex over start, XC539061", 1.29, "ratio", "5"),
        ("f0_ratio_b", "fundamental, apex over start, XC541143", 1.27, "ratio", "5"),
        ("f0_rise_a", "that rise, XC539061", 4.4, "semitones", "3.1"),
        ("f0_rise_b", "that rise, XC541143", 4.1, "semitones", "3.2"),
        ("birds", "birds behind the three recordings, at most", 2.0, "birds", "0, 5"),
        ("paris_notes", "usable notes of the Paris bird, two days", 40.0, "notes", "0"),
        ("falloff_db", "partial level at 550 to 600 Hz against the note's loudest", -10.0, "dB", "0, 4"),
    ),
}
