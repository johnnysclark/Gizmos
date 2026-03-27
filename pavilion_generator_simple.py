"""
Pavilion Generator (Simple) — GhPython Component for Rhino 8 / Grasshopper

Generates field-condition pavilions inspired by Stan Allen's field conditions
theory and Aldo van Eyck's 1966 Sonsbeek Pavilion. A 50'x50' open-air
pavilion on a marsh site.

Walls are generated from tangent lines between randomly placed circles,
creating a varied, non-orthogonal field of wall elements. Some circles
also produce semicircular arc walls. Apertures are random-sized boxes
that cut through all geometry (walls, arcs, and deck).

SETUP: Paste this entire script into a GhPython component in Grasshopper.
Right-click the component and add the inputs listed below (matching names
exactly). Connect Number Sliders to each. All inputs have defaults, so the
component runs immediately with zero connections.

Inputs (add these as GhPython component inputs — names must match exactly):

  CIRCLES (source geometry for tangent-line walls)
    num_circles             int     8       Number of circles scattered in the field
    circle_radius_min       float   2.0     Minimum circle radius (feet)
    circle_radius_max       float   8.0     Maximum circle radius (feet)
    circle_seed             int     42      Random seed for circle placement

  WALL SELECTION
    wall_probability        float   0.4     Chance each tangent line becomes a wall (0-1)
    seed                    int     42      Random seed for wall selection

  WALL GEOMETRY
    wall_thickness          float   0.5     Wall thickness (feet)
    wall_height_min         float   8.0     Minimum wall height (feet)
    wall_height_max         float   14.0    Maximum wall height (feet)
    wall_height_seed        int     7       Random seed for wall heights

  ARC WALLS (semicircular walls from the circles themselves)
    num_arcs                int     3       Number of circles that also produce arc walls
    arc_seed                int     99      Random seed for arc selection

  DECK
    deck_height             float   2.5     Deck elevation above ground (feet)
    deck_thickness          float   0.33    Deck slab thickness (feet)

  APERTURES (random-sized box cuts through ALL geometry)
    num_apertures           int     12      Total number of aperture cuts
    aperture_seed           int     55      Random seed for aperture placement

Outputs (add these as GhPython component outputs — names must match exactly):
    walls           - list of Brep: trimmed wall solids inside boundary
    arcs            - list of Brep: trimmed arc wall solids
    deck            - Brep: the floating deck platform
    boundary_crv    - Curve: the 50'x50' boundary rectangle
    cutting_volumes - list of Brep: aperture cutting boxes (for review)
    ground_plane    - Brep: flat ground surface
    full_field_walls- list of Brep: all walls before boundary trim
    circles_crv     - list of Curve: the source circles (for reference)
    info            - str: summary text
"""

import Rhino.Geometry as rg
import math
import random

# ============================================================================
# SECTION 1: INPUT DEFAULTS
# ============================================================================

if num_circles is None: num_circles = 8
if circle_radius_min is None: circle_radius_min = 2.0
if circle_radius_max is None: circle_radius_max = 8.0
if circle_seed is None: circle_seed = 42

if wall_probability is None: wall_probability = 0.4
if seed is None: seed = 42

if wall_thickness is None: wall_thickness = 0.5
if wall_height_min is None: wall_height_min = 8.0
if wall_height_max is None: wall_height_max = 14.0
if wall_height_seed is None: wall_height_seed = 7

if num_arcs is None: num_arcs = 3
if arc_seed is None: arc_seed = 99

if deck_height is None: deck_height = 2.5
if deck_thickness is None: deck_thickness = 0.33

if num_apertures is None: num_apertures = 12
if aperture_seed is None: aperture_seed = 55

# --- Hardcoded constants ---
BOUNDARY = 50.0
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
    """4 corner points offset perpendicular to a line segment."""
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


