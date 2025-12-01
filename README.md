# mopidy-orfradio

[![Latest PyPI version](https://img.shields.io/pypi/v/mopidy-orfradio)](https://pypi.org/p/mopidy-orfradio)
[![CI build status](https://img.shields.io/github/actions/workflow/status/mopidy/mopidy-orfradio/ci.yml)](https://github.com/mopidy/mopidy-orfradio/actions/workflows/ci.yml)
[![Test coverage](https://img.shields.io/codecov/c/gh/mopidy/mopidy-orfradio)](https://codecov.io/gh/mopidy/mopidy-orfradio)

[Mopidy](https://mopidy.com/) extension to access the
[Austrian ORF radio stations](https://sound.orf.at/).
It provides access to the live streams and the 7 day archive.

Note that timestamps from the API are somewhat inaccurate (especially on
non-music segments). This can cause a slight glitch between tracks, or in very
few extreme cases the beginning getting cut off. The implementation avoids
cutting off the end of tracks, with the trade off of sometimes appending a few
seconds from the next to the previous.


## Installation

Install by running:

```sh
python3 -m pip install mopidy-orfradio
```

See https://mopidy.com/ext/orfradio/ for alternative installation methods.


## Configuration

Before starting Mopidy, you must add configuration for
mopidy-orfradio to your Mopidy configuration file:

```ini
[orfradio]

# Stations to display
#
# Default:
stations =
    oe1
    oe3
    fm4
    campus
    bgl
    ktn
    noe
    ooe
    sbg
    stm
    tir
    vbg
    slo

# Remove from list to automatically skip tracks of the type.
#
# Available types: [M]usik, [B]eitrag, [BJ]ournal, [N]achrichten,
# [J]ingle, [W]erbung, [S]onstiges
#
# Default:
archive_types =
    M
    B
    BJ
    N

# Live stream is available as 128 or 192 kbit/s. The archive always plays
# at 192 kbit/s.
#
# Default:
livestream_bitrate = 192
```


## Project resources

- [Source code](https://github.com/mopidy/mopidy-orfradio)
- [Issues](https://github.com/mopidy/mopidy-orfradio/issues)
- [Releases](https://github.com/mopidy/mopidy-orfradio/releases)


## Development

### Set up development environment

Clone the repo using, e.g. using [gh](https://cli.github.com/):

```sh
gh repo clone mopidy/mopidy-orfradio
```

Enter the directory, and install dependencies using [uv](https://docs.astral.sh/uv/):

```sh
cd mopidy-orfradio/
uv sync
```

### Running tests

To run all tests and linters in isolated environments, use
[tox](https://tox.wiki/):

```sh
tox
```

To only run tests, use [pytest](https://pytest.org/):

```sh
pytest
```

To format the code, use [ruff](https://docs.astral.sh/ruff/):

```sh
ruff format .
```

To check for lints with ruff, run:

```sh
ruff check .
```

To check for type errors, use [pyright](https://microsoft.github.io/pyright/):

```sh
pyright .
```

### Making a release

To make a release to PyPI, go to the project's [GitHub releases
page](https://github.com/mopidy/mopidy-orfradio/releases)
and click the "Draft a new release" button.

In the "choose a tag" dropdown, select the tag you want to release or create a
new tag, e.g. `v0.1.0`. Add a title, e.g. `v0.1.0`, and a description of the changes.

Decide if the release is a pre-release (alpha, beta, or release candidate) or
should be marked as the latest release, and click "Publish release".

Once the release is created, the `release.yml` GitHub Action will automatically
build and publish the release to
[PyPI](https://pypi.org/project/mopidy-orfradio/).


## Credits

- Original author: [Tobias Girstmair](https://gir.st/), [David Tischler](https://github.com/tischlda)
- Current maintainer: [Tobias Girstmair](https://gir.st/)
- [Contributors](https://github.com/mopidy/mopidy-orfradio/graphs/contributors)
