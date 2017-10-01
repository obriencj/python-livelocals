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


from livelocals import livelocals
from unittest import TestCase


class TestLiveLocals(TestCase):

    def test_fastvars(self):

        def simple():
            ll = livelocals()

            a = 100
            b = 200

            self.assertEqual(ll["a"], 100)
            ll["a"] = 300

            self.assertEqual(a, 300)
            self.assertEqual(ll["a"], 300)

            return ll

        ll = simple()
        self.assertEqual(ll["a"], 300)
        self.assertEqual(ll["b"], 200)

        ll["b"] = 400
        self.assertEqual(ll["b"], 400)

        del ll


    def test_closure(self):

        outer_value = 777

        def make_closure(value=None):
            def val_1_getter():
                return value
            def val_2_getter():
                return outer_value
            return val_1_getter, val_2_getter, livelocals()

        getter_1, getter_2, ll = make_closure(999)

        self.assertEqual(getter_1(), 999)
        self.assertEqual(ll["value"], 999)

        self.assertEqual(getter_2(), 777)
        self.assertEqual(outer_value, 777)
        self.assertEqual(ll["outer_value"], 777)

        ll["value"] = 888
        self.assertEqual(getter_1(), 888)
        self.assertEqual(ll["value"], 888)

        ll["outer_value"] = 123
        self.assertEqual(getter_2(), 123)
        self.assertEqual(outer_value, 123)
        self.assertEqual(ll["outer_value"], 123)

        del ll


    def test_fast_del(self):
        ll = livelocals()

        value = 100
        self.assertEqual(value, 100)
        self.assertEqual(ll["value"], 100)

        del value

        # can't use a lambda to look up value, that would make it a
        # closure cell
        try:
            value
        except NameError:
            pass
        else:
            self.assertTrue(False)

        try:
            ll["value"]
        except NameError:
            pass
        else:
            self.assertTrue(False)

        value = 200
        self.assertEqual(value, 200)
        self.assertEqual(ll["value"], 200)

        del ll["value"]

        try:
            value
        except NameError:
            pass
        else:
            self.assertTrue(False)

        try:
            ll["value"]
        except NameError:
            pass
        else:
            self.assertTrue(False)


    def test_closure_del(self):

        outer_value = 777

        def get_outer_value():
            return outer_value

        def make_closure(value=None):
            def val_1_getter():
                return value
            def val_2_getter():
                return outer_value;
            return val_1_getter, val_2_getter, livelocals()

        getter_1, getter_2, ll = make_closure(999)

        self.assertEqual(getter_1(), 999)
        del ll["value"]
        self.assertRaises(NameError, getter_1)
        ll["value"] = 123
        self.assertEqual(getter_1(), 123)

        self.assertEqual(getter_2(), 777)
        del ll["outer_value"]
        self.assertRaises(NameError, getter_2)
        self.assertRaises(NameError, get_outer_value)

        ll["outer_value"] = 456
        self.assertEqual(getter_2(), 456)

        del ll


    def test_intern(self):

        ll1 = livelocals()
        ll2 = livelocals()

        self.assertTrue(ll1 is ll2)
        self.assertEqual(repr(ll1), repr(ll2))

        def make_inner():
            return livelocals()

        ll1 = make_inner()
        ll2 = make_inner()

        self.assertFalse(ll1 is ll2)

        del ll1
        del ll2


    def test_name_error(self):

        def make_inner():
            x = 100
            del x
            return livelocals()

        ll = make_inner()

        try:
            ll["x"]
        except NameError as ne:
            self.assertEqual(ne.args[0], "name 'x' is not defined")
        else:
            self.assertFalse(True)

        del ll


    def test_generator(self):
        def make_gen(value=None):
            yield livelocals()
            try:
                while True:
                    tmp = value
                    del value
                    yield tmp
            except NameError:
                pass

        seq = make_gen(100)
        ll = next(seq)

        self.assertEqual(next(seq), 100)
        ll["value"] = 101
        self.assertEqual(next(seq), 101)
        ll["value"] = 102
        self.assertEqual(next(seq), 102)

        self.assertRaises(StopIteration, next, seq)

        del ll


    def test_map_accessors(self):
        a = 100
        b = 200
        c = 300

        z = 999
        del z

        ll = livelocals()

        self.assertEqual(sorted(ll.items()),
                         [("a", 100),
                          ("b", 200),
                          ("c", 300),
                          ("ll", ll),
                          ("self", self)])

        self.assertEqual(sorted(ll.keys()),
                         ["a", "b", "c", "ll", "self"])

        self.assertEqual(set(ll.values()),
                         set([100, 200, 300, ll, self]))

        self.assertEqual(ll.get("a", 123), 100)

        self.assertEqual(ll.setdefault("b", 321), 200)
        self.assertEqual(b, 200)

        del c
        self.assertEqual(ll.get("c", 123), 123)
        self.assertEqual(ll.setdefault("c", 321), 321)
        self.assertEqual(c, 321)

        del ll


    def test_contains(self):
        a = 100

        ll = livelocals()

        self.assertTrue("a" in ll)
        self.assertTrue("c" in ll)
        self.assertFalse("z" in ll)

        # c is defined late, but it should still be a key in
        # livelocals.
        c = 300


    def test_update(self):
        a = 100
        b = 200

        c = 300
        del c

        ll = livelocals()

        self.assertEqual(ll["a"], 100)
        self.assertEqual(ll["b"], 200)
        self.assertEqual(ll.get("c"), None)

        ll.update({"a": 123, "b": 456, "c": 789, "z": 999})

        self.assertEqual(ll["a"], 123)
        self.assertEqual(ll["b"], 456)
        self.assertEqual(ll["c"], 789)
        self.assertRaises(KeyError, ll.__getitem__, "z")


#
# The end.
