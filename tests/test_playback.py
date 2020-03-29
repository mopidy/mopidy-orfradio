import unittest

from unittest.mock import Mock

from mopidy_orfradio.playback import (
    ORFLibraryUri,
    ORFPlaybackProvider,
    ORFUriType,
)


class ORFLibraryUriTest(unittest.TestCase):
    def test_playback_archive_item(self):
        library_uri = ORFLibraryUri(
            ORFUriType.ARCHIVE_ITEM, "oe1", "20140914", "1234567"
        )
        client_mock = Mock()
        client_mock.get_item_url = Mock(return_value="result_uri")
        playback = ORFPlaybackProvider(None, None, client=client_mock)

        result = playback.translate_uri(str(library_uri))

        self.assertEqual(result, "result_uri")

    def test_playback_live(self):
        library_uri = ORFLibraryUri(ORFUriType.LIVE, "oe1")

        client_mock = Mock()
        client_mock.get_live_url = Mock(return_value="result_uri")
        playback = ORFPlaybackProvider(None, None, client=client_mock)

        result = playback.translate_uri(str(library_uri))

        self.assertEqual(result, "result_uri")

    def test_playback_invalid_url(self):
        audio_mock = Mock()
        audio_mock.set_uri = Mock()

        playback = ORFPlaybackProvider(audio_mock, None, client=None)
        result = playback.translate_uri("invalid")

        self.assertIsNone(result)

    def test_playback_unplayable_url(self):
        library_uri = ORFLibraryUri(ORFUriType.STATION, "oe1")
        playback = ORFPlaybackProvider(None, None, client=None)

        result = playback.translate_uri(str(library_uri))

        self.assertIsNone(result)
