---
as_of: 1131b2d9d2c8ce14
---

# A pigeon whistle for the palm

This is a whistle in the shape of a chubby city pigeon. A person blows through the tail. With the one finger hole closed the bird sounds a low note, and with the hole open it sounds a higher note.

The targets are 340 Hz with the hole closed and 470 Hz with the hole open. The bird is 117.8 mm long, and it prints belly-down in one piece.

## What is checked, and by what

The model holds the dimensions, the print file and two calculations of the pitch. Evaluators check 20 claims against it.

- A closed form and a potential-flow solve each give the two notes. They agree within 1 % in four states (C3).
- Evaluators that read the model check the vent trim, the jet, the finger hole, the lip stop, the walls and the size.
- Seven evaluators of the fdm-print pack check the print rules, and five project evaluators read the print file.

Each evaluator passes a known-good case and fails a known-bad case before its verdict counts. Checked means that the evaluators pass on the current design. It does not mean that a printed whistle sounds these notes.

## What is not checked

Nothing is printed yet, and nothing is blown. Each pitch is a modelled passive resonance: the note at which the air in the chamber rings. The jet, the lips, the temperature and the printer are outside the model.

A first print can miss a target by about 10 %. The vent trim recovers about 5 % each way (C4).

The person chose the low note of 340 Hz. An independent re-measurement of the recordings reads the low note nearer 380 Hz.

5 claims wait for a built part: the two played notes, the print, the glide and the loudness (C21, C22, C24, C25, C26). 7 claims are gaps. Six of them are assumptions and one is a judgment, and only the person records them.
