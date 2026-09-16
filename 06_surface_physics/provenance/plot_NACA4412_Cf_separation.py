from pathlib import Path
import csv
import matplotlib.pyplot as plt

ROOT = Path(".")
OUT = ROOT / "CF_SEPARATION_PLOTS"
OUT.mkdir(exist_ok=True)

CASES = [
    ("00",   0.0),
    ("02",   2.0),
    ("04",   4.0),
    ("06",   6.0),
    ("08",   8.0),
    ("10",  10.0),
    ("12",  12.0),
    ("14",  14.0),
    ("14p5",14.5),
    ("15",  15.0),
    ("15p5",15.5),
    ("16",  16.0),
]

REP = [
    ("00", 0.0),
    ("06", 6.0),
    ("12", 12.0),
    ("14", 14.0),
    ("16", 16.0),
]


def read_cf(tag):
    path = ROOT / (
        "NACA4412_V9_SST_AoA{}_Cf_airfoil.csv".format(tag)
    )

    rows = []

    with path.open() as f:
        reader = csv.DictReader(f)

        for r in reader:
            if r["surface"] != "upper":
                continue

            rows.append((
                float(r["x_over_c"]),
                float(r["Cf"]),
            ))

    rows.sort()

    return rows


# ============================================================
# 1. Representative upper-surface Cf
# ============================================================

fig, ax = plt.subplots(figsize=(7.4, 5.2))

for tag, aoa in REP:
    pts = read_cf(tag)

    ax.plot(
        [p[0] for p in pts],
        [p[1] for p in pts],
        label=r"$\alpha={:.0f}^\circ$".format(aoa),
    )

ax.axhline(0.0, linewidth=1.0)

ax.set_xlim(0.0, 1.0)
ax.set_xlabel("$x/c$")
ax.set_ylabel("$C_f$")
ax.set_title("NACA4412 SST: upper-surface skin friction")
ax.grid(True, alpha=0.3)
ax.legend()

fig.tight_layout()

fig.savefig(
    OUT / "NACA4412_upper_surface_Cf_representative.png",
    dpi=300,
)

fig.savefig(
    OUT / "NACA4412_upper_surface_Cf_representative.pdf"
)

plt.close(fig)


# ============================================================
# 2. Aft-chord zoom
# ============================================================

fig, ax = plt.subplots(figsize=(7.4, 5.2))

for tag, aoa in [
    ("06", 6.0),
    ("08", 8.0),
    ("10",10.0),
    ("12",12.0),
    ("14",14.0),
    ("16",16.0),
]:
    pts = read_cf(tag)

    pts = [
        p for p in pts
        if p[0] >= 0.60
    ]

    ax.plot(
        [p[0] for p in pts],
        [p[1] for p in pts],
        label=r"$\alpha={:.0f}^\circ$".format(aoa),
    )

ax.axhline(0.0, linewidth=1.0)

ax.set_xlim(0.60, 1.0)
ax.set_xlabel("$x/c$")
ax.set_ylabel("$C_f$")
ax.set_title("NACA4412 SST: upper-surface aft-chord $C_f$")
ax.grid(True, alpha=0.3)
ax.legend()

fig.tight_layout()

fig.savefig(
    OUT / "NACA4412_upper_surface_Cf_AFT_ZOOM.png",
    dpi=300,
)

fig.savefig(
    OUT / "NACA4412_upper_surface_Cf_AFT_ZOOM.pdf"
)

plt.close(fig)


# ============================================================
# 3. Separation location versus AoA
# ============================================================

summary = ROOT / "NACA4412_V9_SST_Cf_SEPARATION_SUMMARY.csv"

sep = []

with summary.open() as f:
    reader = csv.DictReader(f)

    for r in reader:
        if r["surface"] != "upper":
            continue

        val = r["TE_connected_sep_x_over_c"].strip()

        if val:
            sep.append((
                float(r["AoA_deg"]),
                float(val),
                int(r["TE_connected_negative_faces"]),
            ))

fig, ax = plt.subplots(figsize=(7.0, 5.0))

ax.plot(
    [p[0] for p in sep],
    [p[1] for p in sep],
    marker="o",
)

for aoa, xsep, nfaces in sep:
    ax.annotate(
        "{} faces".format(nfaces),
        (aoa, xsep),
        xytext=(5, 5),
        textcoords="offset points",
        fontsize=8,
    )

ax.set_xlabel("Angle of attack, $\\alpha$ [deg]")
ax.set_ylabel("Start of TE-connected reversed flow, $x/c$")
ax.set_title("NACA4412 SST: upstream progression of separation")
ax.set_ylim(0.60, 1.01)
ax.grid(True, alpha=0.3)

fig.tight_layout()

fig.savefig(
    OUT / "NACA4412_separation_location_vs_AoA.png",
    dpi=300,
)

fig.savefig(
    OUT / "NACA4412_separation_location_vs_AoA.pdf"
)

plt.close(fig)


print("Created:")
for p in sorted(OUT.glob("*.png")):
    print(" ", p)
