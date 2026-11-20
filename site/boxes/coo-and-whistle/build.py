#!/usr/bin/env python3
"""Build this box: the real coo against the whistle's two modelled notes.

    python3 site/boxes/coo-and-whistle/build.py

Writes index.html (one self-contained page: inline style, script, data, audio), thumb.png and box.json
beside this file.  Needs ffmpeg (to decode the recording and to encode the short excerpt), numpy, scipy
and Pillow.  Deterministic on one machine: the same inputs give the same bytes.

What is measured and what is modelled, and the box says so on its face:
* measured: the spectrogram and the sound of the excerpt, from the recording
  inputs/measurements/coo-xc539061-paris-feral-pigeon.mp3 (input coo-xc539061-paris-feral-pigeon;
  Marie-Lan Tay Pamart, CC BY-SA 4.0, xeno-canto XC539061), and the note length and spacing used
  for the synthesised notes (input coo-pitch-analysis, section 3.1: medians of 18 notes);
* modelled: the two lines (build() keys f_closed_hz and f_open_hz of model/pigeon.py) and the
  synthesised sound.  No whistle has been printed: the second sound is a sine wave, not a recording.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
RECORDING = os.path.join(ROOT, "inputs", "measurements", "coo-xc539061-paris-feral-pigeon.mp3")

CLIP = (9.55, 13.35)             # seconds of the recording: four clean notes in a row
RATE = 11025                     # analysis rate, Hz (as the pitch analysis used)
WINDOW, HOP, NFFT = 512, 32, 4096
F_LO, F_HI = 120.0, 720.0        # what the picture shows, Hz
RANGE_DB = 42.0                  # the picture's dynamic range under its loudest point
COLS, ROWS = 420, 160
BAND = 0.08                      # the tolerance the coo evidence justifies (input coo-pitch-analysis, section 5)
NOTE_S, ONSET_S = 0.380, 0.941   # median note length and onset-to-onset time (input coo-pitch-analysis, section 3.1)
ATTRIBUTION = "Marie-Lan Tay Pamart, CC BY-SA 4.0, xeno-canto XC539061"


def model_notes():
    sys.path.append(os.path.join(ROOT, "model"))
    import pigeon
    built = pigeon.build()
    return float(built["f_closed_hz"]), float(built["f_open_hz"])


def decode(path, start, stop, workdir):
    raw = os.path.join(workdir, "clip.f32")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", "%.3f" % start, "-t", "%.3f" % (stop - start),
                    "-i", path, "-ac", "1", "-ar", str(RATE), "-f", "f32le", raw], check=True)
    return np.fromfile(raw, dtype="<f4").astype(np.float64)


def spectrogram(x):
    """(levels 0..255 as uint8 [ROWS, COLS], top row = F_HI; the first note's onset in seconds;
    fundamental and second harmonic at the first note's loudest instant)."""
    win = np.hanning(WINDOW)
    pad = np.concatenate([np.zeros(WINDOW // 2), x, np.zeros(WINDOW // 2)])
    n = 1 + (len(pad) - WINDOW) // HOP
    frames = np.stack([pad[i * HOP:i * HOP + WINDOW] * win for i in range(n)])
    mag = np.abs(np.fft.rfft(frames, NFFT, axis=1))
    freqs = np.fft.rfftfreq(NFFT, 1.0 / RATE)
    times = np.arange(n) * HOP / RATE
    keep = (freqs >= F_LO) & (freqs <= F_HI)
    db = 20.0 * np.log10(np.maximum(mag[:, keep], 1e-12))
    db -= db.max()
    f_kept = freqs[keep]
    # resample to the picture's grid (linear)
    t_grid = np.linspace(0.0, len(x) / RATE, COLS)
    f_grid = np.linspace(F_HI, F_LO, ROWS)
    ti = np.clip(np.searchsorted(times, t_grid), 1, len(times) - 1)
    tw = (t_grid - times[ti - 1]) / (times[ti] - times[ti - 1])
    cols = db[ti - 1] * (1.0 - tw)[:, None] + db[ti] * tw[:, None]
    fi = np.clip(np.searchsorted(f_kept, f_grid), 1, len(f_kept) - 1)
    fw = (f_grid - f_kept[fi - 1]) / (f_kept[fi] - f_kept[fi - 1])
    grid = cols[:, fi - 1] * (1.0 - fw)[None, :] + cols[:, fi] * fw[None, :]
    level = np.clip(1.0 + grid.T / RANGE_DB, 0.0, 1.0)
    # the first note: where the band 150-700 Hz first comes within 12 dB of its loudest in the first second
    energy = 10.0 * np.log10(np.maximum((mag[:, keep] ** 2).sum(axis=1), 1e-24))
    first = times < 1.0
    loud = int(np.argmax(np.where(first, energy, -np.inf)))
    on = loud
    while on > 0 and energy[on - 1] > energy[loud] - 12.0:
        on -= 1
    lower = (f_kept >= 170.0) & (f_kept < 330.0)
    upper = (f_kept >= 330.0) & (f_kept < 660.0)
    # the two ridges through the first note: the fundamental's lowest and the second harmonic's highest point
    off = loud
    while off < len(times) - 1 and energy[off + 1] > energy[loud] - 12.0:
        off += 1
    note = slice(on, off + 1)
    f0_low = float(np.percentile(f_kept[lower][np.argmax(db[note][:, lower], axis=1)], 10))
    h2_top = float(np.percentile(f_kept[upper][np.argmax(db[note][:, upper], axis=1)], 90))
    return (level * 255.0 + 0.5).astype(np.uint8), float(times[on]), float(times[loud]), f0_low, h2_top


def excerpt_mp3(path, start, stop, workdir):
    """The excerpt as a small mono MP3: peak brought to -1.5 dB, 30 ms fades."""
    x = decode(path, start, stop, workdir)
    gain = 10.0 ** (-1.5 / 20.0) / max(float(np.abs(x).max()), 1e-6)
    out = os.path.join(workdir, "clip.mp3")
    length = stop - start
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", "%.3f" % start, "-t", "%.3f" % length, "-i", path,
                    "-af", "volume=%.4f,afade=t=in:d=0.03,afade=t=out:st=%.3f:d=0.03" % (gain, length - 0.03),
                    "-ac", "1", "-ar", "22050", "-c:a", "libmp3lame", "-b:a", "48k",
                    "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact", "-id3v2_version", "0",
                    "-write_xing", "0", out], check=True)
    with open(out, "rb") as fh:
        return fh.read()


def thumbnail(level, f_closed, f_open, length, path):
    """The same picture as a still: 1280 x 720, light."""
    from PIL import Image, ImageDraw, ImageFont
    import matplotlib
    def font(size, bold=False):
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        return ImageFont.truetype(os.path.join(matplotlib.get_data_path(), "fonts", "ttf", name), size)
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), (255, 255, 255))
    x0, y0, x1, y1 = 96, 92, W - 36, H - 96
    shade = (255 - (level.astype(np.float64) / 255.0) ** 0.9 * 215).astype(np.uint8)
    plot = Image.fromarray(shade, "L").resize((x1 - x0, y1 - y0), Image.BICUBIC).convert("RGB")
    img.paste(plot, (x0, y0))
    draw = ImageDraw.Draw(img, "RGBA")
    ink, muted = (22, 25, 28), (107, 116, 128)
    fy = lambda f: y0 + (F_HI - f) / (F_HI - F_LO) * (y1 - y0)       # noqa: E731
    for f, rgb, name in ((f_closed, (42, 120, 214), "model, hole closed"), (f_open, (235, 104, 52), "model, hole open")):
        draw.rectangle([x0, fy(f * (1 + BAND)), x1, fy(f * (1 - BAND))], fill=rgb + (46,))
        draw.line([x0, fy(f), x1, fy(f)], fill=rgb + (255,), width=4)
        text = "%s: %.0f Hz" % (name, f)
        box = draw.textbbox((x1 - 14, fy(f) - 8), text, font=font(26), anchor="rb")
        draw.rounded_rectangle([box[0] - 8, box[1] - 5, box[2] + 8, box[3] + 5], radius=6, fill=(255, 255, 255, 235))
        draw.text((x1 - 14, fy(f) - 8), text, font=font(26), fill=ink, anchor="rb")
    for f in (200, 300, 400, 500, 600, 700):
        draw.line([x0 - 8, fy(f), x0, fy(f)], fill=muted, width=2)
        draw.text((x0 - 14, fy(f)), "%d" % f, font=font(24), fill=muted, anchor="rm")
    draw.text((x0 - 14, y0 - 22), "Hz", font=font(24), fill=muted, anchor="rm")
    for t in range(0, int(length) + 1):
        x = x0 + t / length * (x1 - x0)
        draw.line([x, y1, x, y1 + 8], fill=muted, width=2)
        draw.text((x, y1 + 14), "%d s" % t, font=font(24), fill=muted, anchor="mt")
    draw.rectangle([x0, y0, x1, y1], outline=(222, 217, 210), width=2)
    draw.text((x0, 30), "A real coo (measured) and the whistle's two notes (modelled)", font=font(28, True), fill=ink)
    draw.text((x0, H - 44), "Recording: %s. Lines: model, no whistle printed." % ATTRIBUTION, font=font(22), fill=muted)
    img.save(path, format="PNG", optimize=True)


