import unittest
from datetime import timedelta
from unittest import mock
from unittest.mock import mock_open

from config import Config
from main import val_in_range, file_type_changed, parse_delta, Analysis, get_rev_list_params, parse_diff_shortstat
from test_config import config_data

analysis = Analysis('commit ID', 'commit time', 'analysis image', 'analysis command')


class TestAnalysis(unittest.TestCase):

    def test_get_commit_id(self):
        self.assertEqual('commit ID', analysis.get_commit_id())

    def test_get_commit_time(self):
        self.assertEqual('commit time', analysis.get_commit_time())

    def test_get_analysis_image(self):
        self.assertEqual('analysis image', analysis.get_analysis_image())

    def test_get_analysis_command(self):
        self.assertEqual('analysis command', analysis.get_analysis_command())

    def test_get_details(self):
        self.assertEqual(('commit ID', 'commit time', 'analysis image', 'analysis command'), analysis.get_details())


class TestMain(unittest.TestCase):

    def test_val_in_range(self):
        self.assertTrue(val_in_range(20, '>10'))
        self.assertTrue(val_in_range(5, '>10,4-6'))
        self.assertTrue(val_in_range(100, '<200'))
        self.assertTrue(val_in_range(6, '5 - 6'))

        self.assertFalse(val_in_range(26, '< 26'))
        self.assertFalse(val_in_range(50, '40-49'))
        self.assertFalse(val_in_range(30, '< 25, > 35'))
        self.assertFalse(val_in_range(0, '>0'))

    @mock.patch("builtins.open", mock_open(read_data=config_data))
    def test_get_rev_list_params(self):
        config = Config('test_file.yml')

        expected_target_revision = 'main..9a46c3c4fde7eab96b4519ed595b1eb24bdb5d66'

        expected_rev_list_args = {
            'ancestry-path': True,
            'author': [
                '*@gmail.com',
                '*@yahoo.com'
            ],
            'before': '2023-04-05T19:12:46Z',
            'max-count': 1000,
            'no-merges': True
        }

        self.assertEqual((expected_target_revision, expected_rev_list_args), get_rev_list_params(config))

    def test_file_type_changed(self):
        self.assertTrue(file_type_changed(['test.py'], ['py']))
        self.assertTrue(file_type_changed(['test.inc.php'], ['.inc.php']))
        self.assertTrue(file_type_changed(['test.py', 'test.java'], ['java']))
        self.assertTrue(file_type_changed(['test.py', 'test.java'], ['java', 'py']))

        self.assertFalse(file_type_changed(['test.java'], ['py']))
        self.assertFalse(file_type_changed(['py.java.php'], ['py', 'java']))
        self.assertFalse(file_type_changed(['test.py'], ['java', 'php']))
        self.assertFalse(file_type_changed(['py.log'], ['py']))

    def test_parse_diff_shortstat(self):
        self.assertEqual((2, 4, 4), parse_diff_shortstat(' 2 files changed, 4 insertions(+), 4 deletions(-)'))
        self.assertEqual((6, 299, 0), parse_diff_shortstat(' 6 files changed, 299 insertions(+)'))
        self.assertEqual((1, 0, 3), parse_diff_shortstat(' 1 file changed, 3 deletions(-)'))
        self.assertEqual((0, 0, 0), parse_diff_shortstat(''))

    def test_parse_timedelta(self):
        # Days
        self.assertEqual(timedelta(days=3), parse_delta('3d'))
        self.assertEqual(timedelta(days=-3), parse_delta('-3d'))
        self.assertEqual(timedelta(days=-37), parse_delta('-37D'))

        # Hours
        self.assertEqual(timedelta(hours=18), parse_delta('18h'))
        self.assertEqual(timedelta(hours=-5), parse_delta('-5h'))
        self.assertEqual(timedelta(hours=11), parse_delta('11H'))

        # Mins
        self.assertEqual(timedelta(minutes=129), parse_delta('129m'))
        self.assertEqual(timedelta(minutes=-68), parse_delta('-68m'))
        self.assertEqual(timedelta(minutes=12), parse_delta('12M'))

        # Combined
        self.assertEqual(timedelta(days=3, hours=5), parse_delta('3d5h'))
        self.assertEqual(timedelta(days=-3, hours=-5), parse_delta('-3d-5h'))
        self.assertEqual(timedelta(days=13, hours=4, minutes=19), parse_delta('13d4h19m'))
        self.assertEqual(timedelta(days=13, minutes=19), parse_delta('13d19m'))
        self.assertEqual(timedelta(days=-13, minutes=-19), parse_delta('-13d-19m'))
        self.assertEqual(timedelta(days=-13, minutes=19), parse_delta('-13d19m'))
        self.assertEqual(timedelta(days=13, minutes=-19), parse_delta('13d-19m'))
        self.assertEqual(timedelta(hours=4, minutes=19), parse_delta('4h19m'))
        self.assertEqual(timedelta(hours=-4, minutes=-19), parse_delta('-4h-19m'))
        self.assertEqual(timedelta(hours=-4, minutes=19), parse_delta('-4h19m'))
        self.assertEqual(timedelta(hours=4, minutes=-19), parse_delta('4h-19m'))


if __name__ == '__main__':
    unittest.main()
