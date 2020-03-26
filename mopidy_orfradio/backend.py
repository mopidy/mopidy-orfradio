from __future__ import unicode_literals

import logging

from mopidy import backend

import pykka

from mopidy_orfradio.library import ORFLibraryProvider
from mopidy_orfradio.playback import ORFPlaybackProvider

logger = logging.getLogger(__name__)


class ORFBackend(pykka.ThreadingActor, backend.Backend):
    def __init__(self, config, audio):
        super(ORFBackend, self).__init__()

        self.config = config

        self.library = ORFLibraryProvider(backend=self)
        self.playback = ORFPlaybackProvider(audio=audio, backend=self)
        self.uri_schemes = ['orfradio']

    def on_start(self):
        logger.info('Starting ORFBackend')

    def on_stop(self):
        pass
