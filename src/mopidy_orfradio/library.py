from __future__ import annotations

import datetime
import logging
import re
import urllib
from enum import IntEnum
from typing import ClassVar, override

from mopidy import backend
from mopidy.models import Album, Artist, Ref, Track

from mopidy_orfradio import TZ
from mopidy_orfradio.client import ORFClient

logger = logging.getLogger(__name__)


class ORFUris:
    ROOT = "orfradio"

    # Mapping from audioapi_slug to (name, loopstream_slug)
    stations: ClassVar[dict[str, tuple[str, str | None]]] = {
        "oe1": ("Ö1", "oe1"),
        "oe3": ("Ö3", "oe3"),
        "fm4": ("FM4", "fm4"),
        "campus": ("Ö1 Campus", None),
        "bgl": ("Radio Burgenland", "oe2b"),
        "ktn": ("Radio Kärnten", "oe2k"),
        "noe": ("Radio Niederösterreich", "oe2n"),
        "ooe": ("Radio Oberösterreich", "oe2o"),
        "sbg": ("Radio Salzburg", "oe2s"),
        "stm": ("Radio Steiermark", "oe2st"),
        "tir": ("Radio Tirol", "oe2t"),
        "vbg": ("Radio Vorarlberg", "oe2v"),
        "wie": ("Radio Wien", "oe2w"),
        "slo": ("ORF Slovenski spored", None),
    }


class ORFLibraryProvider(backend.LibraryProvider):
    root_directory = Ref.directory(uri=f"{ORFUris.ROOT}:", name="ORF Radio")

    def __init__(self, backend, client=None):
        super().__init__(backend)
        self.client = client or ORFClient(backend=self.backend)
        self.root = [
            Ref.directory(uri=f"{ORFUris.ROOT}:{slug}", name=name)
            for slug, (name, _) in ORFUris.stations.items()
            if slug in self.backend.config["orfradio"]["stations"]
        ]

    @override
    def browse(self, uri):
        try:
            library_uri = ORFLibraryUri.parse(uri)
        except InvalidORFUriError as e:
            logger.error(e)  # noqa: TRY400
            return []

        match library_uri.uri_type:
            case ORFUriType.ROOT:
                return self.root
            case ORFUriType.STATION:
                return self._browse_station(library_uri.station)
            case ORFUriType.ARCHIVE_DAY:
                return self._browse_day(library_uri.station, library_uri.day_id)
            case ORFUriType.ARCHIVE_SHOW:
                return self._browse_show(
                    library_uri.station, library_uri.day_id, library_uri.show_id
                )
            case ORFUriType.LIVE | ORFUriType.ARCHIVE_ITEM:
                logger.warning(
                    "ORFLibraryProvider.browse called with URI "
                    f"that does not support browsing: {uri!r}"
                )
                return []

    def _browse_station(self, station):
        if station not in ORFUris.stations:
            return []

        name, loopstream_slug = ORFUris.stations[station]
        live = Ref.track(
            uri=str(ORFLibraryUri(ORFUriType.LIVE, station)),
            name=f"{name} Live",
        )

        last_week = [
            datetime.date.fromordinal(
                datetime.datetime.now(tz=TZ).date().toordinal() - d
            )
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

        if loopstream_slug is None:
            return [live]
        return [live, *archive]

    def _get_track_title(self, item, *, afterhours=False):
        time = item["time"]
        if afterhours and self.backend.config["orfradio"]["afterhours"]:
            time = re.sub(r"^0([0-4]:)", r"O\1", time)
        return "{}: {}".format(time, item["title"])

    def _browse_day(self, station, day_id):
        return [
            Ref.directory(
                uri=str(
                    ORFLibraryUri(ORFUriType.ARCHIVE_SHOW, station, day_id, show["id"])
                ),
                name=self._get_track_title(show, afterhours=True),
            )
            for show in self.client.get_day(station, day_id)
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
            for item in self.client.get_show(station, day_id, show_id)
        ]

    @override
    def lookup(self, uri):  # noqa: PLR0911
        try:
            library_uri = ORFLibraryUri.parse(uri)
        except InvalidORFUriError as e:
            logger.error(e)  # noqa: TRY400
            return []

        match library_uri.uri_type:
            case ORFUriType.ROOT:
                logger.warning(
                    "ORFLibraryProvider.lookup called with URI "
                    f"that does not support lookup: {uri!r}"
                )
                return []
            case ORFUriType.LIVE:
                return [Track(uri=str(library_uri), name="Live")]
            case ORFUriType.STATION:
                return self._browse_station(library_uri.station)
            case ORFUriType.ARCHIVE_DAY:
                return self._browse_day(library_uri.station, library_uri.day_id)
            case ORFUriType.ARCHIVE_SHOW:
                return self._browse_show(
                    library_uri.station, library_uri.day_id, library_uri.show_id
                )
            case ORFUriType.ARCHIVE_ITEM:
                return self._lookup_item(
                    library_uri.station,
                    library_uri.day_id,
                    library_uri.show_id,
                    library_uri.item_id,
                )

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
                album=Album(name=f"{item['show_long']} ({item['show_date']})"),
                genre=item["type"],
                name=item["title"],
            )
        ]

    @override
    def refresh(self, uri=None):
        self.client.refresh()


class ORFLibraryUri:
    def __init__(
        self,
        uri_type: ORFUriType,
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
        _scheme, _, path, _, _ = urllib.parse.urlsplit(uri)
        station, live_or_day, show, item, *_ = path.split("/", 4) + 4 * [None]

        if station == "":
            return ORFLibraryUri(ORFUriType.ROOT)
        if live_or_day is None:
            return ORFLibraryUri(ORFUriType.STATION, station)
        if live_or_day == "live":
            return ORFLibraryUri(ORFUriType.LIVE, station)
        if item:
            return ORFLibraryUri(
                ORFUriType.ARCHIVE_ITEM, station, live_or_day, show, item
            )
        if show:
            return ORFLibraryUri(ORFUriType.ARCHIVE_SHOW, station, live_or_day, show)
        return ORFLibraryUri(ORFUriType.ARCHIVE_DAY, station, live_or_day)

        raise InvalidORFUriError(uri)

    @property
    def loopstream(self):
        _name, loopstream_slug = ORFUris.stations[self.station]
        return loopstream_slug

    def __str__(self) -> str:
        match self.uri_type:
            case ORFUriType.ROOT:
                return f"{ORFUris.ROOT}:"
            case ORFUriType.STATION:
                return f"{ORFUris.ROOT}:{self.station}"
            case ORFUriType.LIVE:
                return f"{ORFUris.ROOT}:{self.station}/live"
            case ORFUriType.ARCHIVE_DAY:
                return f"{ORFUris.ROOT}:{self.station}/{self.day_id}"
            case ORFUriType.ARCHIVE_SHOW:
                return f"{ORFUris.ROOT}:{self.station}/{self.day_id}/{self.show_id}"
            case ORFUriType.ARCHIVE_ITEM:
                return (
                    f"{ORFUris.ROOT}:{self.station}/{self.day_id}"
                    f"/{self.show_id}/{self.item_id}"
                )


class InvalidORFUriError(TypeError):
    def __init__(self, uri):
        super().__init__(f"The URI is not a valid ORFLibraryUri: {uri!r}")


class ORFUriType(IntEnum):
    ROOT = 0
    STATION = 1
    LIVE = 2
    ARCHIVE_DAY = 3
    ARCHIVE_SHOW = 4
    ARCHIVE_ITEM = 5
