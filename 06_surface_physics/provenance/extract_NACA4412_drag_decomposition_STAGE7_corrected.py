from pathlib import Path
import re
import csv
import math

ROOT = Path(".")

RHO = 1.0
UINF = 15.0
AREF = 0.01
LREF = 1.0

QREF = 0.5 * RHO * UINF**2 * AREF
MREF = QREF * LREF

CASES = [
    ("00",    0.0, "FORMAL", None),
    ("02",    2.0, "FORMAL", None),
    ("04",    4.0, "FORMAL", None),
    ("06",    6.0, "FORMAL", None),
    ("08",    8.0, "FORMAL", None),
    ("10",   10.0, "FORMAL", None),
    ("12",   12.0, "FORMAL", None),
    ("14",   14.0, "FORMAL", None),
    ("14p5", 14.5, "FORMAL", None),
    ("15",   15.0, "STABLE_NOT_FORMAL", (15001, 16000)),
    ("15p5", 15.5, "STABLE_NOT_FORMAL", (11001, 12000)),
    ("16",   16.0, "STABLE_NOT_FORMAL", (11001, 12000)),
]


def case_path(tag):
    return (
        ROOT
        / ("AoA" + tag)
        / ("OF_NACA4412_V9_Re1e6_AoA{}_SST".format(tag))
    )


def latest_forces_file(case):
    root = case / "postProcessing" / "forcesIncompressible"

    candidates = []

    for p in root.iterdir():
        if not p.is_dir():
            continue

        try:
            t = float(p.name)
        except ValueError:
            continue

        f = p / "forces.dat"

        if f.is_file():
            candidates.append((t, p.name, f))

    if not candidates:
        raise RuntimeError(
            "No forcesIncompressible/forces.dat in {}".format(case)
        )

    return max(candidates, key=lambda x: x[0])


def parse_forces(path):
    lines = [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip()
        and not line.lstrip().startswith("#")
    ]

    if not lines:
        raise RuntimeError("No data in {}".format(path))

    line = lines[-1]

    vecs = re.findall(
        r"\(\s*"
        r"([-+0-9.eE]+)\s+"
        r"([-+0-9.eE]+)\s+"
        r"([-+0-9.eE]+)\s*\)",
        line
    )

    if len(vecs) != 4:
        raise RuntimeError(
            "Expected 4 vectors in {}, got {}".format(
                path, len(vecs)
            )
        )

    vals = [
        tuple(float(x) for x in v)
        for v in vecs
    ]

    return vals[0], vals[1], vals[2], vals[3]


def canonical_forcecoeff_rows(case):
    root = case / "postProcessing" / "forceCoeffs"

    segments = []

    for p in root.iterdir():
        if not p.is_dir():
            continue

        try:
            start = float(p.name)
        except ValueError:
            continue

        f = p / "forceCoeffs.dat"

        if f.is_file():
            segments.append((start, f))

    segments.sort(key=lambda x: x[0])

    canonical = {}

    # Later restart segments overwrite duplicate iteration numbers.
    for _, path in segments:
        for line in path.read_text().splitlines():
            s = line.strip()

            if not s or s.startswith("#"):
                continue

            vals = s.split()

            if len(vals) < 4:
                continue

            t = float(vals[0])

            canonical[t] = {
                "time": t,
                "Cm": float(vals[1]),
                "Cd": float(vals[2]),
                "Cl": float(vals[3]),
            }

    if not canonical:
        raise RuntimeError(
            "No forceCoeffs rows found in {}".format(case)
        )

    return [
        canonical[t]
        for t in sorted(canonical)
    ]


def row_at_time(rows, target):
    matches = [
        r for r in rows
        if abs(r["time"] - target) < 1.0e-9
    ]

    if len(matches) != 1:
        raise RuntimeError(
            "Could not uniquely find forceCoeffs time {}".format(target)
        )

    return matches[0]


def reported_coefficients(rows, status, window):
    if status == "FORMAL":
        r = rows[-1]

        return {
            "method": "FINAL_CONVERGED_ROW",
            "window": "{:g}".format(r["time"]),
            "n_rows": 1,
            "Cm": r["Cm"],
            "Cd": r["Cd"],
            "Cl": r["Cl"],
        }

    start, end = window

    selected = [
        r for r in rows
        if start <= r["time"] <= end
    ]

    if not selected:
        raise RuntimeError(
            "No forceCoeffs rows in {}-{}".format(start, end)
        )

    def mean(name):
        return (
            sum(r[name] for r in selected)
            / float(len(selected))
        )

    return {
        "method": "FINAL_ITERATIVE_WINDOW_MEAN",
        "window": "{}-{}".format(start, end),
        "n_rows": len(selected),
        "Cm": mean("Cm"),
        "Cd": mean("Cd"),
        "Cl": mean("Cl"),
    }


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


