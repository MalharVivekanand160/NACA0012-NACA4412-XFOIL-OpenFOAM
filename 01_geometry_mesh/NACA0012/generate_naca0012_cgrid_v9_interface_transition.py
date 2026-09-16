#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# NACA 0012 structured supervisor-topology mesh
#
# This script writes the mesh directly as Gmsh MSH2.
# No automatic Gmsh 2D meshing is used.
#
# Topology:
#   1. nose C-block around leading edge
#   2. upper structured outer block
#   3. lower structured outer block
#   4. finite wake-throat transition block
#   5. central wake block
#
# Output:
#   structured_supervisor_topology.msh
#   structured_supervisor_topology_preview.png
# ============================================================

out_msh = Path("naca0012_cgrid_v9_interface_transition.msh")
out_png = Path("naca0012_cgrid_v9_interface_transition_preview.png")

# -----------------------------
# Geometry
# -----------------------------
t = 0.12

x_le = 0.0
x_te = 1.0
x_split = 0.20
x_throat = 1.30
x_out = 8.00

y_top = 2.00
y_bottom = -2.00

r_far = 2.00
x_c = x_split

# Numerically finite but visually closed trailing edge.
# Small enough to avoid a visible/kinked blunt TE, but nonzero to avoid
# zero-length edges at the wake start.
te_half_gap = 0.0

# Wake band
wake_half_height = 0.12
wake_out_half_height = 0.12 * 1.45

# -----------------------------
# Mesh resolution
# -----------------------------
n_nose_half = 140         # split -> LE and LE -> split
n_airfoil_upper = 300     # split -> TE
n_transition = 30         # TE -> wake throat
n_wake = 320              # shared wake centreline -> outlet, V12

n_radial = 75             # airfoil/wake to farfield
n_wake_y = 31             # across wake band

growth_radial = 1.14      # Airfoil/TE radial growth, target y+ ~0.5-1.0
growth_wake_out = 1.07     # Relaxed radial growth at downstream outlet

# V8 high-AoA outer buffer
# Keep the verified V6 mesh as the inner grid and attach a coarser
# outer domain around it.
r_far_outer = 10.00
y_top_outer = 10.00
y_bottom_outer = -10.00
x_out_outer = 15.00

# 32 intervals from 2c to 10c -> approximately 0.25c spacing,
# closely matching the outermost spacing of the verified V6 grid.
n_outer_radial = 33

# Physical tags
TAG_AIRFOIL = 1
TAG_TOP = 2
TAG_INLET = 3
TAG_BOTTOM = 4
TAG_OUTLET = 5
TAG_FLUID = 7


def naca00xx_thickness(x, t):
    x = np.asarray(x)
    return 5.0 * t * (
        0.2969 * np.sqrt(x)
        - 0.1260 * x
        - 0.3516 * x**2
        + 0.2843 * x**3
        - 0.1036 * x**4
    )


def radial_eta(n, growth):
    ds = growth ** np.arange(n - 1)
    ds = ds / ds.sum()
    eta = np.zeros(n)
    eta[1:] = np.cumsum(ds)
    return eta


def interp_curve(p0, p1, n):
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    s = np.linspace(0.0, 1.0, n)
    return (1.0 - s)[:, None] * p0 + s[:, None] * p1


def cosine_segment(x0, x1, n):
    """
    Two-sided cosine spacing. Use carefully: it clusters at both endpoints.
    """
    beta = np.linspace(0.0, np.pi, n)
    s = 0.5 * (1.0 - np.cos(beta))
    return x0 + (x1 - x0) * s


def one_sided_cosine_segment(x0, x1, n, cluster="start"):
    """
    One-sided cosine spacing.
    cluster="start": clusters near x0, spacing opens toward x1.
    cluster="end"  : clusters near x1, spacing opens from x0.

    This is better here because we want strong clustering near the LE,
    but not artificial clustering at the split point or TE.
    """
    u = np.linspace(0.0, 1.0, n)

    if cluster == "start":
        q = 1.0 - np.cos(0.5 * np.pi * u)
    elif cluster == "end":
        q = np.sin(0.5 * np.pi * u)
    else:
        raise ValueError("cluster must be 'start' or 'end'")

    return x0 + (x1 - x0) * q


