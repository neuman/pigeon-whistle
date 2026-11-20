---
as_of: 433fa2140dffcd62
---

The next steps belong to the person, in this order. The first whistle is printed and played on video (input first-print-test). Its results wait for the person to record them.

## What the review found

An adversarial review read this candidate after it was built. It found no reason for the print to fail, and the print did not fail. It found these changes for the next candidate:

- The look. The eyes, the feet and the wings can read more as a pigeon, and the side view is weak.
- The pitch. The review expected the first print to play flat, because the walls of the chamber take a little energy from the note. The test video shows the other side: at a normal breath it plays sharp, because the jet pushes the note up.
- The print file. No evaluator reads the windway gap or the labium from the file itself, and the file name does not change when some construction constants change.
- The print package. `PRINT.md` does not give the top and bottom layers, the seam or the care of the bird. No small test print comes before the long one.

These changes are in work for the next candidate. Record the results of the first print first, as the last section says.

## Record what only you can record

Type these commands in your own shell. An agent cannot record them for you.

- Each assumption that you accept: `nopekit claim physical C27 assume`, and the same for C28, C29, C30, C31 and C32.
- Your choice of the low note over 380 Hz: `nopekit prefer match-the-loudest-part-of-the-coo`.

If the bed of your printer is smaller than 180 mm, say so first. The model then takes the real bed.

## Export the print package

Run `nopekit export print-v0-1 --dry-run`. It runs again each evaluator that the print requires. When it says `would write`, run `nopekit export print-v0-1`. The package holds the print file, `PRINT.md` and `TUNING.md`. Write down the hash that the export prints.

## Print

- Print the file as it sits: belly down, tail on the bed. Do not turn it, and do not scale it.
- Supports off. Nozzle 0.4 mm, layers of 0.12 mm, lines of 0.45 mm, 5 walls, infill 18 %.
- Use PLA for the first print. PETG can leave strings across the windway.
- Keep the seam off the labium edge and the windway exit.

## Look, then blow

Shake the bird: nothing rattles. Pass a thin drill shank through the windway from the tail to the window. Seal the finger hole and blow a gentle breath. A steady note must start at once (C24).

## Trim the low note with the vent

Hold the bird as you play it: tail in the mouth to the lip stop, fingers forward of the window. Do not rest it on a desk, because a surface under the belly lowers the closed note by 34.3 cents. Warm it with a few breaths. Read the note on a tuner at the length of your arm. Blow three times and take the middle reading.

- If the closed note is sharp, plug the vent with wax. The model gives a fall of 89.8 cents.
- If the closed note is flat, ream the vent by hand, one drill size at a time. The solve gives a rise of 24.1 cents at 2.5 mm, 56.2 cents at 3 mm and 88.7 cents at 3.5 mm.
- Stop at 3.5 mm. No larger vent is in the model.

The vent moves the open note about half as far. If the closed note stays outside 313 to 367 Hz, the vent cannot repair this print. The window must change, and that is a new print.

## Trim the high note with the finger hole

Lift the finger clear and read the open note. If it is flat, ream the finger hole a little. Each 0.1 mm of diameter raises the open note by 7.2 cents, and the closed note does not move. The hole must stay small enough for a fingertip to seal.

## Measure and record

Record each result yourself, with the hash of the export as the built part.

- The closed note after the trim, between 313 and 367 Hz (C21): `nopekit claim physical C21 pass --measured <Hz> --article <hash> --evidence <file> --detail "<what you did to the vent>"`.
- The open note, between 432 and 508 Hz (C22), in the same way.
- The print and the first breath (C24), with a photo and a sound clip.
- The glide (C25): rock a fingertip over the hole on one steady breath, and record a clip.
- The loudness (C26): a sound level app half a metre from the window, A-weighted, slow. Read a gentle breath and a hard breath. The band is 60 to 90 decibels, and a phone can be wrong by three decibels.
- The look (C23), which you judge on the printed bird: `nopekit claim physical C23 pass --authority neuman --evidence <photo>`.

Use `fail` in place of `pass` when a result is outside its band. A fail is a result too, and it says what to change.
