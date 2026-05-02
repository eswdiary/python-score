# Timeline v6 Color — Audio Track Timeline Visualizer

> 🌐 Language: **English** | [繁體中文](README.md) | [日本語](README_ja.md)

> [!NOTE]
> This documentation was written with AI assistance (Claude Sonnet 4.6), based on the script's source code, and is provided for reference only. Please verify actual parameters and logic against the code before use.

Combine DAW-exported marker files with stem WAV files to automatically generate colorful amplitude timeline images — ideal for music analysis, score layout, or mixing reference.

---

## Features

- Parses `marker.txt` exported from DAWs (Reaper, Logic Pro, Cubase, etc.)
- Loads the corresponding stem WAV for each Part
- Computes **RMS amplitude** (volume contour) and **Spectral Centroid** (timbral brightness)
- Maps spectral centroid to **HSL hue** (low freq = warm orange-red, high freq = cool blue-violet)
- Automatically splits the piece into multiple rows (up to N markers per row) and exports A4 landscape PNG / SVG / PDF

---

## File Structure

```
v6_color/
├── timeline_v6_color.py   # Main script
├── marker.txt             # DAW-exported marker list
├── key.wav                # Stem WAVs (prepare yourself)
├── pad.wav
├── rhythm.wav
├── texture.wav
└── README.md
```

---

## Requirements

| Package | Purpose |
|---------|---------|
| Python 3.9+ | Interpreter |
| `matplotlib` | Plot output |
| `numpy` | Numerical computation |
| `librosa` | Audio feature analysis (RMS, Spectral Centroid) |
| `scipy` | Gaussian smoothing |

### One-line Install

```bash
pip install matplotlib numpy librosa scipy
```

---

## Quick Start (5 Minutes)

### Step 1 — Prepare `marker.txt`

One marker per line, number and timecode separated by ` - `, timecode format `HH:MM:SS.FF` (FF = frame number):

```
1 - 00:00:00.00
2 - 00:00:33.07
3 - 00:00:48.12
...
```

> **Note**: The last number in the timecode is a **frame number**, not milliseconds. Default FPS = 30; change the `FPS` variable at the top of the script to match your DAW project.

### Step 2 — Prepare Stem WAVs

Place each part's WAV file in the same directory as the script, or provide the full path.

### Step 3 — Configure the Script

Open `timeline_v6_color.py` and edit the `PARTS` list:

```python
PARTS = [
    {
        'label': 'K',           # Part name (used in output filenames)
        'audio_file': 'key.wav',
        'show_markers': None    # None = show all markers; or use [1, 3, 5] to show specific ones
    },
    {
        'label': 'P',
        'audio_file': 'pad.wav',
        'show_markers': None
    },
    # Add more parts as needed...
]
```

### Step 4 — Run

```bash
python timeline_v6_color.py
```

Output files will be created in the same directory:

```
timeline_v6_K_row_1.png
timeline_v6_K_row_2.png
timeline_v6_P_row_1.png
...
```

---

## Parameter Reference

### Global Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `FPS` | `30` | Frame rate of marker timecodes (must match DAW project) |
| `MARKERS_PER_ROW` | `6` | Maximum markers displayed per row |
| `INPUT_MARKERS` | `'marker.txt'` | Path to the marker file |
| `OUTPUT_PREFIX` | `'timeline_v6'` | Prefix for output filenames |

### Export Formats

| Parameter | Default | Description |
|-----------|---------|-------------|
| `EXPORT_PNG` | `True` | Export PNG |
| `EXPORT_SVG` | `False` | Export SVG (vector) |
| `EXPORT_PDF` | `False` | Export PDF |
| `PNG_DPI` | `300` | PNG resolution (dpi) |

### Page Layout

| Parameter | Default | Description |
|-----------|---------|-------------|
| `PAGE_W` | `11.69` in | Page width (A4 landscape) |
| `ROW_H` | `2.0` in | Row height |
| `PAD_LEFT / PAD_RIGHT` | `0.6` in | Left/right padding |
| `PAD_TOP / PAD_BOTTOM` | `0.5` in | Top/bottom padding |

