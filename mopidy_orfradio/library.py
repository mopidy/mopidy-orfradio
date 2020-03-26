from __future__ import unicode_literals

import logging
import re

from mopidy import backend
from mopidy.models import Ref, Track

from .client import ORFClient

logger = logging.getLogger(__name__)


class ORFUris(object):
    ROOT = 'orfradio:oe1:directory'
    LIVE = 'orfradio:oe1:live'
    CAMPUS = 'orfradio:oe1:campus'
    ARCHIVE = 'orfradio:oe1:archive'


class ORFLibraryProvider(backend.LibraryProvider):
    root_directory = Ref.directory(uri=ORFUris.ROOT, name='ORF Radio')
    root = [
        Ref.track(uri=ORFUris.LIVE, name='OE1 Live'),
        Ref.track(uri=ORFUris.CAMPUS, name='OE1 Campus'),
        Ref.directory(uri=ORFUris.ARCHIVE, name='OE1 7 Tage')]

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

        if library_uri.uri_type == ORFUriType.ARCHIVE:
            return self._browse_archive()

        if library_uri.uri_type == ORFUriType.ARCHIVE_DAY:
            return self._browse_day(library_uri.day_id)

        logger.warning('ORFLibraryProvider.browse called with uri '
                       'that does not support browsing: \'%s\'.' % uri)
        return []

    def _browse_archive(self):
        return [Ref.directory(uri=str(ORFLibraryUri(ORFUriType.ARCHIVE_DAY,
                                                    day['id'])),
                              name=day['label'])
                for day in self.client.get_days()]

    def _get_track_title(self, item):
        return '%s: %s' % (item['time'], item['title'])

    def _browse_day(self, day_id):
        return [Ref.track(uri=str(ORFLibraryUri(ORFUriType.ARCHIVE_ITEM,
                                                day_id, item['id'])),
                          name=self._get_track_title(item))
                for item in self.client.get_day(day_id)['items']]

    def lookup(self, uri):
        try:
            library_uri = ORFLibraryUri.parse(uri)
        except InvalidORFUri as e:
            logger.error(e)
            return []

        if library_uri.uri_type == ORFUriType.LIVE:
            return [Track(uri=ORFUris.LIVE, name='Live')]

        if library_uri.uri_type == ORFUriType.CAMPUS:
            return [Track(uri=ORFUris.CAMPUS, name='Campus')]

        if library_uri.uri_type == ORFUriType.ARCHIVE_DAY:
            return self._browse_day(library_uri.day_id)

        if library_uri.uri_type == ORFUriType.ARCHIVE_ITEM:
            return self._lookup_item(library_uri.day_id, library_uri.item_id)

        logger.warning('ORFLibraryProvider.lookup called with uri '
                       'that does not support lookup: \'%s\'.' % uri)
        return []

    def _lookup_item(self, day_id, item_id):
        item = self.client.get_item(day_id, item_id)
        return [Track(uri=str(ORFLibraryUri(ORFUriType.ARCHIVE_ITEM,
                                            day_id, item['id'])),
                      name=self._get_track_title(item))]

    def refresh(self, uri=None):
        self.client.refresh()


class ORFLibraryUri(object):
    def __init__(self, uri_type, day_id=None, item_id=None):
        self.uri_type = uri_type
        self.day_id = day_id
        self.item_id = item_id

    archive_parse_expression = r'^' + re.escape(ORFUris.ARCHIVE) +\
                               r':(?P<day_id>\d{8})(:(?P<item_id>\d+))?$'
    archive_parser = re.compile(archive_parse_expression)

    @staticmethod
    def parse(uri):
        if uri == ORFUris.ROOT:
            return ORFLibraryUri(ORFUriType.ROOT)
        if uri == ORFUris.LIVE:
            return ORFLibraryUri(ORFUriType.LIVE)
        if uri == ORFUris.CAMPUS:
            return ORFLibraryUri(ORFUriType.CAMPUS)
        if uri == ORFUris.ARCHIVE:
            return ORFLibraryUri(ORFUriType.ARCHIVE)

        matches = ORFLibraryUri.archive_parser.match(uri)

        if matches is not None:
            day_id = matches.group('day_id')
            item_id = matches.group('item_id')

            if day_id is not None:
                if matches.group('item_id') is not None:
                    return ORFLibraryUri(ORFUriType.ARCHIVE_ITEM,
                                         day_id, item_id)
                return ORFLibraryUri(ORFUriType.ARCHIVE_DAY, day_id)
        raise InvalidORFUri(uri)

    def __str__(self):
        if self.uri_type == ORFUriType.ROOT:
            return ORFUris.ROOT
        if self.uri_type == ORFUriType.LIVE:
            return ORFUris.LIVE
        if self.uri_type == ORFUriType.CAMPUS:
            return ORFUris.CAMPUS
        if self.uri_type == ORFUriType.ARCHIVE:
            return ORFUris.ARCHIVE
        if self.uri_type == ORFUriType.ARCHIVE_DAY:
            return ORFUris.ARCHIVE + ':' + self.day_id
        if self.uri_type == ORFUriType.ARCHIVE_ITEM:
            return ORFUris.ARCHIVE + ':' + self.day_id + ':' + self.item_id


class InvalidORFUri(TypeError):
    def __init__(self, uri):
        super(TypeError, self).__init__(
            'The URI is not a valid ORFLibraryUri: \'%s\'.' % uri)


class ORFUriType(object):
    ROOT = 0
    LIVE = 1
    CAMPUS = 2
    ARCHIVE = 3
    ARCHIVE_DAY = 4
    ARCHIVE_ITEM = 5
