import argparse
import gettext
import logging
import os
import sys

import git
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
    logging.info(_('  Working directory: \t{}').format(args.working_directory))
    logging.info(_('  Logging level: \t\t{}').format(args.log_level))
    logging.info('')


def traverse_from_current_commit() -> None:
    logging.debug(_('Beginning traversal from current commit'))
    repo = Repo(args.working_directory)

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

        logging.info('Listing files in directory:')
        logging.info(' > ' + ', '.join(os.listdir(args.working_directory)))
        logging.info('...done!')

    logging.info('')
    logging.info(_("Restoring original branch ({})").format(original_branch))

    repo.git.checkout(original_branch)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=_("{} - {}".format(project_constants.project_name,
                                                                    project_constants.project_description)),
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-w", "--working-directory", help="directory to copy project to", required=True)
    parser.add_argument("-l", "--log-level", help="logging level, lowering this value will increase verbosity",
                        type=int, default=20)

    # Ignore first argument from parsing as this will be the filename
    args = parser.parse_args(sys.argv[1:])

    logging.basicConfig(level=args.log_level)

    runtime_info()

    traverse_from_current_commit()
