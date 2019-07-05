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


__all__ = ("LiveLocals", "livelocals", "generatorlocals",
           "LocalVar", "localvar", "getvar", "setvar", "delvar", )


class RaiseError(object):
    def __repr__(self):
        return "<raise NameError>"


# this is just a fun sentinel default value for getvar.
_raise_error = RaiseError()


del RaiseError


# simple way to hold the getter, setter, and clear functions for each
# var in a frame.
LocalVar = namedtuple("LocalVar", ("getvar", "setvar", "delvar",
                                   "frame", "name", ))


def _local_fast(frame, index, name):
    """
    Create an object with three functions for getting, setting, and
    clearing a fast var with the given index on the specified frame.
    """

    return LocalVar(partial(frame_get_fast, frame, index),
                    partial(frame_set_fast, frame, index),
                    partial(frame_del_fast, frame, index),
                    frame, name)


def _local_cell(frame, index, name):
    """
    Create an object with three functions for getting, setting, and
    clearing a cell or free var with the given index on the specified
    frame.
    """

    return LocalVar(partial(frame_get_cell, frame, index),
                    partial(frame_set_cell, frame, index),
                    partial(frame_del_cell, frame, index),
                    frame, name)


def localvar(name, frame=None):
    """
    Returns a LocalVar namedtuple instance with accessors for getting,
    setting, and clearing the relevant variable in its frame. If no
    local variable with a matching name was found, returns None.

    If frame is None, the calling frame is used.
    """

    if frame is None:
        frame = currentframe().f_back

    code = frame.f_code

    i = -1
    for i, n in enumerate(code.co_varnames):
        if n == name:
            return _local_fast(frame, i, n)

    for i, n in enumerate(code.co_cellvars, i + 1):
        if n == name:
            return _local_cell(frame, i, n)

    for i, n in enumerate(code.co_freevars, i + 1):
        if n == name:
            return _local_cell(frame, i, n)

    return None


def getvar(name, default=_raise_error, frame=None):
    """
    Get the value of a frame's local variable with the given name. If
    no matching variable was found, or if the variable was found but
    currently holds no value, returns a default value if one was
    supplied, otherwise raises a NameError.

    If frame is None, the calling frame is used.
    """

    if frame is None:
        frame = currentframe().f_back

    var = localvar(name, frame)

    if var is None:
        if default is _raise_error:
            raise NameError("name %r is not defined" % name)
        else:
            return default

    elif default is _raise_error:
        return var.getvar()

    else:
        return var.getvar(default)


def setvar(name, value, frame=None):
    """
    Assign the value of a frame's local variable with the given
    name. If no matching variable was found, does nothing.

    If frame is None, the calling frame is used.
    """

    if frame is None:
        frame = currentframe().f_back

    var = localvar(name, frame)
    if var is not None:
        var.setvar(value)


def delvar(name, frame=None):
    """
    Clear the value of a frame's local variable with the given
    name. If no matching variable was found, does nothing.

    If frame is None, the calling frame is used.
    """

    if frame is None:
        frame = currentframe().f_back

    var = localvar(name, frame)
    if var is not None:
        var.delvar()


class LiveLocals(object):
    """
    Living view of a frame's local fast, free, and cell variables.

    This instance will keep a reference to the frame alive. If the
    frame in turn holds a reference to this instance, a circular
    reference will be created which will prevent the frame and all its
    variables from being deallocated. The `clear()` method of this
    instance will release all references to the frame, and will remove
    any references the frame may have to the instance as well.
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
            vars[name] = _local_fast(frame, i, name)

        for i, name in enumerate(code.co_cellvars, i + 1):
            vars[name] = _local_cell(frame, i, name)

        for i, name in enumerate(code.co_freevars, i + 1):
            vars[name] = _local_cell(frame, i, name)


    def __enter__(self):
        return self


    def __exit__(self, _tb_type, _tb_value, _tb_traceback):
        self.clear()


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

        return self._vars[key].getvar()


    def __setitem__(self, key, value):
        """
        Implements  `livelocals()[key] = var`

        Assigns value to the given declared variable.

        If the variable is not declared in the underlying frame,
        raises a KeyError.
        """

        return self._vars[key].setvar(value)


    def __delitem__(self, key):
        """
        Implements  `del livelocals()[key]`

        Clears the value for the given declared variable.

        If the variable is not declared in the underlying frame,
        raises a KeyError.
        """

        return self._vars[key].delvar()


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

            return (key for key, value in self.items())


        def values(self):
            """
            Iterator of the values of defined variables for the underlying
            frame.
            """

            return (value for key, value in self.items())


        def items(self):
            """
            Iterator of (key, value) tuples representing the defined variables
            for the underlying frame. Variables which are declared but
            not set to a value (ie. declared but undefined) are
            omitted.
            """

            for key, var in self._vars.items():
                try:
                    yield (key, var.getvar())
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

            return (key for key, value in self.iteritems())


        def keys(self):
            """
            List of variable names with defined values in the underlying
            frame. Omits variables which are declared but not
            currently defined.
            """

            return [key for key, value in self.iteritems()]


        def itervalues(self):
            """
            Iterator of the values of defined variables for the underlying
            frame.
            """

            return (value for key, value in self.iteritems())


        def values(self):
            """
            List of the values of defined variables for the underlying frame.
            """

            return [value for key, value in self.iteritems()]


        def iteritems(self):
            """
            Iterator of (key, value) tuples representing the defined variables
            for the underlying frame. Variables which are declared but
            not set to a value (ie. declared but undefined) are
            omitted.
            """

            for key, var in self._vars.iteritems():
                try:
                    yield (key, var.getvar())
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
            return self._vars[key].getvar(default)
        except KeyError:
            return default


    def localvar(self, key):
        """
        Returns the underlying LocalVar namedtuple for the given key, or
        None if that variable isn't in this scope.
        """

        return self._vars.get(key, None)


    def update(self, mapping, allow=None):
        """
        Updates matching scoped variables to the value from mapping, if
        any. All non-matching keys from mapping are ignored.

        If allow is specified, it may be a unary function or a
        sequence. If it is a function, then only keys from mapping
        which return True when passed to the function will be used to
        update the local variables. If it is a sequence, then only
        keys from mapping which are in the sequence will be used to
        update the local variables.
        """

        if allow is None:
            source = mapping.items()

        elif callable(allow):
            source = ((key, value) for key, value in mapping.items()
                      if allow(key))

        else:
            source = ((key, value) for key, value in mapping.items()
                      if key in allow)

        vars = self._vars

        for key, val in source:
            if key in vars:
                vars[key].setvar(val)


    def setdefault(self, key, default=None):
        """
        Returns the value of a scoped variable if it is both declared and
        assigned. If unassigned, assigns and returns the given default
        value. If undeclared, simply returns the given default value.
        """

        try:
            return self._vars[key].getvar()
        except KeyError:
            return default
        except NameError:
            self._vars[key].setvar(default)
            return default


    def clear(self):
        """
        Releases the references to the underlying frame, and removes any
        references in the frame to this livelocals by clearing the
        variable.
        """

        for key, val in self.items():
            if val is self:
                self._vars[key].delvar()
                break

        self._vars.clear()


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
