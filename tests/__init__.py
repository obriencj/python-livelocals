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


    def test_del(self):

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


    def test_intern(self):

        ll1 = livelocals()
        ll2 = livelocals()

        self.assertIs(ll1, ll2)
        self.assertEqual(repr(ll1), repr(ll2))


#
# The end.
