"""
2D side-view renderer for the robot mast + arm stack.
Pure drawing — no GUI, no state.
"""

from matplotlib.patches import Rectangle, Circle
from calculations import Params, Derived


# Visual constants (only affect drawing, not physics)
MAST_WIDTH = 80
MAST_GAP = 220                # horizontal gap between the two mast columns
PLATFORM_WIDTH = MAST_GAP + 2 * MAST_WIDTH + 80
PLATFORM_THICKNESS = 60       # visual thickness of the "T" base top
WHEEL_RADIUS = 80
STACK_X_OFFSET = 320          # X of the stack centerline, right of mast cx
GROUND_PAD = 400              # extra horizontal margin around drawing

# Per-block cosmetic dimensions and X offsets (NOT in UI — tune here).
# x_offset is measured from the stack centerline (STACK_X_OFFSET).
# Positive x_offset shifts the block to the right of the centerline.
# Widths are visual only; heights come from Params.
BLOCK_DIMS = {
    "elbow":  {"width": 300, "x_offset":   20},   # dark blue, wide
    "wrist":  {"width":  150, "x_offset":   +120},   # light grey, narrower
    "riser":  {"width":  70, "x_offset":   +180},   # light blue, narrow + tall
    "holder": {"width": 280, "x_offset": +250},  # orange, long bar extending left
    "brick":  {"width":  70, "x_offset": +350},  # dark grey, sits at right end
}

# Colors matching the reference image
COLOR_MAST = "#7a7a7a"
COLOR_PLATFORM = "#7a7a7a"
COLOR_WHEEL = "#7a7a7a"
COLOR_ELBOW = "#2f4a87"       # dark blue
COLOR_WRIST = "#bfbfbf"       # light grey
COLOR_RISER = "#9bb4c9"       # light blue
COLOR_HOLDER = "#c87a2f"      # orange
COLOR_BRICK = "#4a4a4a"       # dark grey
COLOR_GROUND = "#1f4e6b"
COLOR_REACH_DOWN = "#c87a2f"  # translucent band (down config)
COLOR_REACH_UP = "#2f4a87"    # translucent band (up config)


def draw(ax, p: Params, d: Derived, elbow_y: float, config: str):
    """
    Draw the full scene into the given matplotlib Axes.
    config: "down" or "up"
    """
    ax.clear()

    mast_cx = 0  # mast assembly centered at x=0

    _draw_base(ax, p, mast_cx)
    _draw_masts(ax, p, mast_cx)
    _draw_reach_envelopes(ax, p, d, mast_cx)
    elbow_line_y = _draw_stack(ax, p, elbow_y, config, mast_cx)
    _draw_ground(ax, mast_cx, p)
    _draw_elbow_marker(ax, mast_cx, elbow_line_y)

    # Frame the view — include full stack extents in both configs
    holder_w = BLOCK_DIMS["holder"]["width"]
    x_min = mast_cx - PLATFORM_WIDTH / 2 - GROUND_PAD
    x_max = mast_cx + STACK_X_OFFSET + holder_w + GROUND_PAD

    # Stack extends from elbow downward by elbow_to_brick_offset_down (down config)
    # and upward by elbow_to_brick_offset_up (up config). Plus brick hangs an
    # extra brick_offset below the orange bar in BOTH configs.
    stack_low_down = elbow_y - d.elbow_to_brick_offset_down
    stack_high_up = elbow_y + d.elbow_to_brick_offset_up
    # In up config the brick hangs below the orange bar, which sits at
    # elbow_y + elbow_wrist_height + 2*gap + riser + gap. The brick bottom is
    # then orange_bottom - brick_offset. Approx with already-computed values:
    up_orange_bottom = elbow_y + (
        p.elbow_wrist_height + 2 * p.gap_height + p.riser_height + p.gap_height
    )
    up_brick_bottom = up_orange_bottom - p.brick_offset

    y_candidates_low = [
        0,                              # ground
        stack_low_down,                 # down-config brick bottom
        up_brick_bottom,                # up-config brick bottom (hangs below bar)
        -p.brick_offset - p.brick_holder_height - 100,
    ]
    y_candidates_high = [
        p.tower_height,                 # mast top
        stack_high_up + 100,            # up-config top of stack
        elbow_y + p.elbow_wrist_height, # down-config dark blue top
    ]
    y_min = min(y_candidates_low) - 200
    y_max = max(y_candidates_high) + 200

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def _draw_base(ax, p: Params, cx: float):
    """
    Clean wagon base:
      - one horizontal platform at the top (mast bottoms sit on it)
      - one chassis block below the platform
      - two wheels resting on the ground, axles at y = WHEEL_RADIUS
    """
    plat_top = p.bottoms_track_ground_offset
    chassis_top = plat_top - PLATFORM_THICKNESS
    chassis_bottom = WHEEL_RADIUS               # chassis sits on the wheel axles
    chassis_w = PLATFORM_WIDTH * 0.85

    # Chassis (vertical block) — drawn first so platform overlays its top edge
    if chassis_top > chassis_bottom:
        ax.add_patch(Rectangle(
            (cx - chassis_w / 2, chassis_bottom),
            chassis_w, chassis_top - chassis_bottom,
            facecolor=COLOR_PLATFORM, edgecolor="black", linewidth=1.2,
        ))

    # Platform top slab
    ax.add_patch(Rectangle(
        (cx - PLATFORM_WIDTH / 2, chassis_top),
        PLATFORM_WIDTH, PLATFORM_THICKNESS,
        facecolor=COLOR_PLATFORM, edgecolor="black", linewidth=1.2,
    ))

    # Wheels
    wheel_dx = chassis_w / 2 - WHEEL_RADIUS * 0.6
    for sign in (-1, 1):
        ax.add_patch(Circle(
            (cx + sign * wheel_dx, WHEEL_RADIUS),
            WHEEL_RADIUS,
            facecolor=COLOR_WHEEL, edgecolor="black", linewidth=1.2,
        ))


