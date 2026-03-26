"""
Pavilion Generator (Simple) — GhPython Component for Rhino 8 / Grasshopper

Generates field-condition pavilions inspired by Stan Allen's field conditions
theory and Aldo van Eyck's 1966 Sonsbeek Pavilion. A 50'x50' open-air
pavilion on a marsh site, composed of wall segments on a rotated grid
with semicircular wall disruptions, a floating deck, and wall apertures.

SETUP: Paste this entire script into a GhPython component in Grasshopper.
Right-click the component and add the inputs listed below (matching names
exactly). Connect Number Sliders to each. All inputs have defaults, so the
component runs immediately with zero connections.

Inputs (add these as GhPython component inputs — names must match exactly):

  GRID
    grid_spacing_x          float   5.0     Column spacing in X direction (feet)
    grid_spacing_y          float   4.0     Row spacing in Y direction (feet)

  WALL SELECTION
    seed                    int     42      Random seed for which walls appear
    wall_probability_x      float   0.35    Chance a horizontal segment becomes a wall (0-1)
    wall_probability_y      float   0.28    Chance a vertical segment becomes a wall (0-1)

  WALL GEOMETRY
    wall_thickness          float   0.5     Wall thickness (feet)
    wall_height_min         float   8.0     Minimum wall height (feet)
    wall_height_max         float   14.0    Maximum wall height (feet)
    wall_height_seed        int     7       Random seed for wall height assignment

  ARC WALLS (semicircles that replace the middle of a straight wall)
    num_arcs                int     3       Number of walls to convert to arcs
    arc_seed                int     99      Random seed for which walls get arcs

  DECK
    deck_height             float   2.5     Deck elevation above ground (feet)
    deck_thickness          float   0.33    Deck slab thickness (feet)

  APERTURES (rectangular cuts in walls only)
    num_apertures           int     12      Total number of aperture cuts
    aperture_seed           int     55      Random seed for aperture placement
    aperture_width          float   1.5     Aperture opening width (feet)
    aperture_height         float   3.0     Aperture opening height (feet)

Outputs (add these as GhPython component outputs — names must match exactly):
    walls           - list of Brep: trimmed wall solids inside boundary
    arcs            - list of Brep: trimmed semicircular wall solids
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
# ============================================================================

# --- Grid ---
if grid_spacing_x is None: grid_spacing_x = 5.0
if grid_spacing_y is None: grid_spacing_y = 4.0

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

# --- Deck ---
if deck_height is None: deck_height = 2.5
if deck_thickness is None: deck_thickness = 0.33

# --- Apertures ---
if num_apertures is None: num_apertures = 12
if aperture_seed is None: aperture_seed = 55
if aperture_width is None: aperture_width = 1.5
if aperture_height is None: aperture_height = 3.0

# --- Hardcoded constants ---
BOUNDARY_SIZE = 50.0
GRID_ROTATION = 15.0      # degrees
GRID_OFFSET_X = 1.5
GRID_OFFSET_Y = 0.0
OVERSHOOT = 8.0
DECK_OVERSHOOT = 1.0

# ============================================================================
# SECTION 2: HELPER FUNCTIONS
# ============================================================================

info_messages = []


def rand_range(rng, lo, hi):
    return lo + rng.random() * (hi - lo)


def extrude_closed_crv(crv, height):
    """Extrude a closed planar curve upward, capping both ends."""
    if crv is None or not crv.IsClosed:
        return None
    srf = rg.Extrusion.Create(crv, height, True)
    if srf:
        return srf.ToBrep()
    return None


def safe_boolean_difference(brep, cutters, info_list):
    if not cutters:
        return brep
    try:
        result = rg.Brep.CreateBooleanDifference(brep, cutters, 0.001)
        if result and len(result) > 0:
            return result[0]
        info_list.append("Boolean diff empty — kept original")
        return brep
    except Exception as e:
        info_list.append("Boolean diff failed: {} — kept original".format(e))
        return brep


def safe_boolean_intersection(brep, cutter, info_list):
    try:
        result = rg.Brep.CreateBooleanIntersection(brep, cutter, 0.001)
        if result and len(result) > 0:
            return result[0]
        info_list.append("Boolean intersect empty — kept original")
        return brep
    except Exception as e:
        info_list.append("Boolean intersect failed: {} — kept original".format(e))
        return brep


def perp_offset_pts(pt_a, pt_b, thickness):
    """Return 4 corner points offset perpendicular to a line segment."""
    dx = pt_b.X - pt_a.X
    dy = pt_b.Y - pt_a.Y
    length = math.sqrt(dx * dx + dy * dy)
    if length < 0.0001:
        return None
    nx = -dy / length * (thickness / 2.0)
    ny = dx / length * (thickness / 2.0)
    return (
        rg.Point3d(pt_a.X + nx, pt_a.Y + ny, 0),
        rg.Point3d(pt_b.X + nx, pt_b.Y + ny, 0),
        rg.Point3d(pt_b.X - nx, pt_b.Y - ny, 0),
        rg.Point3d(pt_a.X - nx, pt_a.Y - ny, 0),
    )


# ============================================================================
# SECTION 3: GRID GENERATION
# Individual wall segments on a rotated grid extending beyond the boundary.
# ============================================================================

center_x = BOUNDARY_SIZE / 2.0
center_y = BOUNDARY_SIZE / 2.0
center_pt = rg.Point3d(center_x, center_y, 0)

field_min_x = -OVERSHOOT + GRID_OFFSET_X
field_max_x = BOUNDARY_SIZE + OVERSHOOT + GRID_OFFSET_X
field_min_y = -OVERSHOOT + GRID_OFFSET_Y
field_max_y = BOUNDARY_SIZE + OVERSHOOT + GRID_OFFSET_Y

x_positions = []
pos = field_min_x
while pos <= field_max_x:
    x_positions.append(pos)
    pos += grid_spacing_x

y_positions = []
pos = field_min_y
while pos <= field_max_y:
    y_positions.append(pos)
    pos += grid_spacing_y

rot_rad = math.radians(GRID_ROTATION)
rotation_xform = rg.Transform.Rotation(rot_rad, rg.Vector3d.ZAxis, center_pt)

# Individual segments: each cell edge is one segment
segments = []  # (Line, "x" or "y")

for y_val in y_positions:
    for i in range(len(x_positions) - 1):
        pt_a = rg.Point3d(x_positions[i], y_val, 0)
        pt_b = rg.Point3d(x_positions[i + 1], y_val, 0)
        pt_a.Transform(rotation_xform)
        pt_b.Transform(rotation_xform)
        segments.append((rg.Line(pt_a, pt_b), "x"))

for x_val in x_positions:
    for j in range(len(y_positions) - 1):
        pt_a = rg.Point3d(x_val, y_positions[j], 0)
        pt_b = rg.Point3d(x_val, y_positions[j + 1], 0)
        pt_a.Transform(rotation_xform)
        pt_b.Transform(rotation_xform)
        segments.append((rg.Line(pt_a, pt_b), "y"))

info_messages.append("Grid: {} segments".format(len(segments)))

# ============================================================================
# SECTION 4: WALL SELECTION & BREP GENERATION
# ============================================================================

wall_rng = random.Random(seed)
height_rng = random.Random(wall_height_seed)

selected_walls = []  # (Line, direction, height)

for seg, direction in segments:
    prob = wall_probability_x if direction == "x" else wall_probability_y
    if wall_rng.random() < prob:
        h = rand_range(height_rng, wall_height_min, wall_height_max)
        selected_walls.append((seg, direction, h))

# Build wall Breps
wall_breps_pre_trim = []
wall_segment_data = []

for seg, direction, h in selected_walls:
    corners = perp_offset_pts(seg.From, seg.To, wall_thickness)
    if corners is None:
        continue
    c0, c1, c2, c3 = corners
    base_crv = rg.PolylineCurve([c0, c1, c2, c3, c0])
    brep = extrude_closed_crv(base_crv, h)
    if brep:
        wall_breps_pre_trim.append(brep)
        wall_segment_data.append((seg, direction, h))

full_field_walls = list(wall_breps_pre_trim)
info_messages.append("Walls: {} selected, {} built".format(
    len(selected_walls), len(wall_breps_pre_trim)))

# ============================================================================
# SECTION 5: ARC WALLS — SEMICIRCLES REPLACING STRAIGHT WALLS
# Randomly pick straight walls. Split each at its midpoint: the first half
# stays straight, the second half is replaced by a semicircle bulging
# outward with the same wall height and thickness.
# ============================================================================

arc_rng = random.Random(arc_seed)
arc_breps_pre_trim = []

if len(wall_breps_pre_trim) > 0 and int(num_arcs) > 0:
    # Pick which walls get converted (without replacement)
    arc_count = min(int(num_arcs), len(wall_breps_pre_trim))
    arc_indices = arc_rng.sample(range(len(wall_breps_pre_trim)), arc_count)

    walls_to_remove = set()

    for idx in arc_indices:
        seg, direction, h = wall_segment_data[idx]

        # Midpoint of the wall segment
        mid_pt = rg.Point3d(
            (seg.From.X + seg.To.X) / 2.0,
            (seg.From.Y + seg.To.Y) / 2.0, 0)

        # Wall direction and perpendicular
        dx = seg.To.X - seg.From.X
        dy = seg.To.Y - seg.From.Y
        seg_len = math.sqrt(dx * dx + dy * dy)
        if seg_len < 0.001:
            continue

        # Semicircle radius = half the segment length / 2
        # (the arc replaces the second half of the wall)
        half_len = seg_len / 2.0
        radius = half_len / 2.0
        if radius < 0.5:
            continue

        # Arc center is at 3/4 point of the segment
        arc_center = rg.Point3d(
            seg.From.X + 0.75 * dx,
            seg.From.Y + 0.75 * dy, 0)

        # Perpendicular direction for the bulge (pick one side randomly)
        perp_x = -dy / seg_len
        perp_y = dx / seg_len
        if arc_rng.random() < 0.5:
            perp_x, perp_y = -perp_x, -perp_y

        # Build the semicircle: arc from midpoint to endpoint, bulging outward
        arc_plane = rg.Plane(arc_center, rg.Vector3d.ZAxis)

        # Start point (midpoint of wall), end point (end of wall), interior point
        interior_pt = rg.Point3d(
            arc_center.X + perp_x * radius,
            arc_center.Y + perp_y * radius, 0)

        arc_obj = rg.Arc(mid_pt, interior_pt, seg.To)
        arc_radius = arc_obj.Radius

        # Build thick arc profile
        r_inner = max(0.1, arc_radius - wall_thickness / 2.0)
        r_outer = arc_radius + wall_thickness / 2.0
        arc_cen = arc_obj.Center

        # Rebuild inner/outer arcs using the same center and angles
        arc_plane2 = rg.Plane(arc_cen, rg.Vector3d.ZAxis)
        outer_arc = rg.Arc(arc_plane2, r_outer, arc_obj.AngleRadians)
        inner_arc = rg.Arc(arc_plane2, r_inner, arc_obj.AngleRadians)

        # Rotate to match the original arc's start angle
        start_angle = math.atan2(
            mid_pt.Y - arc_cen.Y,
            mid_pt.X - arc_cen.X)
        default_start = math.atan2(
            outer_arc.StartPoint.Y - arc_cen.Y,
            outer_arc.StartPoint.X - arc_cen.X)
        angle_diff = start_angle - default_start
        rot_xform = rg.Transform.Rotation(angle_diff, rg.Vector3d.ZAxis, arc_cen)

        outer_crv = outer_arc.ToNurbsCurve()
        inner_crv = inner_arc.ToNurbsCurve()
        outer_crv.Transform(rot_xform)
        inner_crv.Transform(rot_xform)
        inner_crv.Reverse()

        cap1 = rg.LineCurve(outer_crv.PointAtStart, inner_crv.PointAtEnd)
        cap2 = rg.LineCurve(inner_crv.PointAtStart, outer_crv.PointAtEnd)

        joined = rg.Curve.JoinCurves([outer_crv, cap2, inner_crv, cap1], 0.01)
        if joined and len(joined) > 0 and joined[0].IsClosed:
            arc_brep = extrude_closed_crv(joined[0], h)
            if arc_brep:
                arc_breps_pre_trim.append(arc_brep)
                walls_to_remove.add(idx)

                # Rebuild the first half as a shorter straight wall
                corners = perp_offset_pts(seg.From, mid_pt, wall_thickness)
                if corners:
                    c0, c1, c2, c3 = corners
                    half_crv = rg.PolylineCurve([c0, c1, c2, c3, c0])
                    half_brep = extrude_closed_crv(half_crv, h)
                    if half_brep:
                        wall_breps_pre_trim[idx] = half_brep
                        walls_to_remove.discard(idx)
        else:
            info_messages.append("Arc {} failed to close".format(idx))

    # Remove walls that were fully replaced
    if walls_to_remove:
        wall_breps_pre_trim = [b for i, b in enumerate(wall_breps_pre_trim)
                               if i not in walls_to_remove]
        wall_segment_data = [d for i, d in enumerate(wall_segment_data)
                             if i not in walls_to_remove]

info_messages.append("Arcs: {} semicircles built".format(len(arc_breps_pre_trim)))

# ============================================================================
# SECTION 6: DECK
# Floating platform — the horizontal datum between marsh and wall field.
# ============================================================================

deck_ext = BOUNDARY_SIZE + 2.0 * DECK_OVERSHOOT
deck_origin = rg.Point3d(center_x - deck_ext / 2.0,
                         center_y - deck_ext / 2.0, deck_height)
deck_top = rg.Point3d(center_x + deck_ext / 2.0,
                      center_y + deck_ext / 2.0,
                      deck_height + deck_thickness)
deck_brep = rg.Brep.CreateFromBox(rg.BoundingBox(deck_origin, deck_top))

info_messages.append("Deck: {:.1f}x{:.1f} at z={:.1f}".format(
    deck_ext, deck_ext, deck_height))

# ============================================================================
# SECTION 7: APERTURES — WALL CUTS ONLY
# Rectangular voids in walls for transparency and framed views.
# ============================================================================

aperture_rng = random.Random(aperture_seed)
cutting_volumes = []
aperture_depth = wall_thickness * 3.0

if len(wall_breps_pre_trim) > 0 and int(num_apertures) > 0:
    skip_booleans = len(wall_breps_pre_trim) > 50
    if skip_booleans:
        info_messages.append("Over 50 walls — skipping booleans for speed")

    wall_cutters = {}
    for _ in range(int(num_apertures)):
        w_idx = aperture_rng.randint(0, len(wall_breps_pre_trim) - 1)
        seg, direction, w_h = wall_segment_data[w_idx]

        t = rand_range(aperture_rng, 0.15, 0.85)
        pt_on_wall = rg.Point3d(
            seg.From.X + t * (seg.To.X - seg.From.X),
            seg.From.Y + t * (seg.To.Y - seg.From.Y), 0)

        z_base = rand_range(aperture_rng, 0, max(0.1, w_h - aperture_height))

        dx = seg.To.X - seg.From.X
        dy = seg.To.Y - seg.From.Y
        seg_len = math.sqrt(dx * dx + dy * dy)
        if seg_len < 0.001:
            continue
        wall_dir = rg.Vector3d(dx / seg_len, dy / seg_len, 0)
        wall_perp = rg.Vector3d(-wall_dir.Y, wall_dir.X, 0)

        cut_origin = rg.Point3d(
            pt_on_wall.X - wall_dir.X * aperture_width / 2.0
            - wall_perp.X * aperture_depth / 2.0,
            pt_on_wall.Y - wall_dir.Y * aperture_width / 2.0
            - wall_perp.Y * aperture_depth / 2.0,
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
                wall_cutters.setdefault(w_idx, []).append(cut_brep)

    if not skip_booleans:
        for w_idx, cutters in wall_cutters.items():
            wall_breps_pre_trim[w_idx] = safe_boolean_difference(
                wall_breps_pre_trim[w_idx], cutters, info_messages)

info_messages.append("Apertures: {} cuts".format(len(cutting_volumes)))

# ============================================================================
# SECTION 8: BOUNDARY TRIM & OUTPUT
# Always trim to boundary. Always show boundary curve.
# ============================================================================

# Boundary rectangle
boundary_rect = rg.Rectangle3d(
    rg.Plane(rg.Point3d(0, 0, 0), rg.Vector3d.ZAxis),
    rg.Interval(0, BOUNDARY_SIZE),
    rg.Interval(0, BOUNDARY_SIZE))
boundary_crv = boundary_rect.ToNurbsCurve()

# Trimming box
trim_box_brep = rg.Brep.CreateFromBox(rg.BoundingBox(
    rg.Point3d(0, 0, -1),
    rg.Point3d(BOUNDARY_SIZE, BOUNDARY_SIZE, wall_height_max + 2.0)))

# Trim walls
walls = []
for brep in wall_breps_pre_trim:
    trimmed = safe_boolean_intersection(brep, trim_box_brep, info_messages)
    if trimmed:
        walls.append(trimmed)

# Trim arcs
arcs = []
for brep in arc_breps_pre_trim:
    trimmed = safe_boolean_intersection(brep, trim_box_brep, info_messages)
    if trimmed:
        arcs.append(trimmed)

# Alias for output
deck = deck_brep

# Ground plane
gp_m = 3.0
ground_plane = rg.Brep.CreateFromCornerPoints(
    rg.Point3d(-gp_m, -gp_m, 0),
    rg.Point3d(BOUNDARY_SIZE + gp_m, -gp_m, 0),
    rg.Point3d(BOUNDARY_SIZE + gp_m, BOUNDARY_SIZE + gp_m, 0),
    rg.Point3d(-gp_m, BOUNDARY_SIZE + gp_m, 0), 0.001)

# Summary
info_messages.append("--- Pavilion Generator (Simple) ---")
info_messages.append("Boundary: 50' x 50'")
info_messages.append("Grid: {:.1f} x {:.1f} spacing, 15 deg rotation".format(
    grid_spacing_x, grid_spacing_y))
info_messages.append("Seeds: wall={}, height={}, arc={}, aperture={}".format(
    seed, wall_height_seed, arc_seed, aperture_seed))
info_messages.append("Final: {} walls, {} arcs".format(len(walls), len(arcs)))

info = "\n".join(info_messages)
