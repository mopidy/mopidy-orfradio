import pathlib
from importlib.metadata import version

from mopidy import config, ext

__version__ = version("mopidy-orfradio")


class Extension(ext.Extension):
    dist_name = "mopidy-orfradio"
    ext_name = "orfradio"
    version = __version__

    def get_default_config(self):
        return config.read(pathlib.Path(__file__).parent / "ext.conf")

    def get_config_schema(self):
        schema = super().get_config_schema()
        schema["stations"] = config.List()
        schema["afterhours"] = config.Boolean()
        schema["archive_types"] = config.List()
        schema["livestream_bitrate"] = config.Integer(choices=[128, 192])
        return schema

    def setup(self, registry):
        from mopidy_orfradio.backend import ORFBackend  # noqa: PLC0415

        registry.add("backend", ORFBackend)
