import unittest
from unittest import mock
from unittest.mock import mock_open

import yaml

from config import AdditionalFilters, ChangesCategories, Config, RepoTypes

test_config = {
    'Output Directory': '/tmp/users/40234266/csc4006-project/',
    'Output Format': '%COMMIT_TIME%_%COMMIT_ID%',
    'Temp Directory': '/users/40234266/csc4006-project/output/sast/numpy/',
    'Rsync To Temp': True,
    'Repo Directory Name': 'repo',
    'Mount Directory Name': 'mount',
    'Git Repository Type': 'Remote',
    'Git Repository Source': 'https://github.com/numpy/numpy.git',
    'Analysis': {
        '56a676c8058c3bcc213aae3d0cae318aef75ed25': {
            'Image': 'Image ONE',
            'Command': 'Command ONE'
        },
        'c45a101f4ef02a20f63cb39dee04c0577ad7b099': {
            'Image': 'Image TWO',
            'Command': 'Command TWO'
        },
        'Default': {
            'Image': 'Image THREE',
            'Command': 'Command THREE'
        }
    },
    'Starting Point': 'main',
    'Stopping Point': '9a46c3c4fde7eab96b4519ed595b1eb24bdb5d66',
    'Git Rev List Args': {
        'max-count': 1000,
        'author': [
            '*@gmail.com',
            '*@yahoo.com'
        ],
        'before': '2023-04-05T19:12:46Z',
        'no-merges': True
    },
    'Additional Filters': {
        'Limit': 15000,
        'Skip': 250,
        'Changes': {
            'Files': '5-100',
            'Additions': '0, > 100',
            'Deletions': '< 100, 150-175, > 200',
            'File Types': [
                'py',
                'java'
            ]
        },
        'Min Delta': '3d5h19m'
    }
}

config_data = yaml.dump(test_config)


class TestMain(unittest.TestCase):

    @mock.patch("builtins.open", mock_open(read_data=config_data))
    def test_get_output_dir(self):
        config = Config('test_file.yml')

        self.assertEqual(test_config['Output Directory'], config.get_output_dir())

    @mock.patch("builtins.open", mock_open(read_data=config_data))
    def test_get_output_format(self):
        config = Config('test_file.yml')

        self.assertEqual(test_config['Output Format'], config.get_output_format())

    @mock.patch("builtins.open", mock_open(read_data=config_data))
    def test_get_repo_dir(self):
        config = Config('test_file.yml')

        self.assertEqual(
            f"{test_config['Temp Directory']}{config.get_instance_id()}/{test_config['Repo Directory Name']}/",
            config.get_repo_dir())

    @mock.patch("builtins.open", mock_open(read_data=config_data))
    def test_get_mount_dir(self):
        config = Config('test_file.yml')

        self.assertEqual(
            f"{test_config['Temp Directory']}{config.get_instance_id()}/{test_config['Mount Directory Name']}/",
            config.get_mount_dir())

    @mock.patch("builtins.open", mock_open(read_data=config_data))
    def test_get_repo_type(self):
        config = Config('test_file.yml')

        self.assertEqual(config.get_repo_type(), RepoTypes.REMOTE)

    @mock.patch("builtins.open", mock_open(read_data=config_data))
    def test_get_repo_source(self):
        config = Config('test_file.yml')

        self.assertEqual(test_config['Git Repository Source'], config.get_repo_source())

    @mock.patch("builtins.open", mock_open(read_data=config_data))
    def test_get_working_dir(self):
        config = Config('test_file.yml')

        self.assertEqual(f"{test_config['Temp Directory']}{config.get_instance_id()}/", config.get_working_dir())

    @mock.patch("builtins.open", mock_open(read_data=config_data))
    def test_get_rsync_to_temp(self):
        config = Config('test_file.yml')

        self.assertTrue(config.get_rsync_to_temp())

    @mock.patch("builtins.open", mock_open(read_data=config_data))
    def test_get_analysis_dict(self):
        config = Config('test_file.yml')

        self.assertEqual(test_config['Analysis'], config.get_analysis_dict())

    @mock.patch("builtins.open", mock_open(read_data=config_data))
    def test_get_instance_id(self):
        config = Config('test_file.yml')

        self.assertRegex(config.get_instance_id(), r'{?\w{8}-?\w{4}-?\w{4}-?\w{4}-?\w{12}}?')

    @mock.patch("builtins.open", mock_open(read_data=config_data))
    def test_get_starting_point(self):
        config = Config('test_file.yml')

        self.assertEqual(test_config['Starting Point'], config.get_starting_point())

    @mock.patch("builtins.open", mock_open(read_data=config_data))
    def test_get_stopping_point(self):
        config = Config('test_file.yml')

        self.assertEqual(test_config['Stopping Point'], config.get_stopping_point())

    @mock.patch("builtins.open", mock_open(read_data=config_data))
    def test_get_git_rev_list_args(self):
        config = Config('test_file.yml')

        self.assertEqual(test_config['Git Rev List Args'], config.get_git_rev_list_args())

    @mock.patch("builtins.open", mock_open(read_data=config_data))
    def test_get_changes_type(self):
        config = Config('test_file.yml')

        self.assertEqual(test_config['Additional Filters']['Changes']['Files'],
                         config.get_changes_type(ChangesCategories.FILES))
        self.assertEqual(test_config['Additional Filters']['Changes']['Additions'],
                         config.get_changes_type(ChangesCategories.ADDITIONS))
        self.assertEqual(test_config['Additional Filters']['Changes']['Deletions'],
                         config.get_changes_type(ChangesCategories.DELETIONS))
        self.assertEqual(test_config['Additional Filters']['Changes']['File Types'],
                         config.get_changes_type(ChangesCategories.FILE_TYPES))

    @mock.patch("builtins.open", mock_open(read_data=config_data))
    def test_get_additional_filter(self):
        config = Config('test_file.yml')

        self.assertEqual(test_config['Additional Filters']['Limit'],
                         config.get_additional_filter(AdditionalFilters.LIMIT))
        self.assertEqual(test_config['Additional Filters']['Skip'],
                         config.get_additional_filter(AdditionalFilters.SKIP))
        self.assertEqual(test_config['Additional Filters']['Changes'],
                         config.get_additional_filter(AdditionalFilters.CHANGES))
        self.assertEqual(test_config['Additional Filters']['Min Delta'],
                         config.get_additional_filter(AdditionalFilters.MIN_DELTA))


if __name__ == '__main__':
    unittest.main()
