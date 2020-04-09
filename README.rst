****************************
Mopidy-ORFRadio
****************************

.. image:: https://img.shields.io/pypi/v/Mopidy-ORFRadio
    :target: https://pypi.org/project/Mopidy-ORFRadio/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/circleci/build/gh/mopidy/mopidy-orfradio
    :target: https://circleci.com/gh/mopidy/mopidy-orfradio
    :alt: CircleCI build status

.. image:: https://img.shields.io/codecov/c/gh/mopidy/mopidy-orfradio
    :target: https://codecov.io/gh/mopidy/mopidy-orfradio
    :alt: Test coverage

`Mopidy <http://www.mopidy.com/>`_ extension to access the `Austrian ORF radio
stations <https://radiothek.orf.at/>`_.  It provides access to the live streams
and the 7 day archive.

Note that timestamps from the API are somewhat inaccurate (especially on
non-music segments). This can cause a slight glitch between tracks, or in very
few extreme cases the beginning getting cut off. The implementation avoids
cutting off the end of tracks, with the trade off of sometimes appending a few
seconds form the next to the previous.

Installation
============

Install by running::

    python3 -m pip install Mopidy-ORFRadio

See https://mopidy.com/ext/orfradio/ for alternative installation methods.


Configuration
=============

Before starting Mopidy, you may add configuration for
Mopidy-ORFRadio to your Mopidy configuration file::

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

    # Remove from list to automatically skip tracks of the type.
    #
    # available types: [M]usik, [B]eitrag, [BJ]ournal, [N]achrichten,
    # [J]ingle, [W]erbung, [S]onstiges
    # Default:
    archive_types =
        M
        B
        BJ
        N


Project resources
=================

- `Source code <https://github.com/mopidy/mopidy-orfradio>`_
- `Issue tracker <https://github.com/mopidy/mopidy-orfradio/issues>`_
- `Changelog <https://github.com/mopidy/mopidy-orfradio/blob/master/CHANGELOG.rst>`_


Credits
=======

- Original author: `Tobias Girstmair <https://gir.st/>`__, `David Tischler <https://github.com/tischlda>`__
- Current maintainer: `Tobias Girstmair <https://gir.st/>`__
- `Contributors <https://github.com/mopidy/mopidy-orfradio/graphs/contributors>`_
