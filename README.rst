pbxproj-lint
============

A linter for Xcode .pbxproj files. Currently detects the following issues:

- Missing files (files referenced in project but not present on disk)
- Extraneous files (files present on disk but not referenced in project)
- Missing localizations

It can optionally remove all extraneous files.

Usage
=====
Invoke as::

    pbxproj_lint [--strict] [--clean] PBXPROJ_FILE

Options:

- ``--strict``: Treat missing localizations of binary media files as an error
  instead of a warning.
- ``--clean``: Remove extraneous files from disk (you will not be asked for
  confirmation, so be careful!)

Quick Install
=============
This package is not on PyPI, so install with::

    pip install git+https://github.com/amake/pbxproj-lint.git
  
Known Limitations
=================

pbxproj-lint has not been tested and probably does not work with projects that
are not using Base Internationalization.
  
License
=======

pbxproj-lint is distributed under the `MIT license <LICENSE.txt>`__.
