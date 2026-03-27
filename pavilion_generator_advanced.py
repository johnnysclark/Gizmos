"""
Pavilion Generator (Advanced) — GhPython Component for Rhino 8 / Grasshopper

Field-condition pavilion generator inspired by Stan Allen's field conditions
and Aldo van Eyck's 1966 Sonsbeek Pavilion. 50'x50' open-air pavilion on a
marsh site. Walls from tangent lines between scattered circles, arc walls
with variable sweep, cylinder oculi in the deck, rectangular wall apertures.

Every seed is independent — change one without cascading. Defaults produce
a compelling result with zero connections.

SETUP: Paste into a GhPython component. Right-click to add inputs below.

Inputs (names must match exactly):

  CIRCLES (source geometry for tangent-line walls)
    num_circles             int     8       Circles scattered across the field
    circle_radius_min       float   2.0     Min circle radius (ft)
    circle_radius_max       float   8.0     Max circle radius (ft)
    circle_seed             int     42      Seed for circle positions and sizes
    circle_cluster          float   0.3     0=uniform scatter, 1=clustered at center

  WALL SELECTION
    seed                    int     42      Seed for which tangent lines become walls
    wall_probability        float   0.4     Chance a tangent line becomes a wall (0-1)
    tangent_mode            int     0       0=external+internal, 1=external only, 2=internal only
    wall_length_min         float   3.0     Skip tangent lines shorter than this (ft)
    wall_length_max         float   35.0    Skip tangent lines longer than this (ft)

  WALL GEOMETRY
    wall_thickness          float   0.5     Wall thickness (ft)
    wall_height_min         float   8.0     Min wall height (ft)
    wall_height_max         float   14.0    Max wall height (ft)
    wall_height_seed        int     7       Seed for wall height assignment
    height_from_center      float   0.0     Height gradient: >0 taller at center, <0 taller at edges (-1 to 1)

  ARC WALLS (curved walls from source circles)
    num_arcs                int     4       Circles that also produce arc walls
    arc_seed                int     99      Seed for arc selection and sweep
    arc_sweep_min           float   90.0    Min arc sweep angle (degrees)
    arc_sweep_max           float   270.0   Max arc sweep angle (degrees)
    arc_height_min          float   8.0     Min arc wall height (ft)
    arc_height_max          float   14.0    Max arc wall height (ft)

  DECK
    deck_height             float   2.5     Deck elevation above ground (ft)
    deck_thickness          float   0.33    Deck slab thickness (ft)

  DECK OCULI (cylinder holes punched through the deck for light and planting)
    num_oculi               int     6       Number of circular deck penetrations
    oculus_radius_min       float   1.0     Min oculus radius (ft)
    oculus_radius_max       float   3.0     Max oculus radius (ft)
    oculus_seed             int     77      Seed for oculus placement

  WALL APERTURES (rectangular cuts in walls only)
    num_wall_apertures      int     10      Number of rectangular wall cuts
    wall_aperture_seed      int     55      Seed for aperture placement
    wall_ap_width_min       float   1.0     Min aperture width (ft)
    wall_ap_width_max       float   3.0     Max aperture width (ft)
    wall_ap_height_min      float   2.0     Min aperture height (ft)
    wall_ap_height_max      float   5.0     Max aperture height (ft)

Outputs (names must match exactly):
    walls           - list[Brep]: trimmed wall solids
    arcs            - list[Brep]: trimmed arc wall solids
    deck            - Brep: deck with oculi cut out
    boundary_crv    - Curve: 50'x50' boundary rectangle
    wall_cuts       - list[Brep]: rectangular wall cutting volumes
    deck_cuts       - list[Brep]: cylinder oculus cutting volumes
    ground_plane    - Brep: ground surface
    full_field_walls- list[Brep]: all walls before boundary trim
    circles_crv     - list[Curve]: source circles
    info            - str: summary
"""

import Rhino.Geometry as rg
import math
import random

# ============================================================================
# SECTION 1: INPUT DEFAULTS
# ============================================================================

# Circles
if num_circles is None: num_circles = 8
if circle_radius_min is None: circle_radius_min = 2.0
if circle_radius_max is None: circle_radius_max = 8.0
if circle_seed is None: circle_seed = 42
if circle_cluster is None: circle_cluster = 0.3

# Wall selection
if seed is None: seed = 42
if wall_probability is None: wall_probability = 0.4
if tangent_mode is None: tangent_mode = 0
if wall_length_min is None: wall_length_min = 3.0
if wall_length_max is None: wall_length_max = 35.0

