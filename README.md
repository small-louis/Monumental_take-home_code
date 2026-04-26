# Monumental — Extra-DOF Explorer

Interactive 2D visualisation of a proposed extra degree of freedom for the
Monumental bricklaying robot. Sliders let you change every geometric parameter
and toggle between the **down** and **up** arm configurations.

## What it shows

- The mast/wagon assembly (grey)
- The colored arm stack (elbow, wrist, riser, brick-holder bar, brick)
- The ground line (the brick can extend below it)
- Translucent reach-envelope bands showing where the brick can be placed in
  each config as the elbow Y position sweeps the full slider range
- A red dashed line on the elbow pivot

## Run

```bash
pip install -r requirements.txt
python3 app.py
```

Tested with Python 3.11+. Tkinter ships with the standard CPython installer on
macOS / Windows; on some Linux distros you may need `sudo apt install python3-tk`.

## Files

| File | Purpose |
|---|---|
| `System constraints.py` | Original parameter + equation script (the source of truth for the geometry) |
| `calculations.py` | `Params` dataclass and `compute()` reproducing the equations from the original script |
| `renderer.py` | Pure matplotlib drawing of the scene — block widths and X offsets are tuned at the top of this file |
| `app.py` | Tkinter GUI with sliders, input boxes, config toggle, and live readout |

## Notes

- All physical parameters are exposed as sliders (and number entries) in the UI.
- Per-block visual widths and X offsets are **not** in the UI — tune them in
  the `BLOCK_DIMS` dict at the top of `renderer.py`.
- The elbow Y slider is automatically clamped to
  `[bottoms_track_ground_offset, tower_height − tower_height_offset]`.
