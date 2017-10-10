/*
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
*/


/**
   This enables direct access to fast, cell, and free vars on a frame.

   author: Christopher O'Brien  <obriencj@gmail.com>
   license: LGPL v.3
*/


#include <Python.h>
#include <cellobject.h>
#include <frameobject.h>


#define PARSE_ARGS PyArg_ParseTuple


/**
   Given a code object and index, set a NameError exception with the
   appropriate variable name in the exception's message string.
 */
static void name_error(PyCodeObject *code, int index) {
  PyObject *name = NULL;
  int count = 0;

  count = code->co_nlocals;
  if (index < count) {
    name = PyTuple_GET_ITEM(code->co_varnames, index);
    goto found;
  }

  index -= count;
  count = PyTuple_GET_SIZE(code->co_cellvars);
  if (count && index < count) {
    name = PyTuple_GET_ITEM(code->co_cellvars, index);
    goto found;
  }

  index -= count;
  count = PyTuple_GET_SIZE(code->co_freevars);
  if (count && index < count) {
    name = PyTuple_GET_ITEM(code->co_freevars, index);
    goto found;
  }

  PyErr_SetString(PyExc_NameError, "name <unknown> is not defined");
  return;

 found:

#if PY_MAJOR_VERSION >= 3
  PyErr_Format(PyExc_NameError, "name '%.200s' is not defined",
	       PyUnicode_AsUTF8(name));
#else
  PyErr_Format(PyExc_NameError, "name '%.200s' is not defined",
	       PyString_AsString(name));
#endif
}


/**
   Returns 1 if the index is valid within the code object's range of
   fast locals. Otherwise, sets a ValueError to indicate that the
   index is out-of-range and returns 0.
 */
static inline int valid_fast_index(PyCodeObject *code, int index) {
  if (index < 0 || index >= code->co_nlocals) {

    PyErr_Format(PyExc_ValueError, "fast index %i out of range", index);
    return 0;

  } else {
    return 1;
  }
}


/**
   Returns 1 if the index is valid within the code object's range of
   cell or free locals. Otherwise, sets a ValueError to indicate that
   the index is out-of-range and returns 0.
 */
static inline int valid_cell_index(PyCodeObject *code, int index) {
  if ((index < code->co_nlocals) ||
      (index >= (code->co_nlocals +
		 PyTuple_GET_SIZE(code->co_cellvars) +
		 PyTuple_GET_SIZE(code->co_freevars)))) {

    PyErr_Format(PyExc_ValueError, "cell index %i out of range", index);
    return 0;

  } else {
    return 1;
  }
}


/**
   Returns the value of a frame's fast local variable at the given
   index.

   Raises a ValueError if the index is out of range, or a NameError if
   the given variable is declared but not currently assigned a value.

   From Python:
   value = _frame.frame_get_fast(frame_obj, index)
 */
static PyObject *frame_get_fast(PyObject *self, PyObject *args) {

  PyFrameObject *frame = NULL;
  int index = -1;
  PyObject *defval = NULL;
  PyObject **fast = NULL;
  PyObject *result = NULL;

  if (! PARSE_ARGS(args, "O!i|O", &PyFrame_Type, &frame, &index, &defval))
    return NULL;

  if (! valid_fast_index(frame->f_code, index))
    return NULL;

  fast = frame->f_localsplus;

  result = fast[index];
  Py_XINCREF(result);

  if (! result) {
    if (! defval) {
      name_error(frame->f_code, index);

    } else {
      Py_INCREF(defval);
      result = defval;
    }
  }

  return result;
}


/**
   Assigns the value of a frame's fast local variable at the given
   index.

   Raises a ValueError if the index is out of range.

   From Python:
   _frame.frame_set_fast(frame_obj, index, value)
 */
static PyObject *frame_set_fast(PyObject *self, PyObject *args) {
  PyFrameObject *frame = NULL;
  int index = -1;
  PyObject *value = NULL;
  PyObject **fast = NULL;

  if (! PARSE_ARGS(args, "O!iO", &PyFrame_Type, &frame, &index, &value))
    return NULL;

  if (! valid_fast_index(frame->f_code, index))
    return NULL;

  fast = frame->f_localsplus;

  Py_CLEAR(fast[index]);
  fast[index] = value;
  Py_INCREF(value);

  Py_RETURN_NONE;
}


/**
   Clears the value of a frame's fast local variable at the given
   index, leaving it declared but undefined.

   Raises a ValueError if the index is out of range.

   From Python:
   _frame.frame_del_fast(frame_obj, index)
 */