# Wall geometry
if wall_thickness is None: wall_thickness = 0.5
if wall_height_min is None: wall_height_min = 8.0
if wall_height_max is None: wall_height_max = 14.0
if wall_height_seed is None: wall_height_seed = 7
if height_from_center is None: height_from_center = 0.0

# Arc walls
if num_arcs is None: num_arcs = 4
if arc_seed is None: arc_seed = 99
if arc_sweep_min is None: arc_sweep_min = 90.0
if arc_sweep_max is None: arc_sweep_max = 270.0
if arc_height_min is None: arc_height_min = 8.0
if arc_height_max is None: arc_height_max = 14.0

# Deck
if deck_height is None: deck_height = 2.5
if deck_thickness is None: deck_thickness = 0.33

# Deck oculi
if num_oculi is None: num_oculi = 6
if oculus_radius_min is None: oculus_radius_min = 1.0
if oculus_radius_max is None: oculus_radius_max = 3.0
if oculus_seed is None: oculus_seed = 77

# Wall apertures
if num_wall_apertures is None: num_wall_apertures = 10
if wall_aperture_seed is None: wall_aperture_seed = 55
if wall_ap_width_min is None: wall_ap_width_min = 1.0
if wall_ap_width_max is None: wall_ap_width_max = 3.0
if wall_ap_height_min is None: wall_ap_height_min = 2.0
if wall_ap_height_max is None: wall_ap_height_max = 5.0

# Constants
BOUNDARY = 50.0
OVERSHOOT = 8.0
DECK_OVERSHOOT = 1.0

# ============================================================================
# SECTION 2: HELPERS
# ============================================================================

info_messages = []


def rr(rng, lo, hi):
    """Uniform random in [lo, hi]."""
    return lo + rng.random() * (hi - lo)


def extrude_closed(crv, height):
    """Extrude closed planar curve upward, cap both ends."""
    if crv is None or not crv.IsClosed:
        return None
    ex = rg.Extrusion.Create(crv, height, True)
    return ex.ToBrep() if ex else None


def bool_diff(brep, cutters, info_list):
    """Boolean difference with graceful fallback."""
    if not cutters:
        return brep
    try:
        res = rg.Brep.CreateBooleanDifference(brep, cutters, 0.001)
        if res and len(res) > 0:
            return res[0]
        info_list.append("bool diff empty — kept original")
        return brep
    except Exception as e:
        info_list.append("bool diff failed: {} — kept original".format(e))
        return brep


def bool_isect(brep, cutter, info_list):
    """Boolean intersection with graceful fallback."""
    try:
        res = rg.Brep.CreateBooleanIntersection(brep, cutter, 0.001)
        if res and len(res) > 0:
            return res[0]
        info_list.append("bool isect empty — kept original")
        return brep
    except Exception as e:
        info_list.append("bool isect failed: {} — kept original".format(e))
        return brep


def perp_pts(pa, pb, t):
    """4 corners offset perpendicular to segment pa-pb by ±t/2."""
    dx = pb.X - pa.X
    dy = pb.Y - pa.Y
    ln = math.sqrt(dx * dx + dy * dy)
    if ln < 1e-4:
        return None
    nx = -dy / ln * (t / 2.0)
    ny = dx / ln * (t / 2.0)
    return (
        rg.Point3d(pa.X + nx, pa.Y + ny, 0),
        rg.Point3d(pb.X + nx, pb.Y + ny, 0),
        rg.Point3d(pb.X - nx, pb.Y - ny, 0),
        rg.Point3d(pa.X - nx, pa.Y - ny, 0),
    )


def seg_length(pa, pb):
    dx = pb.X - pa.X
    dy = pb.Y - pa.Y
    return math.sqrt(dx * dx + dy * dy)


def ext_tangents(x1, y1, r1, x2, y2, r2):
    """External tangent lines between two circles. Returns [(pt,pt),...]."""
    dx = x2 - x1
    dy = y2 - y1
    d = math.sqrt(dx * dx + dy * dy)
    if d < 0.001 or d <= abs(r1 - r2):
        return []
    ang = math.atan2(dy, dx)
    cv = max(-1.0, min(1.0, (r1 - r2) / d))
    alpha = math.acos(cv)
    out = []
    for s in (1, -1):
        a = ang + s * alpha
        out.append((
            rg.Point3d(x1 + r1 * math.cos(a), y1 + r1 * math.sin(a), 0),
            rg.Point3d(x2 + r2 * math.cos(a), y2 + r2 * math.sin(a), 0)))
    return out


