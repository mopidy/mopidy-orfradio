import logging
import re
import urllib
import datetime

from mopidy import backend
from mopidy.models import Ref, Track, Artist, Album

from .client import ORFClient

logger = logging.getLogger(__name__)


class ORFUris:
    ROOT = "orfradio"
    stations = [
        # name, audioapi_slug, shoutcast_slug
        ("Ö1", "oe1", "oe1"),
        ("Ö3", "oe3", "oe3"),
        ("FM4", "fm4", "fm4"),
        ("Ö1 Campus", "campus", "oe1campus"),  # note: has no archive
        ("Radio Burgenland", "bgl", "oe2b"),
        ("Radio Kärnten", "ktn", "oe2k"),
        ("Radio Niederösterreich", "noe", "oe2n"),
        ("Radio Oberösterreich", "ooe", "oe2o"),
        ("Radio Salzburg", "sbg", "oe2s"),
        ("Radio Steiermark", "stm", "oe2st"),
        ("Radio Tirol", "tir", "oe2t"),
        ("Radio Vorarlberg", "vbg", "oe2v"),
        ("Radio Wien", "wie", "oe2w"),
    ]


class ORFLibraryProvider(backend.LibraryProvider):
    root_directory = Ref.directory(uri=f"{ORFUris.ROOT}:", name="ORF Radio")

    def __init__(self, backend, client=None):
        super().__init__(backend)
        self.client = client or ORFClient(backend=self.backend)
        self.root = [
            Ref.directory(uri=f"{ORFUris.ROOT}:{slug}", name=name)
            for (name, slug, _) in ORFUris.stations
            if slug in self.backend.config["orfradio"]["stations"]
        ]

    def browse(self, uri):
        try:
            library_uri = ORFLibraryUri.parse(uri)
        except InvalidORFUri as e:
            logger.error(e)
            return []

        if library_uri.uri_type == ORFUriType.ROOT:
            return self.root

        if library_uri.uri_type == ORFUriType.STATION:
            return self._browse_station(library_uri.station)

        if library_uri.uri_type == ORFUriType.ARCHIVE_DAY:
            return self._browse_day(library_uri.station, library_uri.day_id)

        if library_uri.uri_type == ORFUriType.ARCHIVE_SHOW:
            return self._browse_show(
                library_uri.station, library_uri.day_id, library_uri.show_id
            )

        logger.warning(
            "ORFLibraryProvider.browse called with uri "
            "that does not support browsing: '%s'." % uri
        )
        return []

    def _browse_station(self, station):
        try:
            name = next(
                name for (name, slug, _) in ORFUris.stations if slug == station
            )
        except StopIteration:
            return []
        live = Ref.track(
            uri=str(ORFLibraryUri(ORFUriType.LIVE, station)),
            name=f"{name} Live",
        )

        last_week = [
            datetime.date.fromordinal(datetime.datetime.today().toordinal() - d)
            for d in range(8)
        ]
        archive = [
            Ref.directory(
                uri=str(
                    ORFLibraryUri(
                        ORFUriType.ARCHIVE_DAY, station, day.strftime("%Y%m%d")
                    )
                ),
                name=day.strftime("%Y-%m-%d %A"),
            )
            for day in last_week
        ]

        if station == "campus":
            return [live]
        return [live] + archive

    def _get_track_title(self, item, afterhours=False):
        time = item["time"]
        if afterhours and self.backend.config["orfradio"]["afterhours"]:
            time = re.sub(r"^0([0-5]:)", r"O\1", time)
        return "{}: {}".format(time, item["title"])

    def _browse_day(self, station, day_id):
        return [
            Ref.directory(
                uri=str(
                    ORFLibraryUri(
                        ORFUriType.ARCHIVE_SHOW, station, day_id, show["id"]
                    )
                ),
                name=self._get_track_title(show, afterhours=True),
            )
            for show in self.client.get_day(station, day_id)["shows"]
        ]

    def _browse_show(self, station, day_id, show_id):
        return [
            Ref.track(
                uri=str(
                    ORFLibraryUri(
                        ORFUriType.ARCHIVE_ITEM,
                        station,
                        day_id,
                        show_id,
                        item["id"],
                    )
                ),
                name=self._get_track_title(item),
            )
            for item in self.client.get_show(station, day_id, show_id)["items"]
        ]

    def lookup(self, uri):
        try:
            library_uri = ORFLibraryUri.parse(uri)
        except InvalidORFUri as e:
            logger.error(e)
            return []

        if library_uri.uri_type == ORFUriType.LIVE:
            return [Track(uri=str(library_uri), name="Live")]

        if library_uri.uri_type == ORFUriType.STATION:
            return self._browse_station(library_uri.station)

        if library_uri.uri_type == ORFUriType.ARCHIVE_DAY:
            return self._browse_day(library_uri.station, library_uri.day_id)

        if library_uri.uri_type == ORFUriType.ARCHIVE_SHOW:
            return self._browse_show(
                library_uri.station, library_uri.day_id, library_uri.show_id
            )

        if library_uri.uri_type == ORFUriType.ARCHIVE_ITEM:
            return self._lookup_item(
                library_uri.station,
                library_uri.day_id,
                library_uri.show_id,
                library_uri.item_id,
            )

        logger.warning(
            "ORFLibraryProvider.lookup called with uri "
            "that does not support lookup: '%s'." % uri
        )
        return []

    def _lookup_item(self, station, day_id, show_id, item_id):
        item = self.client.get_item(station, day_id, show_id, item_id)
        return [
            Track(
                uri=str(
                    ORFLibraryUri(
                        ORFUriType.ARCHIVE_ITEM,
                        station,
                        day_id,
                        show_id,
                        item["id"],
                    )
                ),
                artists=[Artist(name=item["artist"])],
                length=item["length"],
                album=Album(name=item["show_long"]),
                genre=item["type"],
                name=item["title"],
            )
        ]

    def refresh(self, uri=None):
        self.client.refresh()


