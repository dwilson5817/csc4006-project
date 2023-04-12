import logging
import sys
from enum import Enum
from uuid import uuid4

import yaml


class ConfigKeys(Enum):
    """
    This enum contains the keys in the configuration file.
    """

    TEMP_DIR = "Temp Directory"
    RSYNC_TO_TEMP = "Rsync To Temp"
    OUTPUT_DIR = "Output Directory"
    OUTPUT_FORMAT = "Output Format"
    REPO_TYPE = "Git Repository Type"
    REPO_SOURCE = "Git Repository Source"
    ANALYSIS = "Analysis"
    REPO_DIR_NAME = "Repo Directory Name"
    MOUNT_DIR_NAME = "Mount Directory Name"

    STARTING_POINT = "Starting Point"
    STOPPING_POINT = "Stopping Point"

    GIT_REV_LIST_ARGS = "Git Rev List Args"
    ADDITIONAL_FILTERS = "Additional Filters"


class RepoTypes(Enum):
    """
    Acceptable values for the REPO_TYPE key.
    """

    LOCAL = "local"
    REMOTE = "remote"


class AdditionalFilters(Enum):
    """
    Acceptable keys under the ADDITIONAL_FILTERS key.
    """

    LIMIT = "Limit"
    SKIP = "Skip"
    CHANGES = "Changes"
    MIN_DELTA = "Min Delta"


class ChangesCategories(Enum):
    """
    Acceptable keys under the CHANGES key (which itself is under the ADDITIONAL_FILTERS key).
    """

    FILES = "Files"
    ADDITIONS = "Additions"
    DELETIONS = "Deletions"
    FILE_TYPES = "File Types"


class InvalidRepoTypeException(RuntimeError):
    """
    Thrown when the value for REPO_TYPE is not one of the acceptable options given by the RepoTypes enum.
    """

    pass


class Config:
    """
    The configuration object provides access to the values from the configuration file.
    """

    def __init__(self, config_file):
        """
        Initialisation method to load the configuration file as a YAML file and create a UUID for this instance of
        GitSlice.

        :param config_file: Location of the configuration file to load.
        """

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
        """
        Get the location of the output directory from the configuration file.

        :return: String containing the location of the output directory from the configuration file
        """

        return self._get(ConfigKeys.OUTPUT_DIR)

    def get_output_format(self):
        """
        Get the format of output files.

        This string may contain %COMMIT_ID% and %COMMIT_TIME% which are placeholders and should be substituted for the
        correct value.

        :return: Format of output text files from the configuration file
        """

        return self._get(ConfigKeys.OUTPUT_FORMAT)

    def get_repo_dir(self):
        """
        Get the name of the repository directory.  This option is unlikely to be needed and will usually be "repo".
        This directory stored the Git repository which will be analysed.

        :return: Name of the repository directory from the configuration file
        """

        result = "{}{}/".format(self.get_working_dir(), self._get(ConfigKeys.REPO_DIR_NAME))

        logging.debug('Repo directory is %s', result)
        return result

    def get_mount_dir(self):
        """
        The mount point of the RepoFS virtual filesystem.  This function combines the working directory with the name of
        mount directory from the configuration file.

        :return: Mount point of the RepoFS virtual filesystem.
        """

        result = "{}{}/".format(self.get_working_dir(), self._get(ConfigKeys.MOUNT_DIR_NAME))

        logging.debug('Mount directory is %s', result)
        return result

    def get_repo_type(self):
        """
        Get the type of repository, either local or remote.

        :return: A RepoTypes value indicating the type of repository
        """

        if self._get(ConfigKeys.REPO_TYPE).lower() in ("remote", "r"):
            logging.debug('Repo type is remote')
            return RepoTypes.REMOTE
        elif self._get(ConfigKeys.REPO_TYPE).lower() in ("local", "l"):
            logging.debug('Repo type is local')
            return RepoTypes.LOCAL

        raise InvalidRepoTypeException

    def get_repo_source(self):
        """
        Get the source of the repository to clone from or copy from depending on if it is local or remote.

        :return: The repository source, may be a local directory or URL, as indicated by the get_repo_type()
        """

        return self._get(ConfigKeys.REPO_SOURCE)

    def get_working_dir(self):
        """
        Compute the working directory by combining the temporary directory with the instance UUID.

        :return: Location of the working directory
        """

        result = "{}{}/".format(self._get(ConfigKeys.TEMP_DIR), self.uuid)

        logging.debug('Working directory is %s', result)
        return result

    def get_rsync_to_temp(self):
        """
        Get the RSYNC_TO_TEMP value from the configuration file.

        :return: Boolean value indicating if the files should be rsync'd to the temporary directory before analysis
        """

        return self._get(ConfigKeys.RSYNC_TO_TEMP)

    def get_analysis_dict(self):
        """
        Get the configuration options from the ANALYSIS stanza.

        :return: Dictionary containing the values from the ANALYSIS stanza
        """

        return self._get(ConfigKeys.ANALYSIS)

    def get_instance_id(self):
        """
        Get the UUID for this instance of GitSlice.  Used primarily for generating the working directory to ensure it is
        unique across all instances of the GitSlice.

        :return: A randomly generated UUID for this instance of GitSlice
        """

        logging.debug('Getting current UUID...')
        result = self.uuid

        logging.debug('UUID is %s', result)
        return result

    def get_starting_point(self):
        """
        Get the starting point from the configuration file.  This is a reference to a Git object and might be a branch,
        tag or commit.

        :return: Git reference to analysis starting point
        """

        return self._get(ConfigKeys.STARTING_POINT)

    def get_stopping_point(self):
        """
        The point at which analysis should stop, as defined in the configuration file.

        :return: Stopping point of analysis or None when not set
        """

        return self._get(ConfigKeys.STOPPING_POINT)

    def get_git_rev_list_args(self):
        """
        Arguments for the "git rev-list" command as specified in the GIT_REV_LIST_ARGS stanza.

        :return: A dictionary object (which might be empty but not None) of the git-rev-list arguments
        """

        result = self._get(ConfigKeys.GIT_REV_LIST_ARGS)

        if result is None:
            return {}

        return result

    def get_changes_type(self, key):
        """
        Get an option from the CHANGES stanza, the key should be a value within the ChangesTypes enum.

        :param key: ChangesType enum indicating the value to get
        :return: Value from the configuration file which might be None
        """

        logging.debug('Retrieving value for %s', key.value)
        additional_filter = self.get_additional_filter(AdditionalFilters.CHANGES)

        if additional_filter is None:
            return None

        result = additional_filter.get(key.value)

        logging.debug('Got value %s for %s', result, key.value)
        return result

    def get_additional_filter(self, key):
        """
        Get an option from the ADDITIONAL_FILTERS stanza.

        :param key: A AdditionalFilters enum value indicating the value to retrieve
        :return: The value from the configuration file which might be None
        """

        logging.debug('Retrieving value for %s', key.value)

        additional_filters = self._get(ConfigKeys.ADDITIONAL_FILTERS)

        if additional_filters is None:
            return None

        result = self._get(ConfigKeys.ADDITIONAL_FILTERS).get(key.value)

        logging.debug('Got value %s for %s', result, key.value)
        return result

    def _get(self, key):
        """
        A private method for getting values from the configuration file.  Don't call this method directory - instead
        call a helper method from this class and some modification to the value might nessesary.

        :param key: The key to be retrieved from the configuration file
        :return: The value as given by the configuration file
        """

        logging.debug('Retrieving value for %s', key.value)
        result = self.config.get(key.value)

        logging.debug('Got value %s for %s', result, key.value)
        return result
