from pathlib import Path
import csv
import shutil
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

ROOT = Path(__file__).resolve().parent

SRC = (
    Path.home()
    / "Desktop"
    / "Final_stretch"
    / "formal_only_sensitivity_recalc.csv"
)

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

with SRC.open(newline="") as f:
    rows = list(csv.DictReader(f))

AIRFOILS = [
    ("NACA0012", "(a) NACA 0012"),
    ("NACA4412", "(b) NACA 4412"),
]

MODELS = [
    ("SA", "s", "--"),
    ("SSTLM", "^", "-."),
]

# Only complete, formally converged model families are shown
# in the main sensitivity figures.
PLOT_MODELS = [
    ("SA", "s", "--"),
]

# ------------------------------------------------------------
# Build unique SST baseline values from the verified dataset
# ------------------------------------------------------------

sst = {}

for r in rows:
    key = (r["airfoil"], float(r["aoa"]))
    vals = (
        float(r["SST_CL"]),
        float(r["SST_CD"]),
    )

    if key in sst:
        old = sst[key]
        if any(abs(a - b) > 1e-12 for a, b in zip(old, vals)):
            raise RuntimeError(f"Inconsistent SST baseline for {key}")
    else:
        sst[key] = vals

# ------------------------------------------------------------
# Retained formally converged sensitivity cases
# The corrected CSV already contains only retained cases.
# ------------------------------------------------------------

accepted = {}

for airfoil, _ in AIRFOILS:
    for model, _, _ in MODELS:
        rr = [
            r for r in rows
            if r["airfoil"] == airfoil
            and r["model"] == model
        ]
        rr.sort(key=lambda r: float(r["aoa"]))
        accepted[(airfoil, model)] = rr

expected_counts = {
    ("NACA0012", "SA"): 9,
    ("NACA0012", "SSTLM"): 8,
    ("NACA4412", "SA"): 9,
    ("NACA4412", "SSTLM"): 4,
}

for key, expected in expected_counts.items():
    actual = len(accepted[key])
    if actual != expected:
        raise RuntimeError(
            f"{key}: expected {expected} accepted cases, got {actual}"
        )

# Explicit checks against the final convergence policy
aoa_0012_sstlm = [float(r["aoa"]) for r in accepted[("NACA0012", "SSTLM")]]
aoa_4412_sstlm = [float(r["aoa"]) for r in accepted[("NACA4412", "SSTLM")]]

if 6.0 in aoa_0012_sstlm:
    raise RuntimeError("NACA0012 SSTLM AoA6 must be excluded.")

if aoa_4412_sstlm != [0.0, 6.0, 8.0, 12.0]:
    raise RuntimeError(
        f"Unexpected NACA4412 SSTLM retained angles: {aoa_4412_sstlm}"
    )

# Verify corrected NACA4412 SSTLM AoA12 value
row12 = [
    r for r in accepted[("NACA4412", "SSTLM")]
    if float(r["aoa"]) == 12.0
]

if len(row12) != 1:
    raise RuntimeError("Expected one NACA4412 SSTLM AoA12 row.")

if abs(float(row12[0]["MODEL_CL"]) - 1.46557720) > 1e-8:
    raise RuntimeError("Incorrect NACA4412 SSTLM AoA12 CL.")

if abs(float(row12[0]["MODEL_CD"]) - 0.0367661487) > 1e-8:
    raise RuntimeError("Incorrect NACA4412 SSTLM AoA12 CD.")

# ------------------------------------------------------------
# Publication-style plotting
# Same style as original thesis plotting script
# ------------------------------------------------------------

plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 12,
    "xtick.labelsize": 10.5,
    "ytick.labelsize": 10.5,
    "legend.fontsize": 11,
    "lines.linewidth": 2.0,
    "lines.markersize": 5.5,
})


