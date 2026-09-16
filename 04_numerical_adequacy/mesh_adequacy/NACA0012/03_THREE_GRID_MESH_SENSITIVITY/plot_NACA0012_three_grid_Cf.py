from pathlib import Path
import csv
import matplotlib.pyplot as plt

CSV_FILE = Path("NACA0012_AoA14_THREE_GRID_Cf.csv")

ORDER = ["COARSE", "BASELINE", "FINE"]

LABELS = {
    "COARSE": "Coarse (82,642 cells)",
    "BASELINE": "Baseline (165,220 cells)",
    "FINE": "Fine (330,750 cells)",
}

LINESTYLES = {
    "COARSE": "--",
    "BASELINE": "-",
    "FINE": "-.",
}


def load_upper_surface():
    data = {grid: [] for grid in ORDER}

    with CSV_FILE.open() as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row["surface"] != "upper":
                continue

            grid = row["grid"]

            data[grid].append(
                (
                    float(row["x_over_c"]),
                    float(row["Cf"]),
                )
            )

    for grid in ORDER:
        data[grid].sort(key=lambda p: p[0])

    return data


def find_te_connected_separation(points):
    """
    Same operational criterion used previously:
      - Cf < 0
      - at least 5 contiguous faces
      - negative region reaches x/c >= 0.95
    """

    regions = []
    current = []

    for x, cf in points:
        if cf < 0.0:
            current.append((x, cf))
        else:
            if current:
                regions.append(current)
                current = []

    if current:
        regions.append(current)

    valid = [
        region
        for region in regions
        if len(region) >= 5
        and max(x for x, _ in region) >= 0.95
    ]

    if not valid:
        return None

    region = max(valid, key=len)

    return min(x for x, _ in region)


data = load_upper_surface()

print("==============================================")
print("NACA0012 AoA14 THREE-GRID Cf")
print("==============================================")

xsep = {}

for grid in ORDER:
    xsep[grid] = find_te_connected_separation(data[grid])

    if xsep[grid] is None:
        print(f"{grid:8s}: no TE-connected separation")
    else:
        print(
            f"{grid:8s}: x_sep/c = {xsep[grid]:.6f}"
        )


# ============================================================
# FIGURE 1 — FULL CHORD
# ============================================================

fig, ax = plt.subplots(figsize=(7.2, 4.6))

for grid in ORDER:
    x = [p[0] for p in data[grid]]
    cf = [p[1] for p in data[grid]]

    ax.plot(
        x,
        cf,
        linestyle=LINESTYLES[grid],
        linewidth=1.6,
        label=LABELS[grid],
    )

ax.axhline(
    0.0,
    linestyle=":",
    linewidth=1.0,
)

ax.set_xlim(0.0, 1.0)

ax.set_xlabel(r"$x/c$")
ax.set_ylabel(r"$C_f$")

ax.set_title(
    r"NACA 0012 upper-surface $C_f$, $\alpha=14^\circ$"
)

ax.grid(True, alpha=0.25)
ax.legend()

fig.tight_layout()

fig.savefig(
    "NACA0012_AoA14_THREE_GRID_Cf_FULL.pdf",
    bbox_inches="tight",
)

fig.savefig(
    "NACA0012_AoA14_THREE_GRID_Cf_FULL.png",
    dpi=300,
    bbox_inches="tight",
)

plt.close(fig)


# ============================================================
# FIGURE 2 — TRAILING-EDGE ZOOM
# ============================================================

fig, ax = plt.subplots(figsize=(7.2, 4.6))

for grid in ORDER:
    points = [
        (x, cf)
        for x, cf in data[grid]
        if x >= 0.82
    ]

    x = [p[0] for p in points]
    cf = [p[1] for p in points]

    ax.plot(
        x,
        cf,
        linestyle=LINESTYLES[grid],
        linewidth=1.7,
        label=LABELS[grid],
    )

    if xsep[grid] is not None:
        ax.axvline(
            xsep[grid],
            linestyle=":",
            linewidth=0.9,
        )

ax.axhline(
    0.0,
    linestyle=":",
    linewidth=1.0,
)

ax.set_xlim(0.82, 1.0)

ax.set_xlabel(r"$x/c$")
ax.set_ylabel(r"$C_f$")

ax.set_title(
    r"NACA 0012 upper-surface $C_f$: trailing-edge region, "
    r"$\alpha=14^\circ$"
)

ax.grid(True, alpha=0.25)
ax.legend()

fig.tight_layout()

fig.savefig(
    "NACA0012_AoA14_THREE_GRID_Cf_TE_ZOOM.pdf",
    bbox_inches="tight",
)

fig.savefig(
    "NACA0012_AoA14_THREE_GRID_Cf_TE_ZOOM.png",
    dpi=300,
    bbox_inches="tight",
)

plt.close(fig)


print()
print("Created:")
for name in [
    "NACA0012_AoA14_THREE_GRID_Cf_FULL.pdf",
    "NACA0012_AoA14_THREE_GRID_Cf_FULL.png",
    "NACA0012_AoA14_THREE_GRID_Cf_TE_ZOOM.pdf",
    "NACA0012_AoA14_THREE_GRID_Cf_TE_ZOOM.png",
]:
    print(Path(name).resolve())

print("==============================================")
