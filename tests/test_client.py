from __future__ import unicode_literals

import unittest

from mopidy_orfradio.client import ORFClient

from . import utils


class ORFClientTest(unittest.TestCase):
    def setUp(self):
        self.http_client_mock = utils.HttpClientMock()
        self.orf_client = ORFClient(self.http_client_mock)

    def test_get_days(self):
        days = self.orf_client.get_days('oe1')

        self.assertListEqual(days, [
            {'id': '20170605', 'label': 'Mon 05. Jun 2017'},
            {'id': '20170604', 'label': 'Sun 04. Jun 2017'}
        ])

    def test_get_day(self):
        day = self.orf_client.get_day('oe1', '20170604')

        self.assertEqual(day, {
            'id': '20170604',
            'label': 'Sun 04. Jun 2017',
            'items': [{
                'id': '0',
                'title': 'Nachrichten',
                'time': '10:59:49'
            }]
        })

    def test_get_item(self):
        day = self.orf_client.get_item('oe1', '20170604', '0')

        self.assertEqual(day, {
            'id': '0',
            'title': 'Nachrichten',
            'time': '10:59:49'
        })
