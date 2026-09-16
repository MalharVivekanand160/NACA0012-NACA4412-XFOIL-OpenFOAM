# Computational environment

## OpenFOAM

The production CFD calculations were run with:

- OpenFOAM 13
- OpenFOAM.org distribution
- Build 13

The runtime version was verified directly from production SST, SA, and
SSTLM solver logs for both NACA 0012 and NACA 4412.

For each airfoil, the SST, SA, and SSTLM calculations used byte-identical
OpenFOAM `polyMesh` files (`points`, `faces`, `owner`, `neighbour`, and
`boundary` verified by SHA-256).

The NACA 0012 and NACA 4412 meshes have different `points` files because
the geometries differ, while their connectivity/topology files are
identical.

## XFOIL

XFOIL version 6.99 was used for the comparative aerodynamic calculations.

Production settings included:

- Reynolds number: 1e6
- Mach number: 0
- 240 panels
- Ncrit = 9
- maximum viscous iterations = 200

A 320-panel calculation was additionally used for panel-sensitivity
assessment.

## Python post-processing

Repository post-processing scripts require Python 3 with:

- NumPy
- Matplotlib

The PNG files used in the submitted thesis contain metadata identifying
Matplotlib 3.11.2.

The repository portability check was performed with Matplotlib 3.10.7.
The regenerated figures differed from the submitted PNGs by approximately
1--2 pixels in bounding-box dimensions. This is attributed to plotting
and text-layout differences between Matplotlib versions rather than a
change in the underlying aerodynamic data.

For exact raster reproduction, use the original plotting environment,
including Matplotlib 3.11.2 and compatible fonts/backend.

PDF and PNG files corresponding to the submitted thesis are retained
separately from regenerated repository outputs.
