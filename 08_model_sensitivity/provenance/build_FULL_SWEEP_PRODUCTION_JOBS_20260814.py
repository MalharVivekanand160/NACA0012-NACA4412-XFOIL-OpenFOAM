#!/usr/bin/env python3

from pathlib import Path
import csv

ROOT = Path.home() / "NACA0012_4412_XFOIL_RANS_COMPARISON"

MANIFEST = (
    ROOT /
    "FULL_SA_SSTLM_SWEEP_GENERATION_MANIFEST_V2.csv"
)

rows = list(csv.DictReader(MANIFEST.open()))

created = []

for r in rows:

    airfoil = r["Airfoil"]
    model = r["Model"]
    tag = r["AoA_tag"]
    case = Path(r["Case"])

    short_airfoil = (
        "N0012" if airfoil == "NACA0012"
        else "N4412"
    )

    short_model = (
        "SA" if model == "SA"
        else "LM"
    )

    job_name = "{}_{}_{}".format(
        short_airfoil,
        short_model,
        tag,
    )

    sbatch_name = (
        "run_FULL_{}_{}_AoA{}.sbatch"
        .format(
            airfoil,
            model,
            tag,
        )
    )

    log_name = (
        "log.FULL_{}_{}_AoA{}"
        .format(
            airfoil,
            model,
            tag,
        )
    )

    out_name = (
        "slurm_FULL_{}_{}_A{}_%%j.out"
        .format(
            short_airfoil,
            short_model,
            tag,
        )
    )

    err_name = (
        "slurm_FULL_{}_{}_A{}_%%j.err"
        .format(
            short_airfoil,
            short_model,
            tag,
        )
    )

    lines = [
        "#!/bin/bash -l",
        "",
        "#SBATCH --job-name={}".format(job_name),
        "#SBATCH --partition=work",
        "#SBATCH --nodes=1",
        "#SBATCH --ntasks=1",
        "#SBATCH --cpus-per-task=1",
        "#SBATCH --time=04:00:00",
        "#SBATCH --output={}".format(out_name),
        "#SBATCH --error={}".format(err_name),
        "",
        "module purge",
        "module load gcc/12.1.0",
        "module load openmpi/4.1.3-gcc12.1.0",
        "module load openfoam/13",
        "",
    ]

    if model == "SSTLM":
        lines += [
            "# Match verified SSTLM production environment",
            "unset FOAM_SIGFPE",
            "",
        ]

    lines += [
        'cd "$SLURM_SUBMIT_DIR" || exit 1',
        "",
        'echo "========================================"',
        'echo "FULL SA/SSTLM SWEEP PRODUCTION"',
        'echo "========================================"',
        'echo "Airfoil: {}"'.format(airfoil),
        'echo "Model: {}"'.format(model),
        'echo "AoA: {}"'.format(r["AoA_deg"]),
        'echo "Host: $(hostname)"',
        'echo "Case: $(pwd)"',
        'echo "Start: $(date)"',
    ]

    if model == "SSTLM":
        lines.append(
            'echo "FOAM_SIGFPE: ${FOAM_SIGFPE-unset}"'
        )

    lines += [
        "",
    ]

    if model == "SA":
        lines += [
            "foamRun 2>&1 | tee {}".format(
                log_name
            ),
        ]
    else:
        lines += [
            "foamRun -solver incompressibleFluid \\",
            "    2>&1 | tee {}".format(
                log_name
            ),
        ]

    lines += [
        "",
        "STATUS=${PIPESTATUS[0]}",
        "",
        'echo',
        'echo "Solver exit status: $STATUS"',
        'echo "End: $(date)"',
        "",
        'exit "$STATUS"',
        "",
    ]

    path = case / sbatch_name

    if path.exists():
        raise RuntimeError(
            "Refusing overwrite: {}".format(path)
        )

    path.write_text("\n".join(lines))

    created.append({
        "Airfoil": airfoil,
        "Model": model,
        "AoA_tag": tag,
        "Case": str(case),
        "SBATCH": str(path),
        "Log": log_name,
    })

    print(
        "{:<9} {:<5} AoA {:>4} -> {}".format(
            airfoil,
            model,
            tag,
            sbatch_name,
        )
    )


out = ROOT / "FULL_SWEEP_PRODUCTION_JOB_MANIFEST.csv"

with out.open("w", newline="") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "Airfoil",
            "Model",
            "AoA_tag",
            "Case",
            "SBATCH",
            "Log",
        ],
    )

    writer.writeheader()
    writer.writerows(created)


print()
print("=" * 80)
print("PRODUCTION JOB BUILD COMPLETE")
print("=" * 80)
print("Jobs created :", len(created))
print("Expected     : 32")
print("Manifest     :", out)

if len(created) != 32:
    raise RuntimeError(
        "Expected 32, created {}".format(
            len(created)
        )
    )

print("RESULT       : PASS")
print("=" * 80)
