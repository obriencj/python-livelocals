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
livelocals

A read-write view into a frame's local variables.

author: Christopher O'Brien  <obriencj@gmail.com>
license: LGPL v.3
"""


from collections import namedtuple
from functools import partial
from inspect import currentframe

from livelocals._frame import *


_ref = namedtuple("_ref", ("get_ref", "set_ref", "del_ref"))


def _create_fast_ref(frame, index):
    return _ref(partial(frame_get_fast, frame, index),
                partial(frame_set_fast, frame, index),
                partial(frame_del_fast, frame, index))


def _create_cell_ref(frame, index):
    return _ref(partial(frame_get_cell, frame, index),
                partial(frame_set_cell, frame, index),
                partial(frame_del_cell, frame, index))


class LiveLocals(object):
    """
    """


    def __init__(self, frame=None):
        if frame is None:
            frame = currentframe().f_back

        self._repr = "<live locals for frame %r>" % frame
        self._refs = refs = {}

        code = frame.f_code

        for i, name in enumerate(code.co_varnames):
            refs[name] = _create_fast_ref(frame, i)

        offset = code.co_nlocals
        for i, name in enumerate(code.co_cellvars):
            refs[name] = _create_cell_ref(frame, i + offset)

        offset += len(code.co_cellvars)
        for i, name in enumerate(code.co_freevars):
            refs[name] = _create_cell_ref(frame, i + offset)


    def __repr__(self):
        return self._repr


    def __getitem__(self, key):
        return self._refs[key].get_ref()


    def __setitem__(self, key, value):
        return self._refs[key].set_ref(value)


    def __delitem__(self, key):
        return self._refs[key].del_ref()


livelocals = LiveLocals


#
# The end.
