---
as_of: f39b07579c711804
---

The whistle must print in one piece on a printer with a 0.4 mm nozzle. It prints belly-down, as it sits on a desk, with supports off.

## The print rules

Seven evaluators of the fdm-print pack pass on the model and the print file (C11).

- The overhang limit is 45 deg from vertical. The chamber roof leans 42 deg, and 0.0012 % of the surface is past the limit.
- The file has 2 flat bridges: the windway roof and the lintel of the window. The longer bridge is 4.2 mm, and the limit is 5 mm.
- The pack estimates the print time at 0.85 of its limit of one day. The estimate is rough, and the slicer gives a better number.

The pack reads face angles. It cannot see a piece of a layer that starts in mid-air. A project evaluator rasters all 564 layers and finds 0 islands and 0 hanging edges (C12). The raster is not a slicer.

## The print file

The print file is one closed solid with four openings: the windway, the window, the finger hole and the vent (C13). Its chamber volume is 0.054 % from the volume in the model, and the limit is 0.5 % (C14). After a change to the geometry there is no print file under the new name until the mesh is built again.

## Walls and small features

- The thinnest shell wall is the chamber floor, at 2.1 mm. The limit is 1.8 mm, which is four lines (C15).
- The windway exit gap is drawn 1.4 mm, and the limit is 1.2 mm (C16).
- The labium tip is drawn as a flat 0.5 mm wide, and the limit is 0.45 mm (C17). No evaluator reads these two sizes from the print file yet.

A wall this thick can print airtight. Only a built part shows that it does.

## What this board does not show

Nothing is sliced, and nothing is printed. The evaluators judge the geometry of the file. Some faults show only on a built part (C24): strings, sag in the two bridges, a seam on the labium, a closed windway and a leak in a wall.

Two assumptions stand under this board, and the person has not recorded them. The bird prints in one piece with no supports in the airway (C28). The printer bed is 180 mm or more each way (C32). The bird is 117.8 mm long and 67.7 mm wide.