class ORFLibraryUri:
    def __init__(
        self,
        uri_type,
        station_slug=None,
        day_id=None,
        show_id=None,
        item_id=None,
    ):
        self.uri_type = uri_type
        self.station = station_slug
        self.day_id = day_id
        self.show_id = show_id
        self.item_id = item_id

    @staticmethod
    def parse(uri):
        scheme, _, path, _, _ = urllib.parse.urlsplit(uri)
        station, live_or_day, show, item, *_ = path.split("/", 4) + 4 * [None]

        if station == "":
            return ORFLibraryUri(ORFUriType.ROOT)
        if live_or_day is None:
            return ORFLibraryUri(ORFUriType.STATION, station)
        elif live_or_day == "live":
            return ORFLibraryUri(ORFUriType.LIVE, station)
        else:
            if item:
                return ORFLibraryUri(
                    ORFUriType.ARCHIVE_ITEM, station, live_or_day, show, item
                )
            if show:
                return ORFLibraryUri(
                    ORFUriType.ARCHIVE_SHOW, station, live_or_day, show
                )
            return ORFLibraryUri(ORFUriType.ARCHIVE_DAY, station, live_or_day)

        raise InvalidORFUri(uri)

    @property
    def shoutcast(self):
        return next(
            shoutcast
            for (_, slug, shoutcast) in ORFUris.stations
            if slug == self.station
        )

    def __str__(self):
        if self.uri_type == ORFUriType.ROOT:
            return f"{ORFUris.ROOT}:"
        if self.uri_type == ORFUriType.STATION:
            return f"{ORFUris.ROOT}:{self.station}"
        if self.uri_type == ORFUriType.LIVE:
            return f"{ORFUris.ROOT}:{self.station}/live"
        if self.uri_type == ORFUriType.ARCHIVE_DAY:
            return f"{ORFUris.ROOT}:{self.station}/{self.day_id}"
        if self.uri_type == ORFUriType.ARCHIVE_SHOW:
            return f"{ORFUris.ROOT}:{self.station}/{self.day_id}/{self.show_id}"
        if self.uri_type == ORFUriType.ARCHIVE_ITEM:
            return f"{ORFUris.ROOT}:{self.station}/{self.day_id}/{self.show_id}/{self.item_id}"  # noqa: B950


class InvalidORFUri(TypeError):
    def __init__(self, uri):
        super(TypeError, self).__init__(
            "The URI is not a valid ORFLibraryUri: '%s'." % uri
        )


class ORFUriType:
    ROOT = 0
    STATION = 1
    LIVE = 2
    ARCHIVE_DAY = 3
    ARCHIVE_SHOW = 4
    ARCHIVE_ITEM = 5
