pbxproj_lint
============

A linter for Xcode .pbxproj files. Currently detects the following issues:

- Missing files (files referenced in project but not present on disk)
- Extraneous files (files present on disk but not referenced in project)
- Missing localizations

It can optionally remove all extraneous files.

Usage
=====

::
   pbxproj_lint [--strict] [--clean] PBXPROJ_FILE

Options:

- ``--strict``: Treat missing localizations of binary media files as an error
  instead of a warning.
- ``--clean``: Remove extraneous files from disk (you will not be asked for
  confirmation, so be careful!)

Known Limitations
=================

pbxproj_lint has not been tested and probably does not work with projects that
are not using Base Internationalization.
  
License
=======

pbxproj_lint is distributed under the MIT license. See LICENSE.txt.
