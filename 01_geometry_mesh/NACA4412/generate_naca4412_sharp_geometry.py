#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# Final sharp-trailing-edge NACA 4412 geometry
#
# NACA 4412:
#   m = 0.04  maximum camber
#   p = 0.40  location of maximum camber
#   t = 0.12  maximum thickness
#
# Closed-TE thickness coefficient:
#   -0.1036
#
# Outputs:
#   naca4412_sharp_te_coordinates.dat
#   naca4412_sharp_te_geometry.png
#   NACA4412_SHARP_TE_GEOMETRY_SUMMARY.txt
# ============================================================

m = 0.04
p = 0.40
t = 0.12

# Number of points on each surface, including LE and TE.
n_surface = 161

out_dat = Path("naca4412_sharp_te_coordinates.dat")
out_png = Path("naca4412_sharp_te_geometry.png")
out_summary = Path("NACA4412_SHARP_TE_GEOMETRY_SUMMARY.txt")


def naca4_thickness(xc, thickness):
    """Closed-trailing-edge NACA 4-digit thickness distribution."""
    xc = np.asarray(xc, dtype=float)

    return 5.0 * thickness * (
        0.2969 * np.sqrt(xc)
        - 0.1260 * xc
        - 0.3516 * xc**2
        + 0.2843 * xc**3
        - 0.1036 * xc**4
    )


def naca4_camber(xc, maximum_camber, camber_position):
    """Mean camber line and derivative for a NACA 4-digit airfoil."""
    xc = np.asarray(xc, dtype=float)

    yc = np.empty_like(xc)
    dyc_dx = np.empty_like(xc)

    forward = xc <= camber_position
    rearward = ~forward

    yc[forward] = (
        maximum_camber
        / camber_position**2
        * (
            2.0 * camber_position * xc[forward]
            - xc[forward]**2
        )
    )

    dyc_dx[forward] = (
        2.0
        * maximum_camber
        / camber_position**2
        * (camber_position - xc[forward])
    )

    yc[rearward] = (
        maximum_camber
        / (1.0 - camber_position)**2
        * (
            1.0
            - 2.0 * camber_position
            + 2.0 * camber_position * xc[rearward]
            - xc[rearward]**2
        )
    )

    dyc_dx[rearward] = (
        2.0
        * maximum_camber
        / (1.0 - camber_position)**2
        * (camber_position - xc[rearward])
    )

    return yc, dyc_dx


def naca4412_surface_points(xc):
    """Return upper and lower sharp-TE NACA4412 surface coordinates."""
    xc = np.asarray(xc, dtype=float)

    yt = naca4_thickness(xc, t)
    yc, dyc_dx = naca4_camber(xc, m, p)

    theta = np.arctan(dyc_dx)

    xu = xc - yt * np.sin(theta)
    yu = yc + yt * np.cos(theta)

    xl = xc + yt * np.sin(theta)
    yl = yc - yt * np.cos(theta)

    upper = np.column_stack([xu, yu])
    lower = np.column_stack([xl, yl])

    return upper, lower


# Cosine spacing gives strong resolution near LE and TE.
beta = np.linspace(0.0, np.pi, n_surface)
xc = 0.5 * (1.0 - np.cos(beta))

upper, lower = naca4412_surface_points(xc)

# Enforce exact mathematical closure at LE and TE.
upper[0] = [0.0, 0.0]
lower[0] = [0.0, 0.0]

upper[-1] = [1.0, 0.0]
lower[-1] = [1.0, 0.0]

# XFOIL-style ordering:
# upper TE -> LE, then lower LE -> TE.
coordinates = np.vstack([
    upper[::-1],
    lower[1:]
])

np.savetxt(
    out_dat,
    coordinates,
    fmt="% .10f % .10f"
)

te_gap = np.linalg.norm(upper[-1] - lower[-1])
le_gap = np.linalg.norm(upper[0] - lower[0])

summary = f"""NACA4412 FINAL SHARP-TE GEOMETRY

NACA parameters:
m = {m:.6f}
p = {p:.6f}
t = {t:.6f}

Closed-TE thickness coefficient = -0.1036

Points per surface = {n_surface}
Total exported coordinate points = {len(coordinates)}

Leading edge:
upper = ({upper[0,0]:.10f}, {upper[0,1]:.10f})
lower = ({lower[0,0]:.10f}, {lower[0,1]:.10f})
LE gap = {le_gap:.12e}

Trailing edge:
upper = ({upper[-1,0]:.10f}, {upper[-1,1]:.10f})
lower = ({lower[-1,0]:.10f}, {lower[-1,1]:.10f})
TE gap = {te_gap:.12e}

Geometry status:
SHARP/CLOSED TRAILING EDGE
"""

out_summary.write_text(summary)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(coordinates[:, 0], coordinates[:, 1], "-", linewidth=1.2)
ax.set_aspect("equal", adjustable="box")
ax.set_xlabel("x/c")
ax.set_ylabel("y/c")
ax.set_title("NACA 4412 — Final Sharp-Trailing-Edge Geometry")
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(out_png, dpi=300)
plt.close(fig)

print(summary)
print("Created:")
print(" ", out_dat)
print(" ", out_png)
print(" ", out_summary)
