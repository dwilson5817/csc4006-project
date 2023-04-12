import argparse
import logging
import sys

import coloredlogs as coloredlogs
import git
import pyfiglet
import torcpy
from git import Repo
from spython.main import Client

from config import Config
from filesystem import FilesystemManager, FilesystemFailure

PROJECT_NAME = "GitSlice"
PROJECT_DESCRIPTION = "Slicing the repository that feeds us"

# Commands run inside a singularity container before user-specified commands
PRE_RUN = "mkdir -p %%WORKING_DIR%%; rsync --inplace --exclude \".git-descendants\" --exclude \".git-names\" " \
          "--exclude \".git-parents\" --exclude \".author\" --exclude \".author-email\" --chmod=Du=rwx,Dg=rx,Do=rx," \
          "Fu=rw,Fg=r,Fo=r -r /src/ %%WORKING_DIR%% 2>&1 ; cd %%WORKING_DIR%%"
# Commands run inside a singularity container after user-specified commands
POST_RUN = "rm -rf %%WORKING_DIR%%"


def runtime_info(args) -> None:
    """Output some system information which may be useful for debugging."""

    logging.info(pyfiglet.figlet_format(PROJECT_NAME))
    logging.info('Runtime information:')
    logging.info(f'  OS version: \t\t%s', sys.platform)
    logging.info(f'  Python version: \t%s', sys.version)
    logging.info(f'  Python version: \t%s', sys.version)
    logging.info(f'  GitPython version: \t%s', git.__version__)
    logging.info(f'  Config file: \t%s', args.config_file)
    logging.info(f'  Logging level: \t\t%s', args.log_level)
    logging.info('')


def traverse_from_current_commit() -> None:
    logging.debug("Beginning traversal from current commit... ", str(config.get_instance_id()))
    logging.debug("Loading repo from %s", config.get_repo_dir())
    repo = Repo(config.get_repo_dir())

    logging.info('The repository current has the %s branch checked out', repo.active_branch.name)

    tasks = []

    for (i, commit) in enumerate(repo.iter_commits()):
        if i > config.get_commit_limit():
            break

        if i % config.get_commit_skip() == 0:
            logging.debug('Submitting commit %s for analysis', str(commit))
            task = torcpy.submit(run_analysis_singularity, (str(commit), str(commit.committed_date)))
            tasks.append(task)

    logging.debug('All commits are submitted for analysis, waiting for them to complete...')
    torcpy.wait()

    for t in tasks:
        logging.info(t.result())


def run_analysis_singularity(commit) -> str:
    commit_id, commit_time = commit

    logging.info('Beginning analysis on %s', commit_id)

    commit_dir = config.get_mount_dir() + 'commits-by-hash/' + commit_id
    logging.debug('Expecting that %s contains the commit files', commit_dir)

    logging.debug('Loading %s...', config.get_analysis_image())
    Client.load('docker://{}'.format(config.get_analysis_image()))

    if config.get_rsync_to_temp():
        analysis_command = f"{PRE_RUN.replace('%%WORKING_DIR%%', f'/tmp/{commit_id}')} ; {config.get_analysis_command()} ; {POST_RUN.replace('%%WORKING_DIR%%', f'/tmp/{commit_id}')}"
        binds = [f'{commit_dir}:/src', f'{config.get_working_dir()}:/tmp']
    else:
        analysis_command = f"{config.get_analysis_command()}"
        binds = [f'{commit_dir}:/src']

    commands = ['/bin/sh', '-c', analysis_command]

    logging.debug('Running %s with command %s, %s will be bound to /data on the container',
                  config.get_analysis_image(), ' '.join(commands), commit_dir)
    output = Client.execute(command=commands, bind=binds, stream=True, options=['--writable-tmpfs', '--containall'])

    output_format = config.get_output_format().replace('%COMMIT_ID%', commit_id).replace('%COMMIT_TIME%', commit_time)
    output_file = config.get_output_dir() + output_format + '.txt'

    logging.debug('Opening output file %s', output_file)
    with open(output_file, "w+") as file:
        for line in output:
            logging.debug('Writing line to output: %s', line)
            file.write(line)

    logging.info('Commit %s has been analysed', commit_id)

    return commit


def main():
    global config

    logging.info(f"{PROJECT_NAME} - {PROJECT_DESCRIPTION}")
    logging.info(f"Starting on {socket.gethostname()}")
    runtime_info(args)

    config = Config(args.config_file)
    filesystem_manager = FilesystemManager(config)

    try:
        filesystem_manager.up()
    except FilesystemFailure:
        logging.warning("Failed to bring up filesystem, will not proceed with traversal...")
        filesystem_manager.down()
        sys.exit(1)

    try:
        torcpy.start(traverse_from_current_commit)
    except Exception as e:
        logging.error("An error occurred during traversal!")
        logging.exception(e)

    filesystem_manager.down()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="{} - {}".format(PROJECT_NAME, PROJECT_DESCRIPTION),
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-c", "--config-file", help="configuration file location", required=True)
    parser.add_argument("-d", "--dry-run", help="enables dry run mode", action='store_true')
    parser.add_argument("-l", "--log-level", help="logging level, where 0 is the most verbose", type=int, default=20)

    # Ignore first argument from parsing as this will be the filename
    args = parser.parse_args(sys.argv[1:])

    coloredlogs.install(level=args.log_level)

    main()
