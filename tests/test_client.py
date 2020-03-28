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
                'id': '475617',
                'title': 'Nachrichten',
                'time': '10:59'
            }]
        })

    @unittest.skip("This test might be wrong")
    def test_get_item(self):
        day = self.orf_client.get_item('oe1', '20170604', '475617', '1496566789000-1496566977000')

        self.assertEqual(day, {
            'id': '1496566789000-1496566977000',
            'title': 'Nachrichten',
            'time': '10:59'
        })
