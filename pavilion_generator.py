"""
Pavilion Generator — GhPython Component for Rhino 8 / Grasshopper

Generates field-condition pavilions inspired by Stan Allen's field conditions
theory and Aldo van Eyck's 1966 Sonsbeek Pavilion. A 50'x50' open-air
pavilion on a marsh site, composed of wall segments on a rotated grid
with curved wall elements, a floating deck, and apertures.

Paste this entire script into a GhPython component. Connect sliders to
the inputs listed below. All inputs have defaults so the component runs
immediately with no connections.

Outputs:
    walls           - list of Brep: trimmed wall solids inside boundary
    arcs            - list of Brep: trimmed curved wall solids
    deck            - Brep: the floating deck platform
    boundary_crv    - Curve: the 50'x50' boundary rectangle
    cutting_volumes - list of Brep: aperture cutting solids (for review)
    ground_plane    - Brep: flat ground surface
    full_field_walls- list of Brep: all walls before boundary trim
    info            - str: summary text
"""

import Rhino.Geometry as rg
import math
import random

# ============================================================================
# SECTION 1: INPUT DEFAULTS
# All GhPython inputs arrive as component variables. If a slider is not
# connected the variable is None, so we apply defaults here.
# ============================================================================

# --- Boundary ---
if boundary_size is None: boundary_size = 50.0

# --- Grid ---
if grid_spacing_x is None: grid_spacing_x = 5.0
if grid_spacing_y is None: grid_spacing_y = 4.0
if grid_rotation is None: grid_rotation = 15.0          # degrees
if grid_offset_x is None: grid_offset_x = 1.5
if grid_offset_y is None: grid_offset_y = 0.0
if overshoot_margin is None: overshoot_margin = 8.0

# --- Wall selection ---
if seed is None: seed = 42
if wall_probability_x is None: wall_probability_x = 0.35
if wall_probability_y is None: wall_probability_y = 0.28

# --- Wall geometry ---
if wall_thickness is None: wall_thickness = 0.5
if wall_height_min is None: wall_height_min = 8.0
if wall_height_max is None: wall_height_max = 14.0
if wall_height_seed is None: wall_height_seed = 7

# --- Arc walls ---
if num_arcs is None: num_arcs = 3
if arc_seed is None: arc_seed = 99
if arc_radius_min is None: arc_radius_min = 3.0
if arc_radius_max is None: arc_radius_max = 8.0
if arc_angle_min is None: arc_angle_min = 60.0           # degrees
if arc_angle_max is None: arc_angle_max = 180.0
if arc_thickness is None: arc_thickness = 0.5
if arc_height_min is None: arc_height_min = 8.0
if arc_height_max is None: arc_height_max = 12.0
if arc_snap_to_grid is None: arc_snap_to_grid = True

# --- Deck ---
if deck_height is None: deck_height = 2.5
if deck_thickness is None: deck_thickness = 0.33
if deck_overshoot is None: deck_overshoot = 1.0

# --- Apertures ---
if num_apertures is None: num_apertures = 12
if aperture_seed is None: aperture_seed = 55
if aperture_width is None: aperture_width = 1.5
if aperture_height is None: aperture_height = 3.0
if apertures_on_walls is None: apertures_on_walls = True
if apertures_on_deck is None: apertures_on_deck = True

# --- Display ---
if trim_at_boundary is None: trim_at_boundary = True
if show_boundary is None: show_boundary = True

# --- Density gradient (optional) ---
if density_gradient_dir is None: density_gradient_dir = 0.0   # angle degrees
if density_gradient_strength is None: density_gradient_strength = 0.0

# --- Height gradient (optional) ---
if height_gradient_dir is None: height_gradient_dir = 90.0
if height_gradient_strength is None: height_gradient_strength = 0.0

# ============================================================================
# SECTION 2: HELPER FUNCTIONS
# ============================================================================

info_messages = []


def rand_range(rng, lo, hi):
    """Uniform random float in [lo, hi] using the given Random instance."""
    return lo + rng.random() * (hi - lo)


