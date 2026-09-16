# Comparative Aerodynamic Analysis of NACA 0012 and NACA 4412 Using XFOIL and OpenFOAM

Reproducibility archive for the FAU Erlangen-Nürnberg project thesis:

**Comparative Aerodynamic Analysis of NACA 0012 and NACA 4412 Airfoils Using XFOIL and OpenFOAM**

**Author:** Malhar Vivekanand  
**Institution:** FAU Erlangen-Nürnberg  
**Institute:** Institute of Fluid Mechanics (LSTM)  
**Technical Report:** 29/2026

## Overview

This repository contains the curated computational inputs, representative
OpenFOAM cases, aerodynamic data, numerical-adequacy evidence,
post-processing scripts, and final figures associated with a comparative
study of the NACA 0012 and NACA 4412 airfoils.

The study compares:

- XFOIL predictions
- steady incompressible RANS calculations in OpenFOAM
- turbulence/transition-model sensitivity using:
  - k-omega SST
  - Spalart-Allmaras (SA)
  - k-omega SSTLM

The purpose is to compare aerodynamic trends and modelling behaviour.
XFOIL is used as an independent numerical reference and is not treated as
experimental truth.

## Flow conditions

Principal conditions:

- Reynolds number: **1,000,000**
- chord: **1 m**
- freestream velocity: **15 m/s**
- kinematic viscosity: **1.5e-5 m²/s**
- XFOIL Mach number: **0**
- two-dimensional airfoil configuration

Nominal angle-of-attack sweep:

```text
0, 2, 4, 6, 8, 10, 12, 14, 14.5, 15, 15.5, 16 deg

```

The final common quantitative comparison range used in the submitted
thesis is **0--14.5 deg**.

The NACA 4412 SST cases at 15, 15.5, and 16 degrees did not satisfy the
adopted formal steady-convergence criteria. They are retained as
diagnostic evidence but are not used as accepted steady values in the
final quantitative comparison.

## Numerical methods

### XFOIL

XFOIL 6.99 was used with:

- 240 production panels
- Reynolds number = 1e6
- Mach number = 0
- Ncrit = 9
- maximum viscous iterations = 200

A 320-panel calculation was additionally used for panel-sensitivity
assessment.

### OpenFOAM

The CFD calculations were performed with **OpenFOAM 13** from
OpenFOAM.org using a steady incompressible RANS/SIMPLE framework.

The baseline turbulence model was **k-omega SST**.

Additional model-sensitivity calculations used:

- Spalart-Allmaras
- k-omega SSTLM

The production meshes contain **165,220 structured hexahedral cells**
for each airfoil.

For each airfoil, SST, SA, and SSTLM used byte-identical OpenFOAM
polyMesh files. Identity was verified using SHA-256 hashes for
points, faces, owner, neighbour, and boundary.

## Convergence policy

Residual thresholds used in the convergence assessment were:

- pressure: <= 1e-4
- velocity: <= 1e-5
- k: <= 1e-5
- omega: <= 1e-5

Aerodynamic coefficients were monitored in addition to residuals.

All NACA 0012 baseline SST cases satisfied the adopted steady-convergence
criteria.

For NACA 4412, the SST calculations at 15, 15.5, and 16 degrees did not
satisfy the formal steady-convergence criteria.

These high-angle cases are retained as diagnostic evidence but are
excluded from the accepted common-range quantitative comparison.

SIMPLE iterations are numerical solver iterations and are not interpreted
as physical time.

## Model-sensitivity dataset

The final thesis sensitivity assessment uses only retained cases within
the common quantitative range.

| Airfoil | Model | Retained cases |
|---|---|---:|
| NACA 0012 | SA | 9/9 |
| NACA 0012 | SSTLM | 8/9 |
| NACA 4412 | SA | 9/9 |
| NACA 4412 | SSTLM | 3/9 |

Total retained sensitivity cases: **29**.

The final thesis-consistent sensitivity data are stored in:

08_model_sensitivity/final_common_range/

The broader 48-run SA/SSTLM campaign is retained separately as
provenance in:

08_model_sensitivity/provenance/

The provenance dataset documents the wider computational campaign and
should not be interpreted as the final retained quantitative subset.

The repository script

08_model_sensitivity/build_final_thesis_sensitivity_dataset.py

