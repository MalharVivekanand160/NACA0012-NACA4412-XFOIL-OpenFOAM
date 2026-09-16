from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw_inputs"
OUTDIR = ROOT / "reproduced"

OUTDIR.mkdir(parents=True, exist_ok=True)


def read_xfoil_0012(path):
    data = np.loadtxt(path, comments="#")

    x = data[:, 0]
    cp = data[:, 1]

    i_le = np.argmin(x)

    xu = x[:i_le + 1]
    cpu = cp[:i_le + 1]

    xl = x[i_le:]
    cpl = cp[i_le:]

    return xu, cpu, xl, cpl


def read_openfoam_0012(path):
    data = np.loadtxt(path, comments="#")

    x = data[:, 0]
    y = data[:, 1]
    cp = data[:, 2]

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


def read_surface_csv(path):
    data = np.genfromtxt(
        path,
        delimiter=",",
        names=True,
        dtype=None,
        encoding="utf-8",
    )

    x = np.asarray(
        data["x_over_c"],
        dtype=float,
    )

    cp = np.asarray(
        data["Cp"],
        dtype=float,
    )

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


def validate(name, xu, cpu, xl, cpl):
    if min(len(xu), len(xl)) < 10:
        raise RuntimeError(
            f"{name}: too few upper/lower surface points."
        )

    for arr in [xu, cpu, xl, cpl]:
        if not np.all(np.isfinite(arr)):
            raise RuntimeError(
                f"{name}: non-finite values found."
            )

    print(
        f"{name}: "
        f"upper={len(xu)}, lower={len(xl)}, "
        f"Cp range=("
        f"{min(cpu.min(), cpl.min()):.4f}, "
        f"{max(cpu.max(), cpl.max()):.4f})"
    )


def save(fig, stem):
    pdf = OUTDIR / f"{stem}.pdf"
    png = OUTDIR / f"{stem}.png"

    fig.tight_layout()

    fig.savefig(
        pdf,
        bbox_inches="tight",
    )

    fig.savefig(
        png,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    return pdf, png


# ============================================================
# NACA 0012
# ============================================================
xf12_file = RAW / "Cp_AoA14p5.txt"
of12_file = RAW / "Cp_AoA14p5_OpenFOAM.dat"

xu_xf, cpu_xf, xl_xf, cpl_xf = (
    read_xfoil_0012(xf12_file)
)

xu_of, cpu_of, xl_of, cpl_of = (
    read_openfoam_0012(of12_file)
)

validate(
    "NACA0012 XFOIL",
    xu_xf, cpu_xf, xl_xf, cpl_xf,
)

validate(
    "NACA0012 OpenFOAM",
    xu_of, cpu_of, xl_of, cpl_of,
)

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

save(
    fig,
    "cp_0012_aoa14p5",
)


# ============================================================
# NACA 4412
# ============================================================
xf44_file = (
    RAW
    / "NACA4412_XFOIL_AoA14p5_Cp_airfoil.csv"
)

of44_file = (
    RAW
    / "NACA4412_V9_SST_AoA14p5_Cp_airfoil.csv"
)

xu_xf, cpu_xf, xl_xf, cpl_xf = (
    read_surface_csv(xf44_file)
)

xu_of, cpu_of, xl_of, cpl_of = (
    read_surface_csv(of44_file)
)

validate(
    "NACA4412 XFOIL",
    xu_xf, cpu_xf, xl_xf, cpl_xf,
)

validate(
    "NACA4412 OpenFOAM",
    xu_of, cpu_of, xl_of, cpl_of,
)

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
ax.invert_yaxis()
ax.set_xlim(0.0, 1.0)
ax.grid(True, alpha=0.25)
ax.legend(frameon=True)

save(
    fig,
    "cp_4412_aoa14p5",
)

print()
print("=" * 68)
print("REPOSITORY — 14.5-DEGREE Cp FIGURES COMPLETE")
print("=" * 68)
print("Outputs:", OUTDIR)