def make_box_brep(origin, x_vec, y_vec, width, depth, height):
    """Create a solid box Brep from an origin point, orientation vectors,
    and dimensions. Returns a closed Brep or None."""
    plane = rg.Plane(origin, x_vec, y_vec)
    interval_x = rg.Interval(0, width)
    interval_y = rg.Interval(-depth / 2.0, depth / 2.0)
    interval_z = rg.Interval(0, height)
    box = rg.Box(plane, interval_x, interval_y, interval_z)
    return box.ToBrep()


def make_box_from_corners(pt0, pt1, pt2, pt3, height):
    """Create a solid box Brep by extruding a rectangle defined by 4 base
    corner points up to the given height."""
    pt4 = rg.Point3d(pt0.X, pt0.Y, pt0.Z + height)
    pt5 = rg.Point3d(pt1.X, pt1.Y, pt1.Z + height)
    pt6 = rg.Point3d(pt2.X, pt2.Y, pt2.Z + height)
    pt7 = rg.Point3d(pt3.X, pt3.Y, pt3.Z + height)
    corners = [pt0, pt1, pt2, pt3, pt4, pt5, pt6, pt7]
    box = rg.BoundingBox(corners)
    # BoundingBox is axis-aligned — build manually for oriented walls
    # Instead: extrude a planar curve
    base_pts = [pt0, pt1, pt2, pt3, pt0]
    base_crv = rg.PolylineCurve([rg.Point3d(p.X, p.Y, p.Z) for p in base_pts])
    if not base_crv.IsClosed:
        return None
    extrusion = rg.Extrusion.Create(base_crv, height, True)
    if extrusion:
        return extrusion.ToBrep()
    return None


def extrude_closed_crv(crv, height):
    """Extrude a closed planar curve upward by height, cap both ends."""
    if crv is None or not crv.IsClosed:
        return None
    srf = rg.Extrusion.Create(crv, height, True)
    if srf:
        return srf.ToBrep()
    return None


def safe_boolean_difference(brep, cutters, info_list):
    """Boolean difference with fallback. Returns result Brep and appends
    to info_list on failure."""
    if not cutters:
        return brep
    try:
        tol = 0.001
        result = rg.Brep.CreateBooleanDifference(brep, cutters, tol)
        if result and len(result) > 0:
            return result[0]
        else:
            info_list.append("Boolean diff returned empty — kept original")
            return brep
    except Exception as e:
        info_list.append("Boolean diff failed: {} — kept original".format(e))
        return brep


def safe_boolean_intersection(brep, cutter, info_list):
    """Boolean intersection with fallback."""
    try:
        tol = 0.001
        result = rg.Brep.CreateBooleanIntersection(brep, cutter, tol)
        if result and len(result) > 0:
            return result[0]
        else:
            info_list.append("Boolean intersection empty — kept original")
            return brep
    except Exception as e:
        info_list.append("Boolean intersection failed: {} — kept original".format(e))
        return brep


def perp_offset_pts(pt_a, pt_b, thickness):
    """Given two points defining a line segment on the XY plane, return
    4 corner points offset perpendicular by ±thickness/2."""
    dx = pt_b.X - pt_a.X
    dy = pt_b.Y - pt_a.Y
    length = math.sqrt(dx * dx + dy * dy)
    if length < 0.0001:
        return None
    nx = -dy / length * (thickness / 2.0)
    ny = dx / length * (thickness / 2.0)
    c0 = rg.Point3d(pt_a.X + nx, pt_a.Y + ny, 0)
    c1 = rg.Point3d(pt_b.X + nx, pt_b.Y + ny, 0)
    c2 = rg.Point3d(pt_b.X - nx, pt_b.Y - ny, 0)
    c3 = rg.Point3d(pt_a.X - nx, pt_a.Y - ny, 0)
    return (c0, c1, c2, c3)


def density_factor(midpoint, center, grad_dir_rad, grad_strength):
    """Compute a probability multiplier based on position along a gradient
    direction. Returns a value in [1 - strength, 1 + strength]."""
    if abs(grad_strength) < 0.001:
        return 1.0
    dx = midpoint.X - center.X
    dy = midpoint.Y - center.Y
    proj = dx * math.cos(grad_dir_rad) + dy * math.sin(grad_dir_rad)
    max_dist = 35.0  # normalizing distance
    t = max(-1.0, min(1.0, proj / max_dist))
    return 1.0 + grad_strength * t


