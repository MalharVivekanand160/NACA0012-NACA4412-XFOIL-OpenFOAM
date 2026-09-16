from pathlib import Path
import csv

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
CSV = ROOT / "STAGE9_PRIMARY_AIRFOIL_SYNTHESIS.csv"
OUTDIR = ROOT / "reproduced"

OUTDIR.mkdir(parents=True, exist_ok=True)

with CSV.open(newline="") as f:
    rows = list(csv.DictReader(f))

rows = [
    r for r in rows
    if float(r["AoA_deg"]) <= 14.5
]

aoa = [float(r["AoA_deg"]) for r in rows]

expected = [
    0, 2, 4, 6, 8, 10, 12, 14, 14.5
]

if aoa != expected:
    raise RuntimeError(
        f"Unexpected AoA sequence: {aoa}"
    )

ld12 = [
    float(r["NACA0012_L_over_D_SST"])
    for r in rows
]

ld44 = [
    float(r["NACA4412_L_over_D_SST"])
    for r in rows
]

pd12 = [
    float(r["NACA0012_pressure_drag_percent"])
    for r in rows
]

pd44 = [
    float(r["NACA4412_pressure_drag_percent_snapshot"])
    for r in rows
]


def save(fig, stem):
    fig.tight_layout()

    png = OUTDIR / f"{stem}.png"
    pdf = OUTDIR / f"{stem}.pdf"

    fig.savefig(
        png,
        dpi=300,
        bbox_inches="tight",
    )

    fig.savefig(
        pdf,
        bbox_inches="tight",
    )

    plt.close(fig)


# ------------------------------------------------------------
# Aerodynamic efficiency
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.2, 5.0))

ax.plot(
    aoa,
    ld12,
    marker="o",
    label="NACA 0012 — SST",
)

ax.plot(
    aoa,
    ld44,
    marker="s",
    label="NACA 4412 — SST",
)

ax.set_xlabel(r"Angle of attack, $\alpha$ [deg]")
ax.set_ylabel(r"$C_L/C_D$")
ax.set_xlim(-0.4, 14.9)
ax.set_xticks([0, 2, 4, 6, 8, 10, 12, 14])
ax.grid(True, alpha=0.3)
ax.legend()

save(
    fig,
    "STAGE9_L_OVER_D_COMMON_RANGE",
)


# ------------------------------------------------------------
# Pressure-drag fraction
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.2, 5.0))

ax.plot(
    aoa,
    pd12,
    marker="o",
    label="NACA 0012",
)

ax.plot(
    aoa,
    pd44,
    marker="s",
    label="NACA 4412",
)

ax.set_xlabel(r"Angle of attack, $\alpha$ [deg]")
ax.set_ylabel(
    "Pressure drag contribution [% of total drag]"
)
ax.set_xlim(-0.4, 14.9)
ax.set_xticks([0, 2, 4, 6, 8, 10, 12, 14])
ax.grid(True, alpha=0.3)
ax.legend()

save(
    fig,
    "STAGE9_PRESSURE_DRAG_COMMON_RANGE",
)


# ------------------------------------------------------------
# Sustained TE-connected separation
# ------------------------------------------------------------
sep12_aoa = [14.0, 14.5]
sep12_x = [0.924, 0.908]

sep44_aoa = []
sep44_x = []

for r in rows:
    x = r["NACA4412_sep_x_over_c"].strip()

    if x:
        sep44_aoa.append(float(r["AoA_deg"]))
        sep44_x.append(float(x))

fig, ax = plt.subplots(figsize=(7.2, 5.0))

ax.plot(
    sep44_aoa,
    sep44_x,
    marker="s",
    label="NACA 4412",
)

ax.plot(
    sep12_aoa,
    sep12_x,
    marker="o",
    label="NACA 0012",
)

ax.set_xlabel(r"Angle of attack, $\alpha$ [deg]")
ax.set_ylabel(
    r"Separation start, $x_{\mathrm{sep}}/c$"
)
ax.set_xlim(5.5, 14.9)
ax.set_ylim(1.01, 0.70)
ax.set_xticks([6, 8, 10, 12, 14])
ax.grid(True, alpha=0.3)
ax.legend()

save(
    fig,
    "STAGE9_SEPARATION_COMMON_RANGE",
)

print("=" * 68)
print("REPOSITORY — FINAL COMMON-RANGE SYNTHESIS")
print("=" * 68)
print()
print("AoA range:", aoa)
print("Outputs:", OUTDIR)
