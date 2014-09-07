#!/usr/bin/env python

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

class Test_Simple_imports(unittest.TestCase):

    def test_lookup_imported_submod(self):
        root = Module.Root(test_path('simple_imports'))
        self.assertEqual(root.imported_submod.foo, "submod")

    def test_lookup_imported_submod_while_disabled(self):
        root = Module.Root(test_path('simple_imports'), load_submod=False)
        self.assertEqual(root.imported_submod.foo, "submod")

class Test_lazy_loading_and_sys_modules(unittest.TestCase):

    def test_Root_instance_added_to_sys_modules(self):
        before = set(sys.modules.keys())
        root = Module.Root(test_path('single_file'), name='my_root')
        after = set(sys.modules.keys())
        self.assertEqual(after - before, {'my_root'})
        self.assertEqual(sys.modules['my_root'].foo, "bar")

if __name__ == '__main__':
    unittest.main()
