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


def read_xfoil(path):
    data = np.loadtxt(path, comments="#")

    x = data[:, 0]
    cp = data[:, 1]

    i_le = np.argmin(x)

    return (
        x[:i_le + 1],
        cp[:i_le + 1],
        x[i_le:],
        cp[i_le:],
    )


def read_openfoam(path):
    data = np.genfromtxt(
        path,
        delimiter=",",
        names=True,
        dtype=None,
        encoding="utf-8",
    )

    x = np.asarray(data["x_over_c"], dtype=float)
    y = np.asarray(data["y_over_c"], dtype=float)
    cp = np.asarray(data["Cp"], dtype=float)

    upper = y >= 0.0
    lower = y < 0.0

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

    xfoil_file = HERE / f"Cp_AoA{tag}.txt"
    openfoam_file = HERE / f"OpenFOAM_V9_Cp_AoA{tag}.csv"

    xu_xf, cpu_xf, xl_xf, cpl_xf = read_xfoil(xfoil_file)
    xu_of, cpu_of, xl_of, cpl_of = read_openfoam(openfoam_file)

    fig, ax = plt.subplots(figsize=(7.6, 4.8))

    xf_upper, = ax.plot(
        xu_xf,
        cpu_xf,
        linewidth=1.8,
        label="XFOIL upper",
    )

    xf_lower, = ax.plot(
        xl_xf,
        cpl_xf,
        linewidth=1.8,
        linestyle="--",
        label="XFOIL lower",
    )

    ax.plot(
        xu_of,
        cpu_of,
        linestyle="none",
        marker="o",
        markersize=2.8,
        color=xf_upper.get_color(),
        label="OpenFOAM SST upper",
    )

    ax.plot(
        xl_of,
        cpl_of,
        linestyle="none",
        marker="o",
        markersize=2.8,
        color=xf_lower.get_color(),
        label="OpenFOAM SST lower",
    )

    ax.set_xlabel(r"$x/c$")
    ax.set_ylabel(r"$C_p$")

    ax.invert_yaxis()
    ax.set_xlim(0.0, 1.0)

    ax.grid(True, alpha=0.25)
    ax.legend(frameon=True)

    # No embedded title: the thesis caption supplies this information.
    fig.tight_layout()

    local_pdf = HERE / f"NACA0012_AoA{tag}_Cp_CLEAN.pdf"
    local_png = HERE / f"NACA0012_AoA{tag}_Cp_CLEAN.png"

    thesis_pdf = THESIS_DIR / f"cp_0012_aoa{tag}.pdf"

    fig.savefig(local_pdf, bbox_inches="tight")
    fig.savefig(local_png, dpi=300, bbox_inches="tight")
    fig.savefig(thesis_pdf, bbox_inches="tight")

    plt.close(fig)

    print(f"AoA {aoa:2d} deg")
    print(f"  Created: {local_pdf}")
    print(f"  Created: {local_png}")
    print(f"  Thesis:  {thesis_pdf}")


for aoa in (0, 16):
    make_plot(aoa)

print("Finished.")