def int_tangents(x1, y1, r1, x2, y2, r2):
    """Internal tangent lines between two circles. Returns [(pt,pt),...]."""
    dx = x2 - x1
    dy = y2 - y1
    d = math.sqrt(dx * dx + dy * dy)
    if d < 0.001 or d <= r1 + r2:
        return []
    ang = math.atan2(dy, dx)
    cv = max(-1.0, min(1.0, (r1 + r2) / d))
    alpha = math.acos(cv)
    out = []
    for s in (1, -1):
        a = ang + s * alpha
        out.append((
            rg.Point3d(x1 + r1 * math.cos(a), y1 + r1 * math.sin(a), 0),
            rg.Point3d(x2 - r2 * math.cos(a), y2 - r2 * math.sin(a), 0)))
    return out


# ============================================================================
# SECTION 3: CIRCLE FIELD
# Scatter circles. circle_cluster biases placement toward field center.
# ============================================================================

cx_field = BOUNDARY / 2.0
cy_field = BOUNDARY / 2.0
field_half = BOUNDARY / 2.0 + OVERSHOOT * 0.5

crng = random.Random(circle_seed)
circle_data = []
circles_crv = []

for _ in range(int(num_circles)):
    # Blend between uniform and gaussian-centered placement
    if crng.random() < circle_cluster:
        # Clustered: gaussian around center, clipped to field
        cx = crng.gauss(cx_field, BOUNDARY * 0.2)
        cy = crng.gauss(cy_field, BOUNDARY * 0.2)
        cx = max(-OVERSHOOT * 0.5, min(BOUNDARY + OVERSHOOT * 0.5, cx))
        cy = max(-OVERSHOOT * 0.5, min(BOUNDARY + OVERSHOOT * 0.5, cy))
    else:
        cx = rr(crng, -OVERSHOOT * 0.5, BOUNDARY + OVERSHOOT * 0.5)
        cy = rr(crng, -OVERSHOOT * 0.5, BOUNDARY + OVERSHOOT * 0.5)
    r = rr(crng, circle_radius_min, circle_radius_max)
    circle_data.append((cx, cy, r))
    circ = rg.Circle(rg.Plane(rg.Point3d(cx, cy, 0), rg.Vector3d.ZAxis), r)
    circles_crv.append(circ.ToNurbsCurve())

info_messages.append("{} circles placed".format(len(circle_data)))

# ============================================================================
# SECTION 4: TANGENT LINE WALLS
# Compute tangent lines between circle pairs. Filter by length.
# Probabilistically select. Extrude with height gradient from center.
# ============================================================================

wrng = random.Random(seed)
hrng = random.Random(wall_height_seed)

raw_tangents = []
for i in range(len(circle_data)):
    for j in range(i + 1, len(circle_data)):
        c1, c2 = circle_data[i], circle_data[j]
        if tangent_mode != 2:  # external
            raw_tangents.extend(ext_tangents(c1[0], c1[1], c1[2],
                                            c2[0], c2[1], c2[2]))
        if tangent_mode != 1:  # internal
            raw_tangents.extend(int_tangents(c1[0], c1[1], c1[2],
                                            c2[0], c2[1], c2[2]))

# Filter by length
tangents = []
for pa, pb in raw_tangents:
    ln = seg_length(pa, pb)
    if wall_length_min <= ln <= wall_length_max:
        tangents.append((pa, pb))

info_messages.append("{} tangent lines ({} after length filter)".format(
    len(raw_tangents), len(tangents)))

# Height gradient helper: distance from field center → height multiplier
max_dist = math.sqrt(2) * field_half
hfc = max(-1.0, min(1.0, height_from_center))


def height_for_point(mx, my, rng):
    """Random height modulated by distance from center."""
    base_h = rr(rng, wall_height_min, wall_height_max)
    if abs(hfc) < 0.01:
        return base_h
    dx = mx - cx_field
    dy = my - cy_field
    dist = math.sqrt(dx * dx + dy * dy)
    t = dist / max_dist  # 0 at center, ~1 at corners
    # hfc > 0: taller at center (multiply by 1+hfc at center, 1-hfc at edge)
    # hfc < 0: taller at edges
    mult = 1.0 + hfc * (1.0 - 2.0 * t)
    mult = max(0.3, min(1.7, mult))
    return max(wall_height_min, min(wall_height_max, base_h * mult))


# Select and build walls
wall_breps = []
wall_data = []  # (pa, pb, h) for aperture targeting