def external_tangent_lines(c1_x, c1_y, c1_r, c2_x, c2_y, c2_r):
    """Compute external tangent line segments between two circles.
    Returns a list of (Point3d, Point3d) tuples — 0, 1, or 2 tangent lines.
    External tangents touch both circles on the same side."""
    dx = c2_x - c1_x
    dy = c2_y - c1_y
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 0.001:
        return []
    r_diff = abs(c1_r - c2_r)
    if dist <= r_diff:
        return []

    angle = math.atan2(dy, dx)
    cos_val = (c1_r - c2_r) / dist
    cos_val = max(-1.0, min(1.0, cos_val))
    alpha = math.acos(cos_val)

    tangents = []
    for sign in [1, -1]:
        # Normal direction to tangent line
        a = angle + sign * alpha
        # Tangent points: both circles offset in the same normal direction
        t1_x = c1_x + c1_r * math.cos(a)
        t1_y = c1_y + c1_r * math.sin(a)
        t2_x = c2_x + c2_r * math.cos(a)
        t2_y = c2_y + c2_r * math.sin(a)
        tangents.append((rg.Point3d(t1_x, t1_y, 0), rg.Point3d(t2_x, t2_y, 0)))

    return tangents


def internal_tangent_lines(c1_x, c1_y, c1_r, c2_x, c2_y, c2_r):
    """Compute internal (cross) tangent line segments between two circles.
    Returns a list of (Point3d, Point3d) tuples — 0, 1, or 2 tangent lines.
    Internal tangents cross between the circles."""
    dx = c2_x - c1_x
    dy = c2_y - c1_y
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 0.001:
        return []
    r_sum = c1_r + c2_r
    if dist <= r_sum:
        return []

    angle = math.atan2(dy, dx)
    cos_val = (c1_r + c2_r) / dist
    cos_val = max(-1.0, min(1.0, cos_val))
    alpha = math.acos(cos_val)

    tangents = []
    for sign in [1, -1]:
        # Normal direction to tangent line
        a = angle + sign * alpha
        # Circle 1: offset in normal direction
        t1_x = c1_x + c1_r * math.cos(a)
        t1_y = c1_y + c1_r * math.sin(a)
        # Circle 2: offset in OPPOSITE direction (internal tangent)
        t2_x = c2_x - c2_r * math.cos(a)
        t2_y = c2_y - c2_r * math.sin(a)
        tangents.append((rg.Point3d(t1_x, t1_y, 0), rg.Point3d(t2_x, t2_y, 0)))

    return tangents


# ============================================================================
# SECTION 3: CIRCLE GENERATION
# Scatter circles across the field (extending beyond boundary). These are
# the source geometry — tangent lines between them become walls.
# ============================================================================

center_x = BOUNDARY / 2.0
center_y = BOUNDARY / 2.0

circ_rng = random.Random(circle_seed)

circle_data = []   # (cx, cy, radius)
circles_crv = []   # output: NurbsCurve list for visualization

for _ in range(int(num_circles)):
    cx = rand_range(circ_rng, -OVERSHOOT * 0.5, BOUNDARY + OVERSHOOT * 0.5)
    cy = rand_range(circ_rng, -OVERSHOOT * 0.5, BOUNDARY + OVERSHOOT * 0.5)
    r = rand_range(circ_rng, circle_radius_min, circle_radius_max)
    circle_data.append((cx, cy, r))
    circ = rg.Circle(rg.Plane(rg.Point3d(cx, cy, 0), rg.Vector3d.ZAxis), r)
    circles_crv.append(circ.ToNurbsCurve())

info_messages.append("Circles: {} placed".format(len(circle_data)))

# ============================================================================
# SECTION 4: TANGENT LINE WALL GENERATION
# For each pair of circles, compute external and internal tangent lines.
# Probabilistically select tangent lines as walls with random heights.
# ============================================================================

wall_rng = random.Random(seed)
height_rng = random.Random(wall_height_seed)

all_tangent_segs = []  # (pt_a, pt_b) for all tangent lines

for i in range(len(circle_data)):
    for j in range(i + 1, len(circle_data)):
        c1 = circle_data[i]
        c2 = circle_data[j]
        # External tangents
        ext = external_tangent_lines(c1[0], c1[1], c1[2],
                                     c2[0], c2[1], c2[2])
        all_tangent_segs.extend(ext)
        # Internal tangents
        intn = internal_tangent_lines(c1[0], c1[1], c1[2],
                                      c2[0], c2[1], c2[2])
        all_tangent_segs.extend(intn)

info_messages.append("Tangent lines found: {}".format(len(all_tangent_segs)))

# Select walls and build Breps
wall_breps_pre_trim = []
wall_segment_data = []  # (pt_a, pt_b, height) for aperture placement