static PyObject *frame_del_fast(PyObject *self, PyObject *args) {
  PyFrameObject *frame = NULL;
  int index = -1;
  PyObject **fast = NULL;

  if (! PARSE_ARGS(args, "O!i", &PyFrame_Type, &frame, &index))
    return NULL;

  if (! valid_fast_index(frame->f_code, index))
    return NULL;

  fast = frame->f_localsplus;
  Py_CLEAR(fast[index]);

  Py_RETURN_NONE;
}


/**
   Returns the value of a frame's cell or free variable at the given
   index.

   Raises a ValueError if the index is out of range, or a NameError if
   the given variable is declared but not currently assigned a value.

   From Python:
   value = _frame.frame_get_cell(frame_obj, index)
 */
static PyObject *frame_get_cell(PyObject *self, PyObject *args) {

  PyFrameObject *frame = NULL;
  int index = -1;
  PyObject *defval = NULL;
  PyObject **fast = NULL;
  PyObject *result = NULL;

  if (! PARSE_ARGS(args, "O!i|O", &PyFrame_Type, &frame, &index, &defval))
    return NULL;

  if (! valid_cell_index(frame->f_code, index))
    return NULL;

  fast = frame->f_localsplus;
  result = PyCell_Get(fast[index]);

  if (! result) {
    if (! defval) {
      name_error(frame->f_code, index);

    } else {
      Py_INCREF(defval);
      result = defval;
    }
  }

  return result;
}


/**
   Assigns the value of a frame's cell or free variable at the given
   index.

   Raises a ValueError if the index is out of range.

   From Python:
   _frame.frame_set_cell(frame_obj, index, value)
 */
static PyObject *frame_set_cell(PyObject *self, PyObject *args) {
  PyFrameObject *frame = NULL;
  PyObject *value = NULL;
  int index = -1;
  PyObject **fast = NULL;

  if (! PARSE_ARGS(args, "O!iO", &PyFrame_Type, &frame, &index, &value))
    return NULL;

  if (! valid_cell_index(frame->f_code, index))
    return NULL;

  fast = frame->f_localsplus;
  PyCell_Set(fast[index], value);

  Py_RETURN_NONE;
}


/**
   Clears the value of a frame's fast local variable at the given
   index, leaving it declared but undefined.

   Raises a ValueError if the index is out of range.

   From Python:
   _frame.frame_del_cell(frame_obj, index)
 */
static PyObject *frame_del_cell(PyObject *self, PyObject *args) {
  PyFrameObject *frame = NULL;
  int index = -1;
  PyObject **fast = NULL;

  if (! PARSE_ARGS(args, "O!i", &PyFrame_Type, &frame, &index))
    return NULL;

  if (! valid_cell_index(frame->f_code, index))
    return NULL;

  fast = frame->f_localsplus;
  PyCell_Set(fast[index], NULL);

  Py_RETURN_NONE;
}


static PyMethodDef methods[] = {
  { "frame_get_fast",
    (PyCFunction) frame_get_fast, METH_VARARGS,
    "Get the value of a fast variable in a frame. Raises a ValueError"
    " if the index is out of range. Raises a NameError if the variable"
    " is not currently defined."},

  { "frame_set_fast",
    (PyCFunction) frame_set_fast, METH_VARARGS,
    "Set the value of a fast variable in a frame. Raises a ValueError"
    " if the index is out of range." },

  { "frame_del_fast",
    (PyCFunction) frame_del_fast, METH_VARARGS,
    "Clear the value of a fast variable in a frame, marking it as"
    " undefined until a new value is set. Raises a ValueError if the"
    " index is out of range." },

  { "frame_get_cell",
    (PyCFunction) frame_get_cell, METH_VARARGS,
    "Get the value of a cell or free variable in a frame. Raises a"
    " ValueError if the index is out of range. Raises a NameError if"
    " the variable is not currently defined." },

  { "frame_set_cell",
    (PyCFunction) frame_set_cell, METH_VARARGS,
    "Set the value of a cell or free variable in a frame. Raises a"
    " ValueError if the index is out of range." },

  { "frame_del_cell",
    (PyCFunction) frame_del_cell, METH_VARARGS,
    "Clear the value of a cell or free variable in a frame, marking"
    " it as undefined until a new value is set. Raises a ValueError if"
    " the index is out of range." },

  { NULL, NULL, 0, NULL },
};


#if PY_MAJOR_VERSION >= 3
/* Python 3 Mode */


static struct PyModuleDef moduledef = {
  PyModuleDef_HEAD_INIT,
  "livelocals._frame",
  NULL,
  -1,
  methods,
};


PyMODINIT_FUNC PyInit__frame() {
  Py_Initialize();
  return PyModule_Create(&moduledef);
}


#else
/* Python 2 Mode */


PyMODINIT_FUNC init_frame() {
  Py_InitModule("livelocals._frame", methods);
}

#endif


/* The end. */
