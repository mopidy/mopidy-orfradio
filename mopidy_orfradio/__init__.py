import logging
import os

from mopidy import config, ext


__version__ = "2.0.0"

logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = "Mopidy-ORFRadio"
    ext_name = "orfradio"
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), "ext.conf")
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super().get_config_schema()
        schema["stations"] = config.List()
        schema["afterhours"] = config.Boolean()
        schema["archive_types"] = config.List()
        return schema

    def setup(self, registry):
        from .backend import ORFBackend

        registry.add("backend", ORFBackend)
