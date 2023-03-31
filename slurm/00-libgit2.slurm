#!/usr/bin/env sh
#SBATCH --job-name=git-slice     # create a short name for your job
#SBATCH --nodes=1                # node count
#SBATCH --ntasks=1               # total number of tasks across all nodes
#SBATCH --cpus-per-task=1        # cpu-cores per task (>1 if multi-threaded tasks)
#SBATCH --mem-per-cpu=2G         # memory per cpu-core (4G per cpu-core is default)
#SBATCH --time=00:10:00          # total run time limit (HH:MM:SS)
#SBATCH --exclude=node164        # avoid stale file handler errors - whoops!

WORKING_DIR="${HOME}/.gitslice/"

if [ -d "$WORKING_DIR" ]
then
    echo "Directory ${WORKING_DIR} already exists, nothing more to do here."
else
    echo "Directory ${WORKING_DIR} does not exist, compiling libgit2 from source now."

    mkdir -p $WORKING_DIR
    cd $WORKING_DIR

    # RepoFS is provided as a pip package
    module add apps/python3/3.10.5
    # Ensure Git is available to us to
    module add apps/git/2.34.1
    # CMake will be used to compile libgit2 from source, it isn't available on Kelvin
    module add apps/cmake/3.14.3/gcc-7.2.0

    # Setup virtual environment
    python3 -m venv venv
    source venv/bin/activate
    export LIBGIT2=$VIRTUAL_ENV

    wget https://github.com/libgit2/libgit2/archive/refs/tags/v1.5.0.tar.gz -O libgit2-1.5.0.tar.gz
    tar xzf libgit2-1.5.0.tar.gz
    rm libgit2-1.5.0.tar.gz

    cd libgit2-1.5.0/

    cmake . -DCMAKE_INSTALL_PREFIX=$LIBGIT2
    cmake --build . --target install

    export LDFLAGS="-Wl,-rpath,'$LIBGIT2/lib',--enable-new-dtags $LDFLAGS"

    # pygit2 is read is be installed, it is included as a dependency but we explicitly ensure it is available then install
    # repofs which will be used from bringing up the mount
    pip3 install pygit2 repofs

    repofs -h
fi
