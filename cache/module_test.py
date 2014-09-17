#!/usr/bin/env python

import sys
import os
import unittest
from module import Module, LazyModuleImporter

def test_path(path):
    return os.path.join(os.path.dirname(sys.argv[0]), 'module_tests', path)

PYTHON2 = sys.version_info.major == 2
PYTHON3 = sys.version_info.major == 3
DEBUG = False
def debug(cls, mark):
    if not DEBUG:
        return
    print("{}.run({}):\n\tsys.meta_path: {!r}\n\tsys.modules:".format(
        cls.__name__, mark, [str(s) for s in sys.meta_path]))
    for k, v in sorted(sys.modules.items()):
        if k.startswith('root'):
            print("\t\t{!r}: {!r}".format(k, v))

class TestCaseWithLazyModuleImporter(unittest.TestCase):
    """Provide tests with self.root = LazyModuleImporter(path, **args)."""
    path = None # Reimplement in subclasses
    args = {} # Subclasses can add more LazyModuleImporter args here

    def run(self, result=None):
        debug(self.__class__, 'A')
        assert self.path
        importer = LazyModuleImporter(test_path(self.path), **self.args)
        with importer.installed() as root:
            self.root = root
            super(TestCaseWithLazyModuleImporter, self).run(result)
            debug(self.__class__, 'B')

class Test_SingleFile(TestCaseWithLazyModuleImporter):
    path = 'single_file'

    def test_root_lookup(self):
###        print("* Test_SingleFile.test_root_lookup, root={!r} with foo={!r} *".format(self.root, self.root.foo))
        self.assertEqual(self.root.foo, "bar")

    def test_root_lookup_missing(self):
        with self.assertRaises(AttributeError):
            x = self.root.missing

class Test_Submod(TestCaseWithLazyModuleImporter):
    path = 'submod'

    def test_root_lookup(self):
        self.assertEqual(self.root.foo, "bar")

    def test_submod_lookup(self):
        self.assertEqual(self.root.submod.foo, "baz")

    def test_submod_lookup_missing(self):
        with self.assertRaises(AttributeError):
            x = self.root.missing_submod.foo

class Test_Disabled_submod(TestCaseWithLazyModuleImporter):
    path = 'submod'
    args = {'load_submods': False}

    def test_root_lookup(self):
        self.assertEqual(self.root.foo, "bar")

    def test_lookup_submod_fails(self):
        with self.assertRaises(AttributeError):
            x = self.root.submod.foo

class Test_Subdir(TestCaseWithLazyModuleImporter):
    path = 'subdir'

    def test_root_lookup(self):
        self.assertEqual(self.root.foo, "bar")

    def test_subdir_lookup(self):
        self.assertEqual(self.root.subdir.foo, "baz")

    def test_missing_subdir_lookup(self):
        with self.assertRaises(AttributeError):
            x = self.root.missing_subdir.foo

    def test_subdir_lookup_missing(self):
        with self.assertRaises(AttributeError):
            x = self.root.subdir.missing

class Test_Attr_vs_submod(TestCaseWithLazyModuleImporter):
    path = 'attr_submod_clash'

    def test_lookup_prefers_existing_attr(self):
        self.assertEqual(self.root.foo.bar, "from __init__.py")

class Test_Attr_vs_subdir(TestCaseWithLazyModuleImporter):
    path = 'attr_subdir_clash'

    def test_lookup_prefers_existing_attr(self):
        self.assertEqual(self.root.foo.bar, "from __init__.py")

class Test_Submod_vs_subdir(TestCaseWithLazyModuleImporter):
    path = 'submod_subdir_clash'

    def test_lookup_prefers_submod(self):
        self.assertEqual(self.root.foo.bar, "from foo.py")

class Test_Disabled_submod_vs_subdir(TestCaseWithLazyModuleImporter):
    path = 'submod_subdir_clash'
    args = {'load_submods': False}

    def test_lookup_skips_submod(self):
        self.assertEqual(self.root.foo.bar, "from foo/__init__.py")

class Test_Simple_import_from_lazymod(unittest.TestCase):

    def test_lookup_imported_submod(self):
        if PYTHON2: # Old-style relative works in Python2
            with LazyModuleImporter(test_path('simple_imports')).installed() as root:
                self.assertEqual(root.imported_submod.foo, "submod")
        if PYTHON3: # Old-style relative import fails in Python3
            with self.assertRaises(ImportError):
                with LazyModuleImporter(test_path('simple_imports')).installed() as root:
                    pass

    def test_lookup_imported_submod_fails_when_disabled(self): # DESIRED?!
        with self.assertRaises(ImportError):
            with LazyModuleImporter(test_path('simple_imports'), load_submods=False).installed() as root:
                pass

class Test_Relative_imports(TestCaseWithLazyModuleImporter):
    path = 'relative_imports'

    def test_child_loaded(self):
        self.assertEqual(self.root.parent.child.foo, "child module")

    def test_relative_import_sibling(self):
        self.assertEqual(self.root.parent.child.sibling.foo, "sibling module")

    def test_relative_import_parent(self):
        self.assertEqual(self.root.parent.child.parent.foo, "parent module")

    def test_relative_import_aunt(self):
        self.assertEqual(self.root.parent.child.aunt.foo, "aunt module")

    def test_relative_import_cousin(self):
        self.assertEqual(self.root.parent.child.cousin.foo, "cousin module")

    def test_relative_import_grandchild(self):
        self.assertEqual(self.root.parent.child.grandchild.foo, "grandchild module")

    def test_relative_import_niece(self):
        self.assertEqual(self.root.parent.child.niece.foo, "niece module")

class Test_lazy_loading_and_sys_modules(unittest.TestCase):

    def test_my_root_instance_added_to_sys_modules(self):
        before = set(sys.modules.keys())
        with LazyModuleImporter(test_path('single_file'), 'my_root').installed() as root:
            after = set(sys.modules.keys())
            self.assertEqual(after - before, set(['my_root']))
            self.assertEqual(sys.modules['my_root'].foo, "bar")

if __name__ == '__main__':
    unittest.main()

# TODO:
#  - self.root _is_ sys.modules['mymodule']
#  - Missing root package file
#  - loading files NOT called __init__.py
#  - loading __init__.py from deeply nested subdir with missing intermediates
#  - packages vs. lazily-loaded modules.
#  - auto-load AFTER chdir...
