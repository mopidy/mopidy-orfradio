import pathlib
import zoneinfo
from importlib.metadata import version

from mopidy import config, ext

__version__ = version("mopidy-orfradio")

TZ = zoneinfo.ZoneInfo("Europe/Vienna")


class Extension(ext.Extension):
    dist_name = "mopidy-orfradio"
    ext_name = "orfradio"
    version = __version__

    def get_default_config(self) -> str:
        return config.read(pathlib.Path(__file__).parent / "ext.conf")

    def get_config_schema(self) -> config.ConfigSchema:
        schema = super().get_config_schema()
        schema["stations"] = config.List()
        schema["afterhours"] = config.Boolean()
        schema["archive_types"] = config.List()
        schema["livestream_bitrate"] = config.Integer(choices=[128, 192])
        return schema

    def setup(self, registry) -> None:
        from mopidy_orfradio.backend import ORFBackend  # noqa: PLC0415

        registry.add("backend", ORFBackend)
