# First printed whistle: what the test video shows

Source: `first-print-test.mp4`, the person's own phone video (15.7 s, 1920 x 1080, AAC 48 kHz stereo), recorded
2026-11-20. The printed part is the v0.1 print file `print/pigeon-whistle-e93208370219.stl`, export article
`0efcea4610ab`. The person printed it and played it. The vent was not reported as trimmed.

Method: the audio was mixed to mono. A Hann-windowed FFT (4096 points, 10 ms hop) found the loudest peak between
250 and 700 Hz, with parabolic interpolation. Frames louder than -30 dBFS count as playing. The script and the full
track (`first-print-pitch-track.csv`) are beside this file. Nobody listened to it for this analysis: these are spectral
measurements only.

## What it shows

- **It is one piece, and it speaks.** The frames show one glossy black print, held up and then blown through the
  tail with a finger on the top hole. From 7.6 s to 14.7 s it gives a clear tone: 524 playing frames, none with a weak
  tone (every frame more than 35 dB above the spectral floor).
- **The tone is close to a sine wave.** The second harmonic is 30 to 42 dB below the note, and nothing sits at half
  the note. The loudest peak is the note itself.
- **Pitch depends strongly on the breath.** Each open note starts loud at 500 to 513 Hz and falls toward 445 to 475 Hz
  as the breath fades. The closed note reads 341 to 381 Hz, sharper when louder.

| what | reading | model | band of the claim |
|---|---|---|---|
| closed note, softest stable segment (14.30 to 14.46 s) | 342.8 Hz | 340.1 Hz (+15 cents) | C21: 313 to 367 Hz, inside |
| closed note, middle stable segment (12.43 to 12.69 s) | 355.9 Hz | +79 cents | inside |
| closed note, loudest stable segment (8.96 to 9.15 s) | 380.5 Hz | +195 cents | outside, above |
| open note, stable segments (5 of them) | 497.6 to 512.6 Hz, median 503.1 Hz | 469.8 Hz (+118 cents) | C22: 432 to 508 Hz; 3 of 5 inside |
| open note as the breath fades | about 472 Hz near -20 dBFS | +8 cents | inside |

Open and closed note at matched loudness (a rough stand-in for matched breath, because the open note radiates more
strongly at the same breath):

| level (dBFS, uncalibrated) | open note | closed note |
|---|---|---|
| -14 to -8 | 500.7 Hz | none |
| -18 to -14 | 487.8 Hz | none |
| -22 to -18 | 474.4 Hz | 356.6 Hz |
| -26 to -22 | 459.1 Hz | 350.7 Hz |
| -30 to -26 | 445.7 Hz | 340.9 Hz |

- **The interval is wider than modelled at one breath strength:** 503 / 356 Hz is about 600 cents, against 560 in the model.
- **Movement between the notes:** the track passes through 400 to 410 Hz between notes with no break in the tone.
- **Loudness cannot be read here.** The phone's level is uncalibrated digital level (dBFS), the distance is not known,
  and the recording may have automatic gain. C26 needs a sound-level app at 50 cm.
- **A faint steady tone at 372 Hz runs through the whole clip, including the silence before the first breath**
  (about -64 dBFS). It is room noise, not the whistle, and it is left out above.

## What this means for the model

- At a soft breath both notes land within about 15 cents of the modelled passive resonances (340.1 and 469.8 Hz). The
  potential-flow model of the chamber, the window and the finger hole holds on a real print.
- The breath moves the note by up to about 120 cents (open) and 200 cents (closed). The model leaves the jet out, and
  this is the largest effect seen.
- Before the print, the review expected the first print to read about 2 % flat because of wall losses. At a normal
  breath it reads sharp. A v0.2 change to tune the passive resonance sharper would make the played note sharper still,
  so it is withdrawn until a test at a measured breath.
