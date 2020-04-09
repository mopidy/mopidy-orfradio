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
        show = self.orf_client.get_show("oe1", "20170604", "475617")

        self.assertEqual(
            show,
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

    def test_get_show_no_subitems(self):
        show = self.orf_client.get_show("oe1", "20200406", "594692")

        self.assertEqual(
            show,
            {
                "id": "594692",
                "label": "Radiokolleg - Wer ist Opfer?",
                "items": [
                    {
                        "id": "1586156702000",
                        "title": "Radiokolleg - Wer ist Opfer?",
                        "time": "2020-04-06T09:05:02+02:00",
                        "artist": "Johannes Gelich",
                        "length": 1446000,
                        "show_long": "Radiokolleg - Wer ist Opfer?",
                        "type": "",
                    }
                ],
            },
        )

    def test_get_item_broken_unicode(self):
        show = self.orf_client.get_item(
            "fm4", "20200409", "4UP", "1586420063000-1586420268000"
        )

        self.assertEqual(
            show,
            {
                "artist": "",
                "id": "1586420063000-1586420264000",
                "length": 205000,
                "show_long": "Stay At Home, Baby!",
                "time": "2020-04-09T10:14:23+02:00",
                "title": "Joseph Gordon Levitts Platttform HitRecord",
                "type": "B",
            },
        )