# -----------------------------
# Airfoil helper
# -----------------------------
def y_upper_from_x(x):
    xn = (np.asarray(x) - x_le) / (x_te - x_le)
    y = naca00xx_thickness(xn, t)
    return y


# Split point on airfoil
y_split = float(y_upper_from_x(x_split))

p_split_u = np.array([x_split, y_split])
p_split_l = np.array([x_split, -y_split])
p_le = np.array([x_le, 0.0])
p_te = np.array([x_te, 0.0])
p_te_u = p_te.copy()
p_te_l = p_te.copy()

p_throat_u = np.array([x_throat, wake_half_height])
p_throat_l = np.array([x_throat, -wake_half_height])
p_out_wake_u = np.array([x_out, wake_out_half_height])
p_out_wake_l = np.array([x_out, -wake_out_half_height])

p_top_split = np.array([x_split, y_top])
p_bottom_split = np.array([x_split, y_bottom])
p_right_top = np.array([x_out, y_top])
p_right_bottom = np.array([x_out, y_bottom])


# ============================================================
# Build boundary curves
# ============================================================

# Nose inner: split lower -> LE -> split upper
# Cluster only near the leading edge, not at the split point.
x_lower_nose = one_sided_cosine_segment(x_split, x_le, n_nose_half, cluster="end")
y_lower_nose = -y_upper_from_x(x_lower_nose)
lower_nose = np.column_stack([x_lower_nose, y_lower_nose])

x_upper_nose = one_sided_cosine_segment(x_le, x_split, n_nose_half, cluster="start")
y_upper_nose = y_upper_from_x(x_upper_nose)
upper_nose = np.column_stack([x_upper_nose, y_upper_nose])

nose_inner = np.vstack([lower_nose, upper_nose[1:]])

# Nose outer C-arc: bottom split -> left -> top split
theta = np.linspace(-np.pi / 2.0, -3.0 * np.pi / 2.0, nose_inner.shape[0])
nose_outer = np.column_stack([
    x_c + r_far * np.cos(theta),
    r_far * np.sin(theta)
])

# Upper airfoil from split -> TE
# Use linear spacing here to avoid tiny endpoint cells at split/TE.
# With 280 points, the airfoil still remains visually smooth.
x_upper_main = np.linspace(x_split, x_te, n_airfoil_upper)
y_upper_main = y_upper_from_x(x_upper_main)
y_upper_main[-1] = 0.0
upper_airfoil = np.column_stack([x_upper_main, y_upper_main])

# Lower airfoil from split -> TE
x_lower_main = np.linspace(x_split, x_te, n_airfoil_upper)
y_lower_main = -y_upper_from_x(x_lower_main)
y_lower_main[-1] = 0.0
lower_airfoil = np.column_stack([x_lower_main, y_lower_main])

# V12 shared wake centreline:
# Upper and lower rear blocks share the same wake line behind the TE.
# This removes the separate TE fan/wake-band topology.
# V3 graded wake:
# Match the first wake spacing to the final airfoil spacing,
# then grow smoothly toward the outlet.
dx_te = x_upper_main[-1] - x_upper_main[-2]
n_wake_intervals = n_wake - 1
wake_length = x_out - x_te

def geometric_wake_length(r):
    if abs(r - 1.0) < 1.0e-14:
        return dx_te * n_wake_intervals
    return dx_te * (r**n_wake_intervals - 1.0) / (r - 1.0)

lo, hi = 1.0, 1.1
for _ in range(100):
    r_wake = 0.5 * (lo + hi)
    if geometric_wake_length(r_wake) < wake_length:
        lo = r_wake
    else:
        hi = r_wake

r_wake = 0.5 * (lo + hi)

wake_dx = dx_te * r_wake ** np.arange(n_wake_intervals)
wake_x = x_te + np.concatenate(([0.0], np.cumsum(wake_dx)))
wake_x[-1] = x_out

