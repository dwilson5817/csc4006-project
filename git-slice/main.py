import argparse
import gettext
import logging
import sys

import docker as docker
import git
import yaml
from git import Repo

from constants import project_constants

_ = gettext.gettext


def runtime_info() -> None:
    """Output some system information which may be useful for debugging."""

    logging.info(project_constants.ascii_logo)
    logging.info(_('Runtime information:'))
    logging.info(_('  OS version: \t\t{}').format(sys.platform))
    logging.info(_('  Python version: \t{}').format(sys.version))
    logging.info(_('  GitPython version: \t{}').format(git.__version__))
    logging.info(_('  Config file: \t{}').format(args.config_file))
    logging.info(_('  Logging level: \t\t{}').format(args.log_level))
    logging.info('')


def traverse_from_current_commit(working_directory, docker_config) -> None:
    logging.debug(_('Beginning traversal from current commit'))
    repo = Repo(working_directory)

    original_branch = repo.active_branch.name
    logging.info(_("Current branch is {}").format(original_branch))

    for commit in repo.iter_commits():
        # First line of commit message
        commit_title = commit.message.splitlines()[0]

        logging.info('')
        logging.info(_('Checking out commit {} ({})'.format(commit, commit_title)))
        logging.debug(_('Authored by {} on {}').format(commit.author, commit.authored_datetime))
        logging.debug(_('Committed by {} on {}').format(commit.committer, commit.committed_datetime))

        repo.git.checkout(commit)

        run_analysis(working_directory, docker_config)

    logging.info('')
    logging.info(_("Restoring original branch ({})").format(original_branch))

    repo.git.checkout(original_branch)


def load_config(config_file):
    try:
        with open(config_file, "r") as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as e:
                logging.fatal(_("Error parsing YAML.  Cannot continue."))
                logging.exception(e)
                sys.exit(1)
    except FileNotFoundError as e:
        logging.fatal(_("Configuration file cannot be found.  Cannot continue."))
        logging.exception(e)
        sys.exit(1)


def run_analysis(working_directory, docker_config) -> None:
    docker_client = docker.from_env()
    output = docker_client.containers.run(docker_config.get(project_constants.config_keys['docker']['analysis_image']),
                                             command=".",
                                             volumes={working_directory: {'bind': '/data', 'mode': 'ro'}})
    print(output.decode("utf-8"))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=_("{} - {}".format(project_constants.project['name'],
                                                                    project_constants.project['description'])),
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-c", "--config-file", help=_("configuration file"), required=True)
    parser.add_argument("-l", "--log-level", help=_("logging level, lowering this value will increase verbosity"),
                        type=int, default=20)

    # Ignore first argument from parsing as this will be the filename
    args = parser.parse_args(sys.argv[1:])

    logging.basicConfig(level=args.log_level)

    config = load_config(args.config_file)

    runtime_info()

    traverse_from_current_commit(config.get(project_constants.config_keys['working_directory']),
                                 config.get('docker'))