for pt_a, pt_b in all_tangent_segs:
    if wall_rng.random() >= wall_probability:
        continue
    h = rand_range(height_rng, wall_height_min, wall_height_max)
    corners = perp_offset_pts(pt_a, pt_b, wall_thickness)
    if corners is None:
        continue
    c0, c1, c2, c3 = corners
    base_crv = rg.PolylineCurve([c0, c1, c2, c3, c0])
    brep = extrude_closed_crv(base_crv, h)
    if brep:
        wall_breps_pre_trim.append(brep)
        wall_segment_data.append((pt_a, pt_b, h))

full_field_walls = list(wall_breps_pre_trim)
info_messages.append("Walls: {} built from tangent lines".format(
    len(wall_breps_pre_trim)))

# ============================================================================
# SECTION 5: ARC WALLS — SEMICIRCLES FROM SOURCE CIRCLES
# Pick some of the source circles and extrude semicircular thick walls
# from them, using the circle's own radius and a random height.
# ============================================================================

arc_rng = random.Random(arc_seed)
arc_breps_pre_trim = []

if len(circle_data) > 0 and int(num_arcs) > 0:
    arc_count = min(int(num_arcs), len(circle_data))
    arc_indices = arc_rng.sample(range(len(circle_data)), arc_count)

    for idx in arc_indices:
        cx, cy, r = circle_data[idx]
        arc_h = rand_range(arc_rng, wall_height_min, wall_height_max)

        # Random start angle for the semicircle
        start_rad = rand_range(arc_rng, 0, 2 * math.pi)

        r_inner = max(0.1, r - wall_thickness / 2.0)
        r_outer = r + wall_thickness / 2.0

        c_pt = rg.Point3d(cx, cy, 0)
        arc_plane = rg.Plane(c_pt, rg.Vector3d.ZAxis)

        # Build outer and inner semicircular arcs (pi radians = 180 degrees)
        outer_arc = rg.Arc(arc_plane, r_outer, math.pi)
        inner_arc = rg.Arc(arc_plane, r_inner, math.pi)

        rot_xform = rg.Transform.Rotation(start_rad, rg.Vector3d.ZAxis, c_pt)

        outer_crv = outer_arc.ToNurbsCurve()
        inner_crv = inner_arc.ToNurbsCurve()
        outer_crv.Transform(rot_xform)
        inner_crv.Transform(rot_xform)
        inner_crv.Reverse()

        cap1 = rg.LineCurve(outer_crv.PointAtStart, inner_crv.PointAtEnd)
        cap2 = rg.LineCurve(inner_crv.PointAtStart, outer_crv.PointAtEnd)

        joined = rg.Curve.JoinCurves([outer_crv, cap2, inner_crv, cap1], 0.01)
        if joined and len(joined) > 0 and joined[0].IsClosed:
            arc_brep = extrude_closed_crv(joined[0], arc_h)
            if arc_brep:
                arc_breps_pre_trim.append(arc_brep)
        else:
            info_messages.append("Arc from circle {} failed to close".format(idx))

info_messages.append("Arcs: {} semicircles built".format(len(arc_breps_pre_trim)))

# ============================================================================
# SECTION 6: DECK
# Floating platform — the horizontal datum between marsh and wall field.
# ============================================================================

deck_ext = BOUNDARY + 2.0 * DECK_OVERSHOOT
deck_origin = rg.Point3d(center_x - deck_ext / 2.0,
                         center_y - deck_ext / 2.0, deck_height)
deck_top = rg.Point3d(center_x + deck_ext / 2.0,
                      center_y + deck_ext / 2.0,
                      deck_height + deck_thickness)
deck_brep = rg.Brep.CreateFromBox(rg.BoundingBox(deck_origin, deck_top))

info_messages.append("Deck: {:.1f}x{:.1f} at z={:.1f}".format(
    deck_ext, deck_ext, deck_height))

# ============================================================================
# SECTION 7: APERTURES — RANDOM-SIZED BOXES CUTTING THROUGH ALL GEOMETRY
# Each aperture is a randomly sized and placed box. They boolean-difference
# through walls, arcs, AND the deck.
# ============================================================================

ap_rng = random.Random(aperture_seed)
cutting_volumes = []