def _draw_masts(ax, p: Params, cx: float):
    mast_bottom = p.bottoms_track_ground_offset
    mast_top = p.tower_height
    for sign in (-1, 1):
        x = cx + sign * (MAST_GAP / 2 + MAST_WIDTH / 2) - MAST_WIDTH / 2
        ax.add_patch(Rectangle(
            (x, mast_bottom),
            MAST_WIDTH, mast_top - mast_bottom,
            facecolor=COLOR_MAST, edgecolor="black", linewidth=1.2,
        ))


def _draw_reach_envelopes(ax, p: Params, d: Derived, cx: float):
    """Translucent bands showing where the brick can be placed in each config."""
    holder_w = BLOCK_DIMS["holder"]["width"]
    band_x = cx + STACK_X_OFFSET + holder_w + 60
    band_w = 60

    # Brick reach in DOWN config: brick_y range corresponds to elbow sweeping
    # full slider range, so brick_y = elbow_y - elbow_to_brick_offset_down
    down_low = d.elbow_min - d.elbow_to_brick_offset_down
    down_high = d.elbow_max - d.elbow_to_brick_offset_down
    ax.add_patch(Rectangle(
        (band_x, down_low),
        band_w, down_high - down_low,
        facecolor=COLOR_REACH_DOWN, edgecolor=COLOR_REACH_DOWN,
        alpha=0.25, linewidth=0,
    ))
    ax.text(band_x + band_w / 2, down_high + 30, "down\nreach",
            ha="center", va="bottom", fontsize=8, color=COLOR_REACH_DOWN)

    # Brick reach in UP config: brick_y = elbow_y + elbow_to_brick_offset_up
    up_low = d.elbow_min + d.elbow_to_brick_offset_up
    up_high = d.elbow_max + d.elbow_to_brick_offset_up
    ax.add_patch(Rectangle(
        (band_x + band_w + 20, up_low),
        band_w, up_high - up_low,
        facecolor=COLOR_REACH_UP, edgecolor=COLOR_REACH_UP,
        alpha=0.25, linewidth=0,
    ))
    ax.text(band_x + band_w + 20 + band_w / 2, up_high + 30, "up\nreach",
            ha="center", va="bottom", fontsize=8, color=COLOR_REACH_UP)


