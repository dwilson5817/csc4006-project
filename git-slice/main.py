import argparse
import datetime
import logging
import re
import socket
import sys
import time
from datetime import timedelta

import coloredlogs as coloredlogs
import git
from git import Repo

from config import AdditionalFilters, Config, ChangesCategories
from constants import PROJECT_NAME, PROJECT_DESCRIPTION, RSYNC_PRE_RUN, RSYNC_POST_RUN, TIMEDELTA_PATTERN
from filesystem import FilesystemManager, FilesystemFailure


def runtime_info() -> None:
    """
    Output some system information which may be useful for debugging.

    :return: None
    """

    logging.debug('Runtime information:')
    logging.debug('  OS version: \t\t%s', sys.platform)
    logging.debug('  Python version: \t%s', sys.version)
    logging.debug('  Python version: \t%s', sys.version)
    logging.debug('  GitPython version: \t%s', git.__version__)
    logging.debug('  Config file: \t%s', args.config_file)
    logging.debug('  Dry run mode: \t\t%s', args.dry_run)
    logging.debug('  Logging level: \t\t%s', args.log_level)


class Analysis:
    """
    This class represents the details of an analysis.  It's fields will be used by a node to run a Singularity container
    and perform analysis on a commit.
    """

    def __init__(self, commit_id, commit_time, analysis_image, analysis_command) -> None:
        self._commit_id = commit_id
        self._commit_time = commit_time
        self._analysis_image = analysis_image
        self._analysis_command = analysis_command

    def get_analysis_command(self) -> str:
        """
        Provides the command to be run inside the container.

        :return: String of the command to be run.
        """
        return self._analysis_command

    def get_analysis_image(self) -> str:
        """
        Provides the image to be used for analysis.

        :return: String containing the URI of the container.
        """

        return self._analysis_image

    def get_commit_id(self) -> str:
        """
        Returns the commit ID to be analysed.

        :return: String of the SHA1 hash of the commit.
        """

        return self._commit_id

    def get_commit_time(self) -> datetime:
        """
        Returns the time the commit was committed.  Importantly, this is the commit time, not the authored time!

        :return: datetime representation of the time the commit was committed in seconds since the UNIX epoch.
        """

        return self._commit_time

    def get_details(self):
        """
        Returns a list, ready for unpacking of all the data contained within the object.  This includes: the SHA1 hash
        of the commit, the time in seconds since the UNIX epoch it was committed at, the analysis image to be used and
        the command to be run inside the container.

        :return: List containing the commit ID, time, analysis image and command.
        """

        return self.get_commit_id(), self.get_commit_time(), self.get_analysis_image(), self.get_analysis_command()

    def __str__(self) -> str:
        """
        String conversion dunder method for representing this object as a human-readable string.

        :return: String representation of this object, in human readable format.
        """

        return f"{self._commit_id} at {self._commit_time} running {self._analysis_command} in {self._analysis_image}"


def parse_delta(delta) -> datetime:
    """
    Parses a human-readable timedelta (e.g. 3d5h19m) into a datetime.timedelta.

    Delta includes:

    * Xd days
    * Xh hours
    * Xm minutes

    Values can be negative following timedelta's rules. Eg: -5h-30m

    Source: https://gist.github.com/santiagobasulto/698f0ff660968200f873a2f9d1c4113c

    :param delta: String containing the delta
    :return: datetime representation of the delta.
    """
    match = TIMEDELTA_PATTERN.match(delta)
    if match:
        parts = {k: int(v) for k, v in match.groupdict().items() if v}
        return timedelta(**parts)


def get_analysis_details(commit, analysis_config) -> (str, str):
    """
    Given a commit object, and a configuration object, this method returns the analysis image and command which should
    be used for this commit.

    :param commit: GitPython Commit object
    :param analysis_config: Configuration object specifically containing an "Analysis" stanza.
    :return: The image and command to be used for this commit.
    """

    if commit.hexsha in analysis_config:
        return analysis_config[commit.hexsha]['Image'], analysis_config[commit.hexsha]['Command']

    for commit in commit.iter_parents():
        if commit.hexsha in analysis_config:
            return analysis_config[commit.hexsha]['Image'], analysis_config[commit.hexsha]['Command']

    return analysis_config['Default']['Image'], analysis_config['Default']['Command']


def parse_number_from_string(str_to_parse: str):
    """
    Extracts all digits in a string an combines them to form a number.

    For example, "100 insertions(+)" will produce return 100 (as an int).

    :param str_to_parse: The string to extract the number from
    :return: Integer representation of the number in the string
    """

    digits = re.search(r'\d+', str_to_parse)

    if digits is None:
        return None

    return int(digits.group())


def val_in_range(val, ranges_str) -> bool:
    """
    Given a value and a ranges string (e.g. "> 100, 150-175, 200 <") this function returns true or false indicating if
    the value exists within the given range.

    :param val: Integer value which is either within or not within the ranges.
    :param ranges_str: String value which the val will be tested again.
    :return: Boolean indicating if the value is within the ranges.
    """
    for range_str in ranges_str.split(','):
        if '-' in range_str:
            lower, upper = range_str.split('-')

            if int(lower) <= val <= int(upper):
                return True

        if '>' in range_str:
            if val > parse_number_from_string(range_str):
                return True

        if '<' in range_str:
            if val < parse_number_from_string(range_str):
                return True

    return False


