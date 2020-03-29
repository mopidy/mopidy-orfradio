import unittest
import datetime

from unittest.mock import Mock

from mopidy.models import Ref

from mopidy_orfradio.library import (
    ORFLibraryProvider,
    ORFLibraryUri,
    ORFUriType,
)


class ORFLibraryUriTest(unittest.TestCase):
    def test_parse_root_uri(self):
        uri = "orfradio:"
        result = ORFLibraryUri.parse(uri)
        self.assertEqual(result.uri_type, ORFUriType.ROOT)

    def test_parse_station_uri(self):
        uri = "orfradio:oe1"
        result = ORFLibraryUri.parse(uri)
        self.assertEqual(result.uri_type, ORFUriType.STATION)

    def test_parse_live_uri(self):
        uri = "orfradio:oe1/live"
        result = ORFLibraryUri.parse(uri)
        self.assertEqual(result.uri_type, ORFUriType.LIVE)

    def test_parse_day_uri(self):
        uri = "orfradio:oe1/20140914"
        result = ORFLibraryUri.parse(uri)
        self.assertEqual(result.uri_type, ORFUriType.ARCHIVE_DAY)
        self.assertEqual(result.day_id, "20140914")

    def test_parse_show_uri(self):
        uri = "orfradio:oe1/20140914/382176"
        result = ORFLibraryUri.parse(uri)
        self.assertEqual(result.uri_type, ORFUriType.ARCHIVE_SHOW)
        self.assertEqual(result.day_id, "20140914")
        self.assertEqual(result.show_id, "382176")

    def test_create_root_uri(self):
        parsed_uri = ORFLibraryUri(ORFUriType.ROOT)
        self.assertEqual(str(parsed_uri), "orfradio:")

    def test_create_station_uri(self):
        parsed_uri = ORFLibraryUri(ORFUriType.STATION, "oe1")
        self.assertEqual(str(parsed_uri), "orfradio:oe1")

    def test_create_live_uri(self):
        parsed_uri = ORFLibraryUri(ORFUriType.LIVE, "oe1")
        self.assertEqual(str(parsed_uri), "orfradio:oe1/live")

    def test_create_day_uri(self):
        parsed_uri = ORFLibraryUri(ORFUriType.ARCHIVE_DAY, "oe1", "20140914")
        self.assertEqual(str(parsed_uri), "orfradio:oe1/20140914")

    def test_create_show_uri(self):
        parsed_uri = ORFLibraryUri(
            ORFUriType.ARCHIVE_SHOW, "oe1", "20140914", "382176"
        )
        self.assertEqual(str(parsed_uri), "orfradio:oe1/20140914/382176")


class ORFLibraryProviderTest(unittest.TestCase):
    def setUp(self):
        self.client_mock = Mock()
        self.client_mock.get_day = Mock(
            return_value={
                "shows": [
                    {"id": "1", "time": "01:00", "title": "Item1"},
                    {"id": "2", "time": "02:00", "title": "Item2"},
                    {"id": "3", "time": "03:00", "title": "Item3"},
                ]
            }
        )
        self.client_mock.get_show = Mock(
            return_value={
                "items": [
                    {"id": "1", "time": "01:00", "title": "Item1"},
                    {"id": "2", "time": "02:00", "title": "Item2"},
                    {"id": "3", "time": "03:00", "title": "Item3"},
                ]
            }
        )
        self.client_mock.get_item = Mock(
            return_value={"id": "1", "time": "01:00", "title": "Item1"}
        )
        self.backend = Mock()
        self.backend.config = {
            "orfradio": {"stations": ["oe1", "fm4"], "afterhours": False}
        }

        self.library = ORFLibraryProvider(self.backend, client=self.client_mock)

    def test_browse_invalid_uri(self):
        uri = "foo:bar"
        result = self.library.browse(uri)
        self.assertEqual(result, [])

    def test_browse_unbrowsable_uri(self):
        uri = str(ORFLibraryUri(ORFUriType.LIVE, "oe1"))
        result = self.library.browse(uri)
        self.assertEqual(result, [])

    def test_browse_root(self):
        uri = str(ORFLibraryUri(ORFUriType.ROOT))
        result = self.library.browse(uri)
        self.assertEqual(len(result), 2)

    def test_browse_station(self):
        uri = str(ORFLibraryUri(ORFUriType.STATION, "oe1"))
        result = self.library.browse(uri)
        self.assertEqual(len(result), 9)
        self.assertEqual(result[0].type, Ref.TRACK)
        self.assertEqual(result[0].uri, "orfradio:oe1/live")
        self.assertEqual(result[0].name, "Ö1 Live")
        self.assertEqual(result[1].type, Ref.DIRECTORY)
        today = datetime.datetime.today().strftime("%Y%m%d")
        self.assertEqual(result[1].uri, f"orfradio:oe1/{today}")
        labeltext = datetime.datetime.today().strftime("%Y-%m-%d %A")
        self.assertEqual(result[1].name, labeltext)

    def test_browse_archive_day(self):
        uri = str(ORFLibraryUri(ORFUriType.ARCHIVE_DAY, "oe1", "20140914"))
        result = self.library.browse(uri)
        self.client_mock.get_day.assert_called_once_with("oe1", "20140914")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].type, Ref.DIRECTORY)
        self.assertEqual(result[0].uri, "orfradio:oe1/20140914/1")
        self.assertEqual(result[0].name, "01:00: Item1")

    def test_lookup_invalid_uri(self):
        uri = "foo:bar"
        result = self.library.lookup(uri)
        self.assertEqual(result, [])

    def test_browse_unlookable_uri(self):
        uri = str(ORFLibraryUri(ORFUriType.ROOT))
        result = self.library.lookup(uri)
        self.assertEqual(result, [])

    def test_lookup_live(self):
        uri = str(ORFLibraryUri(ORFUriType.LIVE, "oe1"))
        result = self.library.lookup(uri)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].uri, uri)
        self.assertEqual(result[0].name, "Live")

    def test_lookup_archive_day(self):
        uri = str(ORFLibraryUri(ORFUriType.ARCHIVE_DAY, "oe1", "20140914"))
        result = self.library.lookup(uri)
        self.client_mock.get_day.assert_called_once_with("oe1", "20140914")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].type, Ref.DIRECTORY)
        self.assertEqual(result[0].uri, "orfradio:oe1/20140914/1")
        self.assertEqual(result[0].name, "01:00: Item1")

    def test_lookup_archive_show(self):
        uri = str(
            ORFLibraryUri(ORFUriType.ARCHIVE_SHOW, "oe1", "20140914", "1234567")
        )
        result = self.library.lookup(uri)
        self.client_mock.get_show.assert_called_once_with(
            "oe1", "20140914", "1234567"
        )
        self.assertEqual(len(result), 3)
        # this test might be wrong:
        self.assertEqual(result[0].uri, "orfradio:oe1/20140914/1234567/1")
        self.assertEqual(result[0].name, "01:00: Item1")
