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
# module is actually in __builtin__/builtins, but we can't reference it as such!
try:
    from builtins import __class__ as modbase # Python 3
except ImportError:
    from __builtin__ import __class__ as modbase # Python 2

class Module (modbase):
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
    def __init__(self, name, directory, src, load_submod, join=os.path.join):
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