for pa, pb in tangents:
    if wrng.random() >= wall_probability:
        continue
    mx = (pa.X + pb.X) / 2.0
    my = (pa.Y + pb.Y) / 2.0
    h = height_for_point(mx, my, hrng)
    corners = perp_pts(pa, pb, wall_thickness)
    if corners is None:
        continue
    c0, c1, c2, c3 = corners
    crv = rg.PolylineCurve([c0, c1, c2, c3, c0])
    brep = extrude_closed(crv, h)
    if brep:
        wall_breps.append(brep)
        wall_data.append((pa, pb, h))

full_field_walls = list(wall_breps)
info_messages.append("{} walls built".format(len(wall_breps)))

# ============================================================================
# SECTION 5: ARC WALLS
# Variable sweep angles from source circles. Not just semicircles —
# quarter arcs, three-quarter arcs, anything between sweep_min and max.
# ============================================================================

arng = random.Random(arc_seed)
arc_breps = []

if len(circle_data) > 0 and int(num_arcs) > 0:
    n_arcs = min(int(num_arcs), len(circle_data))
    arc_idx = arng.sample(range(len(circle_data)), n_arcs)

    for idx in arc_idx:
        cx, cy, r = circle_data[idx]
        arc_h = rr(arng, arc_height_min, arc_height_max)
        sweep = math.radians(rr(arng, arc_sweep_min, arc_sweep_max))
        start = rr(arng, 0, 2 * math.pi)

        ri = max(0.1, r - wall_thickness / 2.0)
        ro = r + wall_thickness / 2.0
        cpt = rg.Point3d(cx, cy, 0)
        pl = rg.Plane(cpt, rg.Vector3d.ZAxis)

        o_arc = rg.Arc(pl, ro, sweep)
        i_arc = rg.Arc(pl, ri, sweep)
        rot = rg.Transform.Rotation(start, rg.Vector3d.ZAxis, cpt)

        o_crv = o_arc.ToNurbsCurve()
        i_crv = i_arc.ToNurbsCurve()
        o_crv.Transform(rot)
        i_crv.Transform(rot)
        i_crv.Reverse()

        cap1 = rg.LineCurve(o_crv.PointAtStart, i_crv.PointAtEnd)
        cap2 = rg.LineCurve(i_crv.PointAtStart, o_crv.PointAtEnd)

        joined = rg.Curve.JoinCurves([o_crv, cap2, i_crv, cap1], 0.01)
        if joined and len(joined) > 0 and joined[0].IsClosed:
            brep = extrude_closed(joined[0], arc_h)
            if brep:
                arc_breps.append(brep)

info_messages.append("{} arc walls built".format(len(arc_breps)))

# ============================================================================
# SECTION 6: DECK
# ============================================================================

deck_ext = BOUNDARY + 2.0 * DECK_OVERSHOOT
d_origin = rg.Point3d(cx_field - deck_ext / 2.0,
                      cy_field - deck_ext / 2.0, deck_height)
d_top = rg.Point3d(cx_field + deck_ext / 2.0,
                   cy_field + deck_ext / 2.0,
                   deck_height + deck_thickness)
deck_brep = rg.Brep.CreateFromBox(rg.BoundingBox(d_origin, d_top))

# ============================================================================
# SECTION 7A: DECK OCULI — CYLINDER HOLES
# Vertical cylinders punched through the deck. On a marsh site these
# become light wells, rain collectors, and planting pockets — the ground
# pushes up through the horizontal datum.
# ============================================================================

oc_rng = random.Random(oculus_seed)
deck_cuts = []

for _ in range(int(num_oculi)):
    ox = rr(oc_rng, 3, BOUNDARY - 3)
    oy = rr(oc_rng, 3, BOUNDARY - 3)
    orad = rr(oc_rng, oculus_radius_min, oculus_radius_max)

    # Cylinder: circle at deck bottom, extruded through deck + margin
    oc_plane = rg.Plane(rg.Point3d(ox, oy, deck_height - 0.5), rg.Vector3d.ZAxis)
    oc_circle = rg.Circle(oc_plane, orad)
    oc_crv = oc_circle.ToNurbsCurve()
    cyl_h = deck_thickness + 1.0  # penetrate fully
    cyl_brep = extrude_closed(oc_crv, cyl_h)
    if cyl_brep:
        deck_cuts.append(cyl_brep)

if deck_cuts and deck_brep:
    deck_brep = bool_diff(deck_brep, deck_cuts, info_messages)

info_messages.append("{} deck oculi cut".format(len(deck_cuts)))

