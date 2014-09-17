"""Lazy module loading hierarchy.

The idea here is to instantiate LazyMod on a directory and get back a
module-like object except that, on trying to access a non-existent attribute of
that object, or any derived in the following way from it, we attempt to find a
sub-module to import.  If the attribute name matches a *.py file in the
directory, we load it; if it matches a sub-directory we load it as a LazyMod,
recursively.  The constructor takes a filename, defaulting to __init__.py, that
is loaded to give the 'raw' namespace of the object loaded; this is propagated
to recursively-generated instances.  Thus, if a directory hierarchy has a bunch
of (say) config.py files, one per directory, to tell tools about the contents of
the directory, loading the top-level directory as a LazyMod root will let you
automagically reference root.foo.bar.baz, loading 'foo/bar/baz/config.py' to
populate this object's namespace.  The result is thus much the same as a python
package hierarchy, but without the need to explicitly import anything and with
all the imports done lazily.

To reload one of these lazily-loaded attributes, e.g. following an update to its
source file, just del the relevant attribute.  Next time it's accessed, it'll be
lazily reloaded.
"""
import sys
import os
from types import ModuleType
from importlib import import_module
from contextlib import contextmanager

class LazyPackage(ModuleType):
    """Package that auto-loads sub-modules/packages to satisfy attribute lookups

    When about to fail an attribute lookup, first attempt to automatically
    import and return a sub-module or sub-package object that matches the
    requested attribute key. If that also fails, then, finally, raise an
    AttributeError.\n"""

    def __str__(self):
        return "<{} {!r} from {!r}>".format(
            self.__class__.__name__, self.__name__, self.__file__)

    def __repr__(self):
        return str(self)

    def __getattr__(self, key):
        try:
            return super(LazyPackage, self).__getattr__(key)
        except AttributeError: # key does not already exist in module
            # Attempt to satisfy attribute lookup by lazy loading
###            print("Attempting to import '.{}' from within {} ({!r})".format(key, self.__package__, self))
            try:
                mod = import_module("." + key, self.__package__)
                self.__setattr__(key, mod)
                return mod
            except ImportError as e:
                raise AttributeError(
                    'No such attribute, and lazy-loading failed ({})'.format(e),
                    key, self.__name__)

class LazyModuleImporter(object):
    """Create a module hierarchy that mirrors a given directory structure.

    Associate a given directory with a given (absolute) package name ('root' by
    default), and load sub-packages and (optionally) sub-modules underneath that
    directory into corresponding attributes on that package. Also allow
    customization of the special package filename (__init__.py by default).

    This class implements the Importer Protocol documented in PEP 302. As such,
    class instances will need to be installed into sys.meta_path in order to
    intercept module loading for everything under the given 'rootmod' package
    name. The install() and uninstall() methods perform this administrivia.
    For convenience, the installed() context manager perform the necessary
    install() (on enter) and uninstall() (on exit) around a block of code.\n"""

    def __init__(self, rootdir, rootmod='root', pkgfile='__init__.py',
                 load_submods=True):
        self.rootdir = rootdir
        self.rootmod = rootmod
        self.pkgfile = pkgfile
        self.load_submods = load_submods
###        print("* Created {!s}".format(self))

    def __str__(self):
        return "<{0}: {1.rootdir}/*/{1.pkgfile} -> {1.rootmod}.*>".format(
            self.__class__.__name__, self)

    def find_module(self, fullname, path=None):
        """Determine if 'fullname' names a potential module within self.rootmod.

        This implements the 'finder' part of the Importer Protocol documented in
        PEP 302, by checking if the given module name matches self.rootmod, or a
        sub-package/module of self.rootmod. Thus, we 'section' off the part of
        the module namespace that starts with self.rootmod, and reserve all
        module loading within that namespace to be performed by this instance
        (provided that this instance is the first entry in sys.meta_path
        configured for self.rootmod).\n"""
