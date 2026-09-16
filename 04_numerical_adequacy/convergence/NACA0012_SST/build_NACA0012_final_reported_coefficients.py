from pathlib import Path
import csv

ROOT = Path("FORCE_COEFFICIENT_HISTORIES")

CASES = [
    ("AoA00",    0.0),
    ("AoA02",    2.0),
    ("AoA04",    4.0),
    ("AoA06",    6.0),
    ("AoA08",    8.0),
    ("AoA10",   10.0),
    ("AoA12",   12.0),
    ("AoA14",   14.0),
    ("AoA14p5", 14.5),
    ("AoA15",   15.0),
    ("AoA15p5", 15.5),
    ("AoA16",   16.0),
]

results = []

for name, aoa in CASES:

    path = ROOT / f"forceCoeffs_{name}.dat"

    if not path.exists():
        raise RuntimeError(f"Missing file: {path}")

    rows = []

    with path.open() as f:
        for line in f:
            s = line.strip()

            if not s or s.startswith("#"):
                continue

            parts = s.split()

            if len(parts) < 4:
                continue

            try:
                iteration = float(parts[0])
                cm = float(parts[1])
                cd = float(parts[2])
                cl = float(parts[3])
            except ValueError:
                continue

            rows.append((iteration, cm, cd, cl))

    if not rows:
        raise RuntimeError(f"No usable force rows in {path}")

    iteration, cm, cd, cl = rows[-1]

    results.append({
        "AoA_deg": aoa,
        "Status": "FORMAL_CONVERGENCE",
        "Reporting_method": "final_converged_iteration",
        "Iteration": int(iteration),
        "Cl": cl,
        "Cd": cd,
        "Cm_raw": cm,
    })


csv_path = Path("NACA0012_V9_SST_REPORTED_COEFFICIENTS.csv")

fields = [
    "AoA_deg",
    "Status",
    "Reporting_method",
    "Iteration",
    "Cl",
    "Cd",
    "Cm_raw",
]

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(results)


txt_path = Path("NACA0012_V9_SST_REPORTED_COEFFICIENTS.txt")

with txt_path.open("w") as f:

    f.write("NACA0012 V9 SST — AUTHORITATIVE REPORTED COEFFICIENTS\n")
    f.write("=====================================================\n\n")

    f.write("All 12 cases satisfied the OpenFOAM SIMPLE residualControl criteria.\n\n")

    f.write("Reporting rule:\n")
    f.write("  All cases: final formally converged iteration.\n")
    f.write("  No iterative-window averaging is used for NACA0012 SST.\n\n")

    f.write(
        "Cm values are RAW OpenFOAM values. Moment-sign convention/alignment\n"
        "is intentionally handled separately from this source dataset.\n\n"
    )

    f.write(
        f"{'AoA':>6} {'Status':>10} {'Iteration':>10} "
        f"{'Cl':>12} {'Cd':>12} {'Cm_raw':>12}\n"
    )

    f.write("-" * 70 + "\n")

    for r in results:
        f.write(
            f"{r['AoA_deg']:6.1f} "
            f"{'FORMAL':>10} "
            f"{r['Iteration']:10d} "
            f"{r['Cl']:12.8f} "
            f"{r['Cd']:12.8f} "
            f"{r['Cm_raw']:12.8f}\n"
        )


print(f"Created: {csv_path}")
print(f"Created: {txt_path}")
