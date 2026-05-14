# Grasshopper Parametric Design — 4-Month Accelerated Curriculum

**Target outcome (week 16):** build complex parametric systems with disciplined data-tree structure, debug other people's definitions fluently, drive geometry from Python via RhinoCommon, and ship a portfolio of reproducible, fabrication-aware parametric projects.

**Audience:** motivated learner with no Grasshopper background but comfort with basic 3D modeling and arithmetic. ~10 hrs/week.

**Tooling:** Rhino 8 (Windows ideal; Mac workable with caveats noted in Month 4), Grasshopper 1, the Rhino 8 **ScriptEditor** (CPython 3.9+), Git for `.gh` version control. Plugins are introduced when the underlying problem demands them, not before.

---

## Course Philosophy

Three commitments shape every decision below:

1. **Trees over recipes.** A student who deeply understands data trees can self-teach any plugin. A student who memorizes tutorials plateaus around week 8 and never recovers. Month 1 is therefore disproportionately weighted toward data structure discipline.
2. **Reproducibility over polish.** No artifact may rely on post-bake manual edits in Rhino. Every image must be reproducible from the `.gh` file plus internalized inputs. This is the single filter that distinguishes a parametric designer from a "Rhino user who knows some Grasshopper."
3. **Python is the destination, not a footnote.** Month 4 is a real sprint, not a victory lap. The student leaves having replaced at least one plugin with their own RhinoCommon code and shipped a custom user object (`.ghuser`).

---

## Weekly Cadence

| Block | Hours | Purpose |
|---|---|---|
| Theory + targeted tutorial | 2 | Concept introduction, instructor-curated video |
| Guided exercise | 4 | Build along, modify, break, fix |
| Personal project iteration | 3 | Apply to that month's capstone |
| Reading / critique | 1 | One forum thread, one definition teardown |

Profiler always visible. Bake disabled except at end of project sessions. `.gh` files committed to Git after every session.

---

## Setup (Week 0, ~2 hours)

- Install Rhino 8, verify GH1 (`_Grasshopper`).
- Install plugins via Package Manager: **Pufferfish**, **Weaverbird**, **LunchBox**, **Kangaroo 2** (bundled), **Human**, **Wallacei**, **Ladybug Tools**, **OpenNest**, **Anemone**, **Elefront**. *Don't install everything; the rest as the curriculum needs them.*
- Enable canvas widgets: **Profiler**, **Search**, **Tree Statistics** display.
- Configure ScriptEditor: open `_ScriptEditor`, confirm CPython 3 runs `print("hello")`.
- Initialize a Git repo for `.gh` files. Pair every `.gh` with a Rhino `.3dm` of the same basename.

---

# MONTH 1 — Foundations & Data Tree Discipline

**Goal:** stop fighting the canvas. The student should leave Month 1 able to predict the path structure of any output before connecting the wire.

### Week 1 — Anatomy + first algorithms

- GH interface: components vs parameters, wires, data types, double-click search, the right-click menu, `Param Viewer`.
- Rhino ↔ GH link: `Set One X`, internalize/bake, referenced vs internalized data, why internalization matters for reproducibility.
- Basic types: number, point, vector, plane, domain.
- The canonical first exercise: **attractor on a point grid** (distance → `Remap` → transform). This is the template every serious syllabus uses — once it clicks, parametric design clicks.

*Exercise:* radial array of objects on an arbitrary surface using `Evaluate Surface` + perp frames.

### Week 2 — Vectors, planes, transformations

- Point arithmetic: `Point - Point = Vector`, `Point + Vector = Point`. Unitize vs amplitude. Sign conventions.
- Planes: `Plane 3Pt`, `Plane Normal`, `Align Plane`, `Horizontal Frame`. Why `Perp Frame` flips at curve inflection points.
- `Transform`: translation, rotation, scale, `Plane to Plane` (the workhorse of every "place this on that" pattern).
- Domains and `Remap Numbers` — internalize the `Bounds → Remap` pattern.

*Exercise:* parametric staircase where each tread orients to a guide curve via `Perp Frame` *and* `Horizontal Frame`. Compare results.

### Week 3 — Lists and data matching

- List ops: `Range`, `Series`, `Random`, `Cull Pattern`, `Cull Index`, `Dispatch`, `Shift`, `Sort`, `Sub List`, `Partition List`.
- The three **data matching algorithms**: Shortest List, Longest List, Cross Reference. This is the most-skipped topic in self-taught curricula and it is responsible for an enormous fraction of "why does my output have N×M items" bugs.
- Image Sampler. `Graph Mapper` for response shaping.

