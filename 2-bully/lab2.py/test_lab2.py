"""
CPSC 5520, Seattle University
This is free and unencumbered software released into the public domain.
:Authors: Narissa Tsuboi
:Version: 1
:brief: Testing file for lab2.py
"""

import unittest
from lab2 import Lab2

GCD_ADDRESS = ('127.0.0.1', '22')
NEXT_BIRTHDAY = '2023-06-28'
SUID = 123456

class TestLab2(unittest.TestCase):


    def setUp(self) -> None:
        print('setUp')
        self.node = Lab2(GCD_ADDRESS, NEXT_BIRTHDAY, SUID)

    # test constructor
    print('### TEST __INIT__')
    def test_gcd_address(self):
        print('test_gcd_address')
        res = ('127.0.0.1', 22)
        self.assertEqual(self.node.gcd_address, res)

    def test_pid(self):
        print('test_pid')
        res = (269, 123456)
        self.assertEqual(self.node.pid, res)

    def test_members_is_not_None(self):
        print('test_members_is_not_None')
        self.assertIsNotNone(self.node.members)

    def test_states_is_not_None(self):
        print('test_states_is_not_None')
        self.assertIsNotNone(self.node.states)

    def test_bully_is_not_None(self):
        print('test_bully_is_not_None')
        self.assertIsNotNone(self.node.bully)

    def test_selector_is_not_None(self):
        print('test_selector_is_not_None')
        self.assertIsNotNone(self.node.selector)

    def test_listener_is_not_None(self):
        print('test_listener_is_not_None')
        self.assertIsNotNone(self.node.listener)

    def test_listener_address_is_not_None(self):
        print('test_listener_address_is_not_None')
        self.assertIsNotNone(self.node.listener_address)


if __name__ == '__main__':
    unittest.main()
