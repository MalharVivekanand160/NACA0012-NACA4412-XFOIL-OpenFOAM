#!/usr/bin/env python3

from pathlib import Path
import csv
import math
import re


ROOT = Path("01_runs_V9_SST")

CASES = {
    "00": ROOT / "AoA00/OF_NACA0012_V9_Re1e6_AoA00_SST",
    "06": ROOT / "AoA06/OF_NACA0012_V9_Re1e6_AoA06_SST",
    "12": ROOT / "AoA12/OF_NACA0012_V9_Re1e6_AoA12_SST",
    "16": ROOT / "AoA16/OF_NACA0012_V9_Re1e6_AoA16_SST",
}

OUTDIR = ROOT / "wallShear_validation"
OUTDIR.mkdir(exist_ok=True)


def latest_numeric_time(case):
    values = []

    for p in case.iterdir():
        if not p.is_dir():
            continue

        try:
            t = float(p.name)
        except ValueError:
            continue

        values.append((t, p.name))

    if not values:
        raise RuntimeError(f"No numerical times found in {case}")

    return max(values)[1]


def read_wss_airfoil(path):
    text = path.read_text()

    m = re.search(
        r'\bairfoil\s*\{.*?'
        r'value\s+nonuniform\s+List<vector>\s*'
        r'(\d+)\s*'
        r'\(\s*(.*?)\s*\)\s*;',
        text,
        re.S
    )

    if not m:
        raise RuntimeError(
            f"Could not extract airfoil wallShearStress from {path}"
        )

    n = int(m.group(1))

    vectors = [
        tuple(map(float, xyz))
        for xyz in re.findall(
            r'\(\s*'
            r'([-+0-9.eE]+)\s+'
            r'([-+0-9.eE]+)\s+'
            r'([-+0-9.eE]+)\s*'
            r'\)',
            m.group(2)
        )
    ]

    if len(vectors) != n:
        raise RuntimeError(
            f"{path}: expected {n} vectors, found {len(vectors)}"
        )

    return vectors


def read_coordinates(path):
    rows = []

    with path.open() as f:
        reader = csv.DictReader(f)

        for row in reader:
            rows.append({
                "face": int(row["face"]),
                "x": float(row["x_over_c"]),
                "y": float(row["y_over_c"]),
                "z": float(row["z"]),
            })

    rows.sort(key=lambda r: r["face"])

    return rows


def assign_tangents(rows):
    """
    Construct local downstream tangent LE -> TE separately
    on upper and lower surfaces.

    Surface points are sorted by increasing x/c.
    """

    for surface_name, condition in [
        ("upper", lambda r: r["y"] > 0),
        ("lower", lambda r: r["y"] < 0),
    ]:

        surface = [
            r for r in rows
            if condition(r)
        ]

        surface.sort(key=lambda r: r["x"])

        for i, row in enumerate(surface):

            if i == 0:
                a = surface[i]
                b = surface[i + 1]

            elif i == len(surface) - 1:
                a = surface[i - 1]
                b = surface[i]

            else:
                a = surface[i - 1]
                b = surface[i + 1]

            dx = b["x"] - a["x"]
            dy = b["y"] - a["y"]

            mag = math.sqrt(dx*dx + dy*dy)

            tx = dx / mag
            ty = dy / mag

            # Ensure tangent points LE -> TE,
            # therefore positive chordwise direction.
            if tx < 0:
                tx = -tx
                ty = -ty

            row["surface"] = surface_name
            row["tangent_x"] = tx
            row["tangent_y"] = ty


for A, case in CASES.items():

    time = latest_numeric_time(case)

    coord_file = (
        ROOT
        / "Cp_validation"
        / f"OpenFOAM_V9_Cp_AoA{A}.csv"
    )

    wss_file = case / time / "wallShearStress"

    if not coord_file.exists():
        raise RuntimeError(f"Missing coordinate CSV: {coord_file}")

    if not wss_file.exists():
        raise RuntimeError(f"Missing wallShearStress: {wss_file}")

    coords = read_coordinates(coord_file)
    wss = read_wss_airfoil(wss_file)

    if len(coords) != len(wss):
        raise RuntimeError(
            f"AoA{A}: coordinates={len(coords)}, WSS={len(wss)}"
        )

    rows = []

    for coord, vec in zip(coords, wss):

        tx_wss, ty_wss, tz_wss = vec

        row = dict(coord)

        row["wss_x"] = tx_wss
        row["wss_y"] = ty_wss
        row["wss_z"] = tz_wss

        row["wss_mag"] = math.sqrt(
            tx_wss**2
            + ty_wss**2
            + tz_wss**2
        )

        rows.append(row)

    assign_tangents(rows)

    for row in rows:

        projection = (
            row["wss_x"] * row["tangent_x"]
            + row["wss_y"] * row["tangent_y"]
        )

        # Calibrated sign:
        # positive should correspond to attached
        # downstream surface flow.
        row["tau_t_attached"] = -projection

    outfile = (
        OUTDIR
        / f"OpenFOAM_V9_wallShear_AoA{A}.csv"
    )

    fieldnames = [
        "face",
        "surface",
        "x",
        "y",
        "z",
        "wss_x",
        "wss_y",
        "wss_z",
        "wss_mag",
        "tangent_x",
        "tangent_y",
        "tau_t_attached",
    ]

    with outfile.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    upper = sorted(
        [r for r in rows if r["surface"] == "upper"],
        key=lambda r: r["x"]
    )

    # Ignore the immediate LE region for this first diagnostic,
    # because stagnation naturally drives wall shear toward zero.
    upper_diag = [
        r for r in upper
        if r["x"] >= 0.02
    ]

    negative = [
        r for r in upper_diag
        if r["tau_t_attached"] < 0
    ]

    print()
    print("========================================")
    print(f"AoA {A}")
    print("========================================")
    print("time            :", time)
    print("airfoil faces   :", len(rows))
    print("upper faces     :", len(upper))
    print(
        "upper tau range : {:.6e} -> {:.6e}".format(
            min(r["tau_t_attached"] for r in upper_diag),
            max(r["tau_t_attached"] for r in upper_diag),
        )
    )
    print(
        "negative upper  : {} / {} faces (x/c >= 0.02)".format(
            len(negative),
            len(upper_diag)
        )
    )

    if negative:
        print(
            "negative x/c    : {:.6f} -> {:.6f}".format(
                min(r["x"] for r in negative),
                max(r["x"] for r in negative),
            )
        )
    else:
        print("negative x/c    : none")

    print("CSV             :", outfile)


print()
print("Wall-shear extraction complete.")