# ============================================================================
# SECTION 7B: WALL APERTURES — RECTANGULAR CUTS
# Randomly sized rectangular voids cut into walls. Each aperture targets
# a specific wall, positioned along its length at a random height.
# Separate system from deck oculi — walls get boxes, deck gets cylinders.
# ============================================================================

ap_rng = random.Random(wall_aperture_seed)
wall_cuts = []

if len(wall_breps) > 0 and int(num_wall_apertures) > 0:
    skip = len(wall_breps) > 50
    if skip:
        info_messages.append(">50 walls — outputting cut volumes only")

    ap_depth = wall_thickness * 3.0  # ensure full penetration
    cutters_by_wall = {}

    for _ in range(int(num_wall_apertures)):
        wi = ap_rng.randint(0, len(wall_breps) - 1)
        pa, pb, wh = wall_data[wi]

        # Random size within user ranges
        ap_w = rr(ap_rng, wall_ap_width_min, wall_ap_width_max)
        ap_h = rr(ap_rng, wall_ap_height_min, wall_ap_height_max)

        # Position along wall length and height
        t = rr(ap_rng, 0.1, 0.9)
        pt = rg.Point3d(
            pa.X + t * (pb.X - pa.X),
            pa.Y + t * (pb.Y - pa.Y), 0)
        z0 = rr(ap_rng, 0, max(0.1, wh - ap_h))

        # Orient cutting box to wall direction
        dx = pb.X - pa.X
        dy = pb.Y - pa.Y
        sl = math.sqrt(dx * dx + dy * dy)
        if sl < 0.001:
            continue
        wdir = rg.Vector3d(dx / sl, dy / sl, 0)
        wperp = rg.Vector3d(-wdir.Y, wdir.X, 0)

        co = rg.Point3d(
            pt.X - wdir.X * ap_w / 2.0 - wperp.X * ap_depth / 2.0,
            pt.Y - wdir.Y * ap_w / 2.0 - wperp.Y * ap_depth / 2.0,
            z0)
        cp = rg.Plane(co, wdir, wperp)
        cb = rg.Box(cp,
                    rg.Interval(0, ap_w),
                    rg.Interval(0, ap_depth),
                    rg.Interval(0, ap_h))
        cbrep = cb.ToBrep()
        if cbrep:
            wall_cuts.append(cbrep)
            if not skip:
                cutters_by_wall.setdefault(wi, []).append(cbrep)

    if not skip:
        for wi, cutters in cutters_by_wall.items():
            wall_breps[wi] = bool_diff(wall_breps[wi], cutters, info_messages)

info_messages.append("{} wall apertures cut".format(len(wall_cuts)))

# ============================================================================
# SECTION 8: BOUNDARY TRIM & OUTPUT
# ============================================================================

boundary_rect = rg.Rectangle3d(
    rg.Plane(rg.Point3d(0, 0, 0), rg.Vector3d.ZAxis),
    rg.Interval(0, BOUNDARY),
    rg.Interval(0, BOUNDARY))
boundary_crv = boundary_rect.ToNurbsCurve()

trim_brep = rg.Brep.CreateFromBox(rg.BoundingBox(
    rg.Point3d(0, 0, -1),
    rg.Point3d(BOUNDARY, BOUNDARY, wall_height_max + 2.0)))

walls = []
for b in wall_breps:
    tr = bool_isect(b, trim_brep, info_messages)
    if tr:
        walls.append(tr)

arcs = []
for b in arc_breps:
    tr = bool_isect(b, trim_brep, info_messages)
    if tr:
        arcs.append(tr)

deck = deck_brep

gm = 3.0
ground_plane = rg.Brep.CreateFromCornerPoints(
    rg.Point3d(-gm, -gm, 0),
    rg.Point3d(BOUNDARY + gm, -gm, 0),
    rg.Point3d(BOUNDARY + gm, BOUNDARY + gm, 0),
    rg.Point3d(-gm, BOUNDARY + gm, 0), 0.001)

# Summary
info_messages.append("--- Pavilion Generator (Advanced) ---")
info_messages.append("50' x 50' boundary")
info_messages.append("{} circles, {} tangents, {} walls, {} arcs".format(
    len(circle_data), len(tangents), len(walls), len(arcs)))
info_messages.append("{} deck oculi, {} wall apertures".format(
    len(deck_cuts), len(wall_cuts)))
info_messages.append("seeds: circ={} wall={} ht={} arc={} oculi={} ap={}".format(
    circle_seed, seed, wall_height_seed, arc_seed, oculus_seed,
    wall_aperture_seed))

info = "\n".join(info_messages)