def height_factor(midpoint, center, grad_dir_rad, grad_strength):
    """Compute a height multiplier based on position."""
    return density_factor(midpoint, center, grad_dir_rad, grad_strength)


# ============================================================================
# SECTION 3: GRID GENERATION
# Generate individual wall segments on a grid that extends beyond the
# boundary, so trimming creates the "field extends beyond frame" effect.
# ============================================================================

center_x = boundary_size / 2.0
center_y = boundary_size / 2.0
center_pt = rg.Point3d(center_x, center_y, 0)

field_size = boundary_size + 2.0 * overshoot_margin
field_min = -overshoot_margin + grid_offset_x
field_max_x = boundary_size + overshoot_margin + grid_offset_x
field_min_y = -overshoot_margin + grid_offset_y
field_max_y = boundary_size + overshoot_margin + grid_offset_y

# Grid line positions (before rotation)
x_positions = []
pos = field_min
while pos <= field_max_x:
    x_positions.append(pos)
    pos += grid_spacing_x

y_positions = []
pos = field_min_y
while pos <= field_max_y:
    y_positions.append(pos)
    pos += grid_spacing_y

# Rotation transform around the boundary center
rot_rad = math.radians(grid_rotation)
rotation_xform = rg.Transform.Rotation(rot_rad, rg.Vector3d.ZAxis, center_pt)

# Build individual segments
# X-direction segments: horizontal lines between consecutive x_positions at each y
# Y-direction segments: vertical lines between consecutive y_positions at each x
segments = []  # list of (Line, "x" or "y")

for y_val in y_positions:
    for i in range(len(x_positions) - 1):
        pt_a = rg.Point3d(x_positions[i], y_val, 0)
        pt_b = rg.Point3d(x_positions[i + 1], y_val, 0)
        pt_a.Transform(rotation_xform)
        pt_b.Transform(rotation_xform)
        seg = rg.Line(pt_a, pt_b)
        segments.append((seg, "x"))

for x_val in x_positions:
    for j in range(len(y_positions) - 1):
        pt_a = rg.Point3d(x_val, y_positions[j], 0)
        pt_b = rg.Point3d(x_val, y_positions[j + 1], 0)
        pt_a.Transform(rotation_xform)
        pt_b.Transform(rotation_xform)
        seg = rg.Line(pt_a, pt_b)
        segments.append((seg, "y"))

# Grid intersection points (for arc snapping)
grid_pts = []
for x_val in x_positions:
    for y_val in y_positions:
        pt = rg.Point3d(x_val, y_val, 0)
        pt.Transform(rotation_xform)
        grid_pts.append(pt)

info_messages.append("Grid: {}x cols, {}y rows, {} segments".format(
    len(x_positions), len(y_positions), len(segments)))

# ============================================================================
# SECTION 4: WALL SELECTION & BREP GENERATION
# Probabilistically select segments, then extrude into solid wall Breps.
# ============================================================================

wall_rng = random.Random(seed)
height_rng = random.Random(wall_height_seed)

grad_dir_rad = math.radians(density_gradient_dir)
h_grad_dir_rad = math.radians(height_gradient_dir)

selected_walls = []      # list of (Line, direction, height)
full_field_walls = []     # output: Brep list before trimming

for seg, direction in segments:
    mid = rg.Point3d((seg.From.X + seg.To.X) / 2.0,
                     (seg.From.Y + seg.To.Y) / 2.0, 0)
    d_factor = density_factor(mid, center_pt, grad_dir_rad,
                              density_gradient_strength)
    if direction == "x":
        prob = wall_probability_x * d_factor
    else:
        prob = wall_probability_y * d_factor
    prob = max(0.0, min(1.0, prob))
    if wall_rng.random() < prob:
        h_factor = height_factor(mid, center_pt, h_grad_dir_rad,
                                 height_gradient_strength)
        h = rand_range(height_rng, wall_height_min, wall_height_max)
        h = max(wall_height_min, min(wall_height_max, h * h_factor))
        selected_walls.append((seg, direction, h))

# Build wall Breps
wall_breps_pre_trim = []
wall_segment_data = []  # store (seg, direction, height) for apertures