wake_center = np.column_stack([
    wake_x,
    np.zeros(n_wake)
])

# Upper inner path: split upper -> TE -> shared wake centreline -> outlet
upper_inner = np.vstack([
    upper_airfoil,
    wake_center[1:]
])

# Lower inner path: split lower -> TE -> shared wake centreline -> outlet
lower_inner = np.vstack([
    lower_airfoil,
    wake_center[1:]
])

# Upper/lower farfield corresponding paths
upper_outer = np.column_stack([
    upper_inner[:, 0],
    np.full(upper_inner.shape[0], y_top)
])

lower_outer = np.column_stack([
    lower_inner[:, 0],
    np.full(lower_inner.shape[0], y_bottom)
])

# ============================================================
# Node and element storage
# ============================================================

nodes = []
node_map = {}

line_elements = []
tri_elements = []
quad_elements = []


def add_node(x, y, z=0.0, tol=12):
    key = (round(float(x), tol), round(float(y), tol), round(float(z), tol))
    if key in node_map:
        return node_map[key]
    nid = len(nodes) + 1
    node_map[key] = nid
    nodes.append((float(x), float(y), float(z)))
    return nid


def node_xy(nid):
    x, y, _ = nodes[nid - 1]
    return np.array([x, y])


def quad_area(ids):
    pts = np.array([node_xy(i) for i in ids])
    x = pts[:, 0]
    y = pts[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - y * np.roll(x, -1))


def tri_area(ids):
    pts = np.array([node_xy(i) for i in ids])
    x1, y1 = pts[0]
    x2, y2 = pts[1]
    x3, y3 = pts[2]
    return 0.5 * ((x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1))


def add_tri(n1, n2, n3):
    ids = [n1, n2, n3]
    if tri_area(ids) < 0:
        ids = [n1, n3, n2]
    # Skip accidental zero-area triangles
    if abs(tri_area(ids)) > 1.0e-18:
        tri_elements.append((TAG_FLUID, *ids))


def add_quad(n1, n2, n3, n4):
    ids = [n1, n2, n3, n4]
    if quad_area(ids) < 0:
        ids = [n1, n4, n3, n2]
    # Skip accidental degenerate quads
    if abs(quad_area(ids)) > 1.0e-18:
        quad_elements.append((TAG_FLUID, *ids))


def add_boundary_lines(tag, ids):
    for a, b in zip(ids[:-1], ids[1:]):
        if a != b:
            line_elements.append((tag, a, b))


def make_block(inner, outer, n_radial):
    """
    Creates a structured block between inner and outer curves.
    inner and outer must have same number of points.
    j = 0 is inner, j = n_radial-1 is outer.
    """
    assert inner.shape == outer.shape

    grid = np.zeros((inner.shape[0], n_radial), dtype=int)

    for i in range(inner.shape[0]):
        pi = inner[i]
        po = outer[i]

        # V5 near-wake relaxation:
        # Preserve the original y+-target clustering on the airfoil
        # and exactly at the sharp trailing edge.
        # Relax rapidly through the near wake, reaching the relaxed
        # growth factor by x/c = 3.0, then keep it constant downstream.
        x_relax_end = 2.0

        if pi[0] <= x_te:
            local_growth = growth_radial
        else:
            s = (pi[0] - x_te) / (x_relax_end - x_te)
            s = np.clip(s, 0.0, 1.0)

            # Smoothstep gives zero slope at both ends of the transition.
            s_smooth = s * s * (3.0 - 2.0 * s)

            local_growth = (
                growth_radial
                + (growth_wake_out - growth_radial) * s_smooth
            )

        eta = radial_eta(n_radial, local_growth)

        for j in range(n_radial):
            e = eta[j]
            p = (1.0 - e) * pi + e * po
            grid[i, j] = add_node(p[0], p[1])

    for i in range(inner.shape[0] - 1):
        for j in range(n_radial - 1):
            add_quad(
                grid[i, j],
                grid[i + 1, j],
                grid[i + 1, j + 1],
                grid[i, j + 1],
            )

    return grid


