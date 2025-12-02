import logging

from mopidy import backend

from mopidy_orfradio.client import ORFClient
from mopidy_orfradio.library import InvalidORFUriError, ORFLibraryUri, ORFUriType

logger = logging.getLogger(__name__)


class ORFPlaybackProvider(backend.PlaybackProvider):
    def __init__(self, audio, backend, client=None):
        super().__init__(audio, backend)
        self.client = client or ORFClient(backend=self.backend)

    def translate_uri(self, uri):
        try:
            library_uri = ORFLibraryUri.parse(uri)
        except InvalidORFUriError:
            return None

        match library_uri.uri_type:
            case ORFUriType.LIVE:
                return self.client.get_live_url(library_uri.station)
            case ORFUriType.ARCHIVE_ITEM:
                return self.client.get_item_url(
                    library_uri.station,
                    library_uri.loopstream,
                    library_uri.day_id,
                    library_uri.show_id,
                    library_uri.item_id,
                )
            case _:
                return None