for seg, direction, h in selected_walls:
    corners = perp_offset_pts(seg.From, seg.To, wall_thickness)
    if corners is None:
        continue
    c0, c1, c2, c3 = corners
    pts = [c0, c1, c2, c3, c0]
    base_crv = rg.PolylineCurve(pts)
    brep = extrude_closed_crv(base_crv, h)
    if brep:
        wall_breps_pre_trim.append(brep)
        wall_segment_data.append((seg, direction, h))

full_field_walls = list(wall_breps_pre_trim)
info_messages.append("Walls selected: {}, built: {}".format(
    len(selected_walls), len(wall_breps_pre_trim)))

# ============================================================================
# SECTION 5: ARC WALL GENERATION
# Curved wall elements that introduce non-orthogonal field disruptions,
# referencing van Eyck's use of circular and semicircular walls.
# ============================================================================

arc_rng = random.Random(arc_seed)
arc_breps_pre_trim = []

for i in range(int(num_arcs)):
    # Center point
    if arc_snap_to_grid and len(grid_pts) > 0:
        c_pt = grid_pts[arc_rng.randint(0, len(grid_pts) - 1)]
    else:
        cx = rand_range(arc_rng, -overshoot_margin, boundary_size + overshoot_margin)
        cy = rand_range(arc_rng, -overshoot_margin, boundary_size + overshoot_margin)
        c_pt = rg.Point3d(cx, cy, 0)

    radius = rand_range(arc_rng, arc_radius_min, arc_radius_max)
    sweep_deg = rand_range(arc_rng, arc_angle_min, arc_angle_max)
    sweep_rad = math.radians(sweep_deg)
    start_deg = rand_range(arc_rng, 0, 360)
    start_rad = math.radians(start_deg)
    arc_h = rand_range(arc_rng, arc_height_min, arc_height_max)

    # Inner and outer radii
    r_inner = max(0.1, radius - arc_thickness / 2.0)
    r_outer = radius + arc_thickness / 2.0

    # Build the thick arc as a closed planar curve
    # Outer arc
    arc_plane = rg.Plane(c_pt, rg.Vector3d.ZAxis)
    outer_arc = rg.Arc(arc_plane, r_outer, sweep_rad)
    inner_arc = rg.Arc(arc_plane, r_inner, sweep_rad)

    # Rotate arcs to start angle
    rot_xform = rg.Transform.Rotation(start_rad, rg.Vector3d.ZAxis, c_pt)

    outer_crv = outer_arc.ToNurbsCurve()
    inner_crv = inner_arc.ToNurbsCurve()
    outer_crv.Transform(rot_xform)
    inner_crv.Transform(rot_xform)

    # Reverse inner arc so we can join end-to-end
    inner_crv.Reverse()

    # End cap lines
    cap1 = rg.LineCurve(outer_crv.PointAtStart, inner_crv.PointAtEnd)
    cap2 = rg.LineCurve(inner_crv.PointAtStart, outer_crv.PointAtEnd)

    # Join into closed curve
    joined = rg.Curve.JoinCurves([outer_crv, cap2, inner_crv, cap1], 0.01)
    if joined and len(joined) > 0 and joined[0].IsClosed:
        brep = extrude_closed_crv(joined[0], arc_h)
        if brep:
            arc_breps_pre_trim.append(brep)
    else:
        info_messages.append("Arc {} failed to close curve".format(i))

info_messages.append("Arcs built: {}".format(len(arc_breps_pre_trim)))

# ============================================================================
# SECTION 6: DECK GENERATION
# A floating platform at deck_height — the primary horizontal datum that
# mediates between ground (marsh) and the vertical wall field.
# ============================================================================

deck_extent = boundary_size + 2.0 * deck_overshoot
deck_origin = rg.Point3d(center_x - deck_extent / 2.0,
                         center_y - deck_extent / 2.0,
                         deck_height)
deck_corner_opp = rg.Point3d(center_x + deck_extent / 2.0,
                             center_y + deck_extent / 2.0,
                             deck_height + deck_thickness)
deck_box = rg.BoundingBox(deck_origin, deck_corner_opp)
deck_brep = rg.Brep.CreateFromBox(deck_box)

