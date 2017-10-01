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

A living read/write view into a frame's local variables.

author: Christopher O'Brien  <obriencj@gmail.com>
license: LGPL v.3
"""


from collections import namedtuple
from functools import partial
from inspect import currentframe
from sys import version_info
from weakref import WeakValueDictionary

from livelocals._frame import \
    frame_get_fast, frame_set_fast, frame_del_fast, \
    frame_get_cell, frame_set_cell, frame_del_cell


if (2, 0) <= version_info < (3, 0):
    from itertools import imap


__all__ = ("livelocals", )


_var = namedtuple("_var", ("get_var", "set_var", "del_var", ))


def _create_fast_var(frame, index):
    return _var(partial(frame_get_fast, frame, index),
                partial(frame_set_fast, frame, index),
                partial(frame_del_fast, frame, index))


def _create_cell_var(frame, index):
    return _var(partial(frame_get_cell, frame, index),
                partial(frame_set_cell, frame, index),
                partial(frame_del_cell, frame, index))


class LiveLocals(object):
    """
    Living view of a frame's local fast, free, and cell variables.
    """


    __slots__ = ("_frame_id", "_vars", "__weakref__", )

    _intern = WeakValueDictionary()


    def __new__(cls, frame=None):
        if frame is None:
            frame = currentframe().f_back

        found = cls._intern.get(frame, None)
        if found is None:
            found = super(LiveLocals, cls).__new__(cls)
            cls._intern[frame] = found

        return found


    def __init__(self, frame=None):
        if frame is None:
            frame = currentframe().f_back

        self._frame_id = id(frame)
        self._vars = vars = {}

        code = frame.f_code

        i = -1
        for i, name in enumerate(code.co_varnames):
            vars[name] = _create_fast_var(frame, i)

        for i, name in enumerate(code.co_cellvars, i + 1):
            vars[name] = _create_cell_var(frame, i)

        for i, name in enumerate(code.co_freevars, i + 1):
            vars[name] = _create_cell_var(frame, i)


    def __repr__(self):
        return "<livelocals for frame at 0x%08x>" % self._frame_id


    def __getitem__(self, key):
        return self._vars[key].get_var()


    def __setitem__(self, key, value):
        return self._vars[key].set_var(value)


    def __delitem__(self, key):
        return self._vars[key].del_var()


    def __contains__(self, key):
        return key in self._vars


    if (3, 0) <= version_info:
        # Python 3 mode

        def keys(self):
            return map(lambda r: r[0], self.items())


        def values(self):
            return map(lambda r: r[1], self.items())


        def items(self):
            for key, var in self._vars.items():
                try:
                    yield (key, var.get_var())
                except NameError:
                    pass


    else:
        # Python 2 mode

        def iterkeys(self):
            return imap(lambda r: r[0], self.iteritems())


        def keys(self):
            return list(self.iterkeys())


        def itervalues(self):
            return imap(lambda r: r[1], self.iteritems())


        def values(self):
            return list(self.itervalues())


        def iteritems(self):
            for key, var in self._vars.iteritems():
                try:
                    yield (key, var.get_var())
                except NameError:
                    pass


        def items(self):
            return list(self.iteritems())


    def get(self, key, default=None):
        try:
            return self._vars[key].get_var()
        except NameError:
            return default


    def update(self, mapping):
        vars = self._vars
        for key, val in mapping.items():
            if key in vars:
                vars[key].set_var(val)


    def setdefault(self, key, default=None):
        try:
            return self._vars[key].get_var()
        except NameError:
            self._vars[key].set_var(default)
            return default


livelocals = LiveLocals


#
# The end.
