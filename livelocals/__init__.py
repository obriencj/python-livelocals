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


__all__ = ("LiveLocals", "livelocals", "generatorlocals", )


# simple way to hold the getter, setter, and clear functions for each
# var in a frame.
_frame_var = namedtuple("frame_var", ("get_var", "set_var", "del_var", ))


def _create_fast_var(frame, index):
    """
    Create an object with three functions for getting, setting, and
    clearing a fast var with the given index on the specified frame.
    """

    return _frame_var(partial(frame_get_fast, frame, index),
                      partial(frame_set_fast, frame, index),
                      partial(frame_del_fast, frame, index))


def _create_cell_var(frame, index):
    """
    Create an object with three functions for getting, setting, and
    clearing a cell or free var with the given index on the specified
    frame.
    """

    return _frame_var(partial(frame_get_cell, frame, index),
                      partial(frame_set_cell, frame, index),
                      partial(frame_del_cell, frame, index))


class LiveLocals(object):
    """
    Living view of a frame's local fast, free, and cell variables.
    """

    __slots__ = ("_frame_id", "_vars", "__weakref__", )


    def __init__(self, frame):
        """
        Initializes a Live Locals view for a frame.
        """

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
        """
        Implements  `livelocals()[key]`

        Returns the value of the given declared variable.

        If the variable is not declared in the underlying frame,
        raises a KeyError. If the variable is declared but not
        currently defined, raises a NameError.
        """

        return self._vars[key].get_var()


    def __setitem__(self, key, value):
        """
        Implements  `livelocals()[key] = var`

        Assigns value to the given declared variable.

        If the variable is not declared in the underlying frame,
        raises a KeyError.
        """

        return self._vars[key].set_var(value)


    def __delitem__(self, key):
        """
        Implements  `del livelocals()[key]`

        Clears the value for the given declared variable.

        If the variable is not declared in the underlying frame,
        raises a KeyError.
        """

        return self._vars[key].del_var()


    def __contains__(self, key):
        """
        Implements  `key in livelocals()`

        True if key is declared (but not necessarily defined) in the
        underlying frame.
        """

        return key in self._vars


    if (3, 0) <= version_info:
        # Python 3 mode

        def keys(self):
            """
            Iterator of variable names with defined values in the underlying
            frame. Omits variables which are declared but not
            currently defined.
            """
            return map(lambda r: r[0], self.items())


        def values(self):
            """
            Iterator of the values of defined variables for the underlying
            frame.
            """
            return map(lambda r: r[1], self.items())


        def items(self):
            """
            Iterator of (key, value) tuples representing the defined variables
            for the underlying frame. Variables which are declared but
            not set to a value (ie. declared but undefined) are
            omitted.
            """
            for key, var in self._vars.items():
                try:
                    yield (key, var.get_var())
                except NameError:
                    pass


    else:
        # Python 2 mode

        def iterkeys(self):
            """
            Iterator of variable names with defined values in the underlying
            frame. Omits variables which are declared but not
            currently defined.
            """
            return imap(lambda r: r[0], self.iteritems())


        def keys(self):
            """
            List of variable names with defined values in the underlying
            frame. Omits variables which are declared but not
            currently defined.
            """
            return list(self.iterkeys())


        def itervalues(self):
            """
            Iterator of the values of defined variables for the underlying
            frame.
            """
            return imap(lambda r: r[1], self.iteritems())


        def values(self):
            """
            List of the values of defined variables for the underlying frame.
            """
            return list(self.itervalues())


        def iteritems(self):
            """
            Iterator of (key, value) tuples representing the defined variables
            for the underlying frame. Variables which are declared but
            not set to a value (ie. declared but undefined) are
            omitted.
            """
            for key, var in self._vars.iteritems():
                try:
                    yield (key, var.get_var())
                except NameError:
                    pass


        def items(self):
            """
            List of (key, value) tuples representing the defined variables for
            the underlying frame. Variables which are declared but not
            set to a value (ie. declared but undefined) are omitted.
            """

            return list(self.iteritems())


    def get(self, key, default=None):
        """
        Returns the value of a scoped variable if it is declared and
        assigned. If undeclared or unassigned, return the given
        default value.
        """
        try:
            return self._vars[key].get_var()
        except (KeyError, NameError):
            return default


    def update(self, mapping):
        """
        Updates matching scoped variables to the value from mapping, if
        any. All non-matching keys from mapping are ignored.
        """

        vars = self._vars
        for key, val in mapping.items():
            if key in vars:
                vars[key].set_var(val)


    def setdefault(self, key, default=None):
        """
        Returns the value of a scoped variable if it is both declared and
        assigned. If unassigned, assigns and returns the given default
        value. If undeclared, simply returns the given default value.
        """

        try:
            return self._vars[key].get_var()
        except KeyError:
            return default
        except NameError:
            self._vars[key].set_var(default)
            return default


# This is our default cache. Frames can't be weakreferenced, so we
# keep a weak ref to the LiveLocals instance instead.
_cache = WeakValueDictionary()


def livelocals(frame=None, _cache=_cache):
    """
    Given a Python frame, return a live view of its variables. If
    frame is unspecified or None, the calling frame is used.
    """

    if frame is None:
        frame = currentframe().f_back

    if _cache is None:
        found = LiveLocals(frame)

    else:
        found = _cache.get(frame, None)
        if found is None:
            found = LiveLocals(frame)
            _cache[frame] = found

    return found


def generatorlocals(gen):
    """
    Given a Python generator, return a livelocals for its frame.

    Anything other than a generator object (ie. something that doesn't
    have the gi_frame attribute) will result in an AttributeError
    being raised.
    """

    return livelocals(gen.gi_frame)


#
# The end.
