import unittest

from mopidy_orfradio.client import ORFClient

from . import utils


class ORFClientTest(unittest.TestCase):
    def setUp(self):
        self.http_client_mock = utils.HttpClientMock()
        self.orf_client = ORFClient(self.http_client_mock)

    def test_get_day(self):
        day = self.orf_client.get_day("oe1", "20170604")
        day["shows"] = day["shows"][:1]  # only test against first show

        self.assertEqual(
            day,
            {
                "id": "20170604",
                "label": "Sun 04. Jun 2017",
                "shows": [
                    {"id": "475617", "title": "Nachrichten", "time": "10:59"}
                ],
            },
        )

    def test_get_show(self):
        day = self.orf_client.get_show("oe1", "20170604", "475617")

        self.assertEqual(
            day,
            {
                "id": "475617",
                "label": "Nachrichten",
                "items": [
                    {
                        "id": "1496566789000",
                        "title": "Nachrichten",
                        "time": "2017-06-04T10:59:49+02:00",
                        "artist": "",
                        "length": 12345,
                        "show_long": "Nachrichten",
                        "type": "N",
                    }
                ],
            },
        )
