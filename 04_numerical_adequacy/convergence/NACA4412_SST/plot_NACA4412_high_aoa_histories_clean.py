from pathlib import Path
import matplotlib.pyplot as plt

# ============================================================
# PATHS
# ============================================================

ROOT = (
    Path.home()
    / "Desktop/Final_stretch/07_FINAL_PROJECT_PACKAGE_FOR_REVIEW"
    / "03_NUMERICS_AND_CONVERGENCE/NACA4412_SST"
)

DATA_DIR = ROOT / "CANONICAL_FORCE_COEFFICIENT_HISTORIES"

OUT_DIR = Path.home() / "Desktop/Final_stretch/TEMP_CONVERGENCE_FIGURES"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CASES = [
    ("AoA15",   r"$15^\circ$"),
    ("AoA15p5", r"$15.5^\circ$"),
    ("AoA16",   r"$16^\circ$"),
]

# Show the stable high-iteration region.
X_MIN = 7500

# ============================================================
# PLOT SETTINGS
# ============================================================

plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
})

# ============================================================
# READ OPENFOAM forceCoeffs DATA
#
# Column order:
# Time  Cm  Cd  Cl  Cl(f)  Cl(r)
# ============================================================

def read_force_coeffs(path):
    time = []
    cm = []
    cd = []
    cl = []

    with path.open() as f:
        for line in f:
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            parts = stripped.split()

            if len(parts) < 4:
                continue

            try:
                time.append(float(parts[0]))
                cm.append(float(parts[1]))
                cd.append(float(parts[2]))
                cl.append(float(parts[3]))
            except ValueError:
                continue

    if not time:
        raise RuntimeError(f"No numerical data found in:\n{path}")

    return time, cm, cd, cl


# ============================================================
# LOAD ALL THREE HIGH-AOA CASES
# ============================================================

data = {}

for case, label in CASES:

    path = DATA_DIR / f"forceCoeffs_{case}_CANONICAL.dat"

    if not path.is_file():
        raise FileNotFoundError(f"Missing file:\n{path}")

    time, cm, cd, cl = read_force_coeffs(path)

    data[case] = {
        "label": label,
        "time": time,
        "cm": cm,
        "cd": cd,
        "cl": cl,
    }

    # Numerical verification
    n_final = min(1000, len(time))

    cl_mean = sum(cl[-n_final:]) / n_final
    cd_mean = sum(cd[-n_final:]) / n_final

    print()
    print("=" * 60)
    print(case)
    print("=" * 60)
    print(f"First iteration      : {time[0]:.0f}")
    print(f"Last iteration       : {time[-1]:.0f}")
    print(f"Number of data rows  : {len(time)}")
    print(f"Final-1000 mean CL   : {cl_mean:.8f}")
    print(f"Final-1000 mean CD   : {cd_mean:.8f}")


# ============================================================
# GENERIC HISTORY PLOTTER
# ============================================================

def make_plot(quantity, ylabel, output_stem):

    fig, ax = plt.subplots(figsize=(7.2, 4.2))

    for case, _ in CASES:

        d = data[case]

        filtered = [
            (t, q)
            for t, q in zip(d["time"], d[quantity])
            if t >= X_MIN
        ]

        if not filtered:
            raise RuntimeError(
                f"No {quantity} data for {case} at iteration >= {X_MIN}"
            )

        x = [item[0] for item in filtered]
        y = [item[1] for item in filtered]

        ax.plot(
            x,
            y,
            linewidth=1.3,
            label=d["label"],
        )

    # --------------------------------------------------------
    # Clean thesis formatting
    # --------------------------------------------------------

    ax.set_xlabel("Steady solver iteration")
    ax.set_ylabel(ylabel)

    ax.grid(
        True,
        linewidth=0.5,
        alpha=0.25,
    )

    # No plot title.
    # No subtitle.
    # The LaTeX figure caption provides the description.

    ax.legend(
        title="AoA",
        loc="best",
        frameon=True,
    )

    ax.set_xlim(left=X_MIN)

    fig.tight_layout()

    pdf = OUT_DIR / f"{output_stem}.pdf"
    png = OUT_DIR / f"{output_stem}.png"

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

    print()
    print(f"Created: {pdf}")
    print(f"Created: {png}")


# ============================================================
# CREATE CLEAN CL AND CD FIGURES
# ============================================================

make_plot(
    quantity="cl",
    ylabel=r"$C_L$",
    output_stem="naca4412_high_aoa_cl_history_clean",
)

make_plot(
    quantity="cd",
    ylabel=r"$C_D$",
    output_stem="naca4412_high_aoa_cd_history_clean",
)

print()
print("=" * 60)
print("DONE")
print("=" * 60)
