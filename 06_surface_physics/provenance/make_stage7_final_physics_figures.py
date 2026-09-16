from pathlib import Path
import csv
import matplotlib.pyplot as plt

ROOT = Path("07_SURFACE_PHYSICS_AND_SEPARATION")

# ============================================================
# 1. NACA4412 REPRESENTATIVE UPPER-SURFACE Cf
# ============================================================

cf_dir = ROOT / "NACA4412" / "02_Cf_AND_SEPARATION"

cases = [
    ("00", 0.0),
    ("06", 6.0),
    ("12", 12.0),
    ("16", 16.0),
]

fig, ax = plt.subplots(figsize=(8, 5))

for tag, aoa in cases:
    path = cf_dir / f"NACA4412_V9_SST_AoA{tag}_Cf_airfoil.csv"

    x = []
    cf = []

    with path.open() as f:
        for r in csv.DictReader(f):
            if r["surface"] != "upper":
                continue
            x.append(float(r["x_over_c"]))
            cf.append(float(r["Cf"]))

    pts = sorted(zip(x, cf))

    ax.plot(
        [p[0] for p in pts],
        [p[1] for p in pts],
        label=rf"$\alpha={aoa:g}^\circ$",
        linewidth=1.4,
    )

ax.axhline(0.0, linestyle="--", linewidth=1.0)
ax.set_xlim(0, 1)
ax.set_xlabel(r"$x/c$")
ax.set_ylabel(r"Signed upper-surface $C_f$")
ax.set_title("NACA 4412 Upper-Surface Skin-Friction Distribution")
ax.grid(True, alpha=0.3)
ax.legend()
fig.tight_layout()

fig.savefig(
    cf_dir / "NACA4412_STAGE7_upper_surface_Cf_representative.png",
    dpi=300,
)
fig.savefig(
    cf_dir / "NACA4412_STAGE7_upper_surface_Cf_representative.pdf"
)
plt.close(fig)


# ============================================================
# 2. NACA4412 AFT-CHORD Cf ZOOM
# ============================================================

fig, ax = plt.subplots(figsize=(8, 5))

for tag, aoa in cases:
    path = cf_dir / f"NACA4412_V9_SST_AoA{tag}_Cf_airfoil.csv"

    pts = []

    with path.open() as f:
        for r in csv.DictReader(f):
            if r["surface"] != "upper":
                continue

            xv = float(r["x_over_c"])

            if xv >= 0.60:
                pts.append((xv, float(r["Cf"])))

    pts.sort()

    ax.plot(
        [p[0] for p in pts],
        [p[1] for p in pts],
        label=rf"$\alpha={aoa:g}^\circ$",
        linewidth=1.4,
    )

ax.axhline(0.0, linestyle="--", linewidth=1.0)
ax.set_xlim(0.60, 1.0)
ax.set_xlabel(r"$x/c$")
ax.set_ylabel(r"Signed upper-surface $C_f$")
ax.set_title("NACA 4412 Aft-Chord Skin Friction")
ax.grid(True, alpha=0.3)
ax.legend()
fig.tight_layout()

fig.savefig(
    cf_dir / "NACA4412_STAGE7_upper_surface_Cf_AFT_ZOOM.png",
    dpi=300,
)
fig.savefig(
    cf_dir / "NACA4412_STAGE7_upper_surface_Cf_AFT_ZOOM.pdf"
)
plt.close(fig)


# ============================================================
# 3. NACA4412 SEPARATION LOCATION VS AoA
# ============================================================

summary = cf_dir / "NACA4412_V9_SST_Cf_SEPARATION_SUMMARY.csv"

aoa = []
xsep = []

with summary.open() as f:
    for r in csv.DictReader(f):

        if r["surface"] != "upper":
            continue

        val = r["TE_connected_sep_x_over_c"].strip()

        if not val:
            continue

        aoa.append(float(r["AoA_deg"]))
        xsep.append(float(val))

fig, ax = plt.subplots(figsize=(8, 5))

ax.plot(
    aoa,
    xsep,
    marker="o",
    linewidth=1.5,
)

ax.set_xlabel(r"Angle of attack, $\alpha$ [deg]")
ax.set_ylabel(r"Start of TE-connected separation, $x_{\rm sep}/c$")
ax.set_title("NACA 4412 Upstream Progression of TE-Connected Separation")
ax.set_ylim(1.0, 0.60)
ax.grid(True, alpha=0.3)

fig.tight_layout()

fig.savefig(
    cf_dir / "NACA4412_STAGE7_separation_location_vs_AoA.png",
    dpi=300,
)
fig.savefig(
    cf_dir / "NACA4412_STAGE7_separation_location_vs_AoA.pdf"
)
plt.close(fig)


# ============================================================
# 4. PRESSURE-DRAG FRACTION — BOTH AIRFOILS
# ============================================================

n12_file = (
    ROOT
    / "NACA0012"
    / "03_DRAG_DECOMPOSITION"
    / "NACA0012_V9_DRAG_DECOMPOSITION.csv"
)

n44_file = (
    ROOT
    / "NACA4412"
    / "03_DRAG_DECOMPOSITION"
    / "NACA4412_V9_SST_DRAG_DECOMPOSITION_STAGE7_CORRECTED.csv"
)

n12_a = []
n12_p = []

with n12_file.open() as f:
    for r in csv.DictReader(f):
        n12_a.append(float(r["AoA_deg"]))
        n12_p.append(float(r["CD_pressure_pct_of_total"]))

n44_a = []
n44_p = []

with n44_file.open() as f:
    for r in csv.DictReader(f):
        n44_a.append(float(r["AoA_deg"]))
        n44_p.append(float(r["pressure_drag_percent_snapshot"]))

fig, ax = plt.subplots(figsize=(8, 5))

ax.plot(
    n12_a,
    n12_p,
    marker="o",
    linewidth=1.5,
    label="NACA 0012 SST",
)

ax.plot(
    n44_a,
    n44_p,
    marker="s",
    linewidth=1.5,
    label="NACA 4412 SST",
)

ax.set_xlabel(r"Angle of attack, $\alpha$ [deg]")
ax.set_ylabel("Pressure drag contribution [% of total drag]")
ax.set_title("Pressure-Drag Dominance with Increasing Angle of Attack")
ax.set_xlim(0, 16)
ax.set_ylim(0, 100)
ax.grid(True, alpha=0.3)
ax.legend()

fig.tight_layout()

out = ROOT / "STAGE7_PRESSURE_DRAG_FRACTION_COMPARISON"

fig.savefig(out.with_suffix(".png"), dpi=300)
fig.savefig(out.with_suffix(".pdf"))
plt.close(fig)


print("Created final Stage-7 physics figures.")