def make_buffer_block(inner_ids, outer_curve, n_layers):
    """
    Create a structured outer buffer attached conformally to an
    existing boundary.

    inner_ids:
        Existing node IDs from the verified V6 outer boundary.

    outer_curve:
        Coordinates of the new far-field boundary.

    n_layers:
        Number of nodes across the buffer, including both boundaries.

    j = 0 reuses the existing V6 node IDs exactly.
    j = n_layers-1 is the new outer far-field boundary.
    """
    assert len(inner_ids) == outer_curve.shape[0]

    grid = np.zeros((len(inner_ids), n_layers), dtype=int)

    # Reuse the verified V6 interface nodes exactly.
    for i, nid in enumerate(inner_ids):
        grid[i, 0] = nid

    # Fill the new outer-buffer nodes.
    for i, nid in enumerate(inner_ids):
        pi = node_xy(nid)
        po = outer_curve[i]

        for j in range(1, n_layers):
            e = j / (n_layers - 1)
            pnt = (1.0 - e) * pi + e * po
            grid[i, j] = add_node(pnt[0], pnt[1])

    # Structured quadrilateral cells.
    for i in range(len(inner_ids) - 1):
        for j in range(n_layers - 1):
            add_quad(
                grid[i, j],
                grid[i + 1, j],
                grid[i + 1, j + 1],
                grid[i, j + 1],
            )

    return grid


def make_between_curves(curve_upper, curve_lower, n_cross):
    """
    Structured block between upper and lower curves.
    j = 0 upper, j = n_cross-1 lower.

    If the first upper/lower points coincide, this creates a small
    triangular fan from the sharp point to the first finite wake section,
    then continues with quads downstream. This avoids degenerate quads at
    a mathematically sharp trailing edge.
    """
    assert curve_upper.shape == curve_lower.shape

    grid = np.zeros((curve_upper.shape[0], n_cross), dtype=int)

    for i in range(curve_upper.shape[0]):
        pu = curve_upper[i]
        pl = curve_lower[i]
        for j in range(n_cross):
            a = j / (n_cross - 1)
            p = (1.0 - a) * pu + a * pl
            grid[i, j] = add_node(p[0], p[1])

    first_collapsed = np.linalg.norm(curve_upper[0] - curve_lower[0]) < 1.0e-14

    if first_collapsed:
        te_id = grid[0, 0]

        # Triangle fan from sharp TE point to the first finite cross-section.
        for j in range(n_cross - 1):
            add_tri(te_id, grid[1, j + 1], grid[1, j])

        start_i = 1
    else:
        start_i = 0

    for i in range(start_i, curve_upper.shape[0] - 1):
        for j in range(n_cross - 1):
            add_quad(
                grid[i, j],
                grid[i + 1, j],
                grid[i + 1, j + 1],
                grid[i, j + 1],
            )

    return grid


# ============================================================
# V8 outer far-field curves
# ============================================================

# Outer C-shaped inlet: same angular point distribution as the
# verified V6 inlet, but moved from radius 2c to radius 10c.
nose_far_outer = np.column_stack([
    x_c + r_far_outer * np.cos(theta),
    r_far_outer * np.sin(theta)
])

# Map the verified V6 top/bottom streamwise coordinates from
# x_split...x_out onto the larger x_split...x_out_outer domain.
outer_stream_s = (
    (upper_outer[:, 0] - x_split)
    / (x_out - x_split)
)

# V9: smooth streamwise transition at the C-grid/buffer junction.
# A = 0.30 is a TEST value derived from the V8 lowWeightFaces diagnosis.
# The mapping preserves both endpoints and remains monotonic.
outer_stream_transition_A = 0.30

outer_stream_f = (
    outer_stream_s
    + outer_stream_transition_A
    * outer_stream_s
    * (1.0 - outer_stream_s)**2
)

outer_stream_x = (
    x_split
    + outer_stream_f * (x_out_outer - x_split)
)