info_messages.append("Deck: {:.1f}x{:.1f} at z={:.1f}".format(
    deck_extent, deck_extent, deck_height))

# ============================================================================
# SECTION 7: APERTURE GENERATION & BOOLEAN OPERATIONS
# Apertures are rectangular voids cut into walls and deck. They introduce
# transparency, framed views, and light modulation — key to the field
# condition's interplay of solid and void.
# ============================================================================

aperture_rng = random.Random(aperture_seed)
cutting_volumes = []
aperture_depth = wall_thickness * 3.0  # ensure full penetration

# --- Wall apertures ---
if apertures_on_walls and len(wall_breps_pre_trim) > 0:
    skip_booleans = len(wall_breps_pre_trim) > 50
    if skip_booleans:
        info_messages.append("Over 50 walls — skipping wall booleans for speed")

    # Group cutters by wall index
    wall_cutters = {}
    for a_idx in range(int(num_apertures)):
        w_idx = aperture_rng.randint(0, len(wall_breps_pre_trim) - 1)
        seg, direction, w_h = wall_segment_data[w_idx]

        # Position along wall length
        t = rand_range(aperture_rng, 0.15, 0.85)
        pt_on_wall = rg.Point3d(
            seg.From.X + t * (seg.To.X - seg.From.X),
            seg.From.Y + t * (seg.To.Y - seg.From.Y),
            0)

        # Height position — bias toward above deck for windows
        z_base = rand_range(aperture_rng, 0, max(0.1, w_h - aperture_height))

        # Wall direction vector and perpendicular
        dx = seg.To.X - seg.From.X
        dy = seg.To.Y - seg.From.Y
        seg_len = math.sqrt(dx * dx + dy * dy)
        if seg_len < 0.001:
            continue
        wall_dir = rg.Vector3d(dx / seg_len, dy / seg_len, 0)
        wall_perp = rg.Vector3d(-wall_dir.Y, wall_dir.X, 0)

        # Cutting box centered on wall, oriented to wall direction
        cut_origin = rg.Point3d(
            pt_on_wall.X - wall_dir.X * aperture_width / 2.0 - wall_perp.X * aperture_depth / 2.0,
            pt_on_wall.Y - wall_dir.Y * aperture_width / 2.0 - wall_perp.Y * aperture_depth / 2.0,
            z_base)
        cut_plane = rg.Plane(cut_origin, wall_dir, wall_perp)
        cut_box = rg.Box(cut_plane,
                         rg.Interval(0, aperture_width),
                         rg.Interval(0, aperture_depth),
                         rg.Interval(0, aperture_height))
        cut_brep = cut_box.ToBrep()
        if cut_brep:
            cutting_volumes.append(cut_brep)
            if not skip_booleans:
                if w_idx not in wall_cutters:
                    wall_cutters[w_idx] = []
                wall_cutters[w_idx].append(cut_brep)

    # Apply boolean differences to walls
    if not skip_booleans:
        for w_idx, cutters in wall_cutters.items():
            wall_breps_pre_trim[w_idx] = safe_boolean_difference(
                wall_breps_pre_trim[w_idx], cutters, info_messages)

