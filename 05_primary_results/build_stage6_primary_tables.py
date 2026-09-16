#!/usr/bin/env python3

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

AOA_TARGETS = [
    0.0, 2.0, 4.0, 6.0, 8.0, 10.0,
    12.0, 14.0, 14.5, 15.0, 15.5, 16.0
]


def read_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def parse_xfoil_polar(path):
    """
    Parse standard XFOIL polar rows:

    alpha CL CD CDp CM Top_Xtr Bot_Xtr
    """

    data = {}

    number = re.compile(
        r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?$"
    )

    with path.open() as f:
        for line in f:
            parts = line.split()

            if len(parts) < 7:
                continue

            if not all(number.match(x) for x in parts[:7]):
                continue

            alpha, cl, cd, cdp, cm, top_xtr, bot_xtr = map(
                float, parts[:7]
            )

            data[round(alpha, 6)] = {
                "CL": cl,
                "CD": cd,
                "CDp": cdp,
                "Cm": cm,
                "Top_Xtr": top_xtr,
                "Bot_Xtr": bot_xtr,
            }

    return data


def pct_difference(delta, reference):
    if abs(reference) < 1e-14:
        return ""
    return 100.0 * delta / reference


def get_float(row, key, default=""):
    value = row.get(key, "")
    if value in ("", None):
        return default
    return float(value)


def representative_range(airfoil, row):
    if airfoil == "NACA0012":
        return row["Iteration"]

    start = row["Window_start"]
    end = row["Window_end"]

    if start == end:
        return start

    return f"{start}-{end}"


def build_table(airfoil, sst_path, xfoil_path, out_path):

    sst_rows = read_csv(sst_path)
    xfoil = parse_xfoil_polar(xfoil_path)

    sst = {
        round(float(row["AoA_deg"]), 6): row
        for row in sst_rows
    }

    output = []

    for aoa in AOA_TARGETS:

        key = round(aoa, 6)

        if key not in sst:
            raise RuntimeError(
                f"{airfoil}: missing SST AoA {aoa}"
            )

        if key not in xfoil:
            raise RuntimeError(
                f"{airfoil}: missing XFOIL AoA {aoa}"
            )

        s = sst[key]
        x = xfoil[key]

        cl_sst = get_float(s, "Cl")
        cd_sst = get_float(s, "Cd")
        cm_raw = get_float(s, "Cm_raw")

        # OpenFOAM raw Cm is projected onto +z.
        # XFOIL uses the opposite 2-D pitching-moment sign convention.
        cm_xfoil_convention = -cm_raw

        dcl = cl_sst - x["CL"]
        dcd = cd_sst - x["CD"]
        dcm = cm_xfoil_convention - x["Cm"]

        output.append({
            "AoA_deg": aoa,

            "SST_Status": s["Status"],
            "SST_Reporting_method": s["Reporting_method"],
            "SST_Representative_iteration_or_window":
                representative_range(airfoil, s),

            "CL_SST": cl_sst,
            "CL_XFOIL_P240": x["CL"],
            "Delta_CL_SST_minus_XFOIL": dcl,
            "Delta_CL_pct_of_XFOIL":
                pct_difference(dcl, x["CL"]),

            "CD_SST": cd_sst,
            "CD_XFOIL_P240": x["CD"],
            "Delta_CD_SST_minus_XFOIL": dcd,
            "Delta_CD_pct_of_XFOIL":
                pct_difference(dcd, x["CD"]),

            "Cm_SST_raw_OpenFOAM_plusZ": cm_raw,
            "Cm_SST_XFOIL_sign_convention":
                cm_xfoil_convention,
            "Cm_XFOIL_P240": x["Cm"],
            "Delta_Cm_comparable_SST_minus_XFOIL": dcm,
            "Abs_Delta_Cm": abs(dcm),

            "XFOIL_CDp": x["CDp"],
            "XFOIL_Top_Xtr": x["Top_Xtr"],
            "XFOIL_Bot_Xtr": x["Bot_Xtr"],

            "SST_CL_std":
                get_float(s, "Cl_std", ""),
            "SST_CD_std":
                get_float(s, "Cd_std", ""),
            "SST_Cm_raw_std":
                get_float(s, "Cm_std", ""),
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)

    fields = list(output[0].keys())

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)

    return output


n0012 = build_table(
    "NACA0012",
    ROOT /
    "03_NUMERICS_AND_CONVERGENCE/NACA0012_SST/"
    "NACA0012_V9_SST_REPORTED_COEFFICIENTS.csv",
    ROOT /
    "05_XFOIL_REFERENCE/NACA0012/02_PRODUCTION_P240/"
    "NACA0012_SHARP_TE_V9_Re1e6_Ncrit9_P240.pol",
    ROOT /
    "06_PRIMARY_AERODYNAMIC_RESULTS/NACA0012/"
    "NACA0012_STAGE6_SST_vs_XFOIL_P240.csv",
)

n4412 = build_table(
    "NACA4412",
    ROOT /
    "03_NUMERICS_AND_CONVERGENCE/NACA4412_SST/"
    "NACA4412_V9_SST_REPORTED_COEFFICIENTS.csv",
    ROOT /
    "05_XFOIL_REFERENCE/NACA4412/02_PRODUCTION_P240/"
    "NACA4412_SHARP_TE_V9_Re1e6_Ncrit9_P240.pol",
    ROOT /
    "06_PRIMARY_AERODYNAMIC_RESULTS/NACA4412/"
    "NACA4412_STAGE6_SST_vs_XFOIL_P240.csv",
)

print("============================================================")
print("STAGE 6 AUTHORITATIVE TABLE BUILD")
print("============================================================")
print()
print("NACA0012 rows:", len(n0012))
print("NACA4412 rows:", len(n4412))
print()
print("Created:")
print(
    "  06_PRIMARY_AERODYNAMIC_RESULTS/NACA0012/"
    "NACA0012_STAGE6_SST_vs_XFOIL_P240.csv"
)
print(
    "  06_PRIMARY_AERODYNAMIC_RESULTS/NACA4412/"
    "NACA4412_STAGE6_SST_vs_XFOIL_P240.csv"
)
