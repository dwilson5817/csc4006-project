#!/usr/bin/env sh
#SBATCH --job-name=git-slice     # create a short name for your job
#SBATCH --nodes=1                # node count
#SBATCH --ntasks=1               # total number of tasks across all nodes
#SBATCH --cpus-per-task=1        # cpu-cores per task (>1 if multi-threaded tasks)
#SBATCH --mem-per-cpu=128M       # memory per cpu-core (4G per cpu-core is default)
#SBATCH --time=00:01:00          # total run time limit (HH:MM:SS)

# A simple entrypoint to create all other jobs.
#
# This script finds all the SLURM scripts in $SLURM_DIR/*.$FILE_EXT, i.e. slurm/00-job1.slurm, slurm/01-job2.slurm etc.
# and creates a new SLURM job to run them.  The scripts are run in alphanumeric order so it's highly recommended to use
# a number at the beginning of the filename to denote order.

# Directory of SLURM scripts.  No trailing slash please!
SLURM_DIR='slurm'
# File extension for SLURM scripts.  Everything else will be ignored.  No preceding dot please!
FILE_EXT='slurm'


for FILE in "$SLURM_DIR"/*."$FILE_EXT"
do
  echo "> $FILE"

  if [ ! -z "$PREVIOUS_JID" ]
  then
      echo "  > Got previous JID as ${PREVIOUS_JID}, this job will depend on its success"

      re='^[0-9]+$'
      if ! [[ $PREVIOUS_JID =~ $re ]] ; then
         echo "  > fatal: JID not a number, did SLURM give an error?" >&2; exit 1
      fi

      OUTPUT=$(sbatch -d afterok:"$PREVIOUS_JID" --parsable "$FILE")
  else
      OUTPUT=$(sbatch --parsable "$FILE")
  fi

  IFS=',' read -ra OUTPUT <<< "$OUTPUT"
  echo "  > Submitted with job ID of ${OUTPUT[0]}"

  PREVIOUS_JID="${OUTPUT[0]}"
done