# --- Deck apertures ---
if apertures_on_deck and deck_brep:
    deck_cutters = []
    n_deck_ap = max(1, int(num_apertures) // 2)
    for _ in range(n_deck_ap):
        ax = rand_range(aperture_rng, 2, boundary_size - 2)
        ay = rand_range(aperture_rng, 2, boundary_size - 2)
        ap_w = rand_range(aperture_rng, aperture_width * 0.8, aperture_width * 1.5)
        ap_d = rand_range(aperture_rng, aperture_width * 0.8, aperture_width * 1.5)
        cut_origin = rg.Point3d(ax - ap_w / 2.0, ay - ap_d / 2.0,
                                deck_height - 0.5)
        cut_top = rg.Point3d(ax + ap_w / 2.0, ay + ap_d / 2.0,
                             deck_height + deck_thickness + 0.5)
        cut_bb = rg.BoundingBox(cut_origin, cut_top)
        cut_brep = rg.Brep.CreateFromBox(cut_bb)
        if cut_brep:
            cutting_volumes.append(cut_brep)
            deck_cutters.append(cut_brep)

    if deck_cutters:
        deck_brep = safe_boolean_difference(deck_brep, deck_cutters, info_messages)

info_messages.append("Apertures: {} cutting volumes".format(len(cutting_volumes)))

# ============================================================================
# SECTION 8: BOUNDARY TRIMMING & OUTPUT ASSEMBLY
# The boundary acts as a frame that reveals the field — walls extend beyond
# and are clipped, suggesting the field continues infinitely.
# ============================================================================

# Boundary rectangle
boundary_plane = rg.Plane(rg.Point3d(0, 0, 0), rg.Vector3d.ZAxis)
boundary_rect = rg.Rectangle3d(boundary_plane,
                               rg.Interval(0, boundary_size),
                               rg.Interval(0, boundary_size))
boundary_crv = boundary_rect.ToNurbsCurve() if show_boundary else None

# Trimming box — tall enough to contain all geometry
trim_height = wall_height_max + 2.0
trim_origin = rg.Point3d(0, 0, -1)
trim_top = rg.Point3d(boundary_size, boundary_size, trim_height)
trim_bb = rg.BoundingBox(trim_origin, trim_top)
trim_box_brep = rg.Brep.CreateFromBox(trim_bb)

# Trim walls
walls = []
if trim_at_boundary and trim_box_brep:
    for brep in wall_breps_pre_trim:
        trimmed = safe_boolean_intersection(brep, trim_box_brep, info_messages)
        if trimmed:
            walls.append(trimmed)
else:
    walls = list(wall_breps_pre_trim)

# Trim arcs
arcs = []
if trim_at_boundary and trim_box_brep:
    for brep in arc_breps_pre_trim:
        trimmed = safe_boolean_intersection(brep, trim_box_brep, info_messages)
        if trimmed:
            arcs.append(trimmed)
else:
    arcs = list(arc_breps_pre_trim)

# Ground plane — flat surface at z=0, extends slightly beyond boundary
gp_margin = 3.0
gp_pts = [
    rg.Point3d(-gp_margin, -gp_margin, 0),
    rg.Point3d(boundary_size + gp_margin, -gp_margin, 0),
    rg.Point3d(boundary_size + gp_margin, boundary_size + gp_margin, 0),
    rg.Point3d(-gp_margin, boundary_size + gp_margin, 0)
]
ground_plane = rg.Brep.CreateFromCornerPoints(
    gp_pts[0], gp_pts[1], gp_pts[2], gp_pts[3], 0.001)

# Ground contact count
ground_contact = 0
for brep in walls:
    bb = brep.GetBoundingBox(True)
    if bb.Min.Z < 0.1:
        ground_contact += 1

info_messages.append("Trimmed walls: {}, arcs: {}".format(len(walls), len(arcs)))
info_messages.append("Walls touching ground: {}".format(ground_contact))

# ============================================================================
# BONUS: PLAN CURVES
# Project wall and arc footprints onto z=0 for plan-view analysis.
# ============================================================================

plan_curves = []
z_plane = rg.Plane.WorldXY
for brep in walls:
    edges = brep.Edges
    for edge in edges:
        mid = edge.PointAtNormalizedLength(0.5)
        if abs(mid.Z) < 0.1:
            plan_curves.append(edge.ToNurbsCurve())

for brep in arcs:
    edges = brep.Edges
    for edge in edges:
        mid = edge.PointAtNormalizedLength(0.5)
        if abs(mid.Z) < 0.1:
            plan_curves.append(edge.ToNurbsCurve())

# ============================================================================
# FINAL INFO STRING
# ============================================================================

info_messages.append("--- Pavilion Generator ---")
info_messages.append("Boundary: {:.0f}' x {:.0f}'".format(boundary_size, boundary_size))
info_messages.append("Grid: {:.1f}x{:.1f} spacing, {:.0f} deg rotation".format(
    grid_spacing_x, grid_spacing_y, grid_rotation))
info_messages.append("Seeds: wall={}, height={}, arc={}, aperture={}".format(
    seed, wall_height_seed, arc_seed, aperture_seed))

info = "\n".join(info_messages)
