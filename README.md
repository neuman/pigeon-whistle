# Pigeon whistle

A palm-size whistle in the shape of a chubby city pigeon, for a 3D printer. You blow through the tail.
With the one finger hole closed it is designed to sound 340 Hz, and with the hole open 470 Hz: the
loudest part of a feral pigeon's coo, as the owner of this project chose it. It prints belly-down in
one piece, with supports off.

**State: nothing has been printed or blown yet.** Both pitches are modelled passive resonances of the
air in the chamber. A first print can miss by about 10 %; the tuning vent on the rump recovers about
5 % each way. The low note of 340 Hz is the owner's choice; an independent re-measurement of the
recordings reads the coo's low note nearer 380 Hz. `nopekit status` says what is checked and what is
not, and `docs/decisions.md` says what was chosen and what lost.

This is a [nopekit](https://github.com/neuman/nopekit) project. Below, `nopekit` stands for
`PYTHONPATH=<your nopekit checkout>/src python3 -m nopekit`, run from this folder.

## Where things are

- `model/pigeon.py`: every dimension, with its reason (`Config`), and `build()`, which derives the numbers.
- `model/solve.py`, `model/acoustics.py`: the potential-flow solve of the two notes.
- `print/`: the print file (`pigeon-whistle-<geometry hash>.stl`), its measurements and preview pictures.
- `claims/`, `gates/`, `selftest/`: what must be true, what checks it, and the cases each check must fail.
- `inputs/`: the three coo recordings, their pitch analysis, and the acoustics and printing notes.
- `site/`: the two pages. `nopekit site serve --watch --detach` prints their address.

## Regenerate the mesh

The print file's name carries a hash of the geometry. After any change to a dimension in
`model/pigeon.py` there is no print file under the new name until you build it:

```sh
python3 model/mesh.py          # about half a minute: writes the STL, its measurements and the previews
nopekit check --tier 1         # about two minutes: every evaluator, the solve and the mesh checks included
nopekit model trace            # what each choice moves
```

It needs Python 3.10 with numpy, scipy, scikit-image, trimesh, manifold3d and Pillow.
`python3 model/solve.py --h 0.6` prints the two solved notes on one grid; `--study` runs the
seven-grid study (about 12 minutes and 9 GB of memory).

## Print

```sh
nopekit export print-v0-1 --dry-run    # re-runs what the print requires; go on when it says "would write"
nopekit export print-v0-1              # writes the package under out/print-v0-1/
```

The package holds the STL, `PRINT.md` and `TUNING.md`. In short:

- Print it as it sits in the file: belly down, tail on the bed. Do not rotate it and do not scale it.
- Supports off. 0.4 mm nozzle, 0.12 mm layers, 0.45 mm lines, 5 walls, 18 % infill.
- PLA for the first print: PETG strings across the windway.
- Leave hole compensation in the slicer at 0: the file already carries it.
- Keep the seam off the labium edge and the windway exit.

The bird is 117.8 x 67.7 x 67.7 mm. The model assumes a bed of at least 180 mm each way.

## Tune

Read the pitch with a tuner app while you hold the bird as you play it: tail in the mouth up to the
lip stop, fingers forward of the window, not resting on a desk. Warm it with a few breaths first.

1. The low note, finger hole sealed. The small hole on the rump is a tuning vent, printed open at 2.1 mm.
   Too sharp: plug it with wax (about 90 cents down in the model). Too flat: ream it by hand, one drill
   size at a time, up to 3.5 mm (about 89 cents up in the solve; the closed form says 78). If the note
   is still outside 313 to 367 Hz, the vent cannot fix this print: the window has to change.
2. The high note, finger lifted clear. Reaming the finger hole raises it by about 7 cents per 0.1 mm
   and leaves the low note alone. The hole must still seal under a fingertip.
3. Write down the note before, what you did, and the note after.

Then record the results yourself; an agent cannot do it for you. `site/content/next.md` lists the
commands (`nopekit claim physical ...`) and the measurements each one needs.

## Licences of the recordings

The two Paris recordings are by Marie-Lan Taÿ Pamart (xeno-canto XC539061 and XC541143, via Wikimedia
Commons) and the Sangli recording is by Sharadapte (Wikimedia Commons); all three are CC BY-SA 4.0.
The links are in `inputs/*.json`.

<!-- nopekit:begin badge -->
<a href="https://github.com/neuman/nopekit"><img src="https://raw.githubusercontent.com/neuman/nopekit/main/docs/img/made-with-nopekit.png" width="160" alt="Made with nopekit"></a>
<!-- nopekit:end badge -->
