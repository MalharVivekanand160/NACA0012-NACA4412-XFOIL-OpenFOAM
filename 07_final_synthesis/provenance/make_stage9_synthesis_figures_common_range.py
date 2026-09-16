from pathlib import Path
import csv
import shutil
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
CSV = ROOT / "STAGE9_PRIMARY_AIRFOIL_SYNTHESIS.csv"

THESIS_DIR = (
    Path.home()
    / "Desktop/Final_stretch/08_THESIS_REPORT/bilder/thesis"
)

OVERLEAF_DIR = (
    Path.home()
    / "Desktop/Final_stretch/08_OVERLEAF_SOURCE/bilder/thesis"
)

THESIS_DIR.mkdir(parents=True, exist_ok=True)
OVERLEAF_DIR.mkdir(parents=True, exist_ok=True)

with CSV.open(newline="") as f:
    rows = list(csv.DictReader(f))

# Final common quantitative range
rows = [
    r for r in rows
    if float(r["AoA_deg"]) <= 14.5
]

aoa = [float(r["AoA_deg"]) for r in rows]

expected = [0, 2, 4, 6, 8, 10, 12, 14, 14.5]

if aoa != expected:
    raise RuntimeError(f"Unexpected AoA sequence: {aoa}")

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


def save_and_copy(fig, stem, thesis_name):
    fig.tight_layout()

    png = ROOT / f"{stem}.png"
    pdf = ROOT / f"{stem}.pdf"

    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")

    plt.close(fig)

    for dest in [THESIS_DIR, OVERLEAF_DIR]:
        shutil.copy2(pdf, dest / f"{thesis_name}.pdf")
        shutil.copy2(png, dest / f"{thesis_name}.png")


# ============================================================
# 1. Aerodynamic efficiency
# ============================================================

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

save_and_copy(
    fig,
    "STAGE9_L_OVER_D_COMMON_RANGE",
    "l_over_d_comparison",
)


# ============================================================
# 2. Pressure-drag fraction
# ============================================================

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
ax.set_ylabel("Pressure drag contribution [% of total drag]")
ax.set_xlim(-0.4, 14.9)
ax.set_xticks([0, 2, 4, 6, 8, 10, 12, 14])
ax.grid(True, alpha=0.3)
ax.legend()

save_and_copy(
    fig,
    "STAGE9_PRESSURE_DRAG_COMMON_RANGE",
    "pressure_drag_fraction",
)


# ============================================================
# 3. Sustained TE-connected separation
# ============================================================

# Verified NACA 0012 Stage-7 separation results.
sep12_aoa = [14.0, 14.5]
sep12_x = [0.924, 0.908]

# NACA 4412 formally converged values from the synthesis dataset.
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
ax.set_ylabel(r"Separation start, $x_{\mathrm{sep}}/c$")
ax.set_xlim(5.5, 14.9)
ax.set_ylim(1.01, 0.70)
ax.set_xticks([6, 8, 10, 12, 14])
ax.grid(True, alpha=0.3)
ax.legend()

save_and_copy(
    fig,
    "STAGE9_SEPARATION_COMMON_RANGE",
    "separation_comparison",
)


print("=" * 68)
print("FINAL STAGE-9 COMMON-RANGE FIGURES COMPLETE")
print("=" * 68)

print()
print("AoA range:", aoa)

print()
print("L/D at 14.5 deg:")
print("  NACA0012 =", ld12[-1])
print("  NACA4412 =", ld44[-1])

print()
print("Pressure-drag fraction at 14.5 deg:")
print("  NACA0012 =", pd12[-1])
print("  NACA4412 =", pd44[-1])

print()
print("Separation:")
print("  NACA0012:", list(zip(sep12_aoa, sep12_x)))
print("  NACA4412:", list(zip(sep44_aoa, sep44_x)))

print()
print("Copied to:")
print(THESIS_DIR)
print(OVERLEAF_DIR)