*Exercise:* Voronoi panel facade where cell size is driven by an image sampler, with `Graph Mapper` controlling the response curve.

### Week 4 — Data Trees: the make-or-break week

This week is non-negotiable and gets ~12 hours instead of 10. The student walks out of it with genuine tree intuition or every later month silently degrades.

- Path notation: `{A;B;C}[i]`. Read panel paths fluently.
- Operations: `Graft`, `Flatten`, `Simplify`, `Trim Tree`, `Shift Paths`, `Flip Matrix`, `Merge`, `Entwine`.
- **Path Mapper** — lexical re-mapping (`{A;B}→{B;A}`), with the explicit caveat that it breaks if upstream tree shape changes. Pair with `Path Compose` / `Path Decompose` for parametric robustness.
- **Stream Filter** (route a stream by integer gate) and **Stream Gate** (its inverse).
- **Match Tree**, **Tree Statistics** — diagnostic tools.
- Branch vs item access: `Tree Branch` (whole branch by path) vs `List Item` (item by index).

*Drill: the tree calculator.* Given a chain of graft/flatten/simplify/path-mapper operations, **predict the output tree on paper before running it.** Repeat 20 times with increasing complexity. This drill, more than any tutorial, builds the intuition.

### Capstone — "Adaptive Facade Panelization"

