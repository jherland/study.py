#!/usr/bin/env python

import sys
import os
import unittest
from module import Module, LazyModuleImporter

def test_path(path):
    return os.path.join(os.path.dirname(sys.argv[0]), 'module_tests', path)

class TestCaseWithRoot(unittest.TestCase):
    """Provide tests wirh self.root = LazyModuleImporter(path, **args)."""
    path = None # Reimplement in subclasses
    args = {} # Subclasses can add more LazyModuleImporter args here

    def run(self, result=None):
        print "{}.run1(): {!r}".format(self.__class__.__name__, sys.meta_path)
        assert self.path
        with LazyModuleImporter.Root(test_path(self.path), **self.args) as root:
            self.root = root
            super(TestCaseWithRoot, self).run(result)
            print "{}.run2(): {!r}".format(self.__class__.__name__, sys.meta_path)

@unittest.skip("XXX")
class Test_SingleFile(TestCaseWithRoot):
    path = 'single_file'

    def test_root_lookup(self):
        print("* Test_SingleFile.test_root_lookup, root={!r}, foo={!r} *".format(self.root, self.root.foo))
        self.assertEqual(self.root.foo, "bar")

    def test_root_lookup_missing(self):
        with self.assertRaises(AttributeError):
            x = self.root.missing

@unittest.skip("XXX")
class Test_Submod(TestCaseWithRoot):
    path = 'submod'

    def test_root_lookup(self):
        self.assertEqual(self.root.foo, "bar")

    def test_submod_lookup(self):
        self.assertEqual(self.root.submod.foo, "baz")

    def test_submod_lookup_missing(self):
        with self.assertRaises(AttributeError):
            x = self.root.missing_submod.foo

@unittest.skip("XXX")
class Test_Disabled_submod(TestCaseWithRoot):
    path = 'submod'
    args = {'load_submods': False}

    def test_root_lookup(self):
        self.assertEqual(self.root.foo, "bar")

    def test_lookup_submod_fails(self):
        with self.assertRaises(AttributeError):
            x = self.root.submod.foo

@unittest.skip("XXX")
class Test_Subdir(TestCaseWithRoot):
    path = 'subdir'

    def test_root_lookup(self):
        self.assertEqual(self.root.foo, "bar")

    def test_subdir_lookup(self):
        self.assertEqual(self.root.subdir.foo, "baz")

    def test_subdir_lookup_missing(self):
        with self.assertRaises(AttributeError):
            x = self.root.missing_subdir.foo

@unittest.skip("XXX")
class Test_Attr_vs_submod(TestCaseWithRoot):
    path = 'attr_submod_clash'

    def test_lookup_prefers_existing_attr(self):
        print("sys.meta_path:", repr(sys.meta_path))
        self.assertEqual(self.root.foo.bar, "from __init__.py")

@unittest.skip("XXX")
class Test_Attr_vs_subdir(unittest.TestCase):

    def setUp(self):
        self.root = Module.Root(test_path('attr_subdir_clash'))

    def test_lookup_prefers_existing_attr(self):
        self.assertEqual(self.root.foo.bar, "from __init__.py")

@unittest.skip("XXX")
class Test_Submod_vs_subdir(unittest.TestCase):

    def setUp(self):
        self.root = Module.Root(test_path('submod_subdir_clash'))

    def test_lookup_prefers_submod(self):
        self.assertEqual(self.root.foo.bar, "from foo.py")

@unittest.skip("XXX")
class Test_Disabled_submod_vs_subdir(unittest.TestCase):

    def setUp(self):
        self.root = Module.Root(test_path('submod_subdir_clash'),
            load_submod=False)

    def test_lookup_skips_submod(self):
        self.assertEqual(self.root.foo.bar, "from foo/__init__.py")

@unittest.skip("XXX")
class Test_Simple_imports(unittest.TestCase):

    def test_lookup_imported_submod(self):
        root = Module.Root(test_path('simple_imports'))
        self.assertEqual(root.imported_submod.foo, "submod")

    def test_lookup_imported_submod_while_disabled(self):
        root = Module.Root(test_path('simple_imports'), load_submod=False)
        self.assertEqual(root.imported_submod.foo, "submod")

# Relative imports currently fail, probably because Python is missing some kind
# of module/package context in the lazily loaded Module's environment. Instead
# of using exec() to lazy-load modules, we should consider looking into
# Python3's importlib and re-implement Module in a manner more compatible with
# Python's own module loading infrastructure (see
# https://docs.python.org/3/library/importlib.html for details).
#
# In Python v3.5 there's even a "class importlib.util.LazyLoader(loader)" which
# "postpones the execution of the loader of a module until the module has an
# attribute accessed". More details:
#  - Docs: https://docs.python.org/3.5/library/importlib.html#importlib.util.LazyLoader
#  - Code: http://hg.python.org/cpython/annotate/default/Lib/importlib/util.py#l205
#  - Meta: http://bugs.python.org/issue17621
#
# Anyway, until this is solved, modules that use "proper" relative imports (as
# documented in PEP #328) will FAIL to lazy-load into Module instances. However,
# modules can apparently still use "regular" imports to access modules within
# their own directory (like in the test case above) - at least for as long as ''
# remains in sys.path.
@unittest.skip("relative imports not yet supported within lazy-loaded Modules")
class Test_Relative_imports(unittest.TestCase):

    def setUp(self):
        self.root = Module.Root(test_path('relative_imports'))

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

@unittest.skip("XXX")
class Test_lazy_loading_and_sys_modules(unittest.TestCase):

    def test_Root_instance_added_to_sys_modules(self):
        before = set(sys.modules.keys())
        root = Module.Root(test_path('single_file'), name='my_root')
        after = set(sys.modules.keys())
        self.assertEqual(after - before, {'my_root'})
        self.assertEqual(sys.modules['my_root'].foo, "bar")

if __name__ == '__main__':
    unittest.main()

# TODO:
#  - loading files NOT called __init__.py
#  - loading __init__.py from deeply nested subdir with missing intermediates
#  - packages vs. lazily-loaded modules.
