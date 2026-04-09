"""Grasshopper Plant Placement Script (Python 3)

Randomly populates PNG pen drawings of foliage across a landscape surface.
Supports 3 different plant types via PictureFrame references.

GRASSHOPPER SETUP — Script component (Python 3):

INPUTS (right-click > Edit Script > manage inputs):
  S     : Surface      — landscape surface
  Img1  : System.Guid  — PictureFrame for plant 1
  Img2  : System.Guid  — PictureFrame for plant 2
  Img3  : System.Guid  — PictureFrame for plant 3
  N1    : int           — count of plant 1 (default 10)
  N2    : int           — count of plant 2 (default 10)
  N3    : int           — count of plant 3 (default 10)
  H     : float         — base height in model units (default 5.0)
  Var   : float         — scale variation 0-1 (default 0.3)
  Seed  : int           — random seed (default 0)

OUTPUTS:
  M     — DataTree of Mesh   (quad meshes, one branch per plant type)
  Pts   — DataTree of Point3d (base points, one branch per plant type)
  Pln   — DataTree of Plane   (placement planes, one branch per plant type)

IMAGE WORKFLOW:
  1. Drag & drop a PNG into the Rhino viewport (creates a PictureFrame)
  2. In GH, add a Geometry param (Params > Geometry > Geometry)
  3. Right-click > "Set one Geometry" > click the PictureFrame
  4. Connect to Img1 / Img2 / Img3
"""

import Rhino
import Rhino.Geometry as rg
import Grasshopper as gh
from Grasshopper.Kernel.Data import GH_Path
import System
import random
import struct
import math


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_image_path(guid):
    """Extract the PNG file path from a PictureFrame's material."""
    doc = Rhino.RhinoDoc.ActiveDoc
    obj = doc.Objects.FindId(guid)
    if obj is None:
        raise ValueError("Could not find Rhino object for the given reference.")
    mat_index = obj.Attributes.MaterialIndex
    if mat_index < 0:
        raise ValueError("Referenced object has no material. Is it a PictureFrame?")
    mat = doc.Materials[mat_index]
    texture = mat.GetBitmapTexture()
    if texture is None:
        raise ValueError("Material has no bitmap texture. Is it a PictureFrame?")
    return texture.FileName


def get_png_aspect(filepath):
    """Read PNG width/height from the IHDR chunk and return aspect ratio."""
    with open(filepath, "rb") as f:
        header = f.read(24)
    if len(header) < 24 or header[:4] != b"\x89PNG":
        raise ValueError("File is not a valid PNG: " + filepath)
    width, height = struct.unpack(">II", header[16:24])
    return width / height


def make_quad_mesh(plane, half_w, h):
    """Create a single quad mesh standing vertically on the plane.

    Bottom edge is centered at the plane origin (trunk at ground).
    Plane X = width direction, Plane Y = height direction (up).
    """
    mesh = rg.Mesh()
    mesh.Vertices.Add(plane.PointAt(-half_w, 0))   # 0  bottom-left
    mesh.Vertices.Add(plane.PointAt( half_w, 0))   # 1  bottom-right
    mesh.Vertices.Add(plane.PointAt( half_w, h))   # 2  top-right
    mesh.Vertices.Add(plane.PointAt(-half_w, h))   # 3  top-left
    mesh.Faces.AddFace(0, 1, 2, 3)
    mesh.TextureCoordinates.Add(0.0, 0.0)  # BL
    mesh.TextureCoordinates.Add(1.0, 0.0)  # BR
    mesh.TextureCoordinates.Add(1.0, 1.0)  # TR
    mesh.TextureCoordinates.Add(0.0, 1.0)  # TL
    mesh.Normals.ComputeNormals()
    return mesh


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

if N1 is None: N1 = 10
if N2 is None: N2 = 10
if N3 is None: N3 = 10
if H  is None: H  = 5.0
if Var is None: Var = 0.3
if Seed is None: Seed = 0


# ---------------------------------------------------------------------------
# Validate inputs
# ---------------------------------------------------------------------------

if S is None:
    raise ValueError("Connect a surface to S.")

image_guids = [Img1, Img2, Img3]
counts = [N1, N2, N3]

# Get file paths and aspect ratios for each plant type
paths = []
aspects = []
for i, guid in enumerate(image_guids):
    if guid is None or guid == System.Guid.Empty:
        raise ValueError("Connect a PictureFrame to Img{}.".format(i + 1))
    p = get_image_path(guid)
    paths.append(p)
    aspects.append(get_png_aspect(p))


# ---------------------------------------------------------------------------
# Normalize surface domain to [0,1] x [0,1]
# ---------------------------------------------------------------------------

srf = S.Duplicate()
srf.SetDomain(0, rg.Interval(0.0, 1.0))
srf.SetDomain(1, rg.Interval(0.0, 1.0))


# ---------------------------------------------------------------------------
# Generate placements
# ---------------------------------------------------------------------------

rng = random.Random(Seed)

mesh_tree = gh.DataTree[object]()
pts_tree  = gh.DataTree[object]()
pln_tree  = gh.DataTree[object]()

for plant_idx in range(3):
    n = counts[plant_idx]
    aspect = aspects[plant_idx]
    path = GH_Path(plant_idx)

    meshes = []
    points = []
    planes = []

    for _ in range(n):
        # Random UV on the surface
        u = rng.random()
        v = rng.random()

        # Evaluate surface at UV
        pt = srf.PointAt(u, v)

        # Build a vertical plane at the point with random Z rotation
        angle = rng.uniform(0, 2 * math.pi)
        x_axis = rg.Vector3d(math.cos(angle), math.sin(angle), 0)
        y_axis = rg.Vector3d(0, 0, 1)
        plane = rg.Plane(pt, x_axis, y_axis)

        # Random scale
        scale = 1.0 + rng.uniform(-Var, Var)
        h = H * scale
        w = h * aspect
        hw = w * 0.5

        # Create the quad mesh
        mesh = make_quad_mesh(plane, hw, h)

        meshes.append(mesh)
        points.append(pt)
        planes.append(plane)

    mesh_tree.AddRange(meshes, path)
    pts_tree.AddRange(points, path)
    pln_tree.AddRange(planes, path)


# ---------------------------------------------------------------------------
# Assign outputs
# ---------------------------------------------------------------------------

M   = mesh_tree
Pts = pts_tree
Pln = pln_tree
