from pathlib import Path
import csv
import statistics

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "provenance" / "formal_only_sensitivity_recalc.csv"
OUTDIR = ROOT / "final_common_range"

OUTDIR.mkdir(parents=True, exist_ok=True)

with SRC.open(newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields:
    raise RuntimeError("Could not read source CSV header.")

# Final submitted-thesis quantitative range and convergence policy.
rows = [
    r for r in rows
    if float(r["aoa"]) <= 14.5
    and not (
        r["airfoil"] == "NACA4412"
        and r["model"] == "SSTLM"
        and float(r["aoa"]) == 12.0
    )
]

expected_angles = {
    ("NACA0012", "SA"):
        [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 14.5],
    ("NACA0012", "SSTLM"):
        [0.0, 2.0, 4.0, 8.0, 10.0, 12.0, 14.0, 14.5],
    ("NACA4412", "SA"):
        [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 14.5],
    ("NACA4412", "SSTLM"):
        [0.0, 6.0, 8.0],
}

for key, expected in expected_angles.items():
    actual = sorted(
        float(r["aoa"])
        for r in rows
        if (r["airfoil"], r["model"]) == key
    )
    if actual != expected:
        raise RuntimeError(
            f"{key}: expected {expected}, got {actual}"
        )

if len(rows) != 29:
    raise RuntimeError(
        f"Expected 29 retained cases, got {len(rows)}"
    )

final_csv = OUTDIR / "FINAL_THESIS_FORMAL_ONLY_SENSITIVITY.csv"

with final_csv.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

metrics = []
for key in expected_angles:
    airfoil, model = key

    rr = [
        r for r in rows
        if r["airfoil"] == airfoil
        and r["model"] == model
    ]

    # Relative CL at alpha=0 is omitted for NACA0012 because
    # the SST reference lift is approximately zero.
    cl_rows = [
        r for r in rr
        if not (
            airfoil == "NACA0012"
            and float(r["aoa"]) == 0.0
        )
    ]

    cl = [
        abs(float(r["rel_dCL_pct"]))
        for r in cl_rows
    ]

    cd = [
        abs(float(r["rel_dCD_pct"]))
        for r in rr
    ]

    metrics.append({
        "Airfoil": airfoil,
        "Model": model,
        "Cases": f"{len(rr)}/9",
        "Mean_abs_Delta_CL_pct":
            f"{statistics.mean(cl):.2f}",
        "Max_abs_Delta_CL_pct":
            f"{max(cl):.2f}",
        "Mean_abs_Delta_CD_pct":
            f"{statistics.mean(cd):.2f}",
        "Max_abs_Delta_CD_pct":
            f"{max(cd):.2f}",
    })

metrics_file = (
    OUTDIR
    / "FINAL_THESIS_MODEL_SENSITIVITY_METRICS.csv"
)

fieldnames = [
    "Airfoil",
    "Model",
    "Cases",
    "Mean_abs_Delta_CL_pct",
    "Max_abs_Delta_CL_pct",
    "Mean_abs_Delta_CD_pct",
    "Max_abs_Delta_CD_pct",
]

with metrics_file.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames,
    )
    writer.writeheader()
    writer.writerows(metrics)

expected_metrics = {
    ("NACA0012", "SA"):
        ("9/9", "1.81", "3.03", "5.76", "6.21"),
    ("NACA0012", "SSTLM"):
        ("8/9", "2.61", "6.90", "20.02", "54.63"),
    ("NACA4412", "SA"):
        ("9/9", "3.46", "4.98", "4.05", "5.24"),
    ("NACA4412", "SSTLM"):
        ("3/9", "10.63", "18.59", "30.32", "45.09"),
}

for r in metrics:
    key = (r["Airfoil"], r["Model"])
    actual = (
        r["Cases"],
        r["Mean_abs_Delta_CL_pct"],
        r["Max_abs_Delta_CL_pct"],
        r["Mean_abs_Delta_CD_pct"],
        r["Max_abs_Delta_CD_pct"],
    )
    if actual != expected_metrics[key]:
        raise RuntimeError(
            f"{key}: final thesis metric mismatch: {actual}"
        )

print("Final retained sensitivity cases:", len(rows))
print("Metrics verified against submitted thesis.")
