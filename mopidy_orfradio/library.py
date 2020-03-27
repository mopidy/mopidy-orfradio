from __future__ import unicode_literals

import logging
import re
import urllib

from mopidy import backend
from mopidy.models import Ref, Track

from .client import ORFClient

logger = logging.getLogger(__name__)


class ORFUris(object):
    ROOT = 'orfradio'
    stations = [
        # name, audioapi_slug, loopstream_slug==shoutcast_slug
        # TODO: use shoutcast_slug in orfradio: urls. then we can set campus audioapi_slug to None and remove the hack around in _station_directory().
        # TODO: shoutcast_slug is never used
        ('Ö1', 'oe1', 'oe1'),
        ('Ö3', 'oe3', 'oe3'),
        ('FM4', 'fm4', 'fm4'),
        ('Ö1 Campus', 'campus', 'oe1campus'), # note: has no archive
        ('Radio Burgenland', 'bgl', 'oe2b'),
        ('Radio Kärnten', 'ktn', 'oe2k'),
        ('Radio Niederösterreich', 'noe', 'oe2n'),
        ('Radio Oberösterreich', 'ooe', 'oe2o'),
        ('Radio Salzburg', 'sbg', 'oe2s'),
        ('Radio Steiermark', 'stm', 'oe2st'),
        ('Radio Tirol', 'tir', 'oe2t'),
        ('Radio Vorarlberg', 'vbg', 'oe2v'),
        ('Radio Wien', 'wie', 'oe2w'),
    ]


class ORFLibraryProvider(backend.LibraryProvider):
    root_directory = Ref.directory(uri=f'{ORFUris.ROOT}:', name='ORF Radio')
    root = [
        Ref.directory(uri=f'{ORFUris.ROOT}:{slug}', name=name)
            for (name, slug, _) in ORFUris.stations
    ]

    def __init__(self, backend, client=ORFClient()):
        super(ORFLibraryProvider, self).__init__(backend)
        self.client = client

    def browse(self, uri):
        try:
            library_uri = ORFLibraryUri.parse(uri)
        except InvalidORFUri as e:
            logger.error(e)
            return []

        if library_uri.uri_type == ORFUriType.ROOT:
            return self.root

        if library_uri.uri_type == ORFUriType.STATION:
            return self._station_directory(library_uri.station)

        if library_uri.uri_type == ORFUriType.ARCHIVE:
            return self._browse_archive(library_uri.station)

        if library_uri.uri_type == ORFUriType.ARCHIVE_DAY:
            return self._browse_day(library_uri.station, library_uri.day_id)

        logger.warning('ORFLibraryProvider.browse called with uri '
                       'that does not support browsing: \'%s\'.' % uri)
        return []

    def _station_directory(self, station):
        name = next(name for (name, slug, _) in ORFUris.stations if slug == station)
        live = Ref.track(uri=str(ORFLibraryUri(ORFUriType.LIVE, station)), name=f'{name} Live')
        archive = Ref.directory(uri=str(ORFLibraryUri(ORFUriType.ARCHIVE, station)), name=f'{name} 7 Tage')

        if station == 'campus':
            return [live]
        return [live, archive]

    def _browse_archive(self, station):
        return [Ref.directory(uri=str(ORFLibraryUri(ORFUriType.ARCHIVE_DAY,
                                                    station, day['id'])),
                              name=day['label'])
                for day in self.client.get_days(station)]

    def _get_track_title(self, item):
        return '%s: %s' % (item['time'], item['title'])

    def _browse_day(self, station, day_id):
        return [Ref.track(uri=str(ORFLibraryUri(ORFUriType.ARCHIVE_ITEM,
                                                station, day_id, item['id'])),
                          name=self._get_track_title(item))
                for item in self.client.get_day(station, day_id)['items']]

    def lookup(self, uri):
        try:
            library_uri = ORFLibraryUri.parse(uri)
        except InvalidORFUri as e:
            logger.error(e)
            return []

        if library_uri.uri_type == ORFUriType.LIVE:
            return [Track(uri=str(library_uri), name='Live')]

        if library_uri.uri_type == ORFUriType.STATION:
            return self._station_directory(library_uri.station)

        if library_uri.uri_type == ORFUriType.ARCHIVE_DAY:
            return self._browse_day(library_uri.station, library_uri.day_id)

        if library_uri.uri_type == ORFUriType.ARCHIVE_ITEM:
            return self._lookup_item(library_uri.station, library_uri.day_id, library_uri.item_id)

        logger.warning('ORFLibraryProvider.lookup called with uri '
                       'that does not support lookup: \'%s\'.' % uri)
        return []

    def _lookup_item(self, station, day_id, item_id):
        item = self.client.get_item(station, day_id, item_id)
        return [Track(uri=str(ORFLibraryUri(ORFUriType.ARCHIVE_ITEM, station,
                                            day_id, item['id'])),
                      name=self._get_track_title(item))]

    def refresh(self, uri=None):
        self.client.refresh()


class ORFLibraryUri(object):
    def __init__(self, uri_type, station_slug=None, day_id=None, item_id=None):
        self.uri_type = uri_type
        self.station = station_slug
        self.day_id = day_id
        self.item_id = item_id

    @staticmethod
    def parse(uri):
        scheme, _, path, _, _ = urllib.parse.urlsplit(uri)
        station, browse, day, item, *_ = path.split('/', 4) + [None]*4

        if station == '':
            return ORFLibraryUri(ORFUriType.ROOT)
        if station not in [slug for (name, slug, _) in ORFUris.stations]:
            raise InvalidORFUri(uri)
        if browse is None:
            return ORFLibraryUri(ORFUriType.STATION, station)
        if browse == 'live':
            return ORFLibraryUri(ORFUriType.LIVE, station)
        if browse == 'archive':
            if item:
                return ORFLibraryUri(ORFUriType.ARCHIVE_ITEM, station, day, item)
            if day:
                return ORFLibraryUri(ORFUriType.ARCHIVE_DAY, station, day)
            return ORFLibraryUri(ORFUriType.ARCHIVE, station)

        raise InvalidORFUri(uri)

    def __str__(self):
        if self.uri_type == ORFUriType.ROOT:
            return f'{ORFUris.ROOT}:'
        if self.uri_type == ORFUriType.STATION:
            return f'{ORFUris.ROOT}:{self.station}'
        if self.uri_type == ORFUriType.LIVE:
            return f'{ORFUris.ROOT}:{self.station}/live'
        if self.uri_type == ORFUriType.ARCHIVE:
            return f'{ORFUris.ROOT}:{self.station}/archive'
        if self.uri_type == ORFUriType.ARCHIVE_DAY:
            return f'{ORFUris.ROOT}:{self.station}/archive/{self.day_id}'
        if self.uri_type == ORFUriType.ARCHIVE_ITEM:
            return f'{ORFUris.ROOT}:{self.station}/archive/{self.day_id}/{self.item_id}'


class InvalidORFUri(TypeError):
    def __init__(self, uri):
        super(TypeError, self).__init__(
            'The URI is not a valid ORFLibraryUri: \'%s\'.' % uri)


class ORFUriType(object):
    ROOT = 0
    STATION = 1
    LIVE = 2
    ARCHIVE = 3
    ARCHIVE_DAY = 4
    ARCHIVE_ITEM = 5
