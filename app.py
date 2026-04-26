"""
Tkinter GUI app: sliders + input boxes for every parameter,
toggle between 'down' and 'up' configs, live matplotlib render.

Run with:  python app.py
"""

import tkinter as tk
from tkinter import ttk
from dataclasses import fields

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from calculations import Params, compute, clamp_elbow
from renderer import draw


# Slider ranges (min, max, step) for each parameter
PARAM_RANGES = {
    "bottoms_track_ground_offset": (0, 1000, 10),
    "tower_height": (500, 3000, 10),
    "tower_height_offset": (0, 500, 10),
    "riser_height": (50, 800, 10),
    "elbow_wrist_height": (20, 400, 5),
    "gap_height": (0, 100, 1),
    "brick_holder_height": (10, 200, 5),
    "brick_offset": (0, 400, 5),
}

PARAM_LABELS = {
    "bottoms_track_ground_offset": "Platform height",
    "tower_height": "Tower height",
    "tower_height_offset": "Tower top offset",
    "riser_height": "Riser height (light blue)",
    "elbow_wrist_height": "Elbow/Wrist height (blue + grey)",
    "gap_height": "Gap height",
    "brick_holder_height": "Brick holder height",
    "brick_offset": "Brick offset (orange + grey)",
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Robot DOF Explorer")
        self.geometry("1400x900")

        self.params = Params()
        self._building = True
        self.config_var = tk.StringVar(value="down")

        # Create tk variables for each parameter
        self.param_vars: dict[str, tk.DoubleVar] = {}
        for f in fields(self.params):
            self.param_vars[f.name] = tk.DoubleVar(value=getattr(self.params, f.name))

        # Elbow Y slider variable (set after first compute)
        d = compute(self.params)
        initial_elbow = (d.elbow_min + d.elbow_max) / 2
        self.elbow_var = tk.DoubleVar(value=initial_elbow)

        self._build_layout()
        self._building = False
        self._refresh()

    # ---------- layout ----------

    def _build_layout(self):
        root = ttk.Frame(self, padding=8)
        root.pack(fill="both", expand=True)

        # Left: controls
        controls = ttk.Frame(root)
        controls.pack(side="left", fill="y", padx=(0, 10))

        ttk.Label(controls, text="Configuration",
                  font=("", 11, "bold")).pack(anchor="w")
        cfg_row = ttk.Frame(controls)
        cfg_row.pack(anchor="w", pady=(0, 12))
        ttk.Radiobutton(cfg_row, text="Down", variable=self.config_var,
                        value="down", command=self._refresh).pack(side="left")
        ttk.Radiobutton(cfg_row, text="Up", variable=self.config_var,
                        value="up", command=self._refresh).pack(side="left")

        ttk.Label(controls, text="Parameters",
                  font=("", 11, "bold")).pack(anchor="w")

        for name in PARAM_RANGES:
            self._build_param_row(controls, name)

        # Elbow slider (special — bounds depend on params)
        ttk.Separator(controls, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(controls, text="Elbow Y position",
                  font=("", 11, "bold")).pack(anchor="w")
        self.elbow_row = ttk.Frame(controls)
        self.elbow_row.pack(fill="x")
        self.elbow_label = ttk.Label(self.elbow_row, text="", width=22)
        self.elbow_label.pack(side="left")
        self.elbow_scale = ttk.Scale(
            self.elbow_row, from_=0, to=1, orient="horizontal",
            variable=self.elbow_var, command=lambda _=None: self._refresh(),
            length=260,
        )
        self.elbow_scale.pack(side="left", fill="x", expand=True)
        self.elbow_entry = ttk.Entry(self.elbow_row, width=8)
        self.elbow_entry.pack(side="left", padx=4)
        self.elbow_entry.bind("<Return>", self._on_elbow_entry)

        # Info readout
        ttk.Separator(controls, orient="horizontal").pack(fill="x", pady=8)
        self.info_label = ttk.Label(
            controls, text="", font=("Menlo", 9), justify="left",
        )
        self.info_label.pack(anchor="w")

        # Right: matplotlib canvas
        plot_frame = ttk.Frame(root)
        plot_frame.pack(side="right", fill="both", expand=True)

        self.fig = Figure(figsize=(7, 9), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _build_param_row(self, parent, name: str):
        lo, hi, step = PARAM_RANGES[name]
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=PARAM_LABELS[name], width=22).pack(side="left")
        scale = ttk.Scale(
            row, from_=lo, to=hi, orient="horizontal",
            variable=self.param_vars[name],
            command=lambda _=None, n=name: self._on_param_change(n),
            length=220,
        )
        scale.pack(side="left", fill="x", expand=True)
        entry = ttk.Entry(row, width=8)
        entry.insert(0, str(self.param_vars[name].get()))
        entry.pack(side="left", padx=4)
        entry.bind("<Return>", lambda e, n=name, ent=entry: self._on_entry(n, ent))
        # store entry so we can update its text on slider drag
        setattr(self, f"_entry_{name}", entry)

    # ---------- callbacks ----------

    def _on_param_change(self, name: str):
        if self._building:
            return
        # Sync entry box
        ent = getattr(self, f"_entry_{name}", None)
        if ent is not None:
            ent.delete(0, "end")
            ent.insert(0, f"{self.param_vars[name].get():.0f}")
        self._refresh()

    def _on_entry(self, name: str, entry: ttk.Entry):
        try:
            val = float(entry.get())
        except ValueError:
            return
        lo, hi, _ = PARAM_RANGES[name]
        val = max(lo, min(hi, val))
        self.param_vars[name].set(val)
        entry.delete(0, "end")
        entry.insert(0, f"{val:.0f}")
        self._refresh()

    def _on_elbow_entry(self, _event):
        try:
            val = float(self.elbow_entry.get())
        except ValueError:
            return
        self.elbow_var.set(val)
        self._refresh()

    # ---------- refresh ----------

    def _sync_params(self):
        for f in fields(self.params):
            setattr(self.params, f.name, float(self.param_vars[f.name].get()))

    def _refresh(self):
        self._sync_params()
        d = compute(self.params)

        # Update elbow slider bounds
        self.elbow_scale.configure(from_=d.elbow_min, to=d.elbow_max)
        elbow_y = clamp_elbow(self.elbow_var.get(), d)
        self.elbow_var.set(elbow_y)
        self.elbow_label.config(
            text=f"Y = {elbow_y:.0f} mm",
        )
        self.elbow_entry.delete(0, "end")
        self.elbow_entry.insert(0, f"{elbow_y:.0f}")

        # Update info readout
        self.info_label.config(text=(
            f"elbow_to_brick_down = {d.elbow_to_brick_offset_down:.0f}\n"
            f"elbow_to_brick_up   = {d.elbow_to_brick_offset_up:.0f}\n"
            f"max_height_down     = {d.max_height_down:.0f}\n"
            f"min_height_down     = {d.min_height_down:.0f}\n"
            f"min_height_up       = {d.min_height_up:.0f}\n"
            f"max_height_up       = {d.max_height_up:.0f}\n"
            f"elbow range         = [{d.elbow_min:.0f}, {d.elbow_max:.0f}]"
        ))

        # Redraw
        draw(self.ax, self.params, d, elbow_y, self.config_var.get())
        self.canvas.draw_idle()


if __name__ == "__main__":
    App().mainloop()
