import csv
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUTROOT = ROOT / "reproduced"

AOA_EXPECTED = [
    0.0, 2.0, 4.0, 6.0, 8.0, 10.0,
    12.0, 14.0, 14.5
]


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
    ax.set_xticks([0, 2, 4, 6, 8, 10, 12, 14])

    fig.tight_layout()

    outdir = OUTROOT / airfoil
    outdir.mkdir(parents=True, exist_ok=True)

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
        / airfoil
        / f"{airfoil}_STAGE6_SST_vs_XFOIL_P240.csv"
    )

    rows = load_table(table)
    validate(rows, airfoil)

    make_plot(
        rows,
        airfoil,
        "CL_SST",
        "CL_XFOIL_P240",
        r"$C_L$",
        f"{airfoil}_STAGE6_CL_SST_vs_XFOIL",
    )

    make_plot(
        rows,
        airfoil,
        "CD_SST",
        "CD_XFOIL_P240",
        r"$C_D$",
        f"{airfoil}_STAGE6_CD_SST_vs_XFOIL",
    )

    make_plot(
        rows,
        airfoil,
        "Cm_SST_XFOIL_sign_convention",
        "Cm_XFOIL_P240",
        r"$C_m$ about $x/c=0.25$"
        "\n(XFOIL sign convention)",
        f"{airfoil}_STAGE6_Cm_SST_vs_XFOIL",
    )

    return rows


print("=" * 64)
print("REPOSITORY — PRIMARY COMMON-RANGE FIGURES")
print("=" * 64)

n0012 = process("NACA0012")
n4412 = process("NACA4412")

print()
print("Validation passed:")
print("  NACA0012:", [r["AoA_deg"] for r in n0012])
print("  NACA4412:", [r["AoA_deg"] for r in n4412])
print()
print("Common quantitative endpoint = 14.5 deg")
print("Outputs:", OUTROOT)
