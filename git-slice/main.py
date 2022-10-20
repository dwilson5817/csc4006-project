import argparse
import gettext
import logging
import sys

from constants import project_constants

_ = gettext.gettext


def runtime_info() -> None:
    """Output some system information which may be useful for debugging."""

    logging.info(project_constants.ascii_logo)
    logging.info('')
    logging.info(_('Runtime information:'))
    logging.info(_('  OS version: \t\t\t{}').format(sys.platform))
    logging.info(_('  Python version: \t\t{}').format(sys.version))
    logging.info(_('  Working directory: \t\t{}').format(args.working_directory))
    logging.info(_('  Logging level: \t\t\t{}').format(args.log_level))
    logging.info('')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=_("{} - {}".format(project_constants.project_name,
                                                                    project_constants.project_description)),
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-w", "--working-directory", help="directory to copy project to", required=True)
    parser.add_argument("-l", "--log-level", help="logging level, lowering this value will increase verbosity",
                        type=int, default=20)

    args = parser.parse_args(sys.argv[1:])

    logging.basicConfig(level=args.log_level)

    runtime_info()
