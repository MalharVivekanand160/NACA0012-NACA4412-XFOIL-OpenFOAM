#!/usr/bin/env python3

from pathlib import Path
import shutil
import math
import re
import csv

ROOT = Path.home() / "NACA0012_4412_XFOIL_RANS_COMPARISON"

AOAS = [
    ("00", 0.0),
    ("02", 2.0),
    ("04", 4.0),
    ("06", 6.0),
    ("08", 8.0),
    ("10", 10.0),
    ("12", 12.0),
    ("14", 14.0),
    ("14p5", 14.5),
    ("15", 15.0),
    ("15p5", 15.5),
    ("16", 16.0),
]

EXISTING = {
    ("NACA0012", "SA"): {"00", "08", "14", "16"},
    ("NACA0012", "SSTLM"): {"00", "06", "12", "16"},
    ("NACA4412", "SA"): {"00", "08", "14", "16"},
    ("NACA4412", "SSTLM"): {"00", "06", "12", "16"},
}

CONFIG = {
    "NACA0012": {
        "sst_root":
            ROOT /
            "NACA0012_CGRID_V1_OpenFOAM/NEW_FILES/01_runs_V9_SST",

        "sa_root":
            ROOT /
            "NACA0012_CGRID_V1_OpenFOAM/NEW_FILES/02_runs_V9_SA",

        "sa_template":
            ROOT /
            "NACA0012_CGRID_V1_OpenFOAM/NEW_FILES/02_runs_V9_SA/"
            "AoA00/OF_NACA0012_V9_Re1e6_AoA00_SA",

        "sstlm_root":
            ROOT /
            "NACA0012_CGRID_V1_OpenFOAM/NEW_FILES/05_runs_V9_SSTLM",

        "sstlm_template":
            ROOT /
            "NACA0012_CGRID_V1_OpenFOAM/NEW_FILES/05_runs_V9_SSTLM/"
            "AoA00/OF_NACA0012_V9_Re1e6_AoA00_SSTLM",
    },

    "NACA4412": {
        "sst_root":
            ROOT /
            "NACA4412_CGRID_V9_OpenFOAM/01_runs_V9_SST",

        "sa_root":
            ROOT /
            "NACA4412_CGRID_V9_OpenFOAM/02_runs_V9_SA",

        "sa_template":
            ROOT /
            "NACA4412_CGRID_V9_OpenFOAM/02_runs_V9_SA/"
            "AoA00/OF_NACA4412_V9_Re1e6_AoA00_SA",

        "sstlm_root":
            ROOT /
            "NACA4412_CGRID_V9_OpenFOAM/03_runs_V9_SSTLM",

        "sstlm_template":
            ROOT /
            "NACA4412_CGRID_V9_OpenFOAM/03_runs_V9_SSTLM/"
            "AoA00/OF_NACA4412_V9_Re1e6_AoA00_SSTLM",
    },
}

SST_FIELDS = ["U", "p", "k", "omega", "nut"]


def set_entry(text, key, value):
    pattern = (
        r"(^\s*" + re.escape(key) +
        r"\s+)([^;]+)(\s*;)"
    )

    new, n = re.subn(
        pattern,
        lambda m: m.group(1) + str(value) + m.group(3),
        text,
        count=1,
        flags=re.M,
    )

    if n != 1:
        raise RuntimeError(
            "Expected one '{}' entry, found {}".format(key, n)
        )

    return new


def patch_control_dict(path, alpha):
    a = math.radians(alpha)

    ca = math.cos(a)
    sa = math.sin(a)

    drag = "({:.10f} {:.10f} 0)".format(ca, sa)
    lift = "({:.10f} {:.10f} 0)".format(-sa, ca)

    text = path.read_text()

    for key, value in [
        ("startFrom", "startTime"),
        ("startTime", "0"),
        ("endTime", "12000"),
        ("writeControl", "timeStep"),
        ("writeInterval", "100"),
        ("purgeWrite", "2"),
    ]:
        text = set_entry(text, key, value)

    text, nd = re.subn(
        r"(^\s*dragDir\s*)\([^;]+\)(\s*;)",
        lambda m: m.group(1) + drag + m.group(2),
        text,
        flags=re.M,
    )

    text, nl = re.subn(
        r"(^\s*liftDir\s*)\([^;]+\)(\s*;)",
        lambda m: m.group(1) + lift + m.group(2),
        text,
        flags=re.M,
    )

    if nd != 1 or nl != 1:
        raise RuntimeError(
            "{}: dragDir={}, liftDir={}".format(path, nd, nl)
        )

    path.write_text(text)


def patch_SA_U(path, alpha):
    a = math.radians(alpha)

    ux = 15.0 * math.cos(a)
    uy = 15.0 * math.sin(a)

    vec = "({:.10f} {:.10f} 0)".format(ux, uy)

    text = path.read_text()

    text, ni = re.subn(
        r"(^\s*internalField\s+uniform\s*)\([^;]+\)(\s*;)",
        lambda m: m.group(1) + vec + m.group(2),
        text,
        flags=re.M,
    )

    text, nf = re.subn(
        r"(^\s*freestreamValue\s+uniform\s*)\([^;]+\)(\s*;)",
        lambda m: m.group(1) + vec + m.group(2),
        text,
        flags=re.M,
    )

    if ni != 1:
        raise RuntimeError(
            "{}: expected one uniform internalField, found {}"
            .format(path, ni)
        )

    if nf == 0:
        raise RuntimeError(
            "{}: no freestreamValue entries found".format(path)
        )

    path.write_text(text)


