"""pigeon.py - the pigeon whistle model: every input, and what follows from it.

A palm-sized chubby city pigeon that is a vessel flute: blown through its tail, one finger hole
on its back.  Design centre 340 Hz with the hole closed, 470 Hz open.

Frame: X from the tail tip (x = 0, the mouthpiece) to the head, +Y is the bird's LEFT (the window
flank), Z up = build direction, bed at z = 0.  The print pose is the desk pose: belly down.
Units: mm, degrees, grams, Hz; each field's unit is in PARAMS.

build(config) is pure, deterministic and fast (about 0.1 s): closed forms and coarse lattice
integrals of the same signed fields that model/geom.py meshes.  It writes nothing.  The printable
mesh is made by `python3 model/mesh.py`, which writes print/pigeon-whistle-<geometry_hash>.stl;
build() only publishes that path.

Pitch in build() is the lumped Helmholtz closed form of model/acoustics.py,
f = c/(2 pi) sqrt(sum G / V) with G = A / (t + k r_eq) per opening.  Its three end-correction factors
(k_window, k_hole, k_vent) are Config fields CALIBRATED against the potential-flow solve of this
geometry (model/solve.py); the closed form is the fast stand-in, the solve is the reference, and a
gate holds the two within 1 % of each other in all four states (hole closed / open x vent open /
plugged).  Neither has been checked against a printed, blown whistle.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields

import acoustics
import geom


@dataclass
class Config:
    """Every input.  Nothing outside this dataclass is an input; proportions that only make sense
    together (blend radii, wing and chest ratios) are commented constants in geom.py."""

    # ------------------------------------------------------------------ shape
    body_center_x_mm: float = 77.5
    """Body ellipsoid centre.  Leaves x 30-41 for the window and labium ramp behind the body, and
    the breast ends near x = 117 so the whole bird stays inside 118 mm."""
    body_center_z_mm: float = 24.0
    """Body centre height: the belly then meets the bed at 40 deg from vertical with no skirt band."""
    body_radius_x_mm: float = 37.5
    """Body half-length.  With the other two radii, and the rump lobe, it sets the chamber at 118.8 cm^3."""
    body_radius_y_mm: float = 33.4
    """Body half-width: 66.8 mm, plus 0.6 mm wing bars, inside the 68 mm width limit."""
    body_radius_z_mm: float = 35.0
    """Body half-height: back at z = 59, which leaves the head 8.7 mm proud of it."""
    chest_lead_mm: float = 16.5
    """Chest ellipsoid centre ahead of the body centre: the breast leads the head (a pigeon's does)."""
    head_center_x_mm: float = 96.0
    """Head tucked onto the chest; with the beak it ends at x = 115.0, behind the crop (116.7)."""
    head_center_z_mm: float = 54.2
    """Head top at 67.7 mm, inside the 68 mm height limit."""
    head_radius_mm: float = 13.5
    """Small solid head: head diameter / body width = 0.40, the ratio the character judge read as pigeon."""
    beak_length_mm: float = 7.5
    """Slim straight bill, about a quarter of the head's diameter."""
    beak_pitch_deg: float = 35.0
    """Bill points this far below horizontal, its tip resting 1.2 mm deep in the crop."""
    beak_base_radius_mm: float = 3.2
    """Bill radius at the face."""
    beak_tip_radius_mm: float = 1.5
    """Blunt tip: no thorn at face height, and three 0.45 mm lines wide so it prints as a solid."""
    eye_radius_mm: float = 2.0
    """Eye dimple radius at the head surface: nine lines across, it survives the nozzle."""
    eye_depth_mm: float = 1.1
    """Eye dimple depth: a cone this shallow has every face steeper than 45 deg."""
    eye_azimuth_deg: float = 62.0
    """Eyes set to the side, as on a pigeon (0 would look forward)."""
    eye_elevation_deg: float = 18.0
    """Eyes above the head's equator."""
    wing_center_z_mm: float = 28.0
    """Wing centre height: low on the flank so the front view has no raised shoulders."""
    wing_pitch_deg: float = -8.0
    """Wing pitch: tips slightly up toward the rump."""
    wing_bar_width_mm: float = 2.5
    """Two wing bars per wing: the one pigeon marking that works in a single filament colour."""
    wing_bar_proud_mm: float = 0.6
    """Bar relief: five 0.12 mm layers, readable but not a ledge."""
    wing_bar_length_mm: float = 18.0
    """Bar length across the upper flank."""
    foot_length_mm: float = 14.0
    """Two low oval foot pads under the chest."""
    foot_width_mm: float = 9.0
    """Foot pad width."""
    foot_height_mm: float = 3.5
    """Foot pad height."""
    tail_half_width_mm: float = 14.0
    """Half-width of the tail root and rump: 28 mm, so the window flank is a flat vertical wall with
    room for the lobe (lobe_width_mm) behind it."""
    tail_tip_half_width_mm: float = 12.3
    """Half-width at the tail tip: a 24.6 x 14 mm mouthpiece that leaves >= 1.5 mm of rim beside the inlet."""
    tail_top_z_mm: float = 14.0
    """Tail top: 4.7 mm over the windway, 3.5 mm of roof rim left at the inlet after the edge radius."""
    lip_stop_x_mm: float = 15.0
    """A full-width rise in the tail top stops the lips here, 15 mm short of the window."""
    lip_stop_rise_mm: float = 3.0
    """Height of the lip stop."""
    self_support_deg: float = 40.0
    """Bottom-up trim of the skin: nothing leans out more than this from vertical (limit 45)."""

    # ------------------------------------------------------------------ chamber
    shell_wall_mm: float = 2.2
    """Shell wall: five 0.45 mm perimeters, airtight."""
    floor_mm: float = 2.1
    """Chamber floor above the bed (17 layers): the thinnest section of the shell."""
    roof_angle_deg: float = 42.0
    """Every chamber roof plane leans this far from vertical: 3 deg inside the 45 deg limit."""
    lobe_ridge_z_mm: float = 23.25
    """Ridge of the rump lobe.  Its eave on the window wall then sits 0.76 mm ABOVE the lintel, so the
    roof lands on a wall, and the rump crest above it is 25.65 mm."""
    lobe_width_mm: float = 15.0
    """Width of the rump lobe, from the window's inner plane to its far wall (the rest of the rump, on
    the bird's right, is solid).  The lobe section beside the jet is then 253 mm^2 = 5.7 x the window:
    the narrowest the design allows (>= 250 mm^2 and >= 4.5 x), taken because the window's own
    conductance was 16 % too high for 340 Hz and a throat lowers it without narrowing the jet."""

    # ------------------------------------------------------------------ voicing (acoustic nominal sizes)
    windway_length_mm: float = 30.0
    """Windway from the tail tip to its exit at x = 30."""
    windway_height_mm: float = 6.3
    """Slot height (Z) = jet width = window height.  Solved: with the 7.0 mm cut-up it makes the 44 mm^2
    window whose conductance (4.08 mm) leaves the vent-plugged note 90 cents under 340 Hz."""
    windway_floor_z_mm: float = 3.0
    """Windway floor above the bed, clear of elephant foot; the window sill is at the same height,
    0.9 mm above the chamber floor, so the bird drains tail-down."""
    windway_gap_inlet_mm: float = 2.6
    """Slot gap at the lips: 2:1 convergence to the exit."""
    windway_gap_exit_mm: float = 1.3
    """Slot gap at the exit (the jet thickness)."""
    windway_skew_deg: float = 4.5
    """The slot is turned this far outward in plan: the inlet sits 2.9 mm inside the tail tip while the
    exit reaches the flank.  Windway, window and labium turn together, so the jet still meets the edge."""
    windway_exit_chamfer_mm: float = 0.6
    """45 deg chamfers on both exit lips (recorder and organ practice: 0.5-0.7 mm)."""
    cutup_mm: float = 7.0
    """Cut-up: windway exit to labium edge."""
    window_wall_mm: float = 4.0
    """Wall depth at the window, mid cut-up (the deep end of the 3-4 mm allowed).  The window opens
    straight from the flank into the lobe."""
    lintel_flat_mm: float = 4.0
    """Flat bridge over the window at the labium; with the ramp receding the outermost of its three
    strands is 4.2 mm.  The rest of the window top is 43 deg haunches."""
    labium_tip_mm: float = 0.5
    """Flat on the labium tip: one line wide.  A knife edge is truncated by the slicer anyway and that
    lengthens the cut-up by an unknown amount."""
    labium_ramp_deg: float = 25.0
    """Ramp on the outer face of the labium."""
    labium_offset_mm: float = 0.05
    """Labium tip centre outside the windway mid-plane (0 to +0.1 mm)."""

    # ------------------------------------------------------------------ finger hole and vent (acoustic nominal sizes)
    hole_d_mm: float = 7.05
    """Finger hole diameter.  Solved: the open note is 470 Hz in the potential-flow solve (the hole
    adds 4.11 mm of conductance).  Must stay <= 7.5 mm to seal under a child's fingertip."""
    hole_x_mm: float = 70.0
    """Finger hole on the centre line of the back, a vertical bore through the roof ridge: either hand."""
    hole_chimney_mm: float = 2.5
    """Cylindrical length of the finger hole below the dimple floor; below it the bore opens downward
    at roof_angle_deg (an undercut tone hole, printable like the roof).  A plain bore through the 42 deg
    gable is 2.05 mm long on the ridge line and 5.5 mm at the sides."""
    dimple_radius_mm: float = 13.0
    """Finger dimple sphere radius."""
    dimple_depth_mm: float = 0.8
    """Finger dimple depth: found by feel, 9 mm across."""
    vent_d_mm: float = 2.1
    """Tuning vent diameter, printed OPEN.  Solved: with the vent open the closed note is 340 Hz
    (vent conductance 0.446 mm).  Plug it to lower the closed note 90 cents, ream it to raise it."""
    vent_x_mm: float = 35.5
    """Vent on the rump crown, a vertical bore through the lobe ridge: behind the gripping fingers and
    20 mm in front of the lips, with a 2.8 mm chimney."""

    # ------------------------------------------------------------------ CAD compensation
    hole_comp_mm: float = 0.2
    """Added to both bore diameters in the mesh: FDM holes print 0.1-0.3 mm small."""
    windway_gap_comp_mm: float = 0.1
    """Added to the windway gap in the mesh (1.4 drawn for 1.3): slots close up the same way."""

    # ------------------------------------------------------------------ print settings
    nozzle_d_mm: float = 0.4
    """The person's nozzle (requirement R3)."""
    extrusion_width_mm: float = 0.45
    """Line width: 5 perimeters = 2.25 mm = the shell wall."""
    layer_height_mm: float = 0.12
    """Fine layers for a smooth airway (R3: "high quality"); 0.16 is allowed."""
    perimeters: int = 5
    """Walls: the whole 2.2 mm shell is perimeters, no infill seam to leak."""
    infill_fraction: float = 0.18
    """Sparse infill in the thick roof wedges, head and tail block (15-20 %)."""
    print_speed_mm_s: float = 40.0
    """Average speed assumed by the pack's time estimate (+-30 %)."""
    filament_density_g_cm3: float = 1.24
    """PLA first."""
    bed_x_mm: float = 180.0
    """ASSUMPTION: the person's printer is not recorded; 180 x 180 x 180 mm is the smallest common bed."""
    bed_y_mm: float = 180.0
    """ASSUMPTION, as bed_x_mm."""
    bed_z_mm: float = 180.0
    """ASSUMPTION, as bed_x_mm."""
    brim_mm: float = 5.0
    """Allowance round the footprint for a brim or skirt."""
    overhang_limit_deg: float = 45.0
    """Overhang limit the mesh is judged against (the fdm-print pack's conservative default)."""
    max_bridge_mm: float = 5.0
    """Longest flat bridge allowed: the design has two, the windway roof (2.8 mm) and the lintel (4.2 mm)."""

    # ------------------------------------------------------------------ envelope
    max_length_mm: float = 118.0
    """Palm size (R4: about 10-12 cm)."""
    max_width_mm: float = 68.0
    """Palm size: a hand closes round it."""
    max_height_mm: float = 68.0
    """Palm size."""

    # ------------------------------------------------------------------ acoustic inputs
    c_air_m_s: float = 346.0
    """Speed of sound in the played instrument: about 25 C, breath-warmed air."""
    target_closed_hz: float = 340.0
    """Design centre, hole closed: the loudest part of the coo (R2)."""
    target_open_hz: float = 470.0
    """Design centre, hole open: the top of the coo's rise (R2)."""
    k_window: float = 1.811
    """End-correction factor of the window in G = A / (t + k r_eq), with A = cut-up x window height and
    t = window_depth_mm.  CALIBRATED against the potential-flow solve of THIS geometry (model/solve.py
    GRID_STUDY: cut-cell grids 0.25-0.8 mm, least squares to h = 0): window conductance 4.084 mm.
    Textbook range for a voiced window 1.5-2.3; no source gives one number."""
    k_hole: float = 2.014
    """End-correction factor of the finger hole (t = hole_depth_mm).  CALIBRATED against the same solve
    on the same grids: the open hole adds 4.109 mm (4.106 with the vent plugged, 4.112 with it open).
    Textbook range for a bore through a flat wall 1.46-1.70; higher here because the bore's inner end
    sits in the 84 deg gable under the roof ridge."""
    k_vent: float = 4.69
    """End-correction factor of the tuning vent (t = vent_depth_mm).  CALIBRATED against the same solve
    on the same grids: the open vent adds 0.446 mm.  Textbook range 1.46-1.70; far above it because the
    vent enters the lobe at the apex of its 84 deg roof wedge, which is narrower than the bore itself
    for the first 1.2 mm below the ridge."""
    vent_ream_max_mm: float = 3.5
    """Largest diameter the vent is reamed to when tuning the closed note up (a 3.5 mm drill): the
    upward reach.  It is the largest size that was solved (2.5 / 3.0 / 3.5 mm raise the closed note
    24 / 56 / 89 cents); nothing larger has been looked at."""
    blow_pressure_pa: float = 200.0
    """Nominal blowing pressure for the jet numbers: the common point at which both notes speak
    (inputs/references/vessel-flute-acoustics-notes.md section 2.2: 150-250 Pa; each note alone speaks
    from about 100 to 650 Pa).  Not measured on a player."""


CONFIG = Config()

NOT_GEOMETRY = frozenset({
    "nozzle_d_mm", "extrusion_width_mm", "layer_height_mm", "perimeters", "infill_fraction", "print_speed_mm_s",
    "filament_density_g_cm3", "bed_x_mm", "bed_y_mm", "bed_z_mm", "brim_mm", "overhang_limit_deg", "max_bridge_mm",
    "max_length_mm", "max_width_mm", "max_height_mm", "c_air_m_s", "target_closed_hz", "target_open_hz",
    "k_window", "k_hole", "k_vent", "vent_ream_max_mm", "blow_pressure_pa"})
"""Fields that do not change the solid; every other field is hashed into geometry_hash."""

GEOMETRY_FIELDS = tuple(f.name for f in fields(Config) if f.name not in NOT_GEOMETRY)

_UNITS = {"deg": [n for n in (f.name for f in fields(Config)) if n.endswith("_deg")],
          "Hz": ["target_closed_hz", "target_open_hz"], "m/s": ["c_air_m_s"], "mm/s": ["print_speed_mm_s"],
          "g/cm^3": ["filament_density_g_cm3"], "count": ["perimeters"], "fraction": ["infill_fraction"],
          "ratio": ["k_window", "k_hole", "k_vent"], "Pa": ["blow_pressure_pa"]}
_UNIT_OF = {n: u for u, names in _UNITS.items() for n in names}

_REJECTED = {
    "body_radius_x_mm": [
        {"value": "34.5 x 32.3 x 31.3 mm body (character-first)", "why": "92.4 cm^3 chamber: the quietest and breathiest of the three concepts (radiated share of losses 4.7 %)"},
        {"value": "145 cm^3 chamber (acoustics-first)", "why": "cost a 117 x 67 mm body, an 8.2 mm finger hole and a 21 h print"}],
    "head_radius_mm": [
        {"value": "14.0 mm on a visible neck (print-first)", "why": "head / body width 0.44 read as a chick or sparrow"}],
    "beak_pitch_deg": [
        {"value": "49 deg down, base radius 4.3 mm", "why": "read as a parrot hook, and the tip started in mid-air for 2.55 mm (21 layers)"}],
    "eye_depth_mm": [
        {"value": "raised eye bumps 1.2 mm proud", "why": "looked frog-like"}],
    "wing_center_z_mm": [
        {"value": "31.5 mm with -17 deg pitch", "why": "wings stood proud of the chest as raised shoulders: a penguin from the front"}],
    "foot_length_mm": [
        {"value": "six toe nubs", "why": "showed as a fringe under the chest in the top view"}],
    "tail_top_z_mm": [
        {"value": "11.8 mm with a 3 mm edge radius", "why": "inlet rim 0.2 mm at x = 0.2 mm: a feather edge where teeth and lips land"}],
    "lip_stop_x_mm": [
        {"value": "a stop on the centre line only", "why": "at y = +-9 mm the tail top stayed under 14 mm until x = 22 mm: lips slid on to the window flank"}],
    "self_support_deg": [
        {"value": "43.5 deg trim", "why": "left 261 mm^2 of skin in the 43-45 deg bin: fdm.overhang failed at 0.71-0.82 % at every resolution"},
        {"value": "33 deg bottom fill", "why": "hung a cone under the beak tip that did not reach the chest: an island"}],
    "roof_angle_deg": [
        {"value": "43.5 deg", "why": "failed fdm.overhang at every resolution tried (no margin against a strict > 45 deg test)"},
        {"value": "43 deg", "why": "4384 mm^2 of roof within 2 deg of the limit"},
        {"value": "a flat cap under the ridge", "why": "flat strips are bridges inside the chamber: 10-12 mm spans measured"}],
    "lobe_ridge_z_mm": [
        {"value": "25.5 mm (the first build, over an 8 mm high window)", "why": "once the window was lowered to 6.3 mm the eave stood 3.0 mm above the lintel for nothing: a rump crest of 27.9 mm against the 22-27 mm asked for"},
        {"value": "22.4 mm or less", "why": "the lobe roof's eave comes out below the lintel: a hanging edge along the top of the window (measured on the first build: 1.1 mm below at 23.2 mm under the taller window)"}],
    "lobe_width_mm": [
        {"value": "22 mm, the whole rump (385 mm^2 beside the jet)", "why": "window conductance 4.93 mm on the 121 cm^3 chamber: the note solved at 352 Hz with the vent PLUGGED, above the 340 Hz target before any vent is opened"},
        {"value": "10 mm (184 mm^2 = 3.3 x the window)", "why": "lowered the window conductance 10 %, but is under the 250 mm^2 / 4.5 x floor set for the lobe: a throat again"}],
    "windway_height_mm": [
        {"value": "8.0 mm (a 7 x 8 = 56 mm^2 window)", "why": "with a 263 mm^2 lobe and a 4 mm wall the vent-plugged note still solved about 25 cents ABOVE 340 Hz (h = 0.4 mm, extrapolated); it has to be 60-140 cents below for the vent to trim both ways"},
        {"value": "7.0 mm", "why": "vent-plugged note about 41 cents under 340 Hz (h = 0.4 mm, extrapolated): short of the 60 cents wanted"}],
    "windway_length_mm": [
        {"value": "43.5 mm skewed slot", "why": "twice the length in which a string or seam can sit, about 30 Pa more pressure drop"},
        {"value": "22 mm", "why": "put the window 7.4 mm from the lip stop"}],
    "window_wall_mm": [
        {"value": "5.5 mm", "why": "2 mm more wall lowered the window conductance only 5 % (the passage flares on the ramp and lintel sides); 16 % was needed"},
        {"value": "a window opening into a throat (L_eff 15.8-17 mm)", "why": "independent solve read 317 Hz and 331 Hz against the designers' 340 Hz: the throat junction was not in their models"},
        {"value": "a 21 x 17 mm flank scoop", "why": "under the gripping thumb: -64 cents with a pad resting over it"}],
    "lintel_flat_mm": [
        {"value": "a 7-12.6 mm flat bridge over the jet", "why": "the largest flat ceiling of the three concepts, directly at the jet top"},
        {"value": "4.5 mm", "why": "with the ramp receding at 25 deg the outermost strand of a 1.5 mm deep strip would be 5.0 mm"}],
    "hole_d_mm": [
        {"value": "8.2 mm", "why": "what a 145 cm^3 chamber needed: marginal for a child's fingertip (7-8 mm limit)"}],
    "hole_chimney_mm": [
        {"value": "a plain bore through the gable (no undercut)", "why": "8 % less conductance at the same diameter (solved at 6.6 and 7.0 mm): 470 Hz would need an estimated 7.5-7.6 mm, at or over the 7.5 mm a child's fingertip seals"},
        {"value": "3.0 mm", "why": "2.5 % less hole conductance than 2.5 mm for no gain: the roof is 2.05 mm on the ridge line either way"}],
    "dimple_depth_mm": [
        {"value": "the same dimple sunk vertically", "why": "left 1.73 mm of roof on the uphill side of the hole (measured on the 0.35 mm mesh)"}],
    "vent_d_mm": [
        {"value": "2.15 mm", "why": "closed note 340.8 Hz in the solve (+0.23 %); 2.1 mm centres it (340.1 Hz)"},
        {"value": "a blind pilot to drill out", "why": "one-sided trim: no clean way down if the print lands sharp"},
        {"value": "1.5 mm horizontal vent", "why": "likely to print shut"}],
    "vent_x_mm": [
        {"value": "39 mm (the spec asked for 42-48)", "why": "the body's back rises there: chimney 3.99 mm at x = 39, against the 3 mm limit"}],
    "layer_height_mm": [
        {"value": "0.2 mm", "why": "coarser steps on the windway and labium; 0.16 is the stated fallback"}],
    "filament_density_g_cm3": [
        {"value": "PETG, 1.27", "why": "strings across the windway"}],
    "infill_fraction": [
        {"value": "solid", "why": "107 g and a 21 h print for the same shell"}],
    "target_closed_hz": [
        {"value": "380 Hz", "why": "an independent re-measurement of the coo's low note; the person chose 340 -> 470, and a print that lands sharp is still inside the measured band"}],
}

PARAMS = [dict({"name": f.name, "units": _UNIT_OF.get(f.name, "mm")},
               **({"rejected": _REJECTED[f.name]} if f.name in _REJECTED else {}))
          for f in fields(Config)]

# fdm-print pack settings left at the pack's own defaults, stated so they are visible beside the model
OVERHANG_AREA_ALLOW_FRAC = 0.005   # share of the whole surface (inside and out) allowed past the overhang limit
BRIDGE_CEILING_DEG = 80.0          # faces flatter than this are ceilings (bridges), not overhangs
MAX_CANTILEVER_MM = 2.0            # one-sided ceiling reach; the tapered windway roof reads as 1.35 mm by this rule
MAX_PRINT_TIME_H = 24.0            # one overnight-and-a-day print
MAX_FILAMENT_G = 1000.0            # one spool

MESH_NAME = "pigeon-whistle"


def mesh_path(config: Config | None = None) -> str:
    """Project-relative path of the print mesh for this Config (whether or not it has been built)."""
    c = config or CONFIG
    return "print/%s-%s.stl" % (MESH_NAME, geom.geometry_hash(c, GEOMETRY_FIELDS))


def notes(c: Config, d: dict) -> dict:
    """The acoustic closed form: every pitch and jet number build() publishes, from the Config and the
    geometric numbers `d` of geom.derive().  Conductances add (openings are masses in parallel on one
    spring), so the four states are sums of the same three terms."""
    volume = max(d["chamber_volume_mm3"], 1.0)
    g_window = acoustics.conductance(max(d["window_area_mm2"], 1e-6), d["window_depth_mm"], c.k_window)
    g_hole = acoustics.conductance(max(d["hole_area_mm2"], 1e-6), d["hole_depth_mm"], c.k_hole)
    g_vent = acoustics.conductance(max(d["vent_area_mm2"], 1e-6), d["vent_depth_mm"], c.k_vent)
    # the reamed vent keeps its chimney and its end factor: the solve gives 3-6 % more conductance at 3.5 mm
    # than this (k falls as the bore outgrows the wedge), so the upward reach published here is an underestimate
    g_reamed = acoustics.conductance(acoustics.circle_area(max(c.vent_ream_max_mm, 0.1)), d["vent_depth_mm"], c.k_vent)
    speed = c.c_air_m_s

    def hz(*conductances):
        return acoustics.helmholtz_hz(volume, conductances, speed)
    f_closed, f_open = hz(g_window, g_vent), hz(g_window, g_vent, g_hole)
    f_plugged, f_reamed = hz(g_window), hz(g_window, g_reamed)
    pressure = max(c.blow_pressure_pa, 1e-6)
    return {
        "g_window_mm": g_window, "g_hole_mm": g_hole, "g_vent_mm": g_vent,
        "f_closed_hz": f_closed,                          # hole closed, vent open: the design state
        "f_open_hz": f_open,                              # hole open, vent open
        "f_closed_plugged_hz": f_plugged,                 # vent plugged
        "f_open_plugged_hz": hz(g_window, g_hole),
        "f_closed_reamed_hz": f_reamed,                   # vent reamed to vent_ream_max_mm
        "closed_error_cents": acoustics.cents(f_closed, c.target_closed_hz),
        "open_error_cents": acoustics.cents(f_open, c.target_open_hz),
        "interval_ratio": f_open / f_closed,
        "tune_down_reach_cents": max(acoustics.cents(f_closed, f_plugged), 0.0),
        "tune_up_reach_cents": max(acoustics.cents(f_reamed, f_closed), 0.0),
        "lumped_ratio": acoustics.lumped_ratio(d["cavity_length_mm"], f_open, speed),
        "jet_speed_m_s": acoustics.jet_speed(pressure),
        "strouhal_closed": acoustics.strouhal(f_closed, c.cutup_mm, pressure),
        "strouhal_open": acoustics.strouhal(f_open, c.cutup_mm, pressure),
        "flow_l_min": acoustics.windway_flow_l_min(pressure, c.windway_height_mm, c.windway_gap_exit_mm),
        "radiated_fraction": acoustics.radiated_fraction(volume, f_closed, max(d["window_area_mm2"], 1e-6),
                                                         d["window_depth_mm"], c.k_window, speed)["fraction"],
        # what the printer is given: acoustic nominal + compensation
        "hole_cad_d_mm": c.hole_d_mm + c.hole_comp_mm,
        "vent_cad_d_mm": c.vent_d_mm + c.hole_comp_mm,
        "windway_exit_gap_cad_mm": c.windway_gap_exit_mm + c.windway_gap_comp_mm,
    }


def build(config: Config | None = None) -> dict:
    """Derived values.  Pure and deterministic: no files, no clock.

    Geometric keys (mm, mm^2, mm^3) come from geom.derive(): chamber_volume_mm3 is a partial-volume
    integral of the chamber field on a 0.8 mm lattice and agrees with the 0.35 mm mesh to 0.06 %;
    plastic_volume_mm3 agrees to 0.2 %, the extents to 0.01 mm.  Acoustic keys come from notes().
    """
    c = config or CONFIG
    d, _layout = geom.derive(c)
    out = {k: round(float(v), 4) for k, v in d.items()}
    out.update({k: round(float(v), 4) for k, v in notes(c, d).items()})
    path = mesh_path(c)
    bbox = [out["overall_length_mm"], out["overall_width_mm"], out["overall_height_mm"]]
    out.update({
        "geometry_hash": geom.geometry_hash(c, GEOMETRY_FIELDS),
        # ---- fdm-print: ONE part, in print orientation ----
        "fdm.part_bbox_mm": bbox,
        "fdm.part_volume_mm3": out["plastic_volume_mm3"],
        "fdm.surface_area_mm2": out["surface_area_mm2"],
        "fdm.part_min_wall_mm": out["shell_wall_min_mm"],   # the shell; the labium tip is labium_tip_mm, on purpose
        "fdm.mesh_path": path,
        "fdm.build_axis": "z",
        "fdm.load_axis": "x",          # the one slender member is the tail in the mouth: bending puts tension along X, in the layers
        "overhang_area_allow_frac": OVERHANG_AREA_ALLOW_FRAC,
        "bridge_ceiling_deg": BRIDGE_CEILING_DEG,
        "max_cantilever_mm": MAX_CANTILEVER_MM,
        "max_print_time_h": MAX_PRINT_TIME_H,
        "max_filament_g": MAX_FILAMENT_G,
        # ---- cad-solid: the "assembly" is the single part ----
        "cad.meshes": {MESH_NAME: path},
        "cad.assembly_bbox_mm": bbox,
        "cad.assembly_bbox_limit_mm": [c.max_length_mm, c.max_width_mm, c.max_height_mm],
        # cad.process_min_wall_mm is deliberately NOT published: cad.wall_thickness casts one ray per facet
        # and reads ~0 mm at every acute voicing edge (labium, chamfers, bore rims), so it would fail on the
        # features that make the whistle speak.  The shell wall is measured by geom.measure() instead.
    })
    return out


if __name__ == "__main__":
    import json
    print(json.dumps({"config": asdict(CONFIG), "derived": build()}, indent=2, sort_keys=True))
