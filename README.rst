Flake8-diff
===========

A tool to limit what files are flake8 checked so that you can
gradually reach PEP8 compliance.

Example usage::

 $ ./flake8-diff.py -h
 usage: flake8-diff.py [-h] [-v] [-a]

 optional arguments:
   -h, --help     show this help message and exit
   -v, --verbose  Increase verbosity (specify multiple times for more).
                  (default: 0)
   -a, --all      Check the entire repository, not just changed files.
                  (default: False)