top_far_outer = np.column_stack([
    outer_stream_x,
    np.full(outer_stream_x.shape[0], y_top_outer)
])

bottom_far_outer = np.column_stack([
    outer_stream_x,
    np.full(outer_stream_x.shape[0], y_bottom_outer)
])


# ============================================================
# Build blocks
# ============================================================

# 1. Nose C-block
nose_grid = make_block(nose_inner, nose_outer, n_radial)

# 2. Upper outer block
upper_grid = make_block(upper_inner, upper_outer, n_radial)

# 3. Lower outer block
lower_grid = make_block(lower_inner, lower_outer, n_radial)

# 4. No separate wake block in V12.
# The wake centreline is shared by upper_grid and lower_grid, so it becomes internal.

# ============================================================
# V8 high-AoA outer-buffer blocks
# ============================================================

# Outer buffer around the C-shaped inlet.
nose_buffer_grid = make_buffer_block(
    list(nose_grid[:, -1]),
    nose_far_outer,
    n_outer_radial,
)

# Outer buffer above the verified V6 domain.
top_buffer_grid = make_buffer_block(
    list(upper_grid[:, -1]),
    top_far_outer,
    n_outer_radial,
)

# Outer buffer below the verified V6 domain.
bottom_buffer_grid = make_buffer_block(
    list(lower_grid[:, -1]),
    bottom_far_outer,
    n_outer_radial,
)

# Existing V6 outlet interface, ordered bottom -> top.
inner_outlet_ids = (
    list(lower_grid[-1, :])[::-1]
    + list(upper_grid[-1, :])[1:]
)

inner_outlet_xy = np.array([
    node_xy(nid) for nid in inner_outlet_ids
])

# New physical outlet at x/c = 15.
# Preserve the normalized vertical distribution of the V6 outlet
# while expanding from y = +/-2c to y = +/-10c.
outlet_far_outer = np.column_stack([
    np.full(len(inner_outlet_ids), x_out_outer),
    inner_outlet_xy[:, 1] * (y_top_outer / y_top),
])

# Downstream buffer from the old x/c = 8 interface to x/c = 15.
# Its upper/lower edges coincide exactly with the downstream edges
# of the top and bottom outer buffers.
outlet_buffer_grid = make_buffer_block(
    inner_outlet_ids,
    outlet_far_outer,
    n_outer_radial,
)


# ============================================================
# Boundary line elements
# ============================================================

# Airfoil boundary:
# split lower -> LE -> split upper
nose_airfoil_ids = list(nose_grid[:, 0])

# split upper -> TE upper
upper_airfoil_ids = list(upper_grid[:n_airfoil_upper, 0])

# No finite TE closure face in V4.
# The upper and lower airfoil curves meet at one sharp TE point.
# The wake opens behind this point using a tiny internal triangular fan.
lower_airfoil_ids = list(lower_grid[:n_airfoil_upper, 0])[::-1]

add_boundary_lines(TAG_AIRFOIL, nose_airfoil_ids)
add_boundary_lines(TAG_AIRFOIL, upper_airfoil_ids)
add_boundary_lines(TAG_AIRFOIL, lower_airfoil_ids)

# ============================================================
# V8 physical far-field boundaries
# ============================================================

# The original V6 inlet/top/bottom/outlet are now internal
# conformal interfaces between the verified V6 mesh and the
# new high-AoA outer buffer. Therefore they receive no boundary tags.

# New inlet: outer C-arc at radius 10c.
add_boundary_lines(
    TAG_INLET,
    list(nose_buffer_grid[:, -1]),
)

# New top boundary: y/c = +10.
add_boundary_lines(
    TAG_TOP,
    list(top_buffer_grid[:, -1]),
)

# New bottom boundary: y/c = -10.
add_boundary_lines(
    TAG_BOTTOM,
    list(bottom_buffer_grid[:, -1]),
)

# New outlet: x/c = 15, ordered bottom -> top.
add_boundary_lines(
    TAG_OUTLET,
    list(outlet_buffer_grid[:, -1]),
)