def make_figure(metric, sst_index, ylabel, stem):

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(11.2, 4.4),
        sharex=True,
        sharey=True,
    )

    legend_handles = None
    legend_labels = None

    for i, (ax, (airfoil, panel_title)) in enumerate(
        zip(axes, AIRFOILS)
    ):

        # Final common quantitative range: 0--14.5 deg
        base_aoa = sorted(
            a for (af, a) in sst
            if af == airfoil and a <= 14.5
        )

        ax.plot(
            base_aoa,
            [sst[(airfoil, a)][sst_index] for a in base_aoa],
            marker="o",
            linestyle="-",
            label="SST baseline",
        )

        for model, marker, linestyle in PLOT_MODELS:
            rr = accepted[(airfoil, model)]

            full_aoa = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 14.5]

            values = {
                float(r["aoa"]): float(r[f"MODEL_{metric}"])
                for r in rr
            }

            ax.plot(
                full_aoa,
                [values.get(a, float("nan")) for a in full_aoa],
                marker=marker,
                linestyle=linestyle,
                label=model,
            )

        ax.set_title(panel_title, pad=8)

        ax.set_xlabel(
            r"Angle of attack, $\alpha$ [deg]"
        )

        if i == 0:
            ax.set_ylabel(ylabel)

        ax.set_xlim(-0.4, 14.9)
        ax.set_xticks([0, 2, 4, 6, 8, 10, 12, 14])

        ax.grid(
            True,
            alpha=0.25,
            linewidth=0.7,
        )

        ax.tick_params(
            direction="out",
            length=4,
            width=0.8,
        )

        if metric == "CD":
            ax.yaxis.set_major_formatter(
                FormatStrFormatter("%.3f")
            )

        if i == 0:
            legend_handles, legend_labels = (
                ax.get_legend_handles_labels()
            )

    fig.legend(
        legend_handles,
        legend_labels,
        loc="upper center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, 0.995),
    )

    fig.subplots_adjust(
        left=0.09,
        right=0.99,
        bottom=0.16,
        top=0.80,
        wspace=0.12,
    )

    pdf_path = ROOT / f"{stem}.pdf"
    png_path = ROOT / f"{stem}.png"

    fig.savefig(
        pdf_path,
        bbox_inches="tight",
        pad_inches=0.05,
    )

    fig.savefig(
        png_path,
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.05,
    )

    plt.close(fig)

    return pdf_path, png_path


cl_pdf, cl_png = make_figure(
    metric="CL",
    sst_index=0,
    ylabel=r"$C_L$",
    stem="STAGE8_THESIS_CL_MODEL_SENSITIVITY_FORMAL_ONLY",
)

cd_pdf, cd_png = make_figure(
    metric="CD",
    sst_index=1,
    ylabel=r"$C_D$",
    stem="STAGE8_THESIS_CD_MODEL_SENSITIVITY_FORMAL_ONLY",
)

for dest in [THESIS_DIR, OVERLEAF_DIR]:
    shutil.copy2(
        cl_pdf,
        dest / "model_sensitivity_cl.pdf",
    )
    shutil.copy2(
        cd_pdf,
        dest / "model_sensitivity_cd.pdf",
    )
    shutil.copy2(
        cl_png,
        dest / "model_sensitivity_cl.png",
    )
    shutil.copy2(
        cd_png,
        dest / "model_sensitivity_cd.png",
    )

print("==============================================")
print("FORMAL-ONLY SENSITIVITY FIGURES COMPLETE")
print("==============================================")
print()
print("Accepted cases:")
for key in expected_counts:
    print(
        f"{key[0]} {key[1]}: "
        f"{[float(r['aoa']) for r in accepted[key]]}"
    )

print()
print("NACA4412 SSTLM AoA12:")
print(
    "CL =",
    row12[0]["MODEL_CL"],
    "CD =",
    row12[0]["MODEL_CD"],
    "iteration =",
    row12[0]["model_final_iter"],
)

print()
print("Copied final figures to:")
print(THESIS_DIR)
print(OVERLEAF_DIR)