def parse_diff_shortstat(diff_output: str):
    """
    Parses output from git-diff with shortstat option.

    Given a string such as "2 files changed, 4 insertions(+), 4 deletions(-)", returns the files changed, insertions
    and deletions as integers.

    :param diff_output: Output from git-diff
    :return: Tuple of files changed, insertions and deletions
    """

    files_changed = additions = deletions = 0

    for stat in diff_output.split(','):
        if stat is not None:
            stat_int = parse_number_from_string(stat)

            if ' changed' in stat:
                files_changed = stat_int
            elif 'insertion' in stat:
                additions = stat_int
            elif 'deletion' in stat:
                deletions = stat_int

    return files_changed, additions, deletions


def get_analysis_list(repo, config_dict):
    """
    Given a Git repository and a configuration, returns a list of Analysis objects representing the commits to be
    analysed with the image and command to be run.

    :param repo: The GitPython Repo object to be analysed.
    :param config_dict: The configuration object which contains the configuration from the config file.
    :return: List of Analysis objects which contain the commits to be analysed with the container and command to be used
    """

    result = []

    commit_limit = config_dict.get_additional_filter(AdditionalFilters.LIMIT)
    commit_skip = config.get_additional_filter(AdditionalFilters.SKIP)

    files_changed_ranges = config_dict.get_changes_type(ChangesCategories.FILES)
    additions_ranges = config_dict.get_changes_type(ChangesCategories.ADDITIONS)
    deletions_ranges = config_dict.get_changes_type(ChangesCategories.DELETIONS)
    file_types_list = config_dict.get_changes_type(ChangesCategories.FILE_TYPES)

    current_skip = 0

    target_rev, rev_list_args = get_rev_list_params(config_dict=config_dict)

    min_commit_time_delta = config_dict.get_additional_filter(AdditionalFilters.MIN_DELTA)

    if min_commit_time_delta is not None:
        print(min_commit_time_delta)

        parse_delta(min_commit_time_delta)

    last_commit_time = None

    for commit in repo.iter_commits(target_rev, **rev_list_args):
        if commit_limit is not None and len(result) >= commit_limit:
            logging.debug(f'Hit commit limit ({commit_limit})')
            break

        logging.debug("Testing commit %s...", commit.hexsha)

        if None not in (min_commit_time_delta, last_commit_time) and (
                last_commit_time - min_commit_time_delta) < commit.committed_datetime:
            logging.debug("Minimum time between commits not met for commit %s, last commit at %s, this commit at %s",
                          commit.hexsha, last_commit_time.isoformat(), commit.committed_datetime.isoformat())
            continue

        diff = repo.git.diff(f'{commit.hexsha}^@', shortstat=True)

        logging.debug("git-diff gave %s", diff)

        files_changed, additions, deletions = parse_diff_shortstat(diff)

        logging.debug("Commit %s changed %i files, with %i additions and %i deletions", commit.hexsha, files_changed,
                      additions, deletions)

        if files_changed_ranges and not val_in_range(files_changed, files_changed_ranges):
            logging.debug('Commit %s changed %i files which is not within %s so is deselected', commit.hexsha,
                          files_changed, files_changed_ranges)
            continue

        if additions_ranges and not val_in_range(additions, additions_ranges):
            logging.debug('Commit %s had %i additions which is not within %s so is deselected', commit.hexsha,
                          additions, additions_ranges)
            continue

        if deletions_ranges and not val_in_range(deletions, deletions_ranges):
            logging.debug('Commit %s had %i deletions which is not within %s so is deselected', commit.hexsha,
                          deletions, deletions_ranges)
            continue

        if file_types_list:
            changed_files = repo.git.diff(f'{commit.hexsha}^@', name_only=True).splitlines(keepends=False)

            if not file_type_changed(changed_files, file_types_list):
                logging.debug('Commit %s did not change any files with types: %s', commit.hexsha,
                              ', '.join(file_types_list))
                continue

        if not commit_skip or current_skip == commit_skip:
            logging.debug('Commit %s matches all filters and is selected', commit.hexsha)
            current_skip = 0
            last_commit_time = commit.committed_datetime

            analysis = Analysis(commit.hexsha, commit.committed_datetime,
                                *get_analysis_details(commit, config_dict.get_analysis_dict()))

            result.append(analysis)
        else:
            logging.debug('Commit %s would have been selected, but skipping commit %i/%i', commit.hexsha, current_skip,
                          commit_skip)
            current_skip += 1

    return result


def file_type_changed(changed_files, file_types) -> bool:
    """
    Given a list of files, return true or false indicating if at least one of those files ends in one of the endings
    provided by the file_types list.

    :param changed_files: A list of files.
    :param file_types: A list of endings (i.e. file extensions)
    :return: True when at least on file ends in one of the endings.
    """

    for changed_file in changed_files:
        for file_type in file_types:
            if changed_file.endswith(file_type):
                return True

    return False


