from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "09_FINAL_AIRFOIL_SYNTHESIS"

F0012 = (
    ROOT /
    "06_PRIMARY_AERODYNAMIC_RESULTS/NACA0012/"
    "NACA0012_STAGE6_SST_vs_XFOIL_P240.csv"
)

F4412 = (
    ROOT /
    "06_PRIMARY_AERODYNAMIC_RESULTS/NACA4412/"
    "NACA4412_STAGE6_SST_vs_XFOIL_P240.csv"
)

SEP0012 = (
    ROOT /
    "07_SURFACE_PHYSICS_AND_SEPARATION/NACA0012/"
    "02_Cf_AND_SEPARATION/"
    "NACA0012_STAGE7_TE_CONNECTED_SEPARATION_AUDIT.csv"
)

SEP4412 = (
    ROOT /
    "07_SURFACE_PHYSICS_AND_SEPARATION/NACA4412/"
    "02_Cf_AND_SEPARATION/"
    "NACA4412_V9_SST_Cf_SEPARATION_SUMMARY.csv"
)

DRAG0012 = (
    ROOT /
    "07_SURFACE_PHYSICS_AND_SEPARATION/NACA0012/"
    "03_DRAG_DECOMPOSITION/"
    "NACA0012_V9_DRAG_DECOMPOSITION.csv"
)

DRAG4412 = (
    ROOT /
    "07_SURFACE_PHYSICS_AND_SEPARATION/NACA4412/"
    "03_DRAG_DECOMPOSITION/"
    "NACA4412_V9_SST_DRAG_DECOMPOSITION_STAGE7_CORRECTED.csv"
)

OUT = OUTDIR / "STAGE9_PRIMARY_AIRFOIL_SYNTHESIS.csv"


def read_by_aoa(path):
    with path.open(newline="") as f:
        return {
            float(r["AoA_deg"]): r
            for r in csv.DictReader(f)
        }


p0012 = read_by_aoa(F0012)
p4412 = read_by_aoa(F4412)
d0012 = read_by_aoa(DRAG0012)
d4412 = read_by_aoa(DRAG4412)


# ------------------------------------------------------------
# NACA0012 separation:
# Stage 7 explicitly assessed representative AoA 0, 6, 12, 16.
# Do NOT infer values for the other AoAs.
# ------------------------------------------------------------

sep0012 = {}

with SEP0012.open(newline="") as f:
    for r in csv.DictReader(f):
        sep0012[float(r["AoA_deg"])] = r


# ------------------------------------------------------------
# NACA4412 separation:
# source contains upper and lower rows; use upper surface only.
# ------------------------------------------------------------

sep4412 = {}

with SEP4412.open(newline="") as f:
    for r in csv.DictReader(f):

        if r["surface"].strip().lower() != "upper":
            continue

        sep4412[float(r["AoA_deg"])] = r


aoas = sorted(set(p0012) & set(p4412))

if len(aoas) != 12:
    raise RuntimeError(
        "Expected 12 common AoAs, got {}".format(aoas)
    )


# ------------------------------------------------------------
# Correct authoritative NACA4412 AoA15 provenance.
#
# Direct force-history audit:
# final data extent = 16000
# authoritative final-1000 mean = 15001-16000
# ------------------------------------------------------------

r15 = p4412[15.0]

r15["SST_Status"] = (
    "STABLE_ITERATIVE_PLATEAU_NOT_FORMAL"
)

r15["SST_Reporting_method"] = (
    "final_1000_iteration_mean"
)

r15["SST_Representative_iteration_or_window"] = (
    "15001-16000"
)

r15["CL_SST"] = "1.60833532733"
r15["CD_SST"] = "0.0523796501698"
r15["Cm_SST_raw_OpenFOAM_plusZ"] = "0.052298732905"
r15["Cm_SST_XFOIL_sign_convention"] = "-0.052298732905"


fields = [
    "AoA_deg",

    "NACA0012_SST_Status",
    "NACA0012_SST_Representative",
    "NACA4412_SST_Status",
    "NACA4412_SST_Representative",

    "NACA0012_CL_SST",
    "NACA4412_CL_SST",
    "Delta_CL_SST_4412_minus_0012",

    "NACA0012_CD_SST",
    "NACA4412_CD_SST",
    "Delta_CD_SST_4412_minus_0012",

    "NACA0012_L_over_D_SST",
    "NACA4412_L_over_D_SST",
    "Delta_L_over_D_SST_4412_minus_0012",

    "NACA0012_Cm_SST_standard_sign",
    "NACA4412_Cm_SST_standard_sign",
    "Delta_Cm_SST_4412_minus_0012",

    "NACA0012_CL_XFOIL",
    "NACA4412_CL_XFOIL",
    "Delta_CL_XFOIL_4412_minus_0012",

    "NACA0012_CD_XFOIL",
    "NACA4412_CD_XFOIL",
    "Delta_CD_XFOIL_4412_minus_0012",

    "NACA0012_Cm_XFOIL",
    "NACA4412_Cm_XFOIL",

    "NACA0012_pressure_drag_percent",
    "NACA4412_pressure_drag_percent_snapshot",

    "NACA0012_separation_assessed",
    "NACA0012_TE_connected_separation",
    "NACA0012_sep_x_over_c",

    "NACA4412_TE_connected_separation",
    "NACA4412_sep_x_over_c",
]


outrows = []

