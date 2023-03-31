#!/usr/bin/env sh

# usage: fsUp.sh working_dir

WORKING_DIR=$1
SHARED_DIR="$HOME/.gitslice/"

if [ -d "$SHARED_DIR" ]
then
    echo "Directory ${SHARED_DIR} exists, bringing up virtual filesystem."

    cd "${SHARED_DIR}/libgit2-1.5.0"

    module add apps/python3/3.10.5
    module add apps/git/2.34.1
    module add apps/cmake/3.14.3/gcc-7.2.0

    # Activate virtual environment
    source ../venv/bin/activate

    repofs "$WORKING_DIR/repo" "$WORKING_DIR/mount"
else
    echo "Directory ${SHARED_DIR} does not exist, did the libgit2 SLURM job fail?"
    echo "In any event, we can't continue, exiting now with error status"

    exit 1
fi
