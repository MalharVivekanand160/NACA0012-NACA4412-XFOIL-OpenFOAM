import csv
import shutil
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]

AOA_EXPECTED = [
    0.0, 2.0, 4.0, 6.0, 8.0, 10.0,
    12.0, 14.0, 14.5
]

THESIS_DIR = (
    Path.home()
    / "Desktop"
    / "Final_stretch"
    / "08_THESIS_REPORT"
    / "bilder"
    / "thesis"
)

OVERLEAF_DIR = (
    Path.home()
    / "Desktop"
    / "Final_stretch"
    / "08_OVERLEAF_SOURCE"
    / "bilder"
    / "thesis"
)

THESIS_DIR.mkdir(parents=True, exist_ok=True)
OVERLEAF_DIR.mkdir(parents=True, exist_ok=True)


def load_table(path):
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        row["AoA_deg"] = float(row["AoA_deg"])

        for key in [
            "CL_SST",
            "CL_XFOIL_P240",
            "CD_SST",
            "CD_XFOIL_P240",
            "Cm_SST_raw_OpenFOAM_plusZ",
            "Cm_SST_XFOIL_sign_convention",
            "Cm_XFOIL_P240",
        ]:
            row[key] = float(row[key])

    # Final common quantitative range
    rows = [
        row for row in rows
        if row["AoA_deg"] <= 14.5
    ]

    return rows


def validate(rows, airfoil):
    aoa = [r["AoA_deg"] for r in rows]

    if aoa != AOA_EXPECTED:
        raise RuntimeError(
            f"{airfoil}: unexpected retained AoA sequence: {aoa}"
        )

    if len(rows) != 9:
        raise RuntimeError(
            f"{airfoil}: expected 9 retained rows, got {len(rows)}"
        )

    # No non-formal SST case is allowed in the retained range
    bad = [
        r for r in rows
        if r.get("SST_Status", "") ==
        "STABLE_ITERATIVE_PLATEAU_NOT_FORMAL"
    ]

    if bad:
        raise RuntimeError(
            f"{airfoil}: non-formal SST cases found in retained range: "
            f"{[r['AoA_deg'] for r in bad]}"
        )


def make_plot(
    rows,
    airfoil,
    sst_column,
    xfoil_column,
    ylabel,
    filename,
):
    aoa = [r["AoA_deg"] for r in rows]
    sst = [r[sst_column] for r in rows]
    xfoil = [r[xfoil_column] for r in rows]

    fig, ax = plt.subplots(figsize=(8.0, 5.4))

    ax.plot(
        aoa,
        sst,
        marker="o",
        linewidth=1.8,
        markersize=5.5,
        label="OpenFOAM SST",
    )

    ax.plot(
        aoa,
        xfoil,
        marker="s",
        linestyle="--",
        linewidth=1.8,
        markersize=5.0,
        label="XFOIL",
    )

    ax.set_xlabel(r"Angle of attack, $\alpha$ [deg]")
    ax.set_ylabel(ylabel)

    ax.grid(True, alpha=0.3)
    ax.legend()

    ax.set_xlim(-0.4, 14.9)
    ax.set_xticks(
        [0, 2, 4, 6, 8, 10, 12, 14]
    )

    fig.tight_layout()

    outdir = (
        ROOT
        / "06_PRIMARY_AERODYNAMIC_RESULTS"
        / airfoil
    )

    png = outdir / f"{filename}_COMMON_RANGE.png"
    pdf = outdir / f"{filename}_COMMON_RANGE.pdf"

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

    return pdf, png


def process(airfoil):

    table = (
        ROOT
        / "06_PRIMARY_AERODYNAMIC_RESULTS"
        / airfoil
        / f"{airfoil}_STAGE6_SST_vs_XFOIL_P240.csv"
    )

    rows = load_table(table)
    validate(rows, airfoil)

    cl = make_plot(
        rows,
        airfoil,
        "CL_SST",
        "CL_XFOIL_P240",
        r"$C_L$",
        f"{airfoil}_STAGE6_CL_SST_vs_XFOIL",
    )

    cd = make_plot(
        rows,
        airfoil,
        "CD_SST",
        "CD_XFOIL_P240",
        r"$C_D$",
        f"{airfoil}_STAGE6_CD_SST_vs_XFOIL",
    )

    cm = make_plot(
        rows,
        airfoil,
        "Cm_SST_XFOIL_sign_convention",
        "Cm_XFOIL_P240",
        r"$C_m$ about $x/c=0.25$"
        "\n(XFOIL sign convention)",
        f"{airfoil}_STAGE6_Cm_SST_vs_XFOIL",
    )

    return rows, cl, cd, cm


print("=" * 64)
print("STAGE 6 — FINAL COMMON-RANGE FIGURES")
print("=" * 64)

n0012, n12_cl, n12_cd, n12_cm = process("NACA0012")
n4412, n44_cl, n44_cd, n44_cm = process("NACA4412")

mapping = {
    n12_cl[0]: "cl_0012_sst_xfoil.pdf",
    n12_cd[0]: "cd_0012_sst_xfoil.pdf",
    n12_cm[0]: "cm_0012_sst_xfoil.pdf",
    n44_cl[0]: "cl_4412_sst_xfoil.pdf",
    n44_cd[0]: "cd_4412_sst_xfoil.pdf",
    n44_cm[0]: "cm_4412_sst_xfoil.pdf",
}

png_mapping = {
    n12_cl[1]: "cl_0012_sst_xfoil.png",
    n12_cd[1]: "cd_0012_sst_xfoil.png",
    n12_cm[1]: "cm_0012_sst_xfoil.png",
    n44_cl[1]: "cl_4412_sst_xfoil.png",
    n44_cd[1]: "cd_4412_sst_xfoil.png",
    n44_cm[1]: "cm_4412_sst_xfoil.png",
}

for dest in [THESIS_DIR, OVERLEAF_DIR]:
    for src, name in mapping.items():
        shutil.copy2(src, dest / name)

    for src, name in png_mapping.items():
        shutil.copy2(src, dest / name)

print()
print("Validation passed:")
print("  NACA0012:", [r["AoA_deg"] for r in n0012])
print("  NACA4412:", [r["AoA_deg"] for r in n4412])

print()
print("No stable-plateau/non-formal SST cases retained.")
print("Common quantitative endpoint = 14.5 deg")

print()
print("Copied six final PDFs + PNGs to:")
print(THESIS_DIR)
print(OVERLEAF_DIR)
