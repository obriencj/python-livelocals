#!/usr/bin/env python

# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, see
# <http://www.gnu.org/licenses/>.


"""
A Python Project Livelocals

author: Christopher O'Brien <obriencj@gmail.com>
license: LGPL v.3
"""


try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension


PYTHON_SUPPORTED_VERSIONS = (
    ">=2.6",
    "!=3.0.*", "!=3.1.*", "!=3.2.*", "!=3.3.*",
    "<4",
)


TROVE_CLASSIFIERS = (
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved"
    " :: GNU Lesser General Public License v3 or later (LGPLv3+)",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Topic :: Software Development :: Libraries :: Python Modules",
)

ext_frame = Extension("livelocals._frame", ["livelocals/frame.c"])


setup(name = "livelocals",
      version = "1.0.0",

      packages = ["livelocals"],
      ext_modules = [ext_frame],

      test_suite = "tests",

      zip_safe = True,

      # PyPI information
      author = "Christopher O'Brien",
      author_email = "obriencj@gmail.com",
      url = "https://github.com/obriencj/python-livelocals",
      license = "GNU Lesser General Public License v3",

      description = "Live Locals for Python",

      python_requires = ", ".join(PYTHON_SUPPORTED_VERSIONS),
      classifiers = TROVE_CLASSIFIERS)


#
# The end.