def get_rev_list_params(config_dict):
    """
    Given a configuration object, returns the target revision and arguments for the "git rev-list" command.

    :param config_dict: A configuration object, specifically this should contain at least the "Starting Point" option
    :return: A string to be used as the target revision and a list of keyword arguments for "git rev-list
    """

    rev_list_args = config_dict.get_git_rev_list_args()

    if config_dict.get_stopping_point():
        target_rev = f"{config_dict.get_starting_point()}..{config_dict.get_stopping_point()}"
        rev_list_args['ancestry-path'] = True
    else:
        target_rev = f"{config_dict.get_starting_point()}"

    logging.debug(f'Target revision: {target_rev}')
    logging.debug(f'git rev-list args: {rev_list_args}')

    return target_rev, rev_list_args


def traverse_repo() -> None:
    """
    Uses the configuration object to queue a set of commits for analysis based on the configuration options.

    This should only be run on the "primary" node!

    :return: None
    """

    logging.debug("Beginning traversal from current commit (%s)... ", str(config.get_instance_id()))
    logging.debug("Loading repo from %s", config.get_repo_dir())
    repo = Repo(config.get_repo_dir())

    tasks = []

    logging.info("Searching repository to find commits to analyse...")

    for analysis in get_analysis_list(repo, config):
        if not args.dry_run:
            logging.debug('Submitting commit %s for analysis', str(analysis.get_commit_id()))
            task = torcpy.submit(run_analysis_singularity, analysis)
            tasks.append(task)
        else:
            logging.info('Would have submitted commit %s for analysis', str(analysis.get_commit_id()))
            logging.info('  Image: %s', str(analysis.get_analysis_image()))
            logging.info('  Command: %s', str(analysis.get_analysis_command()))

    if not args.dry_run:
        logging.debug('All commits are submitted for analysis, waiting for them to complete...')
        torcpy.wait()

        for t in tasks:
            logging.info(t.result())


def run_analysis_singularity(analysis: Analysis) -> str:
    """
    Given an analysis object, starts up a Singularity container and runs the command to perform analysis on a specific
    commit.

    This function will be executed many times by all the nodes allocated to GitSlice.

    :param analysis: The analysis object containing analysis information.
    :return: A string describing the commit analysed and how long it took (for printing to the screen).
    """

    start_time = time.time()

    commit_id, commit_time, analysis_image, analysis_command = analysis.get_details()

    logging.info('Beginning analysis on %s', commit_id)

    commit_dir = config.get_mount_dir() + 'commits-by-hash/' + commit_id
    logging.debug('Expecting that %s contains the commit files', commit_dir)

    logging.debug('Loading %s...', analysis_image)
    Client.load(analysis_image)

    if config.get_rsync_to_temp():
        full_command = f"{RSYNC_PRE_RUN.replace('%%WORKING_DIR%%', f'/tmp/{commit_id}')} ; {analysis_command} ; " \
                       f"{RSYNC_POST_RUN.replace('%%WORKING_DIR%%', f'/tmp/{commit_id}')}"
        binds = [f'{commit_dir}:/src', f'{config.get_working_dir()}:/tmp']
    else:
        full_command = f"{analysis_command}"
        binds = [f'{commit_dir}:/src']

    commands = ['/bin/sh', '-c', full_command]

    logging.debug('Running %s with command %s, %s will be bound to /data on the container', analysis_image,
                  ' '.join(commands), commit_dir)
    output = Client.execute(command=commands, bind=binds, stream=True, options=['--writable-tmpfs', '--containall'])

    output_format = config.get_output_format().replace('%COMMIT_ID%', commit_id).replace('%COMMIT_TIME%',
                                                                                         commit_time.isoformat())
    output_file = config.get_output_dir() + output_format + '.txt'

    logging.debug('Opening output file %s', output_file)

    with open(output_file, "w+") as file:
        for line in output:
            logging.debug('Writing line to output: %s', line.strip())
            file.write(line)

    logging.info('Commit %s has been analysed', commit_id)

    return f"{commit_id} completed analysis in {time.time() - start_time} seconds"


def main():
    """
    The entry-point into the program.  Prints some runtime information, loads the configuration and prepares the
    filesystem before selecting the commits be analysed.

    :return: None
    """

    global config

    logging.info(f"{PROJECT_NAME} - {PROJECT_DESCRIPTION}")
    logging.info(f"Starting on {socket.gethostname()}")
    runtime_info()

    config = Config(args.config_file)
    filesystem_manager = FilesystemManager(config, args.dry_run)

    try:
        filesystem_manager.up()
    except FilesystemFailure:
        logging.warning("Failed to bring up filesystem, will not proceed with traversal...")
        filesystem_manager.down()
        sys.exit(1)

    try:
        if args.dry_run:
            traverse_repo()
        else:
            torcpy.start(traverse_repo)
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

    if not args.dry_run:
        import torcpy
        from spython.main import Client

    main()
