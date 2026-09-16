from pathlib import Path
import shutil
import numpy as np
import matplotlib.pyplot as plt

HOME = Path.home()
FS = HOME / "Desktop" / "Final_stretch"

THESIS_DIR = (
    FS
    / "08_THESIS_REPORT"
    / "bilder"
    / "thesis"
)

OVERLEAF_DIR = (
    FS
    / "08_OVERLEAF_SOURCE"
    / "bilder"
    / "thesis"
)

THESIS_DIR.mkdir(parents=True, exist_ok=True)
OVERLEAF_DIR.mkdir(parents=True, exist_ok=True)

OUTDIR = Path(__file__).resolve().parent / "CP_14p5_FINAL"
OUTDIR.mkdir(exist_ok=True)


# ============================================================
# NACA 0012 readers
# ============================================================

def read_xfoil_0012(path):
    data = np.loadtxt(path, comments="#")

    x = data[:, 0]
    cp = data[:, 1]

    i_le = np.argmin(x)

    # XFOIL file proceeds TE -> upper -> LE -> lower -> TE
    xu = x[:i_le + 1]
    cpu = cp[:i_le + 1]

    xl = x[i_le:]
    cpl = cp[i_le:]

    return xu, cpu, xl, cpl


def read_openfoam_0012(path):
    # Columns:
    # x/c   y/c   Cp
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

    return xu[iu], cpu[iu], xl[il], cpl[il]


# ============================================================
# NACA 4412 reader
# ============================================================

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

    return xu[iu], cpu[iu], xl[il], cpl[il]


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
        f"Cp range=({min(cpu.min(), cpl.min()):.4f}, "
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
# NACA 0012 at alpha = 14.5 deg
# ============================================================

xf12_file = (
    FS
    / "02_XFOIL_DATA"
    / "NACA0012"
    / "Cp_AoA14p5.txt"
)

of12_file = (
    FS
    / "03_OPENFOAM_NACA0012_V9_SST"
    / "CP"
    / "Cp_AoA14p5_OpenFOAM.dat"
)

xu_xf, cpu_xf, xl_xf, cpl_xf = read_xfoil_0012(
    xf12_file
)

xu_of, cpu_of, xl_of, cpl_of = read_openfoam_0012(
    of12_file
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

pdf12, png12 = save(
    fig,
    "cp_0012_aoa14p5",
)


# ============================================================
# NACA 4412 at alpha = 14.5 deg
# ============================================================

xf44_file = (
    FS
    / "05_NACA4412_V9_VALIDATION"
    / "NACA4412_XFOIL_AoA14p5_Cp_airfoil.csv"
)

of44_file = (
    FS
    / "05_NACA4412_V9_VALIDATION"
    / "NACA4412_V9_SST_AoA14p5_Cp_airfoil.csv"
)

xu_xf, cpu_xf, xl_xf, cpl_xf = read_surface_csv(
    xf44_file
)

xu_of, cpu_of, xl_of, cpl_of = read_surface_csv(
    of44_file
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

pdf44, png44 = save(
    fig,
    "cp_4412_aoa14p5",
)


# ============================================================
# Copy final thesis figures
# ============================================================

for dest in [THESIS_DIR, OVERLEAF_DIR]:
    shutil.copy2(
        pdf12,
        dest / "cp_0012_aoa14p5.pdf",
    )

    shutil.copy2(
        png12,
        dest / "cp_0012_aoa14p5.png",
    )

    shutil.copy2(
        pdf44,
        dest / "cp_4412_aoa14p5.pdf",
    )

    shutil.copy2(
        png44,
        dest / "cp_4412_aoa14p5.png",
    )


print()
print("=" * 68)
print("FINAL Cp FIGURES COMPLETE")
print("=" * 68)

print()
print("Created:")
print(pdf12)
print(pdf44)

print()
print("Copied to:")
print(THESIS_DIR)
print(OVERLEAF_DIR)
