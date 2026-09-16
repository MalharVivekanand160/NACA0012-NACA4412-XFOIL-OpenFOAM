#!/bin/bash -l

#SBATCH --job-name=N4412_V9_A00
#SBATCH --partition=work
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=02:00:00
#SBATCH --output=slurm_V9_N4412_A00_%j.out
#SBATCH --error=slurm_V9_N4412_A00_%j.err

module purge
module load gcc/12.1.0
module load openmpi/4.1.3-gcc12.1.0
module load openfoam/13

cd "$SLURM_SUBMIT_DIR" || exit 1

echo "Host: $(hostname)"
echo "Case: $(pwd)"
echo "Start: $(date)"
echo

foamRun 2>&1 | tee log.foamRun_V9_N4412_AoA00

SOLVER_STATUS=${PIPESTATUS[0]}

echo
echo "Solver exit status: $SOLVER_STATUS"
echo "End: $(date)"

exit "$SOLVER_STATUS"
