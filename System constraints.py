

bottoms_track_ground_offset = 400
tower_height = 1800
tower_height_offset = 100
riser_height = 360
elbow_wrist_height = 120
gap_height = 20
brick_holder_height = 50 
brick_offset = 100
elbow_to_brick_offset_down = elbow_wrist_height + riser_height + 3*gap_height + brick_holder_height + brick_offset
elbow_to_brick_offset_up = elbow_wrist_height + riser_height + 3*gap_height + brick_holder_height - brick_offset

max_height_down = (tower_height - tower_height_offset - elbow_to_brick_offset_down - gap_height)
min_height_down = bottoms_track_ground_offset - elbow_to_brick_offset_down
min_height_up = bottoms_track_ground_offset + elbow_to_brick_offset_up + gap_height
max_height_up = tower_height - tower_height_offset + elbow_to_brick_offset_up - gap_height


print(f"Max height down: {max_height_down}")
print(f"Min height down: {min_height_down}")
print(f"Min height up: {min_height_up}")
print(f"Max height up: {max_height_up}")