def main():
    if not os.path.isfile(RECORDING):
        print("the recording is not there: %s" % os.path.relpath(RECORDING, ROOT))
        return 1
    f_closed, f_open = model_notes()
    with tempfile.TemporaryDirectory() as work:
        x = decode(RECORDING, CLIP[0], CLIP[1], work)
        level, onset, loud_t, f0, h2 = spectrogram(x)
        mp3 = excerpt_mp3(RECORDING, CLIP[0], CLIP[1], work)
    length = len(x) / RATE
    data = {
        "spec": {"w": COLS, "h": ROWS, "f_lo": F_LO, "f_hi": F_HI, "seconds": round(length, 3), "range_db": RANGE_DB,
                 "b64": base64.b64encode(level.tobytes()).decode("ascii")},
        "clip": {"from_s": CLIP[0], "to_s": CLIP[1], "first_onset_s": round(onset, 3),
                 "first_loud_s": round(loud_t, 3), "f0_low_hz": round(f0), "h2_top_hz": round(h2)},
        "model": {"closed_hz": round(f_closed, 1), "open_hz": round(f_open, 1), "band": BAND},
        "coo": {"note_s": NOTE_S, "onset_s": ONSET_S},
        "attribution": ATTRIBUTION,
        "audio": "data:audio/mpeg;base64," + base64.b64encode(mp3).decode("ascii"),
    }
    with open(os.path.join(HERE, "template.html"), "r", encoding="utf-8") as fh:
        page = fh.read()
    page = page.replace("/*__DATA__*/null", json.dumps(data, sort_keys=True, separators=(",", ":")))
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)
    thumbnail(level, f_closed, f_open, length, os.path.join(HERE, "thumb.png"))
    box = {"schema": 1, "kind": "custom",
           "title": "A real coo beside the whistle's two notes",
           "caption": "Measured: a feral pigeon in Paris (recording by %s). Modelled: the two lines, and a "
                      "synthesised sound. No whistle is printed yet, so no whistle is heard here." % ATTRIBUTION,
           "src": "index.html", "thumbnail": "thumb.png", "view": "both", "section": "story", "aspect": "16/9"}
    with open(os.path.join(HERE, "box.json"), "w", encoding="utf-8") as fh:
        json.dump(box, fh, indent=1)
        fh.write("\n")
    print("index.html %d bytes (audio %d bytes of MP3), thumb.png %d bytes; first note at %.2f s, fundamental from %.0f Hz, second harmonic up to %.0f Hz" % (
        os.path.getsize(os.path.join(HERE, "index.html")), len(mp3), os.path.getsize(os.path.join(HERE, "thumb.png")),
        onset, f0, h2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