for aoa in aoas:

    a = p0012[aoa]
    b = p4412[aoa]

    cl1 = float(a["CL_SST"])
    cl4 = float(b["CL_SST"])

    cd1 = float(a["CD_SST"])
    cd4 = float(b["CD_SST"])

    cm1 = float(a["Cm_SST_XFOIL_sign_convention"])
    cm4 = float(b["Cm_SST_XFOIL_sign_convention"])

    xcl1 = float(a["CL_XFOIL_P240"])
    xcl4 = float(b["CL_XFOIL_P240"])

    xcd1 = float(a["CD_XFOIL_P240"])
    xcd4 = float(b["CD_XFOIL_P240"])

    xcm1 = float(a["Cm_XFOIL_P240"])
    xcm4 = float(b["Cm_XFOIL_P240"])

    ld1 = cl1 / cd1
    ld4 = cl4 / cd4

    # NACA0012 representative separation evidence only.
    s1 = sep0012.get(aoa)

    if s1 is None:
        s1_assessed = "False"
        s1_sep = ""
        s1_x = ""
    else:
        s1_assessed = "True"
        s1_sep = s1["TE_connected_separation"]
        s1_x = s1["separation_start_x_over_c"]

    # NACA4412 full upper-surface separation sweep.
    s4 = sep4412.get(aoa)

    if s4 is None:
        s4_sep = ""
        s4_x = ""
    else:
        s4_x = s4["TE_connected_sep_x_over_c"]

        s4_sep = (
            "True"
            if s4_x.strip() != ""
            else "False"
        )

    row = {
        "AoA_deg": "{:g}".format(aoa),

        "NACA0012_SST_Status":
            a["SST_Status"],

        "NACA0012_SST_Representative":
            a["SST_Representative_iteration_or_window"],

        "NACA4412_SST_Status":
            b["SST_Status"],

        "NACA4412_SST_Representative":
            b["SST_Representative_iteration_or_window"],

        "NACA0012_CL_SST": "{:.12g}".format(cl1),
        "NACA4412_CL_SST": "{:.12g}".format(cl4),

        "Delta_CL_SST_4412_minus_0012":
            "{:.12g}".format(cl4 - cl1),

        "NACA0012_CD_SST": "{:.12g}".format(cd1),
        "NACA4412_CD_SST": "{:.12g}".format(cd4),

        "Delta_CD_SST_4412_minus_0012":
            "{:.12g}".format(cd4 - cd1),

        "NACA0012_L_over_D_SST":
            "{:.12g}".format(ld1),

        "NACA4412_L_over_D_SST":
            "{:.12g}".format(ld4),

        "Delta_L_over_D_SST_4412_minus_0012":
            "{:.12g}".format(ld4 - ld1),

        "NACA0012_Cm_SST_standard_sign":
            "{:.12g}".format(cm1),

        "NACA4412_Cm_SST_standard_sign":
            "{:.12g}".format(cm4),

        "Delta_Cm_SST_4412_minus_0012":
            "{:.12g}".format(cm4 - cm1),

        "NACA0012_CL_XFOIL":
            "{:.12g}".format(xcl1),

        "NACA4412_CL_XFOIL":
            "{:.12g}".format(xcl4),

        "Delta_CL_XFOIL_4412_minus_0012":
            "{:.12g}".format(xcl4 - xcl1),

        "NACA0012_CD_XFOIL":
            "{:.12g}".format(xcd1),

        "NACA4412_CD_XFOIL":
            "{:.12g}".format(xcd4),

        "Delta_CD_XFOIL_4412_minus_0012":
            "{:.12g}".format(xcd4 - xcd1),

        "NACA0012_Cm_XFOIL":
            "{:.12g}".format(xcm1),

        "NACA4412_Cm_XFOIL":
            "{:.12g}".format(xcm4),

        "NACA0012_pressure_drag_percent":
            d0012[aoa]["CD_pressure_pct_of_total"],

        # For stable high-AoA NACA4412 cases this is an
        # instantaneous decomposition snapshot, not the
        # final-1000 coefficient mean.
        "NACA4412_pressure_drag_percent_snapshot":
            d4412[aoa]["pressure_drag_percent_snapshot"],

        "NACA0012_separation_assessed":
            s1_assessed,

        "NACA0012_TE_connected_separation":
            s1_sep,

        "NACA0012_sep_x_over_c":
            s1_x,

        "NACA4412_TE_connected_separation":
            s4_sep,

        "NACA4412_sep_x_over_c":
            s4_x,
    }

    outrows.append(row)


with OUT.open("w", newline="") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
    )

    writer.writeheader()
    writer.writerows(outrows)


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

assert len(outrows) == 12

a15 = next(
    r for r in outrows
    if float(r["AoA_deg"]) == 15.0
)

assert (
    a15["NACA4412_SST_Representative"]
    == "15001-16000"
)

assert abs(
    float(a15["NACA4412_CL_SST"])
    - 1.60833532733
) < 1e-12


print("=" * 118)
print("STAGE 9 — PRIMARY AIRFOIL SYNTHESIS TABLE")
print("=" * 118)

print("Rows:", len(outrows))
print("AoA:", ", ".join(r["AoA_deg"] for r in outrows))

print()
print("NACA4412 AoA15 provenance:")
print(
    "  representative =",
    a15["NACA4412_SST_Representative"]
)
print(
    "  CL =",
    a15["NACA4412_CL_SST"]
)
print(
    "  CD =",
    a15["NACA4412_CD_SST"]
)
print(
    "  Cm standard sign =",
    a15["NACA4412_Cm_SST_standard_sign"]
)

print()
print("Output:")
print(OUT)

print()
print("RESULT: PASS")