# Generate random cutting boxes scattered within the boundary
for _ in range(int(num_apertures)):
    # Random position within the boundary
    ax = rand_range(ap_rng, 2, BOUNDARY - 2)
    ay = rand_range(ap_rng, 2, BOUNDARY - 2)

    # Random size for each aperture
    ap_w = rand_range(ap_rng, 0.8, 3.0)    # width along X
    ap_d = rand_range(ap_rng, 0.8, 3.0)    # depth along Y
    ap_h = rand_range(ap_rng, 1.5, 6.0)    # height
    az = rand_range(ap_rng, 0, wall_height_max - ap_h)  # base Z

    # Random rotation so cuts aren't all axis-aligned
    ap_angle = rand_range(ap_rng, 0, math.pi)
    ap_center = rg.Point3d(ax, ay, az)
    ap_plane = rg.Plane(ap_center, rg.Vector3d.ZAxis)
    ap_rot = rg.Transform.Rotation(ap_angle, rg.Vector3d.ZAxis, ap_center)
    ap_plane.Transform(ap_rot)

    cut_box = rg.Box(ap_plane,
                     rg.Interval(-ap_w / 2.0, ap_w / 2.0),
                     rg.Interval(-ap_d / 2.0, ap_d / 2.0),
                     rg.Interval(0, ap_h))
    cut_brep = cut_box.ToBrep()
    if cut_brep:
        cutting_volumes.append(cut_brep)

info_messages.append("Apertures: {} random cutting boxes".format(
    len(cutting_volumes)))

# Apply boolean difference to all walls
if cutting_volumes:
    skip_booleans = (len(wall_breps_pre_trim) + len(arc_breps_pre_trim)) > 60
    if skip_booleans:
        info_messages.append("Over 60 elements — skipping booleans for speed")
    else:
        for i in range(len(wall_breps_pre_trim)):
            wall_breps_pre_trim[i] = safe_boolean_difference(
                wall_breps_pre_trim[i], cutting_volumes, info_messages)

        for i in range(len(arc_breps_pre_trim)):
            arc_breps_pre_trim[i] = safe_boolean_difference(
                arc_breps_pre_trim[i], cutting_volumes, info_messages)

        if deck_brep:
            deck_brep = safe_boolean_difference(
                deck_brep, cutting_volumes, info_messages)

# ============================================================================
# SECTION 8: BOUNDARY TRIM & OUTPUT
# Always trim to boundary. Always show boundary curve.
# ============================================================================

boundary_rect = rg.Rectangle3d(
    rg.Plane(rg.Point3d(0, 0, 0), rg.Vector3d.ZAxis),
    rg.Interval(0, BOUNDARY),
    rg.Interval(0, BOUNDARY))
boundary_crv = boundary_rect.ToNurbsCurve()

trim_box_brep = rg.Brep.CreateFromBox(rg.BoundingBox(
    rg.Point3d(0, 0, -1),
    rg.Point3d(BOUNDARY, BOUNDARY, wall_height_max + 2.0)))

walls = []
for brep in wall_breps_pre_trim:
    trimmed = safe_boolean_intersection(brep, trim_box_brep, info_messages)
    if trimmed:
        walls.append(trimmed)

arcs = []
for brep in arc_breps_pre_trim:
    trimmed = safe_boolean_intersection(brep, trim_box_brep, info_messages)
    if trimmed:
        arcs.append(trimmed)

deck = deck_brep

gp_m = 3.0
ground_plane = rg.Brep.CreateFromCornerPoints(
    rg.Point3d(-gp_m, -gp_m, 0),
    rg.Point3d(BOUNDARY + gp_m, -gp_m, 0),
    rg.Point3d(BOUNDARY + gp_m, BOUNDARY + gp_m, 0),
    rg.Point3d(-gp_m, BOUNDARY + gp_m, 0), 0.001)

# Summary
info_messages.append("--- Pavilion Generator (Simple) ---")
info_messages.append("Boundary: 50' x 50'")
info_messages.append("Circles: {}, tangent lines: {}".format(
    len(circle_data), len(all_tangent_segs)))
info_messages.append("Final: {} walls, {} arcs".format(len(walls), len(arcs)))
info_messages.append("Seeds: circle={}, wall={}, height={}, arc={}, aperture={}".format(
    circle_seed, seed, wall_height_seed, arc_seed, aperture_seed))

info = "\n".join(info_messages)
