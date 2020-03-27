import logging
import urllib

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

import dateutil.parser

import simplejson

logger = logging.getLogger(__name__)


class HttpClient(object):
    cache_opts = {
        'cache.type': 'memory',
    }

    cache = CacheManager(**parse_cache_config_options(cache_opts))

    @cache.cache('get', expire=60)
    def get(self, url):
        try:
            logger.info('Fetching data from \'%s\'.', url)
            response = urllib.request.urlopen(url)
            content = response.read()
            encoding = response.headers['content-type'].split('charset')[-1]
            return content.decode(encoding)
        except Exception as e:
            logger.error('Error fetching data from \'%s\': %s', url, e)

    def refresh(self):
        self.cache.invalidate(self.get, 'get')


class ORFClient(object):
    archive_uri = 'http://audioapi.orf.at/%s/json/2.0/broadcasts/'
    record_uri = 'https://audioapi.orf.at/%s/api/json/current/broadcast/%s/%s'
    item_uri = 'http://loopstream01.apa.at/?channel=%s&shoutcast=0&id=%s'
    live_uri = "https://%sshoutcast.sf.apa.at/;"

    def __init__(self, http_client=HttpClient()):
        self.http_client = http_client

    def get_days(self, station):

        def to_day(rec):
            return {
                'id': _get_day_id(rec),
                'label': _get_day_label(rec)
            }

        json = self._get_archive_json(station)
        if json is not None:
            return [to_day(rec) for rec in reversed(json)]
        return []

    def get_day(self, station, day_id):

        def to_item(i, rec):
            time = dateutil.parser.parse(rec['startISO'])

            return {
                'id': str(i),
                'time': time.strftime("%H:%M:%S"),
                'title': rec['title'],
            }

        day_rec = self._get_day_json(station, day_id)
        items = [to_item(i, broadcast_rec)
                 for i, broadcast_rec in enumerate(day_rec['broadcasts'])
                 if broadcast_rec['isBroadcasted']]

        return {
                'id': day_id,
                'label': _get_day_label(day_rec),
                'items': items
        }

    def get_live_url(self, station):
        shoutcast_slug = { # TODO: move this somewhere else
            'oe1': 'oe1',
            'oe3': 'oe3',
            'fm4': 'fm4',
            'campus': 'oe1campus',
            'bgl': 'oe2b',
            'ktn': 'oe2k',
            'noe': 'oe2n',
            'ooe': 'oe2o',
            'sbg': 'oe2s',
            'stm': 'oe2st',
            'tir': 'oe2t',
            'vbg': 'oe2v',
            'wie': 'oe2w',
        }.get(station)
        return ORFClient.live_uri % shoutcast_slug

    def get_item(self, station, day_id, item_id):
        day = self.get_day(station, day_id)
        return next(item for item in day['items'] if item['id'] == item_id)

    def get_item_url(self, station, day_id, item_id):
        day_rec = self._get_day_json(station, day_id)

        item_id = int(item_id)
        item_rec = day_rec['broadcasts'][item_id]

        json = self._get_record_json(station, item_rec['programKey'], day_id)

        streams = json['streams']
        if len(streams) == 0:
            return ""

        streamId = streams[0]['loopStreamId']
        return ORFClient.item_uri % (station, streamId)

    def refresh(self):
        self.http_client.refresh()

    def _get_json(self, uri):
        try:
            content = self.http_client.get(uri)
            decoder = simplejson.JSONDecoder()
            return decoder.decode(content)
        except Exception as e:
            logger.error('Error decoding content received from \'%s\': %s',
                         uri, e)

    def _get_archive_json(self, station):
        return self._get_json(ORFClient.archive_uri % station)

    def _get_day_json(self, station, day_id):
        json = self._get_archive_json(station)
        return next(rec for rec in json if _get_day_id(rec) == day_id)

    def _get_record_json(self, station, programKey, day):
        return self._get_json(ORFClient.record_uri % (station, programKey, day))


def _get_day_id(day_rec):
    return str(day_rec['day'])


def _get_day_label(day_rec):
    time = dateutil.parser.parse(day_rec['dateISO'])
    return time.strftime("%a %d. %b %Y")
