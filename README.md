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

"Didn't `locals()` already do that?"

At the global or module scope, the `locals()` and `globals()`
functions both return the module's underlying `__dict__`. Once you're
inside of a function however, things change. In a function, the
`locals()` is just a snapshot view of the local fast, free, and cell
variables.


## Such a Memory Leak

Sadly, Python doesn't allow weak references to frame objects.

The livelocals objects therefore have hard references to the
particular frame they were invoked from.  If that frame also happens
to have a lingering reference to the livelocals object, then a
circular reference exists.

For example, this is a memory leak
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

Make sure to do this:

```python
def fine_dandy(data):
	x = do_something(data)
	y = more_work(x)
	l = livelocals()
	...
	del l
	return y
```

There's no reference to the livelocals instance anymore, so it will
get GC'd, which will cause its references to the frame to evaporate,
allowing the frame to also get GC'd


## Supported Versions

This has been tested as working on the following versions and
implementations of Python

* Python 2.6, 2.7
* Python 3.4, 3.5, 3.6


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
