from pathlib import Path
import csv
import math

ROOT = Path("CANONICAL_FORCE_COEFFICIENT_HISTORIES")

CASES = [
    ("AoA00",   0.0,  "FORMAL"),
    ("AoA02",   2.0,  "FORMAL"),
    ("AoA04",   4.0,  "FORMAL"),
    ("AoA06",   6.0,  "FORMAL"),
    ("AoA08",   8.0,  "FORMAL"),
    ("AoA10",  10.0,  "FORMAL"),
    ("AoA12",  12.0,  "FORMAL"),
    ("AoA14",  14.0,  "FORMAL"),
    ("AoA14p5",14.5,  "FORMAL"),
    ("AoA15",  15.0,  "STABLE"),
    ("AoA15p5",15.5,  "STABLE"),
    ("AoA16",  16.0,  "STABLE"),
]

def read_force_file(path):
    rows = []

    with path.open() as f:
        for line in f:
            s = line.strip()

            if not s or s.startswith("#"):
                continue

            p = s.split()

            if len(p) < 4:
                continue

            try:
                iteration = float(p[0])
                cm = float(p[1])
                cd = float(p[2])
                cl = float(p[3])
            except ValueError:
                continue

            rows.append((iteration, cm, cd, cl))

    return rows


def stats(values):
    n = len(values)
    mean = sum(values) / n

    if n > 1:
        variance = sum((x - mean)**2 for x in values) / (n - 1)
        std = math.sqrt(variance)
    else:
        std = 0.0

    return mean, std, min(values), max(values)


results = []

for name, aoa, status in CASES:

    path = ROOT / f"forceCoeffs_{name}_CANONICAL.dat"
    rows = read_force_file(path)

    if not rows:
        raise RuntimeError(f"No usable rows in {path}")

    if status == "FORMAL":
        iteration, cm, cd, cl = rows[-1]

        results.append({
            "AoA_deg": aoa,
            "Status": "FORMAL_CONVERGENCE",
            "Reporting_method": "final_converged_iteration",
            "Window_start": int(iteration),
            "Window_end": int(iteration),
            "Samples": 1,
            "Cm_raw": cm,
            "Cd": cd,
            "Cl": cl,
            "Cm_std": 0.0,
            "Cd_std": 0.0,
            "Cl_std": 0.0,
            "Cm_min": cm,
            "Cm_max": cm,
            "Cd_min": cd,
            "Cd_max": cd,
            "Cl_min": cl,
            "Cl_max": cl,
        })

    else:
        window = rows[-1000:]

        iterations = [r[0] for r in window]
        cms = [r[1] for r in window]
        cds = [r[2] for r in window]
        cls = [r[3] for r in window]

        cm_mean, cm_std, cm_min, cm_max = stats(cms)
        cd_mean, cd_std, cd_min, cd_max = stats(cds)
        cl_mean, cl_std, cl_min, cl_max = stats(cls)

        results.append({
            "AoA_deg": aoa,
            "Status": "STABLE_ITERATIVE_PLATEAU_NOT_FORMAL",
            "Reporting_method": "final_1000_iteration_mean",
            "Window_start": int(iterations[0]),
            "Window_end": int(iterations[-1]),
            "Samples": len(window),
            "Cm_raw": cm_mean,
            "Cd": cd_mean,
            "Cl": cl_mean,
            "Cm_std": cm_std,
            "Cd_std": cd_std,
            "Cl_std": cl_std,
            "Cm_min": cm_min,
            "Cm_max": cm_max,
            "Cd_min": cd_min,
            "Cd_max": cd_max,
            "Cl_min": cl_min,
            "Cl_max": cl_max,
        })


csv_path = Path("NACA4412_V9_SST_REPORTED_COEFFICIENTS.csv")

fields = [
    "AoA_deg",
    "Status",
    "Reporting_method",
    "Window_start",
    "Window_end",
    "Samples",
    "Cl",
    "Cd",
    "Cm_raw",
    "Cl_std",
    "Cd_std",
    "Cm_std",
    "Cl_min",
    "Cl_max",
    "Cd_min",
    "Cd_max",
    "Cm_min",
    "Cm_max",
]

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    for row in results:
        writer.writerow(row)


txt_path = Path("NACA4412_V9_SST_REPORTED_COEFFICIENTS.txt")

with txt_path.open("w") as f:

    f.write("NACA4412 V9 SST — AUTHORITATIVE REPORTED COEFFICIENTS\n")
    f.write("=====================================================\n\n")

    f.write("Reporting rule:\n")
    f.write("  FORMAL cases : final formally converged iteration\n")
    f.write("  STABLE cases : mean over final 1000 steady iterations\n\n")

    f.write(
        "The stable-case averaging window is an ITERATIVE window,\n"
        "not a physical-time average.\n\n"
    )

    f.write(
        "Cm values below are RAW OpenFOAM values. Moment-sign alignment\n"
        "with XFOIL is intentionally handled separately.\n\n"
    )

    f.write(
        f"{'AoA':>6} {'Status':>12} "
        f"{'Cl':>12} {'Cd':>12} {'Cm_raw':>12} "
        f"{'Window':>18}\n"
    )

    f.write("-" * 78 + "\n")

    for r in results:

        status_short = (
            "FORMAL"
            if r["Status"] == "FORMAL_CONVERGENCE"
            else "STABLE"
        )

        window = f"{r['Window_start']}-{r['Window_end']}"

        f.write(
            f"{r['AoA_deg']:6.1f} "
            f"{status_short:>12} "
            f"{r['Cl']:12.8f} "
            f"{r['Cd']:12.8f} "
            f"{r['Cm_raw']:12.8f} "
            f"{window:>18}\n"
        )


print(f"Created: {csv_path}")
print(f"Created: {txt_path}")