def _draw_stack(ax, p: Params, elbow_y: float, config: str, cx: float):
    """
    Draw the colored stack. The elbow pivot is at the bottom edge of the
    dark blue block (down config) or top edge (up config) — i.e. the elbow
    block extends AWAY from the rest of the stack.

    Down config (matches reference image):
        elbow_y is the BOTTOM of the dark blue block.
        - dark blue (elbow) extends UP from elbow_y by elbow_wrist_height
        - everything else hangs DOWN from elbow_y:
          gap, wrist (light grey), gap, riser (light blue), gap,
          orange holder bar, gap, dark grey brick on right end of bar

    Up config: vertical mirror; brick sits on the LEFT end of the bar.

    Returns the y coordinate where the red elbow indicator should sit.
    """
    stack_cx = cx + STACK_X_OFFSET

    if config == "down":
        elbow_sign = +1   # dark blue grows UP from elbow_y
        stack_sign = -1   # rest grows DOWN from elbow_y
    else:
        elbow_sign = -1   # dark blue grows DOWN from elbow_y
        stack_sign = +1   # rest grows UP from elbow_y

    # 1. Elbow block (dark blue) — grows AWAY from the rest of the stack
    _draw_block(ax, stack_cx, elbow_y, elbow_sign, "elbow",
                p.elbow_wrist_height, COLOR_ELBOW)

    # Walk the rest of the stack starting from elbow_y in stack_sign direction
    cursor = elbow_y + stack_sign * p.gap_height

    # 2. Wrist (light grey)
    cursor = _walk_block(ax, stack_cx, cursor, stack_sign, "wrist",
                         p.elbow_wrist_height, COLOR_WRIST)
    cursor += stack_sign * p.gap_height

    # 3. Riser (light blue)
    cursor = _walk_block(ax, stack_cx, cursor, stack_sign, "riser",
                         p.riser_height, COLOR_RISER)
    cursor += stack_sign * p.gap_height

    # 4. Orange holder bar — keeps its x_offset in both configs
    holder_x_offset = BLOCK_DIMS["holder"]["x_offset"]
    holder_w = BLOCK_DIMS["holder"]["width"]
    holder_x_left = stack_cx + holder_x_offset - holder_w / 2
    holder_y_bottom = cursor if stack_sign > 0 else cursor - p.brick_holder_height
    holder_y_top = holder_y_bottom + p.brick_holder_height
    ax.add_patch(Rectangle(
        (holder_x_left, holder_y_bottom),
        holder_w, p.brick_holder_height,
        facecolor=COLOR_HOLDER, edgecolor="black", linewidth=1.0,
    ))

    # 5. Brick (dark grey) — keeps its x_offset; ALWAYS hangs flush below the
    # orange bar (top of brick = bottom of orange bar), no gap, in both configs.
    brick_x_offset = BLOCK_DIMS["brick"]["x_offset"]
    brick_w = BLOCK_DIMS["brick"]["width"]
    brick_x_left = stack_cx + brick_x_offset - brick_w / 2
    brick_y_top = holder_y_bottom
    brick_y_bottom = brick_y_top - p.brick_offset
    ax.add_patch(Rectangle(
        (brick_x_left, brick_y_bottom),
        brick_w, p.brick_offset,
        facecolor=COLOR_BRICK, edgecolor="black", linewidth=1.0,
    ))

    return elbow_y  # red line sits at the elbow pivot (bottom of dark blue)


def _draw_block(ax, stack_cx, y_anchor, sign, name, height, color):
    """Draw a named block at `y_anchor`, growing in `sign` direction (+1 up)."""
    dims = BLOCK_DIMS[name]
    w = dims["width"]
    x_left = stack_cx + dims["x_offset"] - w / 2
    y_bottom = y_anchor if sign > 0 else y_anchor - height
    ax.add_patch(Rectangle(
        (x_left, y_bottom), w, height,
        facecolor=color, edgecolor="black", linewidth=1.0,
    ))


def _walk_block(ax, stack_cx, y_anchor, sign, name, height, color):
    """Like _draw_block but returns the new cursor (far edge in sign dir)."""
    _draw_block(ax, stack_cx, y_anchor, sign, name, height, color)
    return y_anchor + sign * height


def _draw_ground(ax, cx: float, p: Params):
    holder_w = BLOCK_DIMS["holder"]["width"]
    x_left = cx - PLATFORM_WIDTH / 2 - GROUND_PAD
    x_right = cx + STACK_X_OFFSET + holder_w + GROUND_PAD + 200
    ax.plot([x_left, x_right], [0, 0], color=COLOR_GROUND, linewidth=2)


def _draw_elbow_marker(ax, cx: float, elbow_y: float):
    """Small horizontal tick on the mast indicating the current elbow Y."""
    ax.plot(
        [cx - (MAST_GAP / 2 + MAST_WIDTH), cx + (MAST_GAP / 2 + MAST_WIDTH)],
        [elbow_y, elbow_y],
        color="red", linewidth=1.0, linestyle="--", alpha=0.6,
    )
