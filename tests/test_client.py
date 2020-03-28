from __future__ import unicode_literals

import unittest

from mopidy_orfradio.client import ORFClient

from . import utils


class ORFClientTest(unittest.TestCase):
    def setUp(self):
        self.http_client_mock = utils.HttpClientMock()
        self.orf_client = ORFClient(self.http_client_mock)

    def test_get_day(self):
        day = self.orf_client.get_day('oe1', '20170604')

        self.assertEqual(day, {
            'id': '20170604',
            'label': 'Sun 04. Jun 2017',
            'shows': [{
                'id': '0',
                'title': 'Nachrichten',
                'time': '10:59:49'
            }]
        })

    def test_get_show(self):
        # This test might be wrong:
        day = self.orf_client.get_item('oe1', '20170604', '0', '0')

        self.assertEqual(day, {
            'id': '0',
            'title': 'Nachrichten',
            'time': '10:59:49'
        })
