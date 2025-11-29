import unittest

from mopidy_orfradio.client import ORFClient

from . import utils


class ORFClientTest(unittest.TestCase):
    def setUp(self):
        self.http_client_mock = utils.HttpClientMock()
        self.orf_client = ORFClient(self.http_client_mock)

    def test_get_day(self):
        day = self.orf_client.get_day("oe1", "20170604")
        day = day[:1]  # only test against first show

        self.assertEqual(
            day, [{"id": "475617", "title": "Nachrichten", "time": "10:59"}]
        )

    def test_get_show(self):
        show = self.orf_client.get_show("oe1", "20170604", "475617")

        self.assertEqual(
            show,
            [
                {
                    "id": "1496566789000",
                    "title": "Nachrichten",
                    "time": "2017-06-04T10:59:49+02:00",
                    "artist": "",
                    "length": 188000,
                    "show_long": "Nachrichten",
                    "show_date": "Sun 2017-06-04",
                    "type": "N",
                }
            ],
        )

    def test_get_show_no_subitems(self):
        show = self.orf_client.get_show("oe1", "20200406", "594692")

        self.assertEqual(
            show,
            [
                {
                    "id": "1586156702000",
                    "title": "Radiokolleg - Wer ist Opfer?",
                    "time": "2020-04-06T09:05:02+02:00",
                    "artist": "Johannes Gelich",
                    "length": 1446000,
                    "show_long": "Radiokolleg - Wer ist Opfer?",
                    "show_date": "Mon 2020-04-06",
                    "type": "",
                }
            ],
        )

    def test_get_show_zeroth_item(self):
        self.orf_client.media_types += ["S"]
        show = self.orf_client.get_show("oe1", "20210412", "635031")

        self.assertEqual(
            show,
            [
                {
                    "artist": "",
                    "id": "1618203591000-1618203675000",
                    "length": 84000,
                    "show_long": "Ö1 Morgenjournal",
                    "show_date": "Mon 2021-04-12",
                    "time": "2021-04-12T06:59:51+02:00",
                    "title": "ohne Namen",
                    "type": "S",
                }
            ],
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
                "length": 201000,
                "show_long": "Stay At Home, Baby!",
                "show_date": "Thu 2020-04-09",
                "time": "2020-04-09T10:14:23+02:00",
                "title": "Joseph Gordon Levitts Platttform HitRecord",
                "type": "B",
            },
        )

    def test_get_item_url_oe2(self):
        url = self.orf_client.get_item_url(
            "wie", "oe2w", "20200615", "WXWOW", "1592222374000-1592222555000"
        )

        self.assertEqual(
            url,
            "https://loopstream01.apa.at/?channel=oe2w&shoutcast=0&id=2020-06-15_1359_tl_61_7DaysMon7_289462.mp3&offset=0&offsetende=181000",  # noqa: B950
        )