### Amplitude Curve

| Parameter | Default | Description |
|-----------|---------|-------------|
| `RMS_FRAME_LENGTH` | `2048` | RMS analysis window size (samples) |
| `RMS_HOP_LENGTH` | `512` | RMS analysis hop length (samples) |
| `SMOOTH_SIGMA` | `5` | Gaussian smoothing strength (larger = smoother) |
| `AMP_HEIGHT` | `0.5` | Maximum amplitude curve height (inches) |
| `AMP_ALPHA` | `0.85` | Color band opacity (0 = transparent, 1 = solid) |

### Color Mapping (HSL)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `HUE_LOW` | `0.04` (≈ 14°, orange-red) | Hue for low frequencies |
| `HUE_HIGH` | `0.67` (≈ 240°, blue-violet) | Hue for high frequencies |
| `HSL_SATURATION` | `0.65` | Saturation (0 = grayscale, 1 = full color) |
| `HSL_LIGHTNESS` | `0.50` | Lightness |
| `RMS_SILENCE_THRESHOLD` | `0.02` | Silence threshold; segments below this are transparent |
| `CENTROID_HZ_MIN` | `None` | Color mapping lower bound (Hz); `None` = auto-detect |
| `CENTROID_HZ_MAX` | `None` | Color mapping upper bound (Hz); `None` = auto-detect |

---

## Advanced Usage

### Show Only Specific Markers for a Part

```python
{
    'label': 'R',
    'audio_file': 'rhythm.wav',
    'show_markers': [1, 2, 5]   # Only draw tick marks at markers 1, 2, and 5
}
```

### Fix the Color Mapping Range (Consistent Across Parts)

If frequency ranges differ greatly between parts, set a fixed range so colors are comparable:

```python
CENTROID_HZ_MIN = 200   # All parts share the same lower color bound (200 Hz)
CENTROID_HZ_MAX = 8000  # All parts share the same upper color bound (8000 Hz)
```

### Customize the Color Scheme

Hue range can be set freely (0.0–1.0 maps to HSL hue wheel 0°–360°):

```python
HUE_LOW  = 0.33  # Green (low frequencies)
HUE_HIGH = 0.83  # Pink-violet (high frequencies)
```

---

## Output Naming Convention

```
{OUTPUT_PREFIX}_{label}_row_{row_idx}.png
```

Example: `timeline_v6_K_row_1.png` = Part K, row 1 of the timeline.

Row time ranges are determined automatically from markers:
- Row N starts at the time of marker `(N-1) × MARKERS_PER_ROW + 1`
- Row N ends at the first marker of the next row (the final row extends to the end of the audio)

---

## FAQ

**Q: `FileNotFoundError: marker.txt` when running the script**
→ Make sure `marker.txt` is in the working directory, or update `INPUT_MARKERS` with the full path.

**Q: `FileNotFoundError: key.wav`**
→ Verify that each `audio_file` path is correct. WAV files can be mono or stereo — librosa converts to mono automatically.

**Q: Timecodes don't align correctly**
→ Make sure `FPS` matches your DAW project's frame rate (common values: 24, 25, 30).

**Q: All colors look the same or appear gray**
→ Try increasing `HSL_SATURATION`, adjusting `RMS_SILENCE_THRESHOLD`, or fixing `CENTROID_HZ_MIN / MAX` to improve color contrast.

**Q: Amplitude curve is too thick or too thin**
→ Adjust `AMP_HEIGHT` (curve height) and `SMOOTH_SIGMA` (smoothing amount).

---

## marker.txt Format Reference

The following is the supported format (can be exported from Reaper's Region/Marker Manager and lightly cleaned up):

```
1 - 00:00:00.00
2 - 00:00:33.07
3 - 00:00:48.12
4 - 00:00:52.01
```

- Number and timecode separated by ` - ` (space-hyphen-space)
- Timecode format: `HH:MM:SS.FF` (FF is frame number, not milliseconds)
- Blank lines are ignored automatically

---

## License

This is a personal utility tool with no formal license. Feel free to use and modify it.