reconstructs the 29-case final dataset and verifies the summary metrics
against the submitted thesis values.

## Separation criterion

Upper-surface separation was identified using the signed skin-friction
coefficient, Cf.

A separated region was accepted when:

- at least five contiguous upper-surface faces had negative signed Cf,
- the reversed-flow region remained connected to the trailing-edge region,
- the connected reversed-flow region extended to at least x/c >= 0.95.

The reported separation location is the first upstream face belonging to
that trailing-edge-connected reversed-flow region.

This operational criterion was used to reject isolated local sign changes
and provide repeatable separation detection.

Separation is not treated as equivalent to stall, and no stall angle is
claimed from the steady calculations.

## Repository structure

01_geometry_mesh/
    Geometry-generation files, structured C-grid generation,
    production meshes, and mesh audits.

02_openfoam/
    Representative OpenFOAM SST, SA, and SSTLM case configurations.

03_xfoil/
    XFOIL geometry, production calculations, panel-sensitivity data,
    and Cp reference files.

04_numerical_adequacy/
    Convergence evidence, y+ results, mesh-sensitivity calculations,
    and numerical-adequacy checks.

05_primary_results/
    SST-versus-XFOIL aerodynamic coefficient tables and figures,
    including a repository-portable regeneration script.

06_surface_physics/
    Cp distributions, drag decomposition, separation data,
    and the final 14.5-degree Cp comparison.

07_final_synthesis/
    Common-range L/D, pressure-drag, and separation synthesis.

08_model_sensitivity/
    Final thesis-consistent turbulence/transition-model sensitivity
    data, figures, reconstruction script, and provenance material.

## Reproducing selected outputs

The principal repository-portable post-processing scripts are:

python3 05_primary_results/make_stage6_primary_figures_repo.py

python3 06_surface_physics/final_cp_14p5/make_cp_14p5_repo.py

python3 07_final_synthesis/make_stage9_synthesis_figures_repo.py

python3 08_model_sensitivity/build_final_thesis_sensitivity_dataset.py

Regenerated plots are written to dedicated reproduced/ directories so that
the archived figures corresponding to the submitted thesis are not
overwritten.

See ENVIRONMENT.md for software-version information.

## Important limitations

The results should be interpreted with the following limitations:

- no experimental dataset was used as an absolute validation reference,
- XFOIL is an independent numerical comparison rather than ground truth,
- the CFD calculations are two-dimensional,
- steady RANS does not represent physical-time unsteady separated flow,
- the non-converged NACA 4412 high-angle SST cases are excluded from the
  accepted common-range quantitative comparison,
- mesh-sensitivity studies were performed, but no formal Grid Convergence
  Index was claimed,
- aerodynamic predictions, particularly drag, remain sensitive to
  turbulence and transition modelling.

## Provenance and repository curation

This repository is a curated reproducibility archive rather than a raw
dump of every project file.

Files were retained when they directly support the submitted methodology,
results, numerical checks, figures, or documented limitations.

Some original thesis-workflow scripts are preserved as provenance even
when they contain paths associated with the original local working
directory. Separate repository-portable scripts are provided for the main
reproducibility workflows.

OpenFOAM runtime logs were retained as computational evidence. Personal
HPC home-directory prefixes were replaced with:

<HPC_HOME>

This sanitization does not change solver output, convergence histories,
aerodynamic coefficients, mesh diagnostics, or OpenFOAM version
information.

## Figure reproducibility

The archived PNG figures corresponding to the submitted thesis identify
Matplotlib 3.11.2 in their metadata.

Portable reproduction was tested using Matplotlib 3.10.7.

The regenerated images differed by approximately 1--2 pixels in bounding-
box dimensions. This is consistent with plotting-library rendering and
layout differences between versions rather than changes in the underlying
aerodynamic data.

For exact raster reproduction, the original Matplotlib 3.11.2 environment,
compatible fonts, and rendering backend should be used.

## Thesis document

The signed submitted thesis PDF is not included in this repository because
it contains personal signature information.

The repository instead contains the computational material required to
trace and reproduce the principal numerical results.

## License

No open-source license is currently assigned to this repository.

Reuse or redistribution should not be assumed until ownership,
institutional, and publication requirements have been checked.
