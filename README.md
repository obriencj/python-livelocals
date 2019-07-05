# Overview of python-livelocals

[![Build Status](https://travis-ci.org/obriencj/python-livelocals.svg?branch=master)](https://travis-ci.org/obriencj/python-livelocals)

Mapping object that provides an active, living read/write interface
for a frame's local fast, free, and cell variables.

`livelocals()` is similar to the builtin `locals()` function, but is
always up-to-date, and assigning or deleting values in a LiveLocals
instance will also alter the actual variables for the scope in which
it was created.

[python]: http://python.org "Python"


## Wait...

"Doesn't `locals()` already do that?"

At the global or module scope, the `locals()` and `globals()`
functions both return the module's underlying `__dict__`. Once you're
inside of a function however, things change. In a function, the
`locals()` is just a snapshot view of the frame's fast, free, and cell
variables.


## Features

A LiveLocals instance (obtained by calling `livelocals()`) can read
and assign to all of the variables defined or consumed in a scope. It
can also clear them.  It will happily function in concert with a
closure or a generator, allowing you to alter the lexical bindings at
runtime.

It cannot introduce new variables into the scope. It cannot read or
alter global variables (but `globals()` already lets you do that).


## Usage


### `livelocals`

```python
def working_loop(foo=100, bar=200):
    baz = True
    keep_running = True

    while keep_running:
        phone_home(foo, bar, baz)
        data = do_important_stuff(foo, bar)
        livelocals().update(data)
```

In the above contrived example, the `data` mapping returned by the
imaginary `do_important_stuff` call contains new values for the local
scope of the working loop. Instead of extracting the keys and
assigning them to the local scope individually, data may contain ANY
of the local variables for the working loop, and they will be
reassigned to their new values.

There's an optional `allow` argument to the `update` method, which
will limit the modification of local variable to only those which are
either it a specified list, or pass a filtering function.

```python
def working_loop(foo=100, bar=200):
    baz = True
    keep_running = True

    while keep_running:
        phone_home(foo, bar, baz)
        data = do_important_stuff(foo, bar)
        livelocals().update(data, allow=("baz", "keep_running"))
```


### `generatorlocals`

The `generatorlocals` function allows you to access the livelocals of
a running generator function.

```python
def working_loop(foo=100, bar=200):
    tweak = False
    while True:
        yield do_important_stuff(foo, bar, tweak)

gen = working_loop()

for X in gen:
    if X == "cheddar cheese":
        # special case, the working_loop yielded cheddar cheese!
        # Better enable tweak mode!
        generatorlocals(gen)["tweak"] = True
```


### `localvar`

If you only need access to a single variable by name, the `localvar`
function will provide a simple interface for getting, setting, or
clearing it.

```python
def working_loop(foo=100, bar=200):

    # some distant subsystem might kick off a callback, and we want
    # to make that value our new bar
    hook_some_callback(localvar("bar").setvar)

    while bar < 900:
        do_important_stuff(foo, bar)
```


## Circular Reference

Sadly, Python doesn't allow weak references to frame objects. The
livelocals and localvar objects therefore have strong references to
the particular frame they were invoked from. If that frame also
happens to have a lingering reference to the livelocals or localvar
objects, then a circular reference exists.

For example, this will create a circular reference, preventing the
frame or any of its variables from being deallocated.
```python
def such_leak(data):
    x = do_something(data)
    y = more_work(x)
    l = livelocals()
    ...
    return y
```

The livelocals instance refers to the frame, and the frame never
cleared the value of the variable `l` which is a reference to the
livelocals. Circular reference!

To fix this, just make sure to delete any reference to livelocals or
localvar objects.
```python
def fine_dandy(data):
    x = do_something(data)
    y = more_work(x)
    l = livelocals()
    ...
    del l
    return y
```

This decrements the livelocals ref count, letting it be deallocated
right away, which also clears the references it had to the frame, so
it can be similarly deallocated.

A livelocals instance also has a `clear()` method which will release
internal references to the frame, and drop the frame's reference to
the livelocals object if one exists.

In addition, livelocals instances can be used via the context manager
keyword `with`, which will call `clear()` when the context exits.
```python
def fine_dandy(data):
    x = do_something(data)
    with livelocals() as ll:
        y = send_locals_elsewhere(ll)
        ...
    # ll has been cleared safely
    return y
```


## Supported Versions

This has been tested as working on the following versions and
implementations of Python

* Python 2.6, 2.7
* Python 3.4, 3.5, 3.6, 3.7


## Contact

author: Christopher O'Brien <obriencj@gmail.com>

original git repository: <https://github.com/obriencj/python-livelocals>


## License

This library is free software; you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation; either version 3 of the
License, or (at your option) any later version.

This library is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, see
<http://www.gnu.org/licenses/>.