Take a freeform NURBS surface (one provided, one of student's own), divide via UV grid driven by an attractor field (point, curve, image), and generate a panelized facade where each panel's aperture size, depth, and rotation respond to the field.

**Deliverable:** GH file + one hero render + one annotated tree-structure diagram showing the path at each major stage.

**Why this works:** panels live in a `{u;v}` grid, forcing clean tree handling. Image sampler + attractor field exercise the response-shaping skills from week 3. Pushes them into `Surface Box` / `Morph` territory without yet demanding curve-surface theory.

#### Rubric

| Criterion | Weak | Acceptable | Strong |
|---|---|---|---|
| **Tree integrity** | Flattens everywhere; can't predict paths | Trees match panel topology, occasional Flatten with no comment | Uses `Path Mapper`/`Graft`/`Trim Tree` deliberately; explains every branch op |
| **Attractor logic** | Single hard-coded distance | One attractor cleanly remapped via `Bounds`/`Remap` | Composable multi-attractor field with named ranges and `Graph Mapper` response shaping |
| **Parametric range** | Breaks at slider extremes | Works across stated min/max | Edge cases (zero attraction, max attraction, degenerate UV) produce no NaN/null geometry |
| **Definition hygiene** | Wires cross; no groups; "Number Slider" | Color-coded groups, sliders renamed with units | Left-to-right flow, scribbles labeling each section, all inputs internalized, profiler <200ms |
| **Geometric output** | Panels self-intersect or float off surface | Panels seat on surface | Panel response reads as a coherent gradient; bake-ready as closed Breps |
| **Documentation** | None | Canvas screenshot | Annotated tree diagram + slider value table |

#### Failure modes to flag

- `Flatten` used to brute-force fix mismatched lists instead of grafting the attractor.
- Image Sampler resolution mismatched to grid → pixelated panels.
- Attractor field computed in world space but applied in UV space.
- Surface domain not reparameterized → `Evaluate Surface` returns garbage.
- Student rebuilds the panel grid manually after baking.

#### Code review checklist (5 min)

1. Profiler under 200 ms on slider drag?
2. All inputs internalized? (file should open without the `.3dm`)
3. Sliders renamed with units (`panel_depth_mm`) and bounded sensibly?
4. Any ungrouped "junk drawer" zone? (red flag)
5. `Param Viewer` downstream of attractor — does the tree match the claim?
6. Any `Merge` immediately followed by `Flatten`? (logic smell)
7. Wire color: are `Data Dam`s used on heavy ops?

#### Diagnostic — pass all 4 in 60 minutes to advance

1. Restructure a flat 35-point list into `{0;0..6}` of 7 lists of 5 **without** using `Partition`. (Pass = uses `Unflatten`/`Split Tree`/`Path Mapper`.)
2. Place a sphere at every grid point, radius = distance to nearest of 3 attractors. (Pass = no Flatten anywhere, <50 ms.)
3. Image-sample a 512×512 PNG onto a surface as extrusion heights. (Pass = correct aspect, no `Dispatch` hacks.)
4. Fix a broken definition with mismatched tree paths by editing path operations only — no Flatten/Graft sprinkling. (Pass = explains the fix in one sentence.)

---

# MONTH 2 — Curves, Surfaces, Patterns, Meshes

**Goal:** build the geometric vocabulary used in 80% of professional GH definitions. Move from "shapes" to "topology you can fabricate."

### Week 5 — Curves

- Curve types (polyline, NURBS, interpolated, Bezier), degree, continuity (G0/G1/G2), curvature graph.
- `Divide Curve` by count vs length, `Curve Frames`, `Closest Point`, `Curve | Curve` intersection, `Offset on Surface`.
- `Pull Curve to Surface` vs project — when each fails.

*Exercise:* parametric staircase along an arbitrary 3D curve with consistent tread orientation through inflections.

### Week 6 — Surfaces and solids

- Construction: `Loft`, `Sweep1`, `Sweep2`, `Network Surface`, `Patch`. When each fails, and how to fix the seam alignment on `Loft`.
- `Isotrim`, `Reparameterize`, UV coordinates as the lingua franca of surface operations.
- Brep boolean reliability tricks: tiny offset to avoid "kissing" failures, falling back to mesh booleans (vastly improved in Rhino 8).
- SubD in Rhino 8: `SubD From Mesh`, `MultiPipe`, edit-cage workflows. Most pre-2024 courses skip this entirely — don't.

*Exercise:* twisted tower massing, floor plate extraction, core boolean subtraction.

### Week 7 — Patterns, attractors, image sampling (advanced)

- Multi-attractor blending: `min` / `avg` / weighted sum of distances. Why blending feels different from any single attractor.
- Field components in GH (Point Charge, Line Charge, Spin Force). When to use the Field API vs roll-your-own.
- Image and curve-based attractors layered with mathematical fields.

*Exercise:* facade where panel **rotation**, **depth**, and **aperture** each respond to a different attractor source, blended.

### Week 8 — Meshes and SubD

- When to leave NURBS: organic forms, high-poly fabrication, FEA prep, simulation input.
- `Mesh from Brep` settings — most students never touch these and end up with 50k-face meshes by default.
- **Weaverbird**: Catmull-Clark, Loop, mesh thicken, picture-frame.
- **LunchBox** panelization (diamond, hexagonal, triangle, quad).
- Rhino 8 **QuadRemesh** → SubD → ToNURBS pipeline — the modern way to recover clean NURBS from scan/sculpt geometry.

*Exercise:* one input surface, three tessellation versions: triangulated, hex-with-pent, SubD-relaxed.

### Capstone — "Ruled Shell Pavilion (Buildable)"

Design a ~4×4×3 m pavilion whose primary surface is generated from two profile curves via `Loft` or `Sweep2`, then either (a) developable-strip unrolled for fabrication, or (b) re-meshed and relaxed into a quad-dominant mesh shell with planar (or near-planar) faces.

**Deliverable:** GH file, flat-pattern PDF (or mesh + nodes catalog), exploded axonometric, hero render.

#### Rubric

| Criterion | Weak | Acceptable | Strong |
|---|---|---|---|
| **Curve construction** | Points placed by eye; no continuity discipline | Degree set; G1 where needed | Profiles rebuilt, degree-controlled, curvature graph clean |
| **Surface quality** | Pinches, self-intersection, wild isocurves | Clean isocurves, some flipped normals | Uniform isocurves, consistent normals, curvature analysis shows no surprises |
| **Topology / paneling** | Trimmed surface + projected pattern (won't fabricate) | Untrimmed UV pattern | Mesh relaxed via Kangaroo or `Weaverbird`, planar quads or strict triangles, valence-controlled |
| **Fabrication readiness** | "Looks cool" but no flat output | Unrolls with overlaps / missing tabs | Numbered strips, tabs, nested on stock-size sheet, kerf accounted for |
| **Modularity** | One 2-meter spaghetti canvas | Clear groups | Clustered (`Profile`, `Surface`, `Panelize`, `Unroll`), <10 inputs each |
| **Performance** | Slider lag >2 s | <500 ms with `Data Dam`s | Dam discipline, mesh ops isolated, preview disabled on intermediates |
| **Aesthetic** | Generic blob | Recognizable language | Form emerges from a stated constraint, not noise |

#### Failure modes

- `Loft` with mismatched seam direction → twist "fixed" by `Flip Curve` instead of seam alignment.
- Default `Mesh from Brep` settings → 50k faces.
- "Unrolls" a doubly-curved surface and pretends the distortion doesn't exist.
- Pattern applied post-hoc in Rhino instead of in GH.
- Kangaroo solver un-anchored → mesh collapses to a point.
- `Brep Join` used to merge meshes (wrong primitive).

#### Diagnostic — pass 3 of 4

1. `Sweep2` along a helix with a variable cross-section scaling with arc length. (Pass = no twisting, verified with `Length`.)
2. Convert a Brep to a quad-dominant mesh under 5k faces, manifold, 0 non-manifold edges.
3. Relax a hex-grid mesh on a target surface using Kangaroo, anchored at boundary. (Pass = converges in <500 iterations.)
4. Unroll a developable strip and lay 8 numbered copies on a 1.2×2.4 m sheet, 5 mm spacing, no overlaps, all labeled.

---

# MONTH 3 — Simulation, Optimization, Fabrication

**Goal:** stop making shapes; start making *systems*. Add behavior, constraints, and real-world output.

### Week 9 — Kangaroo 2

Mental model: **goals (energies) + solver minimizes total energy.** Teach in this order:

1. `Anchor` + `Length` → catenary.
2. `Spring` + `Load` → hanging chain (inverted compression shell, the Gaudí workflow).
3. `SoapFilm` / `Live Soap` → minimal surfaces.
4. `EdgeLengths` + `Show` + `CollidePoint` → tensile membrane / inflated cushion.
5. `PlanarizeQuad` / `CoPlanar` → planarization for fabricable gridshells.
6. `SphereCollide` + `Anchor` → circle/sphere packing.

Optional: `K2Engineering` for calibrated structural goals (real units for axial force, stress) — only if the student cares about structure-driven form.

*Exercise:* tensile canopy form-found from a flat mesh with 4 fixed anchors and one center load.

### Week 10 — Recursion and growth

Anemone is the canonical loop tool (Hoopsnake is functionally obsolete). Teach `Loop Start` / `Loop End` and the fast-loop variant. One demo each of:

- L-system (Koch curve or branching tree) — string rewriting as a concept.
- Differential growth (curve subdivides + repulsion + spring forces; bulges into Hilbert-like patterns). Best implemented as Anemone + Kangaroo 2 together.
- Diffusion-limited aggregation **or** reaction-diffusion (Gray-Scott).

This week is also the **Python motivator.** Show that Anemone hits a wall around a few hundred iterations on reaction-diffusion; mention that in Month 4 the student will rewrite the same algorithm in CPython 3 with NumPy and watch it run 100× faster. Plant the flag.

### Week 11 — Optimization (and a little environmental analysis)

Decision tree, drilled into the student:

| Situation | Tool |
|---|---|
| Single objective, fast fitness (<1 s/eval) | **Galapagos** (GA or SA, ships with GH) |
| Multi-objective (2–3 goals), need Pareto front | **Wallacei** (NSGA-II) |
| Expensive fitness function (slow simulation) | **Opossum** (RBFOpt, model-based — converges in far fewer evaluations) |

Skip Octopus (superseded by Wallacei).

**Fitness function antipatterns** to call out explicitly:
- Minimizing absolute deviation without normalization → one objective dominates.
- `if/else` creating flat plateaus the GA can't climb.
- Correlated objectives in disguise (effectively single-objective).
- Wallacei with >3 objectives → intractable runs.

**Environmental analysis (½ day, minimum viable):** Ladybug only, not Honeybee. EPW import, Sun Path, Radiation Analysis, Direct Sun Hours, Wind Rose. Daylight Factor and annual daylight need Radiance/EnergyPlus — defer to a future Honeybee course.

### Week 12 — Fabrication output

- **OpenNest** for curve/polyline nesting (NFP algorithm).
- Unrolling strategies for double-curved surfaces: develop into strips (`Unroll Surface` with constant U or V), or tessellate to planar quads/triangles. There is no clean answer — teach the trade-offs.
- **Human plugin** for tags, layers, blocks. Essential for labeling fabrication parts (panel IDs, fold lines, edge codes).
- Generic toolpath thinking: geometry → flatten/orient → label → nest → export DXF/SVG/STL. Stay tool-agnostic.

### Capstone — "Performance-Driven Shading Screen"

Design a south-facing shading screen for a location of the student's choice. Pull an EPW; use Ladybug for solar radiation analysis on the target wall; drive aperture density and fin angle from analysis results. Optimize average aperture rotation with Wallacei against two objectives: minimize incident summer radiation, maximize unobstructed view angle from interior. Output fabrication-ready nested DXF for a 1:5 prototype panel.

**Deliverable:** GH file, Pareto front plot, generation gallery, nested DXF, physical 1:5 prototype photo (cardboard is fine).

#### Rubric

| Criterion | Weak | Acceptable | Strong |
|---|---|---|---|
| **Analysis correctness** | Wrong climate, orientation, or period | Correct EPW + period, normals checked | Validated against external check (sun-path direction), sensitivity understood |
| **Data → form mapping** | Linear remap one-to-one | Multi-variable with `Graph Mapper` shaping | Mapping justified (threshold = view angle, gain = comfort target) |
| **Optimization setup** | No fitness; "maximize something" | Single-objective, converges | Multi-objective Wallacei; Pareto front shown; fitness convergence plotted |
| **Genome design** | 20 sliders (search space explodes) | 4–8 sliders, sensible bounds | Reduced via dimensional analysis; symmetry exploited |
| **Fabrication output** | Manually baked DXF | Auto-nested, kerf-offset | Toolpath simulated, cut order optimized, material yield reported |
| **Iteration documentation** | "Final" only | Before/after of 2 optima | Generation gallery + fitness convergence plot |
| **Definition discipline** | Optimization on un-dammed heavy mesh | Dams in place, sensible analysis resolution | Analysis mesh decoupled from display mesh; fitness function swappable |

#### Failure modes

- Running Galapagos on a definition taking 8 s/iteration and giving up after 50 generations. (Target: <1 s/eval for meaningful convergence.)
- Fitness rewards trivial solutions (close all apertures → zero radiation).
- Ladybug analysis grid at 50 mm on a 10 m facade — solver runs for hours.
- Reporting the last generation's best, not the run's best.
- Baking the optimum and tweaking it in Rhino.
- DXF curves not joined → CNC reads each segment as a separate cut.

#### Diagnostic — pass 3 of 4

1. Set up Ladybug radiation analysis on a tilted surface, report kWh/m² for a summer week. (Within ±10% of instructor reference.)
2. Run Galapagos to maximize the area of a polygon inscribed in a unit circle with N=6 free vertex angles. (Converges to regular hexagon area within 1%.)
3. Generate a nested DXF on a 1.2×2.4 m sheet with <15% waste.
4. Identify the bottleneck in a slow definition using the profiler; reduce solve time by ≥50% without changing output.

---

# MONTH 4 — Python Scripting in Grasshopper

**Goal:** read RhinoCommon docs without flinching. Replace clusters of native components with concise scripts. Ship a custom user object.

**Critical setup decision: teach CPython 3 in the Rhino 8 ScriptEditor, not legacy IronPython.** The shebang `#! python 3` at the top of a script selects CPython via Python.NET. Numpy/scipy/networkx/shapely/compas are all available via inline directives:

```python
#! python 3
# r: numpy
# r: scipy==1.11.*
# r: compas

import numpy as np
import Rhino.Geometry as rg
```

Acknowledge IronPython 2.7 exists for ~30 minutes so students can read legacy `.gh` files, then never touch it. CPython has a documented RhinoCommon call overhead (2–5× slower than IronPython in tight loops) — the remedy is to vectorize with NumPy or push work into RhinoCommon batch methods, both of which the curriculum covers.

Mac caveat: Script component has had stability problems through 2024–2025. Test on the student's actual hardware before week 13.

### Week 13 — Python fundamentals + GH plumbing

- Python 3 syntax speedrun for non-coders (lists, dicts, comprehensions, functions, classes).
- The Script component: inputs, type hints (`Curve`, `Point3d`, `float`), access modes (Item / List / Tree), output assignment, `print` and the output panel.
- `rhinoscriptsyntax` as a temporary stepping stone (acknowledge, then move on).
- `ghpythonlib.components` — call any GH component as a function. Useful bridge; will be deprecated by week 14.
- `ghpythonlib.treehelpers` for `tree_to_list` / `list_to_tree`.

*Exercise:* rewrite a ~30-component Month-1 definition (the attractor on a grid) as a ~20-line script.

### Week 14 — RhinoCommon proper

Drill the five must-know namespaces. Teach by **geometry type, then operation**, in this order: `Point3d`/`Vector3d` → `Plane`/`Transform` → `Line`/`Polyline` → `Curve` (param space, `PointAt`, `TangentAt`, `DivideByCount`, `ClosestPoint`) → `Surface` (UV space) → `Brep` → `Mesh` → `Intersect.Intersection` → `RTree`. Spend half a day on `Transform` — every parametric pattern uses it.

**Top-30 method set** the student should know cold:
`Point3d`/`Vector3d` arithmetic, `Plane.WorldXY` / `PlaneFitFromPoints`, `Transform.PlaneToPlane`/`Rotation`/`Scale`, `Line.PointAt`, `Polyline.ToNurbsCurve`, `Curve.PointAt`/`TangentAt`/`DivideByCount`/`DivideByLength`/`ClosestPoint`/`Offset`/`PullToBrepFace`, `Brep.CreateFromBox`/`CreateFromLoft`/`CreateBooleanUnion`, `Mesh.CreateFromBrep`, `Intersection.CurveCurve`/`CurveBrep`/`MeshMeshAccurate`/`ProjectPointsToBreps`, `RTree.CreateFromPointArray` + `Search`, `BoundingBox.Union`.

**Data trees in Python — explicit `GH_Path`:**

```python
#! python 3
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
import Rhino.Geometry as rg

a = DataTree[rg.Point3d]()
for i in range(5):
    for j in range(5):
        a.Add(rg.Point3d(i, j, 0), GH_Path(i))
```

The most common silent failure: setting **Tree Access** on the input parameter, not List Access. Drill this.

*Exercise:* function that takes a tree of curves and returns a tree of evenly divided points, preserving path structure.

### Week 15 — Algorithms, performance, external libraries

- Recursion in Python (no Anemone needed): quad subdivision with attractor.
- Intersection algorithms from scratch: `Intersection.CurveCurve`, `Intersection.MeshRay`.
- Mesh construction from face lists.
- **RTree** for O(n log n) spatial queries — pairwise distance on 10k points goes from minutes to milliseconds.
- `System.Threading.Tasks.Parallel.For` for embarrassingly parallel work (3–4× on a 4-core machine, but only above ~1000 items and only when the body has no shared mutable state).
- External libraries via `# r:`: NumPy first; one demo each of SciPy, NetworkX, and COMPAS (`compas.geometry`, `compas.datastructures.Mesh` for half-edge mesh work RhinoCommon doesn't expose cleanly).
- Re-implementation challenge: the Month-3 reaction-diffusion exercise, now in NumPy. Watch it run 100× faster.

*Exercise:* recursive quad-subdivision-with-attractor — no plugins, just Python and RhinoCommon. Compare to a `LunchBox` equivalent's performance.

### Week 16 — Packaging, custom components, final project

- Turn a `.py` script into a reusable **user object (`.ghuser`)**: right-click Script component → "Create User Object." Set name, description, icon, locked code. *This is the realistic deliverable for week 16.*
- The new ScriptEditor "Create Plug-in" workflow bundles multiple scripts into a shareable package.
- 30-minute demo of compiled `.gha` (subclass `GH_Component` in C# against the RhinoCommon NuGet) — for awareness only. Compiled components are a C# course.
- One 3-hour **Hops** demo: Flask + `ghhops_server` exposes a Python function as a Grasshopper component over HTTP. The clean answer to "how do I use PyTorch / shapely-with-rtree-index / any slow C extension from Grasshopper without freezing the canvas."

### Capstone — "Replace a Plugin"

Pick a nontrivial component or small plugin (LunchBox triangular paneling, a Mesh+ subdivision, a custom space-truss generator) and **reimplement it in Python with RhinoCommon directly** — no calling the original component. Wrap as a `.ghuser` with clean inputs/outputs. Then use it inside a Month-2 or Month-3 definition, replacing the plugin dependency entirely.

**Deliverable:** `.ghuser` file, GH file demonstrating it in context, side-by-side comparison with the plugin equivalent on 3 test inputs, profiler timings before/after.

#### Rubric

| Criterion | Weak | Acceptable | Strong |
|---|---|---|---|
| **API fluency** | Builds geometry by points/lines only | Uses `Mesh`/`Brep`/`Curve` constructors appropriately | Uses `Brep.CreateFromLoft`, `Mesh.CreateFromBrep`, `Intersection.MeshMeshAccurate` — knows the right method |
| **Type discipline** | All inputs unhinted (`ghdoc Object`) | Inputs hinted | Access modes set correctly; tree input handled with `GH_Path`, not flattened |
| **Code structure** | One 200-line `def`, globals everywhere | Functions split by responsibility | Pure functions for geometry; side effects isolated; docstrings present |
| **Error handling** | Crashes on edge inputs | `try/except` around obvious failures | Validates inputs, raises informative messages, component goes red with reason |
| **Performance** | O(n²) where O(n log n) exists | Reasonable; uses `RTree` or `Point3dList.ClosestIndex` where appropriate | Profiled vs. native components; within 2× of equivalent or faster |
| **Equivalence to original** | Output visually different | Matches plugin on test cases | Numerical match (vertex positions within tolerance) on ≥3 test inputs |
| **Integration** | Script lives alone | Wrapped in cluster with named I/O | Used inside a real Month-2 or -3 definition without breaking it |

#### Failure modes

- `rs.` (rhinoscriptsyntax) everywhere — fine for prototyping, lazy for a capstone.
- Iterating Python lists to build geometry RhinoCommon has a single-call method for.
- Mutating input geometry (RhinoCommon objects are reference types).
- No Item/List/Tree access mode set → silently flattened trees.
- `scriptcontext.doc.Objects.Add` from a script (bakes from script — wrong layer).
- Bare `except:` silently swallowing errors.
- Hardcoded tolerance instead of `sc.doc.ModelAbsoluteTolerance`.
- `print` left as a debug crutch instead of routing through `out`.

#### Diagnostic — pass 4 of 5

1. Component that takes a list of curves and returns the one with highest curvature integral. (Uses `Curve.CurvatureAt` sampled correctly, <100 ms on 50 curves.)
2. Tree of points `{A;B}` in → tree of per-branch convex hulls (polylines), preserving structure.
3. Catmull-Clark one-step subdivision on a quad mesh using only `Rhino.Geometry.Mesh` primitives. (Matches Weaverbird output on a test cube within tolerance.)
4. Build a `.ghuser` exposing the subdivision with an iteration slider. (Appears on toolbar, icon set.)
5. Profile a script; reduce runtime by 2× using RTree or vectorized NumPy.

---

# Final Portfolio Package

Eight artifacts, each = hero image + GH file + 1-page PDF process sheet (intent, parameters, one critical design decision).

1. **M1 Adaptive Facade** — data tree discipline + attractor logic.
2. **M2 Pavilion + Flat Pattern PDF** — curve/surface fluency + fabrication thinking; include the actual unrolled sheet.
3. **M3 Shading Screen + Pareto Plot** — environmental literacy + multi-objective optimization.
4. **M3 1:5 Prototype Photo** — physical artifact (cardboard fine). Closes the design-to-object loop.
5. **M4 Custom Component (`.ghuser`)** — RhinoCommon mastery, installable.
6. **Refactored M2 Definition** — same pavilion, now powered by M4 component. Demonstrates integration.
7. **Process Notebook (8–12 pages)** — failed iterations, profiler before/afters, sketches. Demonstrates judgment, not polish.
8. **Methods Sheet (1 page)** — bulleted list of every component family, plugin, and Python pattern used. Demonstrates scope self-awareness.

Optional 9 & 10: ~60 s screen recording of the M4 component used in real time, and a synthesis definition combining trees + Kangaroo + Python on one canvas.

**Portfolio guiding rule (again):** no artifact relies on post-bake manual edits in Rhino. Reproducible from the `.gh` file alone.

---

# Cross-Cutting: Pro Habits

Drilled every week, surfaced in every code review.

1. **Left-to-right, top-to-bottom flow.** Inputs vertical on the left, outputs/bakes on the right. No backward wires.
2. **Group and color-code by function.** A consistent palette (e.g. orange = inputs, green = geometry, blue = analysis, red = output).
3. **Scribble headings** labeling each group as a function.
4. **Cluster discipline.** Only when (a) the chunk is reused, (b) it has ≤10 inputs, (c) related components only.
5. **Internalize stable inputs only** (sliders, small reference geometry) — never heavy meshes/polysurfaces. Color-mark internalized components.
6. **Name everything.** F2-rename sliders to semantic names with units (`floor_height_mm`).
7. **Profiler on, always.** Measure before optimizing.
8. **Disable preview** aggressively on intermediate geometry; mesh previews dominate canvas slowdowns.
9. **Personal cluster library / userObjects folder** of reusable definitions.
10. **Git for `.gh` files.** Pair every definition with the matching `.3dm`.

---

# Cross-Cutting: Stumbling Blocks (ranked)

1. **Data trees** — reflexive flattening, graft vs flatten confusion, Path Mapper mask syntax, inability to read `{A;B;C}[i]` paths.
2. **Data matching** — Shortest vs Longest vs Cross Reference; cross-reference combinatorial explosions.
3. **Plane / frame orientation** — `Perp Frame` flips at curve inflections; box morph and orient break without solid plane intuition.
4. **Vector math** — sign conventions; unitize vs amplitude; `Point - Point` vs `Point + Vector`.
5. **Boolean / trim failures** — kissing surfaces produce ribbons; fix with a tiny offset or switch to mesh booleans.
6. **Mesh vs NURBS confusion** — trying mesh operations on Breps and vice versa.
7. **Plugin overload** — installing 20 plugins on day one and not knowing where any component lives.
8. **Recipe-following instead of algorithmic thinking** — diving into tutorials before asking "what is the computer iterating over here?"

---

# Plateau Patterns

- **Plateau 1: Recipe Wall (~weeks 4–8).** Can reproduce attractor walls and parametric facades but can't compose new definitions from scratch. *Unlock:* model from a verbal brief with no tutorial; explicit study of data tree path arithmetic.
- **Plateau 2: Tree Wall (~weeks 8–14).** Definitions break when scaled because tree structure isn't planned. *Unlock:* draw the intended tree on paper *before* wiring; master Path Mapper plus `Trim Tree`/`Graft` at specific depths.
- **Plateau 3: Visual-Programming Ceiling (~month 3+).** Recursion, custom data structures, performance-critical loops, anything with state — awkward or impossible visually. *Unlock:* ScriptEditor with CPython, then RhinoCommon, then (post-course) C# for type safety and parallelism.

Realistic curve for a focused student: comfortable in GH at week 6, fluent in trees at week 10, productive in Python-in-Grasshopper at week 14, writing useful RhinoCommon scripts by end of month 4. Compiled plugin development is past this course's horizon.

---

# Resource Library

**Foundational references**
- The Grasshopper Primer (Mode Lab, 3rd ed.) — https://modelab.gitbooks.io/grasshopper-primer/content/
- McNeel official scripting guides — https://developer.rhino3d.com/guides/scripting/
- RhinoCommon API reference — https://developer.rhino3d.com/api/rhinocommon/
- Columbia GSAPP Smorgasbord — https://smorgasbord.cdp.arch.columbia.edu/
- Gramazio Kohler teaching materials — https://gramaziokohler.github.io/teaching_materials/grasshopper/

**Data trees**
- BIM Corner "6 rules for data trees" — https://bimcorner.com/6-rules-how-to-work-with-grasshopper-data-tree/
- BIM Corner "Path Mapper is a BADASS" — https://bimcorner.com/grasshopper-data-tree-path-mapper-is-a-badass/
- Andrew Heumann data trees masterclass — https://www.youtube.com/watch?v=Z6Pb-ScLpFI
- ShapeDiver data trees series — https://www.shapediver.com/blog/grasshopper-data-trees-explained-pt-2

**Best practices**
- parametricbydesign.com — https://parametricbydesign.com/explanation/visual-programming/best-practices/
- Modelical — https://www.modelical.com/en/best-practices-in-grasshopper/
- Daniel Davis "Untangling Grasshopper" — https://www.danieldavis.com/untangling-grasshopper-part-2-optimisation/

**Simulation & optimization**
- Daniel Piker, "Kangaroo: Form Finding with Computational Physics" — https://www.researchgate.net/publication/260745327
- Wallacei research — https://www.wallacei.com/research
- Karamba3D manual — https://manual.karamba3d.com/
- K2Engineering — https://github.com/CecilieBrandt/K2Engineering

**Python in Rhino 8**
- ScriptEditor megathread — https://discourse.mcneel.com/t/rhino-8-feature-scripteditor-cpython-csharp/128353
- McNeel Grasshopper Python guide — https://developer.rhino3d.com/guides/scripting/scripting-gh-python/
- Python packages in Rhino — https://developer.rhino3d.com/guides/rhinopython/python-packages/
- GH data trees in Python — https://developer.rhino3d.com/guides/rhinopython/grasshopper-datatrees-and-python/
- Hops component — https://developer.rhino3d.com/guides/compute/hops-component/
- COMPAS for Rhino 8 — https://compas.dev/compas/latest/userguide/cad.rhino8.html
- Long Nguyen's Python intensives (SimplyRhino) — https://simplyrhino.co.uk/training/courses/python-programming

**Fabrication & interop**
- OpenNest — https://github.com/petrasvestartas/OpenNest
- Speckle (interop) — https://speckle.systems/
- Rhino.Inside.Revit — https://www.rhino3d.com/inside/revit/

**Plugins (current as of 2026)**
- Pufferfish — https://www.food4rhino.com/en/app/pufferfish
- Weaverbird — https://www.giuliopiacentino.com/weaverbird/
- LunchBox, Human, Elefront, Heteroptera, Clipper — Food4Rhino

---

# Opinionated Parting Notes

- **Month 1 is the highest-leverage month.** If trees aren't internalized by the week-4 diagnostic, every later month silently degrades. Don't let the student speed-run it.
- **Resist Kangaroo before Month 3.** It's seductive and hides bad surface modeling.
- **Teach the Rhino 8 ScriptEditor + CPython 3, not legacy IronPython.** NumPy/SciPy access is worth the modest call overhead.
- **Profiler always on.** Single most underused Grasshopper feature among self-taught users.
- **`.gh` files in Git.** Treat them like source code. They are.
- **One forum thread a week.** discourse.mcneel.com — reading failed-definition threads teaches more than tutorials.
- **Post one definition per month** somewhere public for critique. Reading other people's reactions to your data tree decisions is the fastest feedback loop available.
