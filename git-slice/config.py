import logging
import sys
from enum import Enum
from uuid import uuid4

import yaml


class ConfigKeys(Enum):
    TEMP_DIR = "Temp Directory"
    RSYNC_TO_TEMP = "Rsync To Temp"
    OUTPUT_DIR = "Output Directory"
    OUTPUT_FORMAT = "Output Format"
    REPO_TYPE = "Git Repository Type"
    REPO_SOURCE = "Git Repository Source"
    ANALYSIS_IMAGE = "Analysis Image"
    ANALYSIS_COMMAND = "Analysis Command"
    REPO_DIR_NAME = "Repo Directory Name"
    MOUNT_DIR_NAME = "Mount Directory Name"
    COMMIT_LIMIT = "Commit Limit"
    COMMIT_SKIP = "Commit Skip"


class RepoTypes(Enum):
    LOCAL = "local"
    REMOTE = "remote"


class InvalidRepoTypeException(RuntimeError):
    pass


class Config:
    def __init__(self, config_file):
        logging.debug('Opening config file at %s', config_file)

        try:
            with open(config_file, "r") as stream:
                try:
                    logging.debug('Config file loaded, reading YAML')
                    self.config = yaml.safe_load(stream)
                except yaml.YAMLError as e:
                    logging.critical('Error parsing YAML.  Cannot continue.')
                    logging.exception(e)
                    sys.exit(1)
        except FileNotFoundError as e:
            logging.critical('Configuration file cannot be found.  Cannot continue.')
            logging.exception(e)
            sys.exit(1)

        self.uuid = uuid4().hex

    def get_output_dir(self):
        return self._get(ConfigKeys.OUTPUT_DIR)

    def get_output_format(self):
        return self._get(ConfigKeys.OUTPUT_FORMAT)

    def get_repo_dir(self):
        result = "{}{}/".format(self.get_working_dir(), self._get(ConfigKeys.REPO_DIR_NAME))

        logging.debug('Repo directory is %s', result)
        return result

    def get_mount_dir(self):
        result = "{}{}/".format(self.get_working_dir(), self._get(ConfigKeys.MOUNT_DIR_NAME))

        logging.debug('Mount directory is %s', result)
        return result

    def get_repo_type(self):
        if self._get(ConfigKeys.REPO_TYPE).lower() in ("remote", "r"):
            logging.debug('Repo type is remote')
            return RepoTypes.REMOTE
        elif self._get(ConfigKeys.REPO_TYPE).lower() in ("local", "l"):
            logging.debug('Repo type is local')
            return RepoTypes.LOCAL

        raise InvalidRepoTypeException

    def get_repo_source(self):
        return self._get(ConfigKeys.REPO_SOURCE)

    def get_working_dir(self):
        result = "{}{}/".format(self._get(ConfigKeys.TEMP_DIR), self.uuid)

        logging.debug('Working directory is %s', result)
        return result

    def get_rsync_to_temp(self):
        return self._get(ConfigKeys.RSYNC_TO_TEMP)

    def get_analysis_image(self):
        return self._get(ConfigKeys.ANALYSIS_IMAGE)

    def get_analysis_command(self):
        return self._get(ConfigKeys.ANALYSIS_COMMAND)

    def get_instance_id(self):
        logging.debug('Getting current UUID...')
        result = self.uuid

        logging.debug('UUID is %s', result)
        return result

    def get_commit_limit(self):
        return int(self._get(ConfigKeys.COMMIT_LIMIT))

    def get_commit_skip(self):
        return int(self._get(ConfigKeys.COMMIT_SKIP))

    def _get(self, key):
        logging.debug('Retrieving value for %s', key.value)
        result = self.config.get(key.value)

        logging.debug('Got value %s for %s', result, key.value)
        return result
