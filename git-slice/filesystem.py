import logging
import os
import shutil
import subprocess

from git import Repo

from config import RepoTypes


class FilesystemFailure(RuntimeError):
    """Raised when the filesystem manager fails to bring up the filesystem."""
    pass


class FilesystemManager:
    def __init__(self, config):
        logging.debug('Filesystem manager has been created')
        self.config = config

    def up(self):
        logging.debug('Bringing filesystem up...')
        self._create_dirs()
        self._clone_repo()
        self._virtual_fs_up()

    def down(self):
        logging.debug('Bringing filesystem down...')
        self._virtual_fs_down()
        self._nuke_dirs()

    def _virtual_fs_up(self):
        logging.debug('Running fsUp.sh...')
        result = subprocess.call(['sh', 'shell-scripts/fsUp.sh', self.config.get_working_dir()])

        logging.debug('fsUp.sh returned with %i', result)

        if result:
            logging.fatal('Error occurred while bringing up file system, raising FilesystemFailure')
            raise FilesystemFailure

    def _virtual_fs_down(self):
        result = subprocess.call(['sh', 'shell-scripts/fsDown.sh', self.config.get_working_dir()])

        logging.debug('fsDown.sh returned with %i', result)

    def _create_dirs(self) -> None:
        """
        Creates the required directories in the specified working directory.

        :return: None
        """

        dirs_to_create = (self.config.get_repo_dir(), self.config.get_mount_dir())

        logging.debug('Creating directories: %s', ', '.join(dirs_to_create))

        for dir_to_create in dirs_to_create:
            logging.debug('Checking if %s exists...', dir_to_create)
            if not os.path.exists(dir_to_create):
                logging.debug('%s doesn\t exist, creating...', dir_to_create)
                os.makedirs(dir_to_create)

    def _nuke_dirs(self):
        logging.debug('Nuking %s', self.config.get_working_dir())
        shutil.rmtree(self.config.get_working_dir())

    def _clone_repo(self) -> None:
        if self.config.get_repo_type() == RepoTypes.REMOTE:
            logging.info(f'Repo type is REMOTE, cloning from {self.config.get_repo_source()}')
            Repo.clone_from(self.config.get_repo_source(), self.config.get_repo_dir())
        else:
            logging.info('Repo type is LOCAL, copying from %s to %s', self.config.get_repo_source(),
                         self.config.get_repo_dir())
            shutil.copytree(self.config.get_repo_source(), self.config.get_repo_dir())