###        print("- {0}.find_module(fullname = {1!r}, path = {2!r}) called".format(self, fullname, path))
        if fullname == self.rootmod or fullname.startswith(self.rootmod + "."):
            return self
        return None

    def __get_path(self, fullname):
        """Return the existing python file path that corresponds to 'fullname'.

        Given a fully-qualified module name - "root.foo.bar" - where the
        initial component ("root") matches self.rootmod, we can construct a
        couple of corresponding file names under self.rootdir:

         1. A sub-module located at "foo/bar.py" (but only if self.load_submods
            indicates that it is OK to import sub-modules).

         2. A sub-package located at "foo/bar/__init__.py"
            (assuming that self.pkgfile == "__init__.py").

        This method returns the first of these that exist under self.rootdir.
        Along with the returned path, we also return a boolean flag indicating
        whether the returned file name refers to a sub-module (False) or a
        sub-package (True). If no existing path corresponding to 'fullname' is
        found, ImportError is raised.\n"""
        modpath = fullname.split(".")
        assert modpath[0] == self.rootmod # sanity check
        path = os.sep.join(modpath[1:])
        candidates = []

        # sub-module
        if path and self.load_submods:
            candidates.append((path + ".py", False))

        # sub-package
        candidates.append((os.path.join(path, self.pkgfile), True))

        for path, is_package in candidates:
            path = os.path.join(self.rootdir, path)
            if os.path.exists(path):
                return path, is_package

        raise ImportError(
            "Failed to import {0!r}, {1} has none of these files: {2}".format(
                fullname, self.rootdir, ", ".join([c[0] for c in candidates])))

    def load_module(self, fullname):
        """Load a module name from a corresponding file under self.rootdir.

        This implements the 'loader' part of the Importer Protocol documented in
        PEP 302, by creating a module instance of the appropriate type
        (ModuleType for sub-modules, LazyPackage for sub-packages), and
        initializing it following the rules for preparing module objects given
        in PEP 302) and loading the file under self.rootdir that corresponds
        to 'fullname' into that module instance.\n"""
###        print("* {0}.load_module(fullname = {1!r}) called".format(self, fullname))
        path, is_package = self.__get_path(fullname)
        # If 'fullname' refers to a (sub-)package, we need its module object to
        # be of type LazyPackage (in order to propagate lazy attribute lookup).
        # But if 'fullname' is merely a sub-module, we don't need lazy attribute
        # lookup, since modules (as opposed to packages) cannot have sub-
        # packages/modules.
        mod_type = LazyPackage if is_package else ModuleType
        mod = sys.modules.setdefault(fullname, mod_type(fullname,
            "Module {0} loaded from file {1} in {2} by {3}".format(
                fullname, path, self.rootdir, self.__class__.__name__)))
        mod.__file__ = path
        mod.__loader__ = self
        if is_package:
            mod.__path__ = []
            mod.__package__ = fullname
        else:
            mod.__package__ = fullname.rpartition('.')[0]
        with open(path) as f:
###            print("*** Loading {} into {!r}".format(path, mod))
            exec(f.read(), mod.__dict__)
        return mod

    def install(self):
        """Setup and return the lazy-loaded module hierarchy under self.rootmod.

        Install self into sys.meta_path as a handler for importing the module
        hierarchy rooted at self.rootmod.

        Trigger import of self.rootmod, and return its module object.\n"""
        sys.meta_path.insert(0, self)
        assert self.rootmod not in sys.modules
        return import_module(self.rootmod)

    def uninstall(self):
        """Dismantle the module hierarchy rooted at self.rootmod.

        Remove self from sys.meta_path, and remove self.rootmod and all modules
        under it.\n"""
        sys.meta_path.remove(self)
        # Remove all traces of self.rootmod and any children from sys.modules
        must_remove = lambda k: k == self.rootmod or k.startswith(self.rootmod + '.')
        for k in list(filter(must_remove, sys.modules.keys())):
            del sys.modules[k]

    @contextmanager
    def installed(self):
        """Context manager for a temporary lazy-loaded module hierarchy.

        This is a convenience context manager which calls the above install()
        method upon entering the context, and the corresponding uninstall()
        upon leaving the context.\n"""
        try:
            yield self.install()
        finally:
            self.uninstall()

