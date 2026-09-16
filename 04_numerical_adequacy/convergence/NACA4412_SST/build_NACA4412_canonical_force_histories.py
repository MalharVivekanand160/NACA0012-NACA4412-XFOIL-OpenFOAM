from pathlib import Path
from decimal import Decimal

ROOT = Path("RAW_FORCE_COEFFICIENT_HISTORIES")
OUT = Path("CANONICAL_FORCE_COEFFICIENT_HISTORIES")

ANGLES = [
    "AoA00", "AoA02", "AoA04", "AoA06",
    "AoA08", "AoA10", "AoA12", "AoA14",
    "AoA14p5", "AoA15", "AoA15p5", "AoA16",
]

OUT.mkdir(exist_ok=True)

audit = []

for angle in ANGLES:
    force_root = ROOT / angle / "forceCoeffs"

    files = sorted(
        force_root.glob("*/forceCoeffs.dat"),
        key=lambda p: Decimal(p.parent.name)
    )

    if not files:
        raise RuntimeError(f"No forceCoeffs files found for {angle}")

    # Preserve the original OpenFOAM header from the first segment.
    header = []
    with files[0].open() as f:
        for line in f:
            if line.lstrip().startswith("#"):
                header.append(line)
            elif line.strip():
                break

    # Key = OpenFOAM steady-iteration/time index.
    # Later restart segments overwrite duplicate indices from earlier segments.
    rows = {}

    input_rows = 0
    segment_info = []

    for file in files:
        segment_rows = 0

        with file.open() as f:
            for line in f:
                stripped = line.strip()

                if not stripped or stripped.startswith("#"):
                    continue

                parts = stripped.split()

                try:
                    time_index = Decimal(parts[0])
                except Exception:
                    continue

                rows[time_index] = stripped
                input_rows += 1
                segment_rows += 1

        segment_info.append(
            (file.parent.name, segment_rows)
        )

    times = sorted(rows)

    outfile = OUT / f"forceCoeffs_{angle}_CANONICAL.dat"

    with outfile.open("w") as f:
        f.write(
            "# Canonical merged NACA4412 V9 SST forceCoeffs history\n"
        )
        f.write(
            "# Restart overlap is resolved by retaining the later "
            "segment at duplicate iteration indices.\n"
        )

        for line in header:
            f.write(line)

        for t in times:
            f.write(rows[t] + "\n")

    duplicate_count = input_rows - len(rows)

    audit.append(
        {
            "angle": angle,
            "segments": segment_info,
            "input_rows": input_rows,
            "unique_rows": len(rows),
            "duplicates": duplicate_count,
            "first": times[0],
            "last": times[-1],
            "outfile": outfile,
        }
    )

audit_file = OUT / "NACA4412_V9_SST_CANONICAL_FORCE_HISTORY_AUDIT.txt"

with audit_file.open("w") as f:
    f.write("NACA4412 V9 SST — CANONICAL FORCE HISTORY AUDIT\n")
    f.write("================================================\n\n")

    f.write(
        "Raw forceCoeffs files are preserved unchanged in:\n"
        "RAW_FORCE_COEFFICIENT_HISTORIES/\n\n"
    )

    f.write(
        "Canonical histories merge restart segments by OpenFOAM "
        "iteration/time index.\n"
        "If duplicate indices occur at a restart boundary, the later "
        "segment is retained.\n"
        "No interpolation or averaging is applied during merging.\n\n"
    )

    for item in audit:
        f.write("------------------------------------------------\n")
        f.write(f"{item['angle']}\n")
        f.write("------------------------------------------------\n")

        f.write("Segments:\n")
        for segment, nrows in item["segments"]:
            f.write(f"    {segment:>8s} : {nrows} rows\n")

        f.write(f"Input rows      : {item['input_rows']}\n")
        f.write(f"Unique rows     : {item['unique_rows']}\n")
        f.write(f"Duplicates      : {item['duplicates']}\n")
        f.write(f"First index     : {item['first']}\n")
        f.write(f"Last index      : {item['last']}\n")
        f.write(f"Canonical file  : {item['outfile']}\n\n")

print("Created canonical histories for all 12 AoA cases.")
print(f"Audit: {audit_file}")
