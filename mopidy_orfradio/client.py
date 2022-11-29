import logging
import urllib

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

import dateutil.parser
import datetime

import json
import re

logger = logging.getLogger(__name__)


class HttpClient:
    cache_opts = {"cache.type": "memory"}

    cache = CacheManager(**parse_cache_config_options(cache_opts))

    @cache.cache("get", expire=300)
    def get(self, url):
        try:
            logger.debug("Fetching data from %r", url)
            response = urllib.request.urlopen(url)
            content = response.read()
            encoding = response.headers["content-type"].split("charset")[-1]
            return content.decode(encoding)
        except Exception as e:
            logger.error("Error fetching data from '%s': %s", url, e)

    def refresh(self):
        self.cache.invalidate(self.get, "get")


class ORFClient:
    archive_uri = "https://audioapi.orf.at/%s/json/2.0/broadcasts/"
    record_uri = "https://audioapi.orf.at/%s/api/json/4.0/broadcast/%s/%s"
    show_uri = "https://loopstream01.apa.at/?channel=%s&shoutcast=0&id=%s&offset=%s&offsetende=%s"  # noqa: B950
    live_uri = "https://orf-live.ors-shoutcast.at/%s-%s"

    bitrates = {
        128: "q1a",
        192: "q2a",
    }

    def __init__(self, http_client=HttpClient(), backend=None):  # noqa: B008
        self.http_client = http_client
        if backend:
            self.media_types = backend.config["orfradio"]["archive_types"]
            selected_bitrate = backend.config["orfradio"]["livestream_bitrate"]
            self.live_bitrate = self.bitrates[selected_bitrate]
        else:
            self.media_types = ["M", "B", "N"]
            self.live_bitrate = "q2a"

    def get_day(self, station, day_id):
        day_rec = self._get_day_json(station, day_id)
        if not day_rec:
            return []

        def now(offset):
            return datetime.datetime.now(
                datetime.timezone(datetime.timedelta(milliseconds=offset))
            )

        shows = [
            _to_show(i, broadcast_rec)
            for i, broadcast_rec in enumerate(day_rec["broadcasts"])
            if dateutil.parser.parse(broadcast_rec["startISO"])
            < now(broadcast_rec["endOffset"])
        ]

        return shows

    def get_show(self, station, day_id, show_id):
        show_rec = self._get_record_json(station, show_id, day_id)
        if not show_rec:
            return []
        # Sometimes the first item isn't at the beginning of the show, making
        # part of it inaccessible. So we add a fake "zeroth" item when that
        # happens:
        show_date = _get_day_label(day_id)
        first_item = next(iter(show_rec["items"]), None)
        if first_item and show_rec["start"] < first_item["start"]:
            show_rec["items"].insert(
                0,
                {
                    "start": show_rec["start"],
                    "startISO": show_rec["startISO"],
                    "title": None,
                    "type": "S",
                },
            )

        items = [
            {
                "id": _generate_id(show_rec, i),
                "title": _mojibake(track.get("title") or _generic_title(track)),
                "time": track["startISO"],
                # Note: .interpreter can be absent or null. the following
                # statement accounts for both:
                "artist": track.get("interpreter") or "",
                "length": _calculate_length(show_rec, i),
                "show_long": show_rec["title"],
                "show_date": show_date,
                "type": track["type"],
            }
            for i, track in enumerate(show_rec["items"])
            if track["type"] in self.media_types
        ]
        if not items:
            # if the show contains no items, or none we are interested in, play
            # the whole show.
            items = [
                {
                    "id": str(show_rec["start"]),
                    "title": _mojibake(show_rec["title"]),
                    "time": show_rec["startISO"],
                    "artist": show_rec.get("moderator") or "",
                    "length": show_rec["end"] - show_rec["start"],
                    "show_long": show_rec["title"],
                    "show_date": show_date,
                    "type": "",
                }
            ]

        return items

    def get_live_url(self, slug):
        return ORFClient.live_uri % (slug, self.live_bitrate)

    def get_item(self, station, day_id, show_id, item_id):
        show = self.get_show(station, day_id, show_id)
        return next(
            item
            for item in show
            if item["id"].split("-")[0] == item_id.split("-")[0]
        )

    def get_item_url(self, station, shoutcast, day_id, show_id, item_id):
        json = self._get_record_json(station, show_id, day_id)
        if not json:
            return None

        streams = json["streams"]
        if len(streams) == 0:
            return ""

        item_start, item_end, *_ = item_id.split("-", 1) + 1 * [None]
        stream = next(
            stream
            for stream in reversed(streams)
            if stream["start"] <= int(item_start)
        )
        streamId = stream["loopStreamId"]
        offsetstart = int(item_start) - stream["start"]
        offsetende = int(item_end) - stream["start"] if item_end else ""
        return ORFClient.show_uri % (
            shoutcast,
            streamId,
            offsetstart,
            offsetende,
        )

    def refresh(self):
        self.http_client.refresh()

    def _get_json(self, uri):
        try:
            content = self.http_client.get(uri)
            return json.loads(content)
        except Exception as e:
            logger.error(
                "Error decoding content received from '%s': %s", uri, e
            )

    def _get_archive_json(self, station):
        return self._get_json(ORFClient.archive_uri % station)

    def _get_day_json(self, station, day_id):
        json = self._get_archive_json(station)
        return next((rec for rec in json if _get_day_id(rec) == day_id), None)

    def _get_record_json(self, station, programKey, day):
        return self._get_json(ORFClient.record_uri % (station, programKey, day))


def _get_day_id(day_rec):
    return str(day_rec["day"])


def _get_day_label(day_id):
    # The day id is a string in the form "YYYYMMDD".
    date = datetime.datetime.strptime(day_id, "%Y%m%d")
    return date.strftime("%a %Y-%m-%d")


def _to_show(i, rec):
    time = dateutil.parser.parse(rec["scheduledISO"])

    # Note: items with times < 06:00 are from the next day and should be last
    return {
        "id": rec["programKey"],
        "time": time.strftime("%H:%M"),
        "title": rec["title"] + (" *" if not rec["isBroadcasted"] else ""),
    }


def _generic_title(track):
    types = {
        "M": "Musik ",
        "B": "Beitrag ",
        "BJ": "Journal ",
        "N": "Nachrichten ",
        "J": "Jingle ",  # (?)
        "W": "Werbung ",
        # S (Sonstiges) omitted deliberately
    }
    return types.get(track["type"], "") + "ohne Namen"


def _generate_id(show_rec, i):
    start = show_rec["items"][i]["start"]
    if i + 1 < len(show_rec["items"]):
        end = show_rec["items"][i + 1]["start"]
        return f"{start}-{end}"
    else:
        return f"{start}"


def _calculate_length(show_rec, i):
    start = show_rec["items"][i]["start"]
    end = (
        show_rec["items"][i + 1]["start"]
        if i + 1 < len(show_rec["items"])
        else show_rec["end"]
    )
    return end - start


def _mojibake(s):
    """
    The API sometimes returns titles with characters in the C1 control block.
    """
    return re.sub("[\x80-\x9f]", "", s)
