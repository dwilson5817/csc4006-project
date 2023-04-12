import logging
import os
import shutil
import subprocess

from git import Repo

from config import RepoTypes


class FilesystemFailure(RuntimeError):
    """
    Raised when the filesystem manager fails to bring up the filesystem.
    """

    pass


class FilesystemManager:
    """
    The filesystem manager is responsible for preparing the filesystem before execution and destroying it at the end.

    Specifically, it creates the temporary and output directories, and brings up and pulls down the virtual filesystem
    representing the repository.
    """

    def __init__(self, config, dry_run):
        """
        Initialise the filesystem manager.  This does not bring up the filesystem, a call to up() is required.

        :param config: The configuration object used to get information about the location of directories.
        :param dry_run: When enabled, only the repository is cloned
        """

        logging.debug('Filesystem manager has been created')
        self.config = config
        self.dry_run = dry_run

    def up(self):
        """
        Bring up the filesystem, including; create the output and temporary directories, clone the repository and bring
        up the virtual filesystem representation of the repository.

        :return: None
        """

        logging.debug('Bringing filesystem up...')

        self._create_dirs()
        self._clone_repo()
        self._virtual_fs_up()

    def down(self):
        """
        Destroy the filesystem except for the output directory.  Deletes temporary directories and brings down the
        virtual filesystem representation of the Git repository.

        :return: None
        """

        logging.debug('Bringing filesystem down...')
        self._virtual_fs_down()
        self._nuke_dirs()

    def _virtual_fs_up(self):
        """
        Use RepoFS to bring up the virtual filesystem representation of the Git repository.  Raises a FilesystemFailure
        when the RepoFS script fails.

        Has no effect when dry run is enabled.

        :return: None
        """

        if self.dry_run:
            return

        logging.debug('Running fsUp.sh...')
        result = subprocess.call(['sh', 'shell-scripts/fsUp.sh', self.config.get_working_dir()])

        logging.debug('fsUp.sh returned with %i', result)

        if result:
            logging.fatal('Error occurred while bringing up file system, raising FilesystemFailure')
            raise FilesystemFailure

    def _virtual_fs_down(self):
        """
        Reverse ._virtual_fs_up() by unmounting the RepoFS filesystem.

        Has no effect when dry run is enabled.

        :return: None
        """

        if self.dry_run:
            return

        result = subprocess.call(['sh', 'shell-scripts/fsDown.sh', self.config.get_working_dir()])

        logging.debug('fsDown.sh returned with %i', result)

    def _create_dirs(self) -> None:
        """
        Creates the required directories in the working directory.

        Has no effect when dry run is enabled.

        :return: None
        """

        if self.dry_run:
            return

        dirs_to_create = (self.config.get_repo_dir(), self.config.get_mount_dir())

        logging.debug('Creating directories: %s', ', '.join(dirs_to_create))

        for dir_to_create in dirs_to_create:
            logging.debug('Checking if %s exists...', dir_to_create)
            if not os.path.exists(dir_to_create):
                logging.debug('%s doesn\t exist, creating...', dir_to_create)
                os.makedirs(dir_to_create)

    def _nuke_dirs(self):
        """
        Deletes the working directory.  Does not delete the output directory.

        Has no effect when dry run is enabled.

        :return: None
        """

        logging.debug('Nuking %s', self.config.get_working_dir())
        shutil.rmtree(self.config.get_working_dir())

    def _clone_repo(self) -> None:
        """
        When the repository type is remote, the repository will be cloned otherwise will be copied.

        :return: None
        """

        if self.config.get_repo_type() == RepoTypes.REMOTE:
            logging.info(f'Repo type is REMOTE, cloning from {self.config.get_repo_source()}')
            Repo.clone_from(self.config.get_repo_source(), self.config.get_repo_dir())
        else:
            logging.info('Repo type is LOCAL, copying from %s to %s', self.config.get_repo_source(),
                         self.config.get_repo_dir())
            shutil.copytree(self.config.get_repo_source(), self.config.get_repo_dir())