# ============================================================
# Diagnostics
# ============================================================

areas = []
for _, n1, n2, n3, n4 in quad_elements:
    areas.append(quad_area([n1, n2, n3, n4]))
areas = np.array(areas)

print("Structured supervisor topology mesh")
print("-----------------------------------")
print(f"Nodes: {len(nodes)}")
print(f"Triangles: {len(tri_elements)}")
print(f"Quads: {len(quad_elements)}")
print(f"Boundary lines: {len(line_elements)}")
print(f"Min quad area: {areas.min():.6e}")
print(f"Max quad area: {areas.max():.6e}")
print(f"Negative/zero area quads: {np.sum(areas <= 0)}")


# ============================================================
# Write MSH2
# ============================================================

elements = []
eid = 1

# Line elements: type 1
for tag, n1, n2 in line_elements:
    elements.append((eid, 1, tag, tag, [n1, n2]))
    eid += 1

# Triangle elements: type 2
for tag, n1, n2, n3 in tri_elements:
    elements.append((eid, 2, tag, tag, [n1, n2, n3]))
    eid += 1

# Quad elements: type 3
for tag, n1, n2, n3, n4 in quad_elements:
    elements.append((eid, 3, tag, tag, [n1, n2, n3, n4]))
    eid += 1

with out_msh.open("w") as f:
    f.write("$MeshFormat\n")
    f.write("2.2 0 8\n")
    f.write("$EndMeshFormat\n")

    f.write("$PhysicalNames\n")
    f.write("6\n")
    f.write(f'1 {TAG_AIRFOIL} "airfoil"\n')
    f.write(f'1 {TAG_TOP} "top"\n')
    f.write(f'1 {TAG_INLET} "inlet"\n')
    f.write(f'1 {TAG_BOTTOM} "bottom"\n')
    f.write(f'1 {TAG_OUTLET} "outlet"\n')
    f.write(f'2 {TAG_FLUID} "fluid"\n')
    f.write("$EndPhysicalNames\n")

    f.write("$Nodes\n")
    f.write(f"{len(nodes)}\n")
    for i, (x, y, z) in enumerate(nodes, start=1):
        f.write(f"{i} {x:.12e} {y:.12e} {z:.12e}\n")
    f.write("$EndNodes\n")

    f.write("$Elements\n")
    f.write(f"{len(elements)}\n")
    for eid, etype, phys, geom, conn in elements:
        conn_str = " ".join(str(n) for n in conn)
        f.write(f"{eid} {etype} 2 {phys} {geom} {conn_str}\n")
    f.write("$EndElements\n")

print(f"Written: {out_msh}")


# ============================================================
# Preview plot
# ============================================================

plt.figure(figsize=(15, 6))

def plot_grid(grid, every_i=8, every_j=8, lw=0.35):
    ni, nj = grid.shape
    for i in range(0, ni, every_i):
        pts = np.array([node_xy(grid[i, j]) for j in range(nj)])
        plt.plot(pts[:, 0], pts[:, 1], "k-", lw=lw)
    for j in range(0, nj, every_j):
        pts = np.array([node_xy(grid[i, j]) for i in range(ni)])
        plt.plot(pts[:, 0], pts[:, 1], "k-", lw=lw)

plot_grid(nose_grid, every_i=6, every_j=8)
plot_grid(upper_grid, every_i=10, every_j=8)
plot_grid(lower_grid, every_i=10, every_j=8)

# Topology guide lines
plt.plot([x_split, x_split], [y_bottom, y_top], "r--", lw=1.0, label="split behind LE")

plt.axis("equal")
plt.grid(True, alpha=0.25)
# plt.title("Structured NACA 0012 smooth closed-TE C-grid mesh preview")
plt.xlabel("x/c")
plt.ylabel("y/c")
plt.tight_layout()
plt.savefig(out_png, dpi=250)
plt.close()

print(f"Written: {out_png}")
print("")
print("Open with:")
print("  gmsh structured_supervisor_topology_V12_SHARED_WAKE_LINE_CGRID.msh")
