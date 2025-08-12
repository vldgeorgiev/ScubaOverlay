# Dive computer video overlay generator

A cross-platform Python tool that generates a **chroma key–ready dive computer overlay video** from a dive log file. Ideal for compositing depth, time, tank pressures, temperature, and stop information directly into your dive footage.

---

## 📑 Table of Contents

1. [Features](#-features)  
2. [Example Outputs](#-example-outputs)  
3. [Installation](#-installation)  
4. [Quick Start](#-quick-start)  
5. [Compositing into Final Video](#-compositing-the-overlay-into-your-dive-footage)  
6. [Command Reference](#-command-reference)  
7. [Creating & Editing Templates](#-creating--editing-templates)  
8. [Troubleshooting](#-troubleshooting)  
9. [Roadmap](#-roadmap)  
10. [License](#-license)  

---

## ✨ Features

- **Flexible backgrounds** — solid color or PNG with transparency  
- **Chroma key–friendly** background color (default bright green `#00FF00`)  
- **Per-item positioning** — labels and values placed independently  
- **Rich data support** — depth, time, NDL, TTS, temperature, stop depth/time, gas, pressure[n]  
- **Automatic unit conversion** — metric ↔ imperial  
- **Per-item numeric precision** — e.g. 1 decimal for depth, integer for pressures  
- **Font customization** — size, color, style (bold/italic) from any font file  
- **Quick layout testing** — render a single PNG before committing to a video  
- **Multiple tank pressures** via indexed fields (`pressure[0]`, `pressure[1]`, …)  
- **Fallback values** for missing data  
- **Simple YAML configuration** — no code changes required for layout tweaks  

---

## 📸 Example outputs

- [Sample video](https://youtu.be/fo78Rq-cnjI?si=AAkXO1n-fyquQavh&t=31) from a dive with Shearwater Perdix overlay

- Template preview:  
![Template Test Image](docs/sample-test-template.png)

- Sample overlay frame:  
![Overlay Frame Example](docs/sample-overlay-frame.png)

---

## 🚀 Installation

### Requirements
- Python **3.11+**
- `pip` (comes with most Python installations)

### Install on Windows
1. Download Python from [python.org](https://www.python.org) and check **"Add Python to PATH"** during setup.
2. Open **Command Prompt** and navigate to the project folder:
   ```bat
   cd C:\Users\YOU\ScubaOverlay
   ```
3. Install dependencies:
   ```bat
   pip install -r requirements.txt
   ```

### Install on macOS / Linux
1. Check Python version:
   ```bash
   python3 --version
   ```
   If missing, install via:
   ```bash
   brew install python    # macOS
   sudo apt install python3-pip  # Debian/Ubuntu
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🛠 Quick Start

### 1. Preview Your Layout
```bash
python main.py --template templates/perdix-ai-oc-tech.yaml --test-template
```
Generates `test_template.png` for fast iteration.

### 2. Generate Overlay Video
Metric units:
```bash
python main.py --template templates/perdix-ai-oc-tech.yaml --log samples/dive446.ssrf --output overlay.mp4
```
Imperial units:
```bash
python main.py --template templates/perdix-ai-oc-tech.yaml --log samples/dive446.ssrf --units imperial --output overlay_imperial.mp4
```

---

## 🎬 Compositing the Overlay into Your Dive Footage

The output MP4 has a bright green background (`#00FF00`). Use **chroma key** in your video editor to make it transparent.

Popular editors:
- **DaVinci Resolve** (Free) — [Download](https://www.blackmagicdesign.com/products/davinciresolve/)  
- **Adobe Premiere Pro** — [Ultra Key guide](https://helpx.adobe.com/premiere-pro/using/ultra-key.html)  
- **Final Cut Pro** — [Keyer effect](https://support.apple.com/guide/final-cut-pro/keyer-effect-ver5d3c6d45/mac)  
- **Shotcut** (Free) — [Chroma Key tutorial](https://shotcut.org/tutorials/chroma-key/)  

## 🧭 Aligning the overlay with your footage

Getting the overlay to line up with your dive video is mostly about creating **clear reference points** and then applying a small time offset in your editor.

### What to capture underwater (best practice)
- At the **start of the dive**, briefly film your **dive computer screen** on your wrist.
- If you **start/stop** recording during the dive, **begin each clip** with a 1–2 second shot of the computer.  
  This gives you a reference for every clip.

### How to read time
- Some dive computers **show seconds**, while some don't. For example Shearwater Perdix ha sa progress bar above the minutes that indicates the seconds and can be used for estimation.  
- The **depth** is a second reference: compare the depth in the shot of the computer with the one shown on the overlay. This is especially helpful when the depth changes fast.

### Alignment workflow
1. **Import** your main video and the **overlay** into your editor.
2. Move to the frame where your video shows the **dive computer screen**. Read the **time** and **depth**.
3. Shift the overlay track until the **time** and **depth** shown in it match the one above.
4. Play back to verify the timing.

**Expected accuracy:** ~**±10 seconds** with a single reference shot.  
- On **flat, level sections** with minimal depth change, being **20–30 seconds off** usually **won’t be noticeable**.

---

## 📄 Command Reference

| Option          | Description |
|-----------------|-------------|
| `--template`    | Path to YAML template (required) |
| `--log`         | Dive log file (.ssrf) |
| `--output`      | Output MP4 filename (default: `output_overlay.mp4`) |
| `--duration`    | Force duration in seconds |
| `--fps`         | Frames per second (default: 10) |
| `--test-template` | Generate single PNG and exit |
| `--units`       | `metric` or `imperial` (default: metric) |

---

## 🖌 Creating & Editing Templates

Templates are YAML files defining:
- **Background** (solid or PNG)
- **Default fonts**
- **Data items** (field, label, positions, precision, colors)

Example:
```yaml
- field: depth
  label: "DEPTH"
  label_position: { x: 180, y: 200 }
  data_position:  { x: 180, y: 220 }
  precision: 1
```
Run:
```bash
python main.py --template your_template.yaml --test-template
```
until the layout looks right.

---

## 🐞 Troubleshooting

- **Green background visible** — check chroma key matches exactly `#00FF00`.  
- **No data appears** — verify the log file has values and matches expected format.  
- **Render too slow** — lower `--fps`.  

---

## 🛤 Roadmap

- Support for Shearwater XML, Garmin, and other formats  
- PPO2 calculation  
- Dive profile graph overlay  

---

## 📜 License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.  

You are free to:

- **Use** — run the program for any purpose  
- **Share** — copy and redistribute the material in any medium or format  
- **Modify** — remix, transform, and build upon the material  

Under the following terms:

- **Attribution** — You must give appropriate credit to the original author(s).  
- **ShareAlike (Copyleft)** — If you modify this code, you must distribute your contributions under the **same license** (GPL-3.0).  
- **No additional restrictions** — You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.  

Full license text: [GNU GPL v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)