def latest_SST_time(case):
    candidates = []

    for p in case.iterdir():
        if not p.is_dir():
            continue

        try:
            t = float(p.name)
        except ValueError:
            continue

        if t <= 0:
            continue

        if all((p / field).is_file() for field in SST_FIELDS):
            candidates.append((t, p))

    if not candidates:
        raise RuntimeError(
            "No complete SST solution time in {}".format(case)
        )

    candidates.sort(key=lambda x: x[0])

    return candidates[-1][1]


def reset_location(path):
    text = path.read_text()

    text, n = re.subn(
        r'(^\s*location\s+)"[^"]+"(\s*;)',
        r'\1"0"\2',
        text,
        count=1,
        flags=re.M,
    )

    if n != 1:
        raise RuntimeError(
            "Could not reset location in {}".format(path)
        )

    path.write_text(text)


def create_base(template, target):
    if target.exists():
        raise RuntimeError(
            "REFUSING TO OVERWRITE:\n{}".format(target)
        )

    target.mkdir(parents=True)

    for name in ["0", "constant", "system"]:
        src = template / name
        dst = target / name

        if not src.exists():
            raise RuntimeError(
                "Missing template component: {}".format(src)
            )

        shutil.copytree(str(src), str(dst))


manifest = []

print("=" * 104)
print("FULL SA/SSTLM SWEEP V2 GENERATOR")
print("=" * 104)

for airfoil in ["NACA0012", "NACA4412"]:

    cfg = CONFIG[airfoil]

    # ========================================================
    # SA
    # ========================================================

    print()
    print("{} SA".format(airfoil))
    print("-" * 104)

    for tag, alpha in AOAS:

        if tag in EXISTING[(airfoil, "SA")]:
            print("AoA {:>4}: EXISTING — untouched".format(tag))
            continue

        target = (
            cfg["sa_root"] /
            ("AoA" + tag) /
            ("OF_{}_V9_Re1e6_AoA{}_SA".format(
                airfoil, tag
            ))
        )

        target.parent.mkdir(parents=True, exist_ok=True)

        create_base(
            cfg["sa_template"],
            target,
        )

        patch_SA_U(
            target / "0/U",
            alpha,
        )

        patch_control_dict(
            target / "system/controlDict",
            alpha,
        )

        manifest.append({
            "Airfoil": airfoil,
            "Model": "SA",
            "AoA_tag": tag,
            "AoA_deg": alpha,
            "Initialization": "SA_AoA00_template_uniform",
            "SST_initialization_time": "",
            "Case": str(target),
        })

        print(
            "AoA {:>4}: CREATED | SA template".format(tag)
        )

    # ========================================================
    # SSTLM
    # ========================================================

    print()
    print("{} SSTLM".format(airfoil))
    print("-" * 104)

    for tag, alpha in AOAS:

        if tag in EXISTING[(airfoil, "SSTLM")]:
            print("AoA {:>4}: EXISTING — untouched".format(tag))
            continue

        sst_case = (
            cfg["sst_root"] /
            ("AoA" + tag) /
            ("OF_{}_V9_Re1e6_AoA{}_SST".format(
                airfoil, tag
            ))
        )

        if not sst_case.is_dir():
            raise RuntimeError(
                "Missing SST source case:\n{}".format(sst_case)
            )

        source_time = latest_SST_time(sst_case)

        target = (
            cfg["sstlm_root"] /
            ("AoA" + tag) /
            ("OF_{}_V9_Re1e6_AoA{}_SSTLM".format(
                airfoil, tag
            ))
        )

        target.parent.mkdir(parents=True, exist_ok=True)

        create_base(
            cfg["sstlm_template"],
            target,
        )

        # Replace SST variables with same-AoA final SST solution.
        for field in SST_FIELDS:
            src = source_time / field
            dst = target / "0" / field

            shutil.copy2(str(src), str(dst))
            reset_location(dst)

        # ReThetat and gammaInt remain from the verified
        # SSTLM production template.

        patch_control_dict(
            target / "system/controlDict",
            alpha,
        )

        manifest.append({
            "Airfoil": airfoil,
            "Model": "SSTLM",
            "AoA_tag": tag,
            "AoA_deg": alpha,
            "Initialization": "same_AoA_final_SST_solution",
            "SST_initialization_time": source_time.name,
            "Case": str(target),
        })

        print(
            "AoA {:>4}: CREATED | SST init time {}".format(
                tag,
                source_time.name,
            )
        )


manifest_path = (
    ROOT /
    "FULL_SA_SSTLM_SWEEP_GENERATION_MANIFEST_V2.csv"
)

with manifest_path.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "Airfoil",
            "Model",
            "AoA_tag",
            "AoA_deg",
            "Initialization",
            "SST_initialization_time",
            "Case",
        ],
    )

    writer.writeheader()
    writer.writerows(manifest)


print()
print("=" * 104)
print("GENERATION COMPLETE")
print("=" * 104)
print("New cases :", len(manifest))
print("Expected  : 32")
print("Manifest  :", manifest_path)

if len(manifest) != 32:
    raise RuntimeError(
        "Expected 32 cases, generated {}".format(
            len(manifest)
        )
    )

print("RESULT    : PASS")
print("=" * 104)
