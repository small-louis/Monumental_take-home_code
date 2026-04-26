"""
Derived geometry and reach envelopes for the robot.
Pure functions — no rendering, no GUI.
"""

from dataclasses import dataclass


@dataclass
class Params:
    """All adjustable parameters (mirrors System constraints.py)."""
    bottoms_track_ground_offset: float = 400
    tower_height: float = 1800
    tower_height_offset: float = 100
    riser_height: float = 270
    elbow_wrist_height: float = 120
    gap_height: float = 20
    brick_holder_height: float = 50
    brick_offset: float = 100


@dataclass
class Derived:
    """Values computed from Params, matching System constraints.py."""
    elbow_to_brick_offset_down: float
    elbow_to_brick_offset_up: float
    max_height_down: float
    min_height_down: float
    min_height_up: float
    max_height_up: float
    elbow_min: float  # slider lower bound
    elbow_max: float  # slider upper bound


def compute(p: Params) -> Derived:
    e2b_down = (
        p.elbow_wrist_height
        + p.riser_height
        + 3 * p.gap_height
        + p.brick_holder_height
        + p.brick_offset
    )
    e2b_up = (
        p.elbow_wrist_height
        + p.riser_height
        + 3 * p.gap_height
        + p.brick_holder_height
        - p.brick_offset
    )

    max_h_down = (
        p.tower_height - p.tower_height_offset - e2b_down - p.gap_height
    )
    min_h_down = p.bottoms_track_ground_offset - e2b_down
    min_h_up = p.bottoms_track_ground_offset + e2b_up + p.gap_height
    max_h_up = p.tower_height - p.tower_height_offset + e2b_up - p.gap_height

    # Slider bounds for elbow Y position (per user spec)
    elbow_min = p.bottoms_track_ground_offset
    elbow_max = p.tower_height - p.tower_height_offset

    return Derived(
        elbow_to_brick_offset_down=e2b_down,
        elbow_to_brick_offset_up=e2b_up,
        max_height_down=max_h_down,
        min_height_down=min_h_down,
        min_height_up=min_h_up,
        max_height_up=max_h_up,
        elbow_min=elbow_min,
        elbow_max=elbow_max,
    )


def clamp_elbow(elbow_y: float, d: Derived) -> float:
    return max(d.elbow_min, min(d.elbow_max, elbow_y))
