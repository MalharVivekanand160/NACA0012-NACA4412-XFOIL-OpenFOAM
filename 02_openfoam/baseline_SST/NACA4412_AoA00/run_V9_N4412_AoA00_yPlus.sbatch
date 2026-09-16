#!/bin/bash -l

#SBATCH --job-name=N4412_V9_YP
#SBATCH --partition=work
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:15:00
#SBATCH --output=slurm_V9_N4412_A00_YP_%j.out
#SBATCH --error=slurm_V9_N4412_A00_YP_%j.err

module purge
module load gcc/12.1.0
module load openmpi/4.1.3-gcc12.1.0
module load openfoam/13

cd "$SLURM_SUBMIT_DIR" || exit 1

echo "===== LATEST WRITTEN TIME ====="
foamListTimes -latestTime

echo
echo "===== AIRFOIL NUT WALL CONDITION ====="
foamDictionary 0/nut -entry boundaryField/airfoil/type -value

echo
echo "===== YPLUS ====="

foamPostProcess \
-solver incompressibleFluid \
-func yPlus \
-latestTime \
2>&1 | tee log.yPlus_V9_N4412_AoA00

STATUS=${PIPESTATUS[0]}

echo
echo "===== YPLUS SUMMARY ====="
grep -Ei 'y+|yPlus|minimum|maximum|average' \
log.yPlus_V9_N4412_AoA00 | tail -20 || true

exit "$STATUS"