rows_out = []

print()
print("===================================================================")
print("NACA4412 V9 SST — CORRECTED STAGE-7 FORCE DECOMPOSITION")
print("===================================================================")
print("Snapshot decomposition from forcesIncompressible")
print("Reporting coefficient follows Stage-3 convergence policy")
print("Reference force  = {:.9f}".format(QREF))
print("Reference moment = {:.9f}".format(MREF))
print()

for tag, aoa, status, window in CASES:

    case = case_path(tag)

    t, tname, forcefile = latest_forces_file(case)

    fp, fv, mp, mv = parse_forces(forcefile)

    alpha = math.radians(aoa)

    drag = (
        math.cos(alpha),
        math.sin(alpha),
        0.0,
    )

    lift = (
        -math.sin(alpha),
        math.cos(alpha),
        0.0,
    )

    cd_p = dot(fp, drag) / QREF
    cd_v = dot(fv, drag) / QREF
    cd_sum = cd_p + cd_v

    cl_p = dot(fp, lift) / QREF
    cl_v = dot(fv, lift) / QREF
    cl_sum = cl_p + cl_v

    cm_p = mp[2] / MREF
    cm_v = mv[2] / MREF
    cm_sum = cm_p + cm_v

    fc_rows = canonical_forcecoeff_rows(case)

    snapshot_fc = row_at_time(fc_rows, t)

    reported = reported_coefficients(
        fc_rows,
        status,
        window,
    )

    row = {
        "AoA_deg": aoa,
        "Status": status,
        "Snapshot_time": tname,

        "Cd_pressure_snapshot": cd_p,
        "Cd_viscous_snapshot": cd_v,
        "Cd_snapshot_sum": cd_sum,
        "Cd_forceCoeffs_same_snapshot": snapshot_fc["Cd"],
        "Cd_snapshot_closure_error":
            cd_sum - snapshot_fc["Cd"],

        "pressure_drag_percent_snapshot":
            100.0 * cd_p / cd_sum,
        "viscous_drag_percent_snapshot":
            100.0 * cd_v / cd_sum,

        "Cl_pressure_snapshot": cl_p,
        "Cl_viscous_snapshot": cl_v,
        "Cl_snapshot_sum": cl_sum,
        "Cl_forceCoeffs_same_snapshot": snapshot_fc["Cl"],
        "Cl_snapshot_closure_error":
            cl_sum - snapshot_fc["Cl"],

        "Cm_pressure_raw_snapshot": cm_p,
        "Cm_viscous_raw_snapshot": cm_v,
        "Cm_snapshot_sum_raw": cm_sum,
        "Cm_forceCoeffs_same_snapshot_raw": snapshot_fc["Cm"],
        "Cm_snapshot_closure_error_raw":
            cm_sum - snapshot_fc["Cm"],

        "Reporting_method": reported["method"],
        "Reporting_window": reported["window"],
        "Reporting_n_rows": reported["n_rows"],

        "Cd_reported": reported["Cd"],
        "Cl_reported": reported["Cl"],
        "Cm_reported_raw": reported["Cm"],

        "Cd_snapshot_minus_reported":
            cd_sum - reported["Cd"],
        "Cl_snapshot_minus_reported":
            cl_sum - reported["Cl"],
        "Cm_snapshot_minus_reported_raw":
            cm_sum - reported["Cm"],
    }

    rows_out.append(row)

    print(
        "AoA {:>4.1f} | snapshot {:>5s} | "
        "Cd_p={:.8f} Cd_v={:.8f} Cd={:.8f} | "
        "FC_same={:.8f} | closure={:+.3e} | "
        "reported={:.8f} ({})".format(
            aoa,
            tname,
            cd_p,
            cd_v,
            cd_sum,
            snapshot_fc["Cd"],
            cd_sum - snapshot_fc["Cd"],
            reported["Cd"],
            reported["window"],
        )
    )


OUT = ROOT / (
    "NACA4412_V9_SST_DRAG_DECOMPOSITION_STAGE7_CORRECTED.csv"
)

with OUT.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(rows_out[0].keys())
    )

    writer.writeheader()
    writer.writerows(rows_out)


print()
print("Created:")
print(OUT)
