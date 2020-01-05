import unittest

from src.crawler.InfluencerListManager import InfluencerListManager
from src.util import context


class TestInfluencerList(unittest.TestCase):

    def setUp(self):
        self.influencer_list_manager = InfluencerListManager()

    def test_insert_(self):
        self.assertEqual(1, 1)


if __name__ == '__main__':
    context.load_config("test/data/influencer_list", custom_path=True)
    context.load_credentials()
    unittest.main()