###########################################################

class Module:
    @staticmethod
    def Root(directory, name='root', src='__init__.py', load_submod=True):
        import sys
        sys.meta_path.insert(0, LazyModuleImporter(directory, name, src, load_submod)) # How to clean up this? Context manager? Destructor?
        from importlib import import_module
        return import_module(name)


# module is actually in __builtin__/builtins, but we can't reference it as such!
try:
    from builtins import __class__ as modbase # Python 3
except ImportError:
    from __builtin__ import __class__ as modbase # Python 2

class Module2 (modbase):
    """Lazily-loaded module hierarchy.

    Instantiate the root of the hierarchy using Module.Root(); don't use the
    Module() constructor itself, that's reserved for internal use by the class,
    lazily constructing a sub-object hierarchy off the instance returned by
    Root().\n"""

    @classmethod
    def Root(cls, directory, name='root', src='__init__.py', load_submod=True):
        """Instantiate the root of a lazily-loaded module hierarchy.

        Return a module-like object resulting from loading the python file named
        'src' in 'directory'.

        Looking up an non-existing attribute (say, 'foo') on the returned object
        shall serve as a trigger to attempt loading a 'foo.py' sub-module from
        'directory' (if 'load_submod' is enabled), or - failing that - attempt
        loading 'src' from a 'foo' sub-directory. A successful attribute lookup
        is automatically cached by the returned object.\n"""
        import sys
        inst = cls(name, directory, src, load_submod)
        ret = cls.__load_file(inst.__path__, inst, directory)
        sys.modules[name] = ret
        return ret

    __updelat = modbase.__delattr__
    def __delattr__(self, key):
        try: del self.__cache[key]
        except KeyError: pass

        return self.__updelat(key)

    def __getattr__(self, key):
        try: return self.__cache[key]
        except KeyError: pass

        try: ans = self.__load_sub(key)
        except IOError: pass
        else:
            self.__cache[key] = ans
            return ans

        raise AttributeError('No such attribute, submodule or sub-directory',
                             key, self.__name__)

    def __repr__(self):
        return '<' + ' '.join(self.__doc__.split('\n')) + '>'

    @classmethod
    def __sub_mod(cls, name, directory, src, load_submod):
        return cls(name, directory, src, load_submod)

    @staticmethod
    def __sub_raw(name, path, base=modbase):
        inst = base(name, """Lazily-loaded sub-module %s

Loaded from file %s
""" % (name, path))
        inst.__path__ = path
        return inst

    @staticmethod
    def __load_file(path, into, indir):
        """Load python code into the namespace of an object.

        The object should be based on the builtin module type. It is returned,
        after its .__dict__ has been populated from the loaded file.\n"""
        import sys
        sys.path.insert(0, indir)
        try:
            with open(path) as f:
                exec(f.read(), into.__dict__)
        finally:
            try: ind = sys.path.index(indir)
            except ValueError: pass
            else: del sys.path[:ind+1]

        return into

    import os
    def __load_sub(self, key,
                   join=os.path.join,
                   exists=os.path.exists,
                   isdir=os.path.isdir):
        name = self.__name__ + '.' + key
        if self.__load_submod:
            path = join(self.__dir, key + '.py')
            if exists(path):
                return self.__load_file(path, self.__sub_raw(name, path), self.__dir)

        path = join(self.__dir, key)
        if isdir(path):
            inst = self.__sub_mod(name, path, self.__src, self.__load_submod)
            return self.__load_file(inst.__path__, inst, path)

        raise IOError

    __upinit = modbase.__init__
    def __init__(self, name, directory, src, load_submod=True, join=os.path.join):
        """Internal constructor; use Root() to construct your root object."""
        self.__path__ = join(directory, src)
        self.__upinit(name, # and a doc-string:
                      """Lazily-loaded Module %s

Loaded from file %s
in %s
""" % (name, src, directory))
        self.__dir, self.__src = directory, src
        self.__cache = {}
        self.__load_submod = load_submod

    del os

del modbase
