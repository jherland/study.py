#!/usr/bin/env python2

import sys
import os
import unittest
from module import Module

def test_path(path):
    return os.path.join(os.path.dirname(sys.argv[0]), 'module_tests', path)

class Test_SingleFile(unittest.TestCase):

    def setUp(self):
        self.root = Module.Root(test_path('single_file'))

    def test_root_lookup(self):
        self.assertEqual(self.root.foo, "bar")

    def test_root_lookup_missing(self):
        with self.assertRaises(AttributeError):
            x = self.root.missing

class Test_Submod(unittest.TestCase):

    def setUp(self):
        self.root = Module.Root(test_path('submod'))

    def test_root_lookup(self):
        self.assertEqual(self.root.foo, "bar")

    def test_submod_lookup(self):
        self.assertEqual(self.root.submod.foo, "baz")

    def test_submod_lookup_missing(self):
        with self.assertRaises(AttributeError):
            x = self.root.missing_submod.foo

class Test_Disabled_submod(unittest.TestCase):

    def setUp(self):
        self.root = Module.Root(test_path('submod'), load_submod=False)

    def test_root_lookup(self):
        self.assertEqual(self.root.foo, "bar")

    def test_lookup_submod_fails(self):
        with self.assertRaises(AttributeError):
            x = self.root.submod.foo

class Test_Subdir(unittest.TestCase):

    def setUp(self):
        self.root = Module.Root(test_path('subdir'))

    def test_root_lookup(self):
        self.assertEqual(self.root.foo, "bar")

    def test_subdir_lookup(self):
        self.assertEqual(self.root.subdir.foo, "baz")

    def test_subdir_lookup_missing(self):
        with self.assertRaises(AttributeError):
            x = self.root.missing_subdir.foo

class Test_Attr_vs_submod(unittest.TestCase):

    def setUp(self):
        self.root = Module.Root(test_path('attr_submod_clash'))

    def test_lookup_prefers_existing_attr(self):
        self.assertEqual(self.root.foo.bar, "from __init__.py")

class Test_Attr_vs_subdir(unittest.TestCase):

    def setUp(self):
        self.root = Module.Root(test_path('attr_subdir_clash'))

    def test_lookup_prefers_existing_attr(self):
        self.assertEqual(self.root.foo.bar, "from __init__.py")

class Test_Submod_vs_subdir(unittest.TestCase):

    def setUp(self):
        self.root = Module.Root(test_path('submod_subdir_clash'))

    def test_lookup_prefers_submod(self):
        self.assertEqual(self.root.foo.bar, "from foo.py")

class Test_Disabled_submod_vs_subdir(unittest.TestCase):

    def setUp(self):
        self.root = Module.Root(test_path('submod_subdir_clash'),
            load_submod=False)

    def test_lookup_skips_submod(self):
        self.assertEqual(self.root.foo.bar, "from foo/__init__.py")

if __name__ == '__main__':
    unittest.main()
