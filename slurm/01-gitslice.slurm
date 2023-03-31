#!/usr/bin/env sh
#SBATCH --job-name=git-slice     # create a short name for your job
#SBATCH --partition=k2-medpri    # job priority, < 3 hours = --partition=k2-hipri, > 3 hours and < 24 hours = --partition=k2-medpri, > 24 hours = --partition=k2-lowpri
#SBATCH --nodes=5                # node count
#SBATCH --ntasks=25              # total number of tasks across all nodes
#SBATCH --cpus-per-task=1        # cpu-cores per task (>1 if multi-threaded tasks)
#SBATCH --mem-per-cpu=16G        # memory per cpu-core (4G per cpu-core is default)
#SBATCH --time=12:00:00          # total run time limit (HH:MM:SS)

# Core application is written in Python
module add apps/python3/3.10.5
# MPI is used for executing the analysis across multiple nodes, support provided by torcpy
module add mpi/openmpi/4.0.4
# Perhaps unexpectedly, GitSlice requires Git!
module add apps/git/2.34.1
# Singularity will be used to run our Docker containers
module add apps/singularity/3.10.0

# Bring up Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Ensure required packages are available in
python3 -m pip install -r requirements.txt

# Run the program
TORCPY_WORKERS=5 mpirun -np 5 python3 git-slice/main.py -c config.yaml -l 20
