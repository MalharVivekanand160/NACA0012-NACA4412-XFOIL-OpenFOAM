from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


HERE = Path(__file__).resolve().parent

THESIS_DIR = (
    Path.home()
    / "Desktop"
    / "Final_stretch"
    / "08_THESIS_REPORT"
    / "bilder"
    / "thesis"
)

THESIS_DIR.mkdir(parents=True, exist_ok=True)


def read_surface_csv(path):
    data = np.genfromtxt(
        path,
        delimiter=",",
        names=True,
        dtype=None,
        encoding="utf-8",
    )

    x = np.asarray(data["x_over_c"], dtype=float)
    cp = np.asarray(data["Cp"], dtype=float)
    surface = np.asarray(data["surface"])

    upper = surface == "upper"
    lower = surface == "lower"

    xu = x[upper]
    cpu = cp[upper]

    xl = x[lower]
    cpl = cp[lower]

    iu = np.argsort(xu)
    il = np.argsort(xl)

    return (
        xu[iu],
        cpu[iu],
        xl[il],
        cpl[il],
    )


def make_plot(aoa):
    tag = f"{aoa:02d}"

    xfoil_file = HERE / f"NACA4412_XFOIL_AoA{tag}_Cp_airfoil.csv"
    openfoam_file = HERE / f"NACA4412_V9_SST_AoA{tag}_Cp_airfoil.csv"

    xu_xf, cpu_xf, xl_xf, cpl_xf = read_surface_csv(xfoil_file)
    xu_of, cpu_of, xl_of, cpl_of = read_surface_csv(openfoam_file)

    fig, ax = plt.subplots(figsize=(7.6, 4.8))

    ax.plot(
        xu_xf,
        cpu_xf,
        linewidth=1.7,
        label="XFOIL upper",
    )

    ax.plot(
        xl_xf,
        cpl_xf,
        linewidth=1.7,
        label="XFOIL lower",
    )

    ax.plot(
        xu_of,
        cpu_of,
        linewidth=1.7,
        linestyle="--",
        label="OpenFOAM SST upper",
    )

    ax.plot(
        xl_of,
        cpl_of,
        linewidth=1.7,
        linestyle="--",
        label="OpenFOAM SST lower",
    )

    ax.set_xlabel(r"$x/c$")
    ax.set_ylabel(r"$C_p$")

    # Conventional aerodynamic Cp presentation:
    # stronger suction appears higher on the graph.
    ax.invert_yaxis()

    ax.set_xlim(0.0, 1.0)

    ax.grid(True, alpha=0.25)
    ax.legend(frameon=True)

    # Intentionally no embedded title.
    fig.tight_layout()

    local_pdf = HERE / f"NACA4412_AoA{tag}_Cp_CLEAN.pdf"
    local_png = HERE / f"NACA4412_AoA{tag}_Cp_CLEAN.png"

    thesis_pdf = THESIS_DIR / f"cp_4412_aoa{tag}.pdf"

    fig.savefig(local_pdf, bbox_inches="tight")
    fig.savefig(local_png, dpi=300, bbox_inches="tight")
    fig.savefig(thesis_pdf, bbox_inches="tight")

    plt.close(fig)

    print(f"AoA {aoa:2d} deg")
    print(f"  XFOIL upper/lower points: {len(xu_xf)} / {len(xl_xf)}")
    print(f"  OpenFOAM upper/lower faces: {len(xu_of)} / {len(xl_of)}")
    print(f"  Created: {local_pdf}")
    print(f"  Created: {local_png}")
    print(f"  Thesis:  {thesis_pdf}")
    print()


for aoa in (0, 16):
    make_plot(aoa)

print("Finished generating clean NACA4412 Cp thesis figures.")
