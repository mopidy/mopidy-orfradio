import logging

from mopidy import backend

from mopidy_orfradio.library import InvalidORFUri, ORFLibraryUri, ORFUriType

from .client import ORFClient

logger = logging.getLogger(__name__)


class ORFPlaybackProvider(backend.PlaybackProvider):
    def __init__(self, audio, backend, client=None):
        super().__init__(audio, backend)
        self.client = client or ORFClient(backend=self.backend)

    def translate_uri(self, uri):
        try:
            library_uri = ORFLibraryUri.parse(uri)
        except InvalidORFUri:
            return None

        if library_uri.uri_type == ORFUriType.LIVE:
            return self.client.get_live_url(library_uri.shoutcast)

        if library_uri.uri_type == ORFUriType.ARCHIVE_ITEM:
            return self.client.get_item_url(
                library_uri.station,
                library_uri.day_id,
                library_uri.show_id,
                library_uri.item_id,
            )
