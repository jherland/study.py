"""Cacheing data about integer-bounded ranges of the number line.

This module provides classes to manage caches of data about the naturals,
integers or even reals, in so far as the cached data can be delineated by ranges
of integers.  It presumes that you have some way of computing the data for which
it is worth saving the answers to disk (for example, because the cost of
re-computation is high, e.g. due to needing answers from nearer zero to arrive
at answers for further from it).  The cache managed by this system just
remembers the information you computed, in python modules importable with
execfile, organized in a directory hierarchy, with an __init__.py in each
directory to manage the hierarchy itself.  There may be gaps in such caches, a
system may use several of them with distinct roots and a system may remember
several (up to about 26) distinct types of information in a single cache.

For guidance on how to adapt this module's classes to your particular
application, see the template in the .Adaptation attribute of this module.  The
primary use case motivating the initial implementation of this infrastructure is
tracking information about primeness and least common factors for the naturals
(non-negative integers); the intent here is to be generic, but it is possible
some design features should be refactored out to maths.prime.cache in order to
make these classes function truly generically.

See study.LICENSE for copyright and license information.

Hierarchy
=========

Actual data is stored in files, but it's not nice to put too many files into one
directory, so a hierarchy of directories is built up, to hold the data.  The
classes defined here model that hierarchy with objects.  The directory hierarchy
may be extensive, so the object hierarchy to model it is only built (on demand)
as needed and only weakly remembered, so that python's garbage collection can
keep the amount of memory used under control.  The individual data files are apt
to be large, so their contents are, likewise, only read as needed and only
weakly remembered.

An application interacts with each cache via an object, of a class derived from
CacheRoot, describing the root of its directory hierarchy.  The application can
ask this object (via its .locate() method, q.v.) to find the (object
representing a) file in whose integer-bounded range of the number line some
particular number falls.  In so far as the application has extended the classes
here to reflect other data (typically read from the cache files) which increase
monotonically with position in the number line, the root object can also find
files based on a value of such a datum.  Where the cache does not contain a file
with the data required by such a search, the root's .locate() instead returns a
'gap' object describing a range around the target sought, in which data are
lacking.  The application can consult several caches for data in this way,
refining the 'gap' at each consultation.

If none of the consulted caches has the data sought, the 'gap' object the
application is left with describes the range of values for which none of them
have data.  The application is then left to compute the data, for some interval
of the number line within this gap (or all of it), and can then ask a root to
allot a file to it, in which to save the data it has computed, thereby extending
that root's cache.  For this, it needs a modifiable root object, derived from
CacheRoot via WriteRoot.  An application is presumed to normally have one such
modifiable cache, in which it saves the data it computes, backed up by possibly
several read-only caches that save it the need to compute data for the ranges
they know about.

Details:

 * Within a cache, each sub-directory or file describes the range, for which it
   holds data, only relative to the start-point of the range of the directory in
   which it resides, so as to keep numbers small (and hence names, of files and
   directories, short).  The numbers in question are also remembered base 36
   (using 'a' through 'z' as the digits from ten to thirty-five) to help keep
   names short.  The initial numeric part of each name is padded with 0s to make
   it the same length as the longest, so as to ensure that directory listings
   show files in their numeric order.

 * Each directory in a cache contains an __init__.py file in which the
   application can store relevant data, such as summary data covering the whole
   range of the directory; this can be used to save un-necessary loading of
   subordinate directories and files in order to discover such data when
   consulting the cache later.

 * Where some application-specific data increases monotonically along the number
   line, the application can record each directory's range of values for that
   datum in the directory's __init__.py; which makes it possible for the
   application to save the matching data of subordinate files and directories
   only relative to the start-point of the directory's range; as for spans of
   the number line, this can enable some saving in disk space.

 * The root directory shall typically use its __init__.py to record data
   relevant to the whole cache.  Since the root's name is not controlled by this
   cache code, this name does not encode the span of the cache, so the root
   directory records this span in its __init__.py file.

 * Directories support locking so as to prevent clashes and confusion when two
   processes are accessing the same cache.  Locking a directory for reading may
   be done by several processes at one time; but locking a directory for writing
   is incompatible with any other process locking it for either reading or
   writing.  Write locking only applies to the directory it's done to; but read
   locking propagates up via parent directories to the root of the cache, so as
   to ensure no process re-writing an ancestor directory removes a directory
   being read.


Naming
======

Nodes in the hierarchy have names matching regex
        (N|P|)([0-9a-z]+)([A-Z]+)([0-9a-z]+)(\.py|)
wherein:
 * the final (\.py|) is only non-empty for leaf nodes, i.e. files
 * the ([A-Z]+) could in fact be ([^0-9a-z]+) and provides application-specific
   information about the types of data, about integers, that are present in this
   node and any descendants
 * the initial (N|P|) - for negative, positive - is empty unless the parent
   directory's span includes both negative and positive values; this only ever
   arises when the parent directory is the root of a cache;
 * the cache-root class (based on CacheRoot) determines the default sign;
   derived classes may over-ride the positive default set by CacheRoot; any
   child of root with N or P prefix over-rides any such default; all other cache
   nodes inherit sign from their parents;
 * the two ([0-9a-z]+) are interpreted via int(,36) as naturals, measured away
   from zero, in the direction indicated by the node's sign; the first gives the
   start-point (relative to a context-dependent origin, see next point) and the
   second gives the length;
 * when (N|P|) is empty, the start-point in the preceding is given relative to
   that of the node's parent directory; otherwise, the start-point is absolute,
   in the specified direction.

Thus N00X42.py would be a file providing application-specific information of
category 'X'; it could only appear in the root directory of its hierarchy, it
would relate to values between 0 (included) down to (ecluded) minus one hundred
and fourty-six (i.e. 4*36 + 2).  In all likelihood, there would be something in
the same cache root directory whose name would start P01X (for an integer cache;
but P0X in a real cache), providing the same kind of information for positive
values up to some limit.

Files should generally be named for the exact range about which they hold data;
but a file describing work-in-progress to discover data about some range should
be named for that range even if its data are incomplete.  Such partial nodes
should be stored as files of the same type (i.e. [A-Z] above) as they shall have
once complete, with their internal data indicating the incompleteness.  If data
of a particular type may be stored in several formats, these should likewise be
stored using the same type letter, with internal data indicating the format.

The ranges of files containing different types of data may
overlap.  Sub-directories of any given directory shall always have distinct
ranges, except while the parent is write-locked and the exception is required
for re-arringement of the sub-directories.  Each directory's range must subsume
the range of each of its children; it should normally be exactly the union of
the ranges of its children, although the root directory (whose range is not
encoded in its name) can have, as its nominal span, the full range of integers
for which its data are potentially of interest.


Hierarchical tidiness
=====================

The depth of a cache file is 0; the depth of a cache directory is one more than
the depth of its child with greatest depth.  The root directory of each cache
shall avoid variations in depth among its children in so far as is practical.
Each non-root directories shall ensure that all of its children have equal
depth.  Each directory endeavours to keep its number of children close to
twelve.

When it comes to simply growing, outwards from zero, an isolated cache of only
one kind of data, with no data borrowed from other caches, the root has to
endure two adjacent depths some of the time; its deeper children are all
complete and tidy, as are all but the last of the shallower ones; there is a
bleeding-edge of last nodes with between 8 and 20 children, at each depth, all
others being tidy.  When a new node is added, it is always a new last file so it
is added to the depth=1 last node; if a non-root last node finds it has 20
children, it keeps its first 12 children and ceases being a last node by passing
the other eight to its parent, to turn into a new last node; if this is that
parent's 20 child, it does likewise, unless it's the root.  When the root has 20
children all of equal depth, it collects 12 into a sub-node of one greater
depth, retaining the other 8 as direct children; successive additions to the
last of these cause it to push new children of their depth into the root; when
it has n < 8 deeper nodes and 20-n > 12 shallower ones, it collects 12 shallow
ones into a fresh deeper node; when it has 7 or more deeper nodes and 8 or more
shallower ones, it can collect the shallow ones into a new deeper node and get
itself back to having only one depth of child.

The situation is more complex when borrowing from another cache, or when we have
borrowed from a cache in the past, that we no longer see.  If we're borrowing
from a simple cache, as above, then our cache only saves data past the end of
the other, so the dynamics are as before.  This creates a cache that covers a
range, albeit one distant from zero.  If we borrow from several such caches, not
necessarily including the ones that they referenced while being built, these
constitute a read-cache with holes in it and we want to grow a write-cache to
fill the holes.  This write-cache then ends up covering several disjoint
ranges.  It could be structured as above, but I chose to place gaps in the
intervals between directories.

The situation is further complicated in a mixed cache, with some diverse types
of application-specific information.  An interval may be covered by the types
taken together without being covered entirely by any one of them.  New nodes
added to extend one type may fall in the middle of the range of values for all
types taken together.  Nodes of different types might only partially over-lap -
e.g. if files of different types have different lengths, or files of two types
have equal lengths but those of each type start at the mid-point of the other
type's files.

Applications shall be obliged to be able to split data of any types at any
integer, on request from WriteDir.tidy(); however, this shall endeavour to avoid
exercising this right.  If applications have limitations on the values at which
they can split, they should identify a mapping from the integers to possible
split-points and wrap the cache in an object that maps the integers the cache
infrastructure knows about (the end-points of .span attributes of Node()s) to
their corresponding split-points.  If applications have types of data whose
potential split-points are offset from one another, they can wrap the cache in
such a way as to add type-specific offsets to the data to synchronise their
split-points; if this is not possible, the application should keep the distinct
types of data in separate caches.

Policy:
  * each child of a root describes a contiguous range that doesn't straddle zero
    (but may start at it);
  * a sub-directory which is not the first or last child of its parent, or which
    has zero as a boundary value, shall have as close to twelve children as
    circumstances permit, without splitting or uniting files to silly sizes;
  * other directories shall be more liberal about numbers of children, but aim
    to keep within the range from eight to twenty or, when even that is not
    practical, within the range from six to thirty-two; these liberal
    directories shall arise in chains at the boundaries of contiguous ranges;
  * any time root has eight or more contiguous children and at least seven (but
    preferrably eleven) other children it can reasonably bunch up the contiguous
    group; if it has more than twenty children in total, it certainly should do
    so.

When two ranges, each contiguous, have expanded towards each other far enough
that they meet, other than at zero, unifying them shall involve a messy
interaction, where changes ripple through them to ensure tidiness in the
internal child nodes.  This should be mediated by the nearer-zero node
preserving such tidiness as it has, with its neighbour transfering nodes into it
as if the nearer-zero node were simply having nodes added to it after the manner
of simple growth - albeit these additions may be done in bulk, rather than one
at a time.
"""

Adaptation = """
# This is a template for extending the classes provided here.

from study.cache import whole

class Node (whole.Node):
    # optionally extend _load_
    pass
class WriteNode (Node, whole.WriteNode):
    # optionally extend _save_
    pass

class CacheFile (Node, whole.CacheFile):
    # optionally extend _load_ some more
    pass
class WriteFile (WriteNode, whole.WriteFile):
    # optionally extend _save_ some more
    pass
# Optionally complicate further with files for each cached data type

weaklisting = whole.CacheDir.weaklisting
class CacheDir (Node):
    @staticmethod
    def _child_class_(isfile, mode):
        # possibly complicate further for mode
        if isfile: return CacheFile
        return CacheSubDir

    # optionally extend _load_ some more
    # optionally extend _ontidy_, _gap_
    # define any @weaklisting attributes, typically one per cached data type
del weaklisting

class WriteDir (WriteNode, CacheDir):
    @staticmethod
    def _child_class_(isfile, mode):
        # possibly complicate further for mode
        if isfile: return WriteFile
        return WriteSubDir

    # optionally extend _save_ some more

class CacheSubDir (CacheDir, whole.CacheSubDir):
    pass
class WriteSubDir (WriteDir, whole.WriteSubDir):
    pass

class CacheRoot (CacheDir, whole.CacheRoot):
    # optionally: over-ride sign, span
    pass
class WriteRoot (WriteDir, whole.WriteRoot):
    pass

# (Note: this is a good example of where classic single-inheritance falls down,
# although ruby's variation on that theme would be able to cope.)
"""
# Google's protocol buffers might be a neat replacement for saving to a module:
# http://code.google.com/apis/protocolbuffers/docs/proto.html

from study.snake.regular import Interval
from property import Cached, lazyprop, lazyattr
from weak import weakprop
from errno import EWOULDBLOCK
import os

class Node (Cached):
    """Base-class for nodes in a hierarchy of cached data about integers.

    Derived classes should implement attribute _cache_file (absolute path of
    file to be loaded by load; use __init__.py in directories), implement lock
    and unlock methods (with optional boolean arguments (read, write) each
    defaulting False, raising IOError or returning False on failure), extend
    load and implement a (typically lazy) attribute span, describing the range
    of integers this Node describes.  If span is None it means the full range of
    all integers; otherwise, it should be an Interval or the result of negating
    an Interval (a Span with stride -1).\n"""

    @weakprop
    def content(self): return self._load_()

    class Bok (dict): pass # for weakref's sake
    def _load_(self, bok=None, glo={}, Dict=Bok, BLOCKED=EWOULDBLOCK):
        """Loads self._cache_file and returns the result as a mapping.

        Sole optional argument, bok, is a mapping object into which the
        cache-file's namespace is to be imported; if not supplied, an empty
        mapping of a class based on dict (so amenable to weakref) is used; in
        either case, this is the object returned on success.  May raise IOError
        or ParseError.

        Derived classes extending this should take the same optional argument,
        pass it down to base-class load and do any processing of the result,
        e.g. extracting data for use in application-specific attributes, on the
        way back out.\n"""
        # TODO: want to be able to GET a URL instead of reading a file

        if bok is None: bok = Dict()
        if not self.lock(True):
            raise IOError(BLOCKED, 'File temporarily unreadable',
                          self._cache_file)
        try: execfile(self._cache_file, glo, bok) # may raise IOError, ParseError
        finally: self.unlock(True)

        try: self.depth = bok.pop('depth')
        except KeyError: assert isinstance(self, CacheFile)

        return bok
    del Bok

class WriteNode (Node):
    """Extends Node with write-functionality.

    Derived classes should extend save.\n"""
    def _save_(self, formatter=None, **what):
        """Saves a given namespace to a module.

        First argument, formatter, is None (to use a default) or a function
        taking a key, a value and an optional replacement for repr; it should
        output a string to save to file, that shall be used to record the
        key-value pair.  If None, a default is used which formats the pair as a
        simple assignment statement with the key on the left and the value's
        repr() on the right, followed by a newline.

        All other arguments should be given in keyword form.  The name 'depth'
        shall be ignored if given (it is over-written by an attribute of the
        same name) on nodes not descended from CacheFile (whose depth is 0).
        The name '__doc__' shall be replaced by self.__doc__ if this is not the
        same object as self.__class__.__doc__; any __doc__ obtained by either of
        these means shall be saved as doc-string in the module.

        Derived classes should add any relevant attributes to what, to be saved;
        in particular, if called with no args, they should save all self's
        content to disk sensibly.  This class handles .span, .depth and .__doc__
        (see above); derived classes should document which other attributes they
        handle.

        Derived classes may introduce special handling for some keys; to do so,
        they need to hijack the formatter they get and tunnel it through one
        they pass on in its place, that implements the special handling and falls
        back on the given formatter or, if None:
            lambda k, v: '%s = %s\n' % (k, repr(v))
        using the repr optionally passed to them by their caller.  Derived
        classes should document the special handling they implement.  This class
        provides special handling for the keys 'depth' and '__doc__': see above.

        Derived classes may also introduce special formatting of values by
        passing a replacement for repr to their client's (or further derived
        class's) formatter, via their re-formatting wrapper.  If doing so, they
        must take care to use any repr supplied to their wrapper, when *it* is
        called (by a base class), rather than the built-in, as the foundation on
        which they build their modified repr.\n"""

        if formatter is None:
            formatter = lambda k, v: '%s = %s\n' % (k, repr(v))

        if not self.lock(write=True):
            raise IOError(self.__BLOCKED, 'File temporarily unwritable',
                          self._cache_file)
        try:
            fd = open(self._cache_file, 'w')
            try:
                doc = what.pop('__doc__', None)
                if self.__doc__ is not self.__class__.__doc__:
                    doc = self.__doc__
                if doc: fd.write('"""%s"""\n\n', self.__doc__)

                if not isinstance(self, CacheFile):
                    fd.write('depth = %d\n' % self.depth)
                what.pop('depth', None) # don't let what over-ride that.

                for k, v in what.items():
                    fd.write(formatter(k, v))

            finally: fd.close()
        finally: self.unlock(write=True)

        self.parent._onchange_()
        # potentially: return size of file

    __BLOCKED = EWOULDBLOCK

del EWOULDBLOCK, Cached, weakprop

class SubNode (Node):
    def __init__(self, parent, types, start, reach, sign=None,
                 Range=Interval):
        """Initialize a sub-node with type and span data.

        Required arguments:
          parent -- parent node
          types -- string of [A-Z]+ type indicators
          start -- offset into parent's .span at which self starts
          reach -- length of interval self describes
        Optional arguments:
          sign -- either None (default), meaning parent.span doesn't straddle 0;
                  or +1 or -1 to indicate which side of 0 self is, relative to
                  parent's sign.
        Do not supply any further parameters.\n"""

        assert reach > 0
        if sign:
            assert sign in (+1, -1)
            self.__sign = sign
        self.__span = Range(start, reach), 
        self.__type, self.__up = types, parent

    # read-only access to data members
    @property
    def parent(self): return self.__up
    @property
    def types(self): return self.__type
    @property
    def sign(self):
        up = self.__up.sign
        try: return self.__sign * up
        except AttributeError: return up

    def __cmp__(self, other):
        if other is self: return 0

        if isinstance(other, tuple): # NameFragments
            # CacheSubNode layers name and isfile checks on top of this.
            s = (cmp(self.__span.start, other.start) or
                 cmp(len(self.__span), other.reach) or
                 cmp(self.types, other.types))
            if s: return s

            try: s = self.__sign
            except AttributeError: return cmp(None, other.sign)
            return cmp(s, other.sign)

        # If this raises AttributeError, comparison was misguided:
        s = (cmp(self.__span.start, other.__span.start) or
             cmp(len(self.__span), len(other.span)) or
             cmp(self.types, other.types))
        if s: return s

        try: s = other.__sign
        except AttributeError: s = None
        try: return cmp(self.__sign, s)
        except AttributeError: return cmp(None, s)

    @lazyprop
    def span(self):
        ans = self.__span
        if self.sign < 0: ans = -ans
        try: self.__sign
        except AttributeError:
            assert self.__up.span is not None
            return ans + self.__up.span.start

        assert self.__up.straddles0
        return ans

    # Chase parent to its root:
    @property
    def root(self): return self.__up.root

class Gap (SubNode):
    __upinit = SubNode.__init__
    def __init__(self, parent, start, span, sign):
        self.__upinit(parent, '', start, span, sign)

    @lazyprop
    def straddles0(self):
        return self.span is None or (-1 in self.span and +1 in self.span)

class CacheSubNode (SubNode):
    __gapinit = SubNode.__init__
    def __init__(self, name, parent, types, start, span, sign=None, replaces=None):
        """Initialize an subordinate node within the cache.

        Arguments are as for SubNode's constructor but with one extra optional
        parameter, after sign:
          replaces -- either None (default) or an existing cache node this one
                      is to replace; in which case either its .parent is parent
                      or its .parent is a peer of parent that parent shall
                      replace.

        Derived classes may wish to transcribe data from replaces, when given;
        if so, they should do so after calling base class __init__().\n"""
        self.__gapinit(parent, types, start, span, sign)
        self.__name = name

    __upcmp = SubNode.__cmp__
    def __cmp__(self, other):
        s = self.__upcmp(other)

        if not s and isinstance(other, tuple): # NameFragments
            s = cmp(self.__name, other.name)
            if s: return s

            if isinstance(self, CacheFile): s = '.py'
            else: s = ''
            return cmp(s, other.isfile)

        return s

    @property
    def name(self): return self.__name
    def path(self, *tail): return self.parent.path(self.__name, *tail)

    @lazyprop
    def straddles0(self):
        """CacheSubnodes do not straddle zero.

        They may start at it, but never contain values on both sides of it.
        This could simply be a property, except that I want to lazilly assert,
        at most once in the object's life-time, that it really doesn't straddle
        zero.\n"""
        assert self.span is not None
        assert -self.sign not in self.span
        return False

class WriteSubNode (CacheSubNode, WriteNode):
    def relocate(self, parent, move=os.rename):
        """Move self to a new directory.

        Single, required, argument is the parent node under which to create a
        replacement for self.\n"""

        isfile = isinstance(self, CacheFile)
        name = parent._child_name_(self.span, isfile, self.types)
        move(self.path(), parent.path(name))
        cls = parent._child_class(isfile, self.types)
        sign = self.sign * parent.sign
        if parent.straddles0: start = self.span.start * parent.sign
        else: start, sign = self.sign * (self.span.start - parent.span.start), None
        peer = cls(name, parent, self.types, start, len(span), sign, self)
        peer._save_()
        return peer

    @property
    def index(self):
        if self.parent is None:
            raise AttributeError, 'Root has no parent in which to have an index'
        return self.parent.child_index(self)

    @property
    def front(self):
        """Returns the away-from-zero end of self's contiguous block.

        As for rear (q.v.) but away from zero instead of towards it.\n"""

        return self.parent.contiguous(self, +1)

    @property
    def rear(self):
        """Returns the near-zero end of self's contiguous block.

        Go up from self to a child of root; while this node's start abuts the
        end of the one towards zero from it, move towards zero; this gets us to
        the top-level node at the near-zero end of self's contiguous block.  If
        this (with all its descendants) is tidy, it's the rear node; otherwise,
        while the node has an untidy node as its nearest-zero child, step to
        that node.  The result is then the lowest-depth untidy node at the
        near-zero end of self's contiguous block.\n"""

        return self.parent.contiguous(self, -1)

class CacheFile (CacheSubNode):
    @lazyprop
    def _cache_file(self): return self.path()
    @property
    def depth(self): return 0

    def lock(self, read=False, write=False):
        return self.parent.lock(read, write)
    def unlock(self, read=False, write=False):
        return self.parent.unlock(read, write)

    def __spanner(self, val):
        up = self
        try:
            while val not in up:
                val += up.start
                up = up.parent

        except AttributeError: return None # root lacks this value

        ans = up.locate(val, types=self.types)
        if isinstance(ans, CacheFile): return ans
        return None # no such data available under my root

    @lazyprop
    def next(self):
        """Successor node to this one, if in this cache; else None."""
        return self.__spanner(self.span.stop)

    @lazyprop
    def prev(self):
        """Prior node to this one, if in this cache; else None."""
        return self.__spanner(self.span.start - 1)

class WriteFile (CacheFile, WriteSubNode):
    def extend(self, span, move=os.rename):
        """Replaces self with an expanded file.

        Single argument, span, is the range of the new file.  Returns a new
        self.parent._child_class_(True, self.types) instance which can replace
        self, covering both the given span and self.span; caller is responsible
        for supplying the extra data and ._save_()ing the new object.

        Unlike WriteSubDir._update_name_(), which is for internal use, the only
        use I can think of for this is on the client side, to extend a file.
        Derived classes could over-ride this method, modifying the base class's
        return as needed, but should be able to achieve the benefits of that by
        simply supporting the replaces parameter in the classes returned by
        their directories' _child_class_() methods.\n"""

        if self.span.subsumes(span): return self

        assert self.sign == self.span.step
        assert self.sign * self.span.start >= 0
        span = self.span.meet(span)
        if span.step * self.sign < 0: span = span.reversed()
        name = self.parent.child_name(span, True, self.types)
        cls = self.parent._child_class_(True, types)
        move(self.path(), self.parent.path(name))
        self.parent._onchange_()

        if self.parent.straddles0:
            start, sign = span.start, self.sign * self.parent.sign
        else: start, sign = span.start - self.parent.span.start, None
        return cls(name, self.parent, self.types, start, len(span), sign, self)

    # TODO: support being split.  How ?

from lockdir import LockableDir

class LockDir (LockableDir):
    """Implement lock propagation.

    This extends LockableDir's un/locking so that read locks propagate up to
    root (whose .parent must be None) while write locks are only set on the
    directories to which they are directly addressed.  This lets one process
    modify parts of a cache while another is reading other parts, as long as
    their activities don't overlap.\n"""

    __lock, __unlock = LockableDir.lock, LockableDir.unlock
    def lock(self, read=False, write=False):
        if not read or self.parent is None:
            return self.__lock(read, write)
        elif self.parent.lock(read, False):
            if self.__lock(read, write): return True
            self.parent.unlock(read, False)
        return False

    def unlock(self, read=False, write=False):
        if not read or self.parent is None: ok = True
        else: ok = self.parent.unlock(read, False)
        return self.__unlock(read, write) and ok

del LockableDir

from weak import WeakTuple
from study.snake.sequence import Ordered

class CacheDir (Node, LockDir):
    @lazyprop
    def _cache_file(self): return self.path('__init__.py')

    class NameFragments (tuple):
        """Give tuples in .__listing handy names for their entries."""
        def __getattr__(self, key,
                        index={ 'start': 0, 'reach': 1, 'types': 2,
                                'sign': 3, 'name': 4, 'isfile': 5 }):
            try: i = index[key]
            except KeyError: pass
            else: return self[i]

            raise AttributeError, key

        def stop(self, sign):
            ans = self.start + self.reach
            if self.sign is None: return ans
            return ans / (self.sign * sign)

        def begin(self, sign):
            if self.sign is None: return self.start
            return self.start / (self.sign * sign)

    import re
    @lazyprop
    def __listing(self, get=os.listdir, seq=Ordered, row=NameFragments,
                  pat=re.compile(r'^(N|P|)([0-9a-z]+)([A-Z]+)([0-9a-z]+)(\.py|)$'),
                  signmap={ 'N': -1, 'P': +1, '': None }):
        """The (suitably sorted) list of contents of this directory.

        Sort order puts entries near self.span.start at low index and entries
        near self.span.stop at high index.

        Ignores entries not matching the forms of cache file names.\n"""
        ans = seq()
        for name in get(self.path()):
            got = pat.match(name)
            if got is not None:
                sign = signmap[got.group(1)]
                start, size = int(got.group(2), 36), int(got.group(4), 36)
                if sign is not None: # hack to ensure sensible sort order
                    start *= sign * self.sign
                mode, isfile = got.group(3), got.group(5)
                # Be sure to match WeakSeq, and NameFragments' indexing, above:
                ans.append(row((start, size, mode, sign, name, isfile)))

        return ans

    del re, NameFragments

    @lazyattr
    def depth(self): # but usually we'll read this from __init__.py
        return max(self.listing.map(lambda x: x.depth)) + 1

    def child_index(self, child):
        """Find index at which child appears in .listing\n"""

        assert self is child.parent
        if self.straddles0: target = child.span.start
        else: target = child.span.start - self.span.start
        # Would self.__listing.index(target) find this for us ?

        seq = self.__listing
        if seq[0] == child: return 0
        lo, hi = 0, len(seq) - 1
        if seq[-1] == child: return hi

        while lo + 1 < hi:
            mid = (lo + hi) / 2
            p = seq[mid]
            if p < child: lo = mid
            elif p > child: hi = mid
            else:
                assert p == child
                return mid

        raise ValueError

    def __abuts(self, rear, front):
        """Does .listing[rear] abut .listing[front] ?

        Arguments, rear and front, are indices into self.listing; the front
        entry should be the one further from zero.  Loosely, the two .listing
        entries abut if the front one's .span.start is the rear one's
        .span.stop, except that we have to deal with the possibility that spans
        may be nominal: if either node doesn't contain children that provide
        actual data up to the boundary, then the two nodes don't actually abut,
        even if their nominal spans claim they do.  Also, if the two nodes abut
        one another at zero, in which case both start there, they aren't counted
        as abutting.\n"""

        lo = hi = self
        while lo.__listing[rear].stop(lo.sign) >= hi.__listing[front].begin(hi.sign):
            done = True
            down = lo.listing[rear]
            if isinstance(down, CacheDir): lo, done = down, False
            down = hi.listing[front]
            if isinstance(down, CacheDir): hi, done = down, False
            if done: return True
            if lo.sign * hi.sign < 0: return False
            front, rear = 0, -1

        return False

    @staticmethod
    def contiguous(child, sense):
        """Returns a selected end of child's contiguous block.

        Required arguments:
          child -- an entry in self.listing
          sense -- relative direction flag

        If sense is > 0, we search away from zero, else towards zero, for an end
        of the child's contiguous block.  To search upwards (towards +ve
        infinity) pass child.sign; for downwards, -child.sign works.  We first
        navigate from child up to the top-level (direct child of root) node it's
        under; this is presumed to be contiguous. Going in the selected
        direction from here, we search for, and return, the first node whose
        span doesn't abut that of the next node in the selected direction.  See
        WriteDir.contiguous (which is what's actually used in practice) for a
        refinement of this.\n"""

        while child.parent is not None: child = child.parent
        up = child.parent
        i, s, seq = child.index, child.sign * up.sign, up.__listing
        assert isinstance(up, CacheRoot) and seq[i] == child

        if sense > 0:
            while seq[i+s].sign == seq[i].sign and up.__abuts(i, i+s):
                i += s
        else:
            assert sense < 0
            while seq[i-s].sign == seq[i].sign and up.__abuts(i-s, i):
                i -= s

        return up.listing[i]

    def _child_union(self, skip, ts): # tool for WriteDir.__revise_span
        """Data on self's children, optionally ignoring some.

        Required arguments are skip, a list of nodes to ignore if they appear as
        children of self, and ts, a set (typically a TypeSet, q.v.) to update()
        with the types of all non-ignored children.  Computes the lowest offset,
        lo, of any child's start within self and the highest offset, hi, of any
        child's end and returns a tuple ts, lo, hi, with fourth element being
        the list of members of skip that *didn't* show up as children of
        self.\n"""

        first = True
        for k in self.__listing:
            if k in skip:
                assert len(filter(lambda s, p=k: s == p, skip)) == 1
                assert len(filter(lambda k, f=filter(lambda s, p=k: s == p,
                                                     skip)[0]: k == f,
                                  self.__listing)) == 1
                skip = filter(lambda s, p=k: s != p, skip)
                continue

            ts.update(k.types)
            klo, khi = k.begin(self.sign), k.stop(self.sign)
 
            if first: lo, hi, first = klo, khi, False
            else:
                if klo < lo: lo = klo
                if khi > hi: hi = khi

        assert not first
        return ts, lo, hi, skip

    @lazyprop
    def _contrary(self):
        """How many of self's children are reverse-oriented ?

        If self straddles 0, this counts how many of its (direct) children are
        have the opposite sign to self; these are the first entries in
        self.listing and are all at the end of self's range closest to
        .span.start (this is asserted).

        Tool for WriteDir.tidy(), q.v., over-ridden on CacheSubDir and
        WriteSubDir to save needless computation, since only root nodes can
        straddle 0.\n"""

        rev = 0
        if self.straddles0:
            try:
                while self.__listing[rev].sign * self.sign < 0: rev += 1
            except IndexError: pass # ran off end of list
        assert all(x.sign * self.sign >= 0 for x in self.__listing[rev:])

        # ISSUE(?): if root contains a wide file of one type, whose range
        # straddles some directories of another type, this fails to recognize
        # the directory nearest zero.  Not a problem for the prime cache ...
        return rev

    def _ontidy_(self):
        """Update attributes after directory contents have changed.

        When the contents of the directory get changed (see WriteDir), this
        method is called to ensure attributes correctly reflect the contents of
        the directory.  Note that changes to self.span are handled separately;
        also that this function doesn't clear any flags indicating self may need
        tidying, as it's called when *some* tidying has happened, during the
        course of which changes made may have provoked the need for *further*
        tidying.

        Where possible, attributes that depend on directory contents should be
        lazy.  All lazy attributes (notably including every @weaklisting) can
        simply be deleted, since lazyprop doesn't raise any error when the
        attribute is absent; so deletion shall remove the attribute if present,
        ready to be recomputed next time it's needed.  Any non-lazy attributes,
        however, need to be updated.

        Derived classes should extend this method, calling relevant base class
        version and deleting any attributes they add, that are computed from
        those of children.\n"""

        self.clear_propstore_cache()
        del self.depth

    @staticmethod
    def _child_class_(isfile, mode):
        """Child node classes for use by @weaklisting attributes.

        Required arguments:
          isfile -- true if the child is to describe a file, false if it is to
                    describe a directory
          mode -- the '[A-Z]+' part of the child's name (may be ignored)

        Returns a class to use, taking the same constructor arguments as for
        CacheFile and CacheSubDir, to instantiate a child of self.  When isfile
        is true, this class must have CacheFile as a base; when isfile is false,
        the class must have CacheSubDir as a base.

        Derived classes should over-ride this @staticmethod to provide classes
        with suitable @weaklisting (and related) attributes for their specific
        applications.\n"""

        if isfile: return CacheFile
        return CacheSubDir

    class WeakSeq (WeakTuple):
        __upinit = WeakTuple.__init__
        def __init__(self, cdir, getseq):
            def get(ind, s=cdir, g=getseq):
                # be sure to match order in __listing(self, ...), above:
                it = g(s)[ind]
                cls = s._child_class_(it.isfile, it.types)
                assert issubclass(cls, CacheDir._child_class_(it.isfile, it.types))
                return cls(it.name, s, it.types, it.sign, it.begin(cdir.sign), it.reach)
            self.__upinit(get)
            self.__who, self.__att = cdir, getseq

        def __len__(self): return len(self.__att(self.__who))

    @lazyprop
    def listing(self, W=WeakSeq): return W(self, lambda s: s.__listing)

    del WeakSeq

    class WeakSubSeq (WeakTuple):
        """For filtered sub-lists of .listing

        We don't want to force re-loading of every entry in listing just to
        check whether its types match some requirement; so, instead, we rely on
        the fact that .listing is in sync with .__listing; filter the latter to
        find the entry we want, then take the corresponding entry from the
        former.  This ensures that all @weaklistings re-uses the same objects as
        entries, rather than creating duplicate objects.

        Required arguments:
          cdir -- CacheDir object
          getseq -- function to fetch its private __listing attribute
          test -- test to apply to types strings, the [A-Z]+ part of file-names.

        This member class can't refer to .__listing directly, so we have to be
        given getseq to fetch it; our resulting WeakTuple holds the members of
        .listing with indices matching those in cdir.__listing for whose types
        field the given test returns true.\n"""

        __upinit = WeakTuple.__init__
        def __init__(self, cdir, getseq, test):
            def get(ind, s=cdir, g=getseq, f=test):
                j = 0
                for it in g(s):
                    if f(it.types):
                        if ind: ind -= 1
                        else:
                            ans = s.listing[j]
                            assert ans.types == it.types and f(ans.types)
                            return ans
                    j += 1

                raise IndexError
            self.__upinit(get)
            self.__who, self.__att, self.__test = cdir, getseq, test

        def __len__(self): return len(filter(self.__test, self.__att(self.__who)))

    @staticmethod
    def weaklisting(picker, W=WeakSubSeq, L=lazyprop):
        """Lazy WeakTuple decorator for a filter on types.

        The [A-Z]+ portion of each cache file or directory name describes the
        type of data it contains.  This class supports a lazy attribute which
        packages the parsed directory listing; using other classes of this
        module it can convert entries in this to suitable SubNode objects.  The
        lazy attribute listing yields a full list of such objects, as a
        WeakTuple.  However, derived classes may want only a sub-set of that
        listing, also as a WeakTuple.  This decorator helps them implement that.

        Single argument, picker, is a function which takes a type string,
        matching '[A-Z]+', and returns a true result if sub-nodes of that type
        are to be included in the WeakTuple.

        Example: a derived class, for which type 'F' data provides factor
        information about naturals, could use:
           @CacheDir.weaklisting
           def factors(types): 'F' in types
        to provide its instances with a lazily-evaluated .factors attribute,
        whose value is a tuple of weakly referenced sub-node objects describing
        directory entries in whose names 'F' appeared in the type
        component.\n"""

        def get(self, test=picker, S=W):
            return S(self, lambda s: s.__listing, test)

        return L(get, doc=picker.__doc__)

    del WeakSubSeq

    @staticmethod
    def _gap_(before, after, limit=None, Hole=Gap, Range=Interval):
        """Gap object for use by locate.

        Required arguments:
          before -- extant cache node one one side of the gap, or None
          after -- extant cache node on the other side of the gap, or None
        Optional argument:
          limit -- None (default) or an existing Gap
          Hole -- callable, taking the same parameters as Gap and returning an
                  instance of Gap; defaults to Gap, but derived classes might
                  wish to replace it with a class based on Gap.

        At most one of before and after shall be None; when neither is, they
        share a common .parent, each is an entry in its .listing and before's
        index therein is less than after's.  In particular, each shall be an
        instance of some class returned by the ._child_class_() of .parent; and
        .parent's class is the one whose _gap_ implementation is used.

        Returns a Gap object describing the interval between the given nodes.
        If limit is not None, the returned Gap's interval is a sub-interval of
        the one limit describes.

        Derived classes should extend this method, calling their base-class's
        implementation (optionally with a class derived from Gap as Hole) and
        adding application-specific attributes to the returned gap, describing
        such properties of it as they know how to infer from before and after.
        Interval attributes should, where relevant, be sub-intervals of any
        corresponding attribute on limit.\n"""

        # First, work out absolute start, stop
        if after is None: stop = None
        else:
            parent = after.parent
            if after.span.step * parent.sign < 0:
                assert after.span.stop is not None
                stop = after.span.stop - after.span.step
            else: stop = after.span.start

        if before is None:
            assert after is not None # => nor is parent, nor is stop
            if parent.span is None: start = None
            else: start = parent.span.start
        else:
            parent = before.parent
            if before.sign * parent.sign < 0:
                start = before.span.start - before.span.step
            else: start = before.span.stop
            assert start is not None
            if stop is None and parent.span is not None:
                stop = parent.span.stop # which may still be None

        assert parent is not None
        assert parent.span.step == parent.sign
        # Clip to limit:
        if limit is not None:
            assert isinstance(getattr(limit, 'span', None), Range)
            lo, hi = limit.span.start, limit.span.stop
            if limit.span.step * parent.sign < 0: lo, hi = hi, lo

            if start is None: start = limit.span.start
            elif lo is None: pass
            elif (lo - start) * parent.sign > 0: start = lo

            if stop is None: stop = hi
            elif hi is None: pass
            elif (hi - stop) * parent.sign < 0: stop = hi

        assert start is None or stop is None or (stop - start) * parent.sign > 0
        # Now orient away from zero (if possible):
        if start is None:
            assert parent.span is None
            assert stop is not None
            start, stop, sign = stop - parent.sign, None, -parent.sign
        elif stop is None:
            assert parent.span.stop is None
            sign = parent.sign
        elif stop * parent.sign <= 1 and start * parent.sign < 0:
            sign = -parent.sign
            start, stop = stop - sign, start - sign
        else:
            sign = parent.sign

        assert start is not None
        # Fix up relative to parent:
        if parent.straddles0:
            sign /= parent.sign
        else:
            assert sign == parent.sign
            sign = None
            start -= parent.span.start
            if stop is not None:
                stop -= parent.span.start

        # Finally, create our Gap object:
        return Hole(parent, start, stop, sign)

    @staticmethod
    def _bchop(row, value, attr):
        """Find where in a sequence some monotonic attribute takes a given value.

        Required arguments:
          row -- sequence of cache nodes
          value -- the value sought
          attr -- the name of an attribute

        Uses binary chop, with linear interpolation, and endeavours to access as
        few nodes in the sequence as possible, since the sequence may be weakly
        stored, hence accessing entries may involve non-trivial object creation.
        If a node in the sequence is found, in whose range of values, of the
        given attr, our sought value lies, then this node's index in row is
        returned.  Otherwise, an IndexError is raised, whose .args is a twople,
        (before, after), in which: either before is None or it's the index of a
        node whose range of attr is entirely less than value; either after is
        None or it's the index of a node whose range of attr is entirely greater
        than value; if either is None then the other is 0 or len(row)-1; and if
        neither is None they are consecutive (but possibly reversed) indices in
        row.\n"""

        lo, hi = 0, len(row) - 1
        loa, hia = getattr(row[lo], attr), getattr(row[hi], attr)
        if hia > loa: sign = +1
        else:
            assert hia < loa
            sign, lo, hi, loa, hia = -1, hi, lo, hia, loa

        if loa.min > value: raise IndexError(None, lo)
        elif hia.max < value: raise IndexError(hi, None)
        if loa.max >= value: return lo
        if hia.min <= value: return hi
        assert 0 < sign * (lo - hi)

        while 1 < sign * (lo - hi):
            assert loa.max < value < hia.min
            # linear-interpolate a "mid-point" between those:
            mid = int(lo + sign + (hi - lo - sign) * 
                      (value - loa.max - 1) * 1./ (hia.min - loa.max - 1))
            assert (sign < 0 and lo > mid > hi) or (sign > 0 and lo < mid < hi)
            mida = getattr(row[mid], attr)
            if mida.min > value: hi, hia = mid, mida
            elif mida.max < value: lo, loa = mid, mida
            else: return mid

        assert sign * (hi - lo) == 1
        assert loa.max < value < hia.min
        raise IndexError(lo, hi)

    def locate(self, value, attr='span', gap=None, seq='listing', types=None):
        """Find sub-node or gap containing a specified entry.

        Do not pass more than five arguments (beyond self) to this method.
        Required argument:
          value -- what to locate
        Optional arguments:
          attr -- name, default 'span', of the attribute to which value relates.
                  Must be an Interval-valued attribute, whose ranges of values
                  for nodes with disjoint spans are disjoint and abut (i.e. the
                  .stop of one is the .start of the other) if the spans do.
          gap -- a Gap object, or None indicating the full range of integers
          seq -- name, default 'listing', of some @weaklisting attribute for
                 which each entry in the list has the attribute named by attr
          types -- None, to use seq, else an [A-Z]+ string to ignore seq and use
                   the sub-list of .listing whose types include all those listed
                   in types.

        Aims to locate a CacheFile in which the natural with attr equal to value
        would lie, if there is such a natural; however, if the cache contains no
        such file, a Gap object shall be returned, describing an interval in
        which this cache lacks relevant data.  In the latter case, the Gap
        object is obtained by calling self._gap_ (q.v.) with suitable arguments,
        using gap as limit.  This enables derived classes to equip the returned
        object with relevant attributes unknown to this base-class.

        The attribute named by seq (when not superseded by specifying types)
        should be an attribute of self and of all CacheDir descendants of self;
        its value on each such node should be a list (typically the @weaklisting
        filtering on child nodes that shall have attribute attr) in which each
        entry must have attribute attr, with the entries in self.seq and each
        descendant CacheDir's .seq are sorted in increasing order on attr.\n"""

        if types is None: row = getattr(self, seq)
        elif not types: row = self.listing
        else: row = self.typed_children(types)

        if not row: # hopeless !
            if gap is None:
                raise ValueError, 'No gap limits range on empty cache directory'
            return gap

        try: kid = self._bchop(row, value, attr)
        except IndexError, what:
            b, a = what.args
            if (None not in (a, b) and a < b) or \
                   (b is None and a + 1 == len(row)) or \
                   (a is None and b == 0):
                a, b = b, a
            return self._gap_(row[b], row[a], gap)

        if isinstance(kid, CacheDir):
            return kid.locate(value, attr, gap, seq, types)

        assert isinstance(kid, CacheFile)
        return kid

    def typed_children(self, types, alldirs=False):
        """Filter .listing on those entries relevant for given types.

        Required argument, types, is a type string; entries in .listing are
        deemed relevant if their type-string includes every type letter of
        this.  Optional argument, alldirs, defaults to False; when it is true,
        all directories are deemed relevant, regardless of type.  The returned
        list preserves its entries' relative order within .listing (and doesn't
        cause other entries in .listing to be created unnecessarily).\n"""

        row, i = [], 0
        for it in self.__listing:
            if not alldirs or it.isfile:
                for t in types:
                    if t not in it.types: break
                else:
                    row.append(self.listing[i])
            else:
                row.append(self.listing[i])

            i += 1

        return row

del WeakTuple, LockDir, lazyattr

class CacheRoot (CacheDir):
    def __init__(self, path): self.__dir = path
    parent = span = None
    sign = +1
    @lazyprop
    def straddles0(self):
        return self.span is None or (-1 in self.span and +1 in self.span)
    @property
    def root(self): return self
    def path(self, *tail): return self.__path(tail)
    def __path(self, tail, join=os.path.join): return join(self.__dir, *tail)

class TypeSet (set):
    def __str__(self):
        types = list(self)
        types.sort()
        types = ''.join(types)
        return types

from study.crypt.base import intbase
nameber = intbase(36) # its .decode is equivalent to int(,36) used above.
del intbase

class WriteDir (WriteNode, CacheDir):
    # Tool functions for newfile:
    def span_hi(span, row, chop, getargs):
        """Find index in row at which span's end falls.

        See __bracket for args.  Returns the index in row at which we should add
        a file covering span.last; this is either the index of a directory in
        row or a pair of adjacent indices (or None for 'index outside row') of
        entries on either side of span.last; it is None if span is endless.

        Raises ValueError if span strictly subsumes the span of a node in row or
        ends part-way through a file in row.\n"""

        if span.stop is None: return None

        try: end = span.last
        except AttributeError:
            ep = span.step
            if ep is None: ep = 1
            q, r = divmod(span.stop - span.start, ep)
            if not r: q -= 1
            end = span.start + q * ep

        try: hi = chop(row, end, 'span')
        except IndexError, what:
            hi = getargs(what)

            if hi[0] is not None:
                b = row[hi[0]]
                assert b.span is not None
                if b.span.step * span.step < 0:
                    wide = span.step * (span.start - b.span.start) < 1
                elif b.span.stop is None:
                    assert False, "How did that happen ?"
                    wide = True
                else:
                    wide = span.step * (span.start - b.span.stop) < 0

                if wide:
                    raise ValueError(span, 'straddles existing file', b)
        else:
            if isinstance(row[hi], CacheFile):
                raise ValueError(span, 'overlaps existing file', row[hi])

        return hi

    def span_lo(span, row, chop, getargs):
        """Find index in row at which span.start falls.

        See __bracket for args.  Returns index in row at which we should add a
        file covering span.start; this is either the index of a directory in row
        or a pair of indices (or None for 'index outside row') of entries on
        either side of span's start.

        Raises ValueError if span strictly subsumes the span of a node in row or
        starts part-way through a file in row.\n"""

        try: lo = chop(row, span.start, 'span')
        except IndexError, what:
            lo = getargs(what)
            if lo[1] is not None and span.stop is not None:
                a = row[lo[1]]
                assert a.span is not None
                if a.span.step * span.step > 0:
                    wide = span.step * (span.stop - a.span.start) > 0
                elif a.span.stop is None:
                    assert False, "How did that happen ?"
                    wide = True
                else:
                    wide = span.step * (span.stop - a.span.stop) > 1

                if wide:
                    raise ValueError(span, 'straddles existing file', b)
        else:
            if isinstance(row[lo], CacheFile):
                raise ValueError(span, 'overlaps existing file', row[lo])

        return lo

    def delimit(span, row, sign, chop, shi=span_hi, slo=span_lo):
        def getargs(what, r=len(row), swap=sign<0):
            b, a = what.args
            # before, after: indices into row, possibly in reverse order:
            if (None not in (a, b) and a < b) or \
                   (b is None and a + 1 == r) or \
                   (a is None and b == 0):
                a, b = b, a
            # Now we know their order in row,
            # put them into their order relative to span:
            if swap: return a, b
            return b, a

        hi = shi(span, row, chop, getargs)
        lo = slo(span, row, chop, getargs)

        # Set ind, the first and last interesting indices in row:
        ind = [ None, None ]
        if isinstance(hi, tuple): ind[1] = hi[0]
        else: ind[1] = hi
        if isinstance(lo, tuple): ind[0] = lo[1]
        else: ind[0] = lo

        # Now swap from span's order to row's:
        if sign < 0: ind.reverse()
        if ind[0] is None: ind[0] = 0
        if ind[1] is None: ind[1] = len(row) - 1

        assert ind[0] <= ind[1] or lo == (ind[1], ind[0]) == hi
        return ind

    del span_hi, span_lo

    def abutting(lo, gap, hi):
        """Determines whether lo or hi can be grown to include gap.

        Arguments:
          lo -- a span which might abut gap.start
          gap -- a span
          hi -- a span which might abut gap.stop

        Abutting across 0 doesn't count; a node can't be grown across it.\n"""
        ar, op, ep = gap.start, gap.stop, gap.step
        if op == 0:            hia = False
        elif hi.step * ep > 0: hia = (op - hi.start) * ep >= 0
        else:                  hia = (op - hi.stop)  * ep >  0
        if lo.step * ep > 0:    loa = (ar - lo.stop)  * ep <  1
        elif ar * ep in (0, 1): loa = False
        else:                   loa = (ar - lo.start) * ep <= 1
        return loa, hia

    def newfile(self, span, types, abuts=abutting, bracket=delimit, set=TypeSet):
        """Find where to create a new file to be added.

        Required arguments:
          span -- the range of integers to be described by the file
          types -- an [A-Z]+ text specifying application-specific types of
                   information about integers to be stored in the new file.

        Raises ValueError if the given span overlaps any existing file for data
        of the given types.  Otherwise, returns a self._child_class_(True,
        types) instance in the hierarchy under self, into which the client may
        save its data of the given types for the given range of integers.  The
        application should subsequently call self.tidy() to ensure consistency
        of the resulting cache.

        This base-class implementation may instead raise an IndexError whose
        .args is a twople, (before, after), each entry in which is a node on the
        relevant side of the sought file, if any, else None; derived classes
        WriteRoot and WriteDir overload this method to deal with the various
        possibilities in that case.\n"""

        assert span.step in (-1, +1), 'I require a contiguous range'
        assert span > -1 or span < 1, 'Only a cache root can straddle 0'
        assert self.span is None or self.span.subsumes(span)

        row = self.typed_children(types, True)
        sign = span.step * self.span.step

        fom, tom = delimit(span, row, sign, self._bchop) # fra-og-med, til-og-med
        if tom > fom:
            raise ValueError('Interval spans several subordinate nodes',
                             span, row[fom:tom+1])
        elif tom < fom:
            assert fom == 1 + tom

            tom, fom = row[tom], row[fom]
            # tab, fab: True if tom, fom abut span, not across zero:
            if sign < 0: fab, tab = abuts(fom.span, span, tom.span)
            else:        tab, fab = abuts(tom.span, span, fom.span)

            assert not tab or not fab or tom.sign * fom.sign > 0
            # Grow the one further from zero, given a choice:
            if (tom.span.start - fom.span.start) * tom.sign > 0 and \
               tab and isinstance(tom, CacheDir): kid = tom
            elif fab and isinstance(fom, CacheDir): kid = fom
            elif tab and isinstance(tom, CacheDir): kid = tom
            else:
                # Delegate to derived class:
                raise IndexError(tom, fom)
        else:
            kid = row[tom]

        assert isinstance(kid, WriteSubDir), \
               'I should have raised ValueError in span_{hi,lo}'

        # Extend kid to cover union (but filling in gaps to make regular):
        ts = set(types)
        ts.update(kid.types)
        kid = kid._update_name_(self.span.meet(span), str(ts))
        return kid.newfile(span, types)

    del abutting

    @staticmethod
    def contiguous(cls, child, sense, contig=CacheDir.contiguous):
        """Returns a selected end of child's contiguous block.

        Required arguments:
          child -- an entry in self.listing
          sense -- relative direction flag

        If sense is > 0, we search away from zero, else towards zero, for an end
        of the child's contiguous block.  To search upwards (towards +ve
        infinity) pass child.sign; for downwards, -child.sign works.  We start
        at the node found by CacheDir.contiguous(), q.v.; if this node is tidy,
        we return it.  Otherwise, while its end-child in the selected direction
        is untidy, we step to that, returning the lowest-depth untidy node at
        the selected end of the contiguous block.  See WriteSubNode's .front and
        .rear for uses.\n"""

        child = contig(child, sense)
        try:
            if child.__changed or len(child.listing) != 12:
                if sense > 0: last = -1
                else: last = 0
                while True:
                    down = child.listing[last]
                    assert down.sign * child.sign > 0
                    if down.__changed or len(down.listing) != 12:
                        child = down
                    else: break

        except AttributeError: # missing .__changed
            assert not isinstance(child, WriteDir)

        return child

    __changed = False # see tidy() and WriteNode._save_()
    def _onchange_(self, seq=Ordered):
        if not self.__changed:
            self.__changed = True
            if self.parent is not None:
                self.parent._onchange_()
                # Ensure changed node isn't garbage-collected before we tidy() it:
                try: queue = self.parent.__changes
                except AttributeError:
                    queue = self.parent.__changes = seq()
                queue.append(self)

    def tidy(self):
        """Tidy up subordinate nodes.

        Ideally, each directory contains a dozen children, all of equal
        depth.  This method sees how near that ideal it can bring this
        directory.\n"""

        change = False
        while self.__changed:
            del self.__changed # to expose the class value, False
            assert not self.__changed
            # ... but that may change when we tidy() children.

            # Clear .__changes (but hang onto its references for now):
            try: changes = self.__changes
            except AttributeError: continue
            else: del self.__changes
            # ... but that ma be put back when we tidy() children.
            assert self.depth == 1 or changes

            idx = filter(lambda k, c=self._contrary: k.index < c, changes)
            idx.reverse()
            idx += filter(lambda k, c=self._contrary: k.index >= c, changes)
            # Traversing kids away from zero ensures near-zero nodes are always
            # tidy if they can be.

            for node in idx:
                assert node.__changed and isinstance(node, WriteDir)
                if node.tidy(): change = True

            del changes, idx # allow old nodes to be garbage-collected

        try: self.index
        except AttributeError:
            assert self.parent is None
        except ValueError:
            # Those recursive .tidy() have caused a __relocate which has sent
            # kids back up and out through self, leading to self renaming
            # (thanks to some of its children changing their .span), hence
            # actually emptying itself and becoming redundant.  Telling .parent
            # it's seen some change is all that remains to do.
            return True

        if change: self._ontidy_()
        elif len(self.listing) == 12: return False # nothing to do

        if self.parent is None:
            chunks = tuple(self.contigua)
            # Some chunks may have more mixed depth than we like, e.g. due to
            # two previously disjoint ones of different depths colliding.
            split = []
            for chunk in chunks:
                ds = map(lambda x: x.depth, chunk)
                hi, lo = max(ds), min(ds)
                early = min(filter(lambda x, h=hi: x.depth  < h, chunk))
                late  = max(filter(lambda x, h=hi: x.depth >= h, chunk))
                if hi - lo > 1 or early < late:
                    hi, lo = self.__consolidate(chunk, hi-1)

                if hi != lo: split.append(chunk)

            # Some chunks may be long enough to collapse; some of mixed depth
            # may be ready to collapse their shallow ones.
            big = max(6, 12 - len(chunks))

            # There may be too many chunks (we can't always fix that).
            raise NotImplementedError # TODO: implement

        elif len(self.listing) > 19:
            # adopting none should sort out our surplus:
            self, spare = self.__adopt(False, ())
            if spare:
                self.__relocate(spare)

        # elif len(self.listing) < 12, not much we can do about it; we just try
        # to avoid having that situation arise in the first place.
        self._ontidy_() # (again)
        return True

    def __bundle(self, kids, step=+1):
        """Packages a bundle of peers of self's kids as a peer of self.

        Required argument, kids, is a sequence of nodes with depth one less than
        self's; their combined span should abut that of self.  Optional
        argument, step, is +1 (the default) if they abut self at its
        away-from-zero end or -1 to indicate its near-zero end.  Returns a
        twople (peer, ks) in which peer is a new peer of self, which is now the
        parent of at least some of kids, and ks is a (possibly empty) tuple of
        remaining kids that aren't its children.\n"""

        up = self.parent
        ts = up.__child_types(kids)
        cls = up._child_class_(False, ts)
        assert issubclass(cls, WriteDir)
        if step < 0: lo = self.span.start, kids[-1]
        else: lo = self.span.stop, kids[0]
        lo -= up.span.start
        lo *= up.sign
        down = cls(up.child_name(Range(lo, 0), False, ts), up, ts, None, lo, 0)
        down, kids = down.__adopt(False, kids)
        # kids should now be empty, unless it was really long before ...
        return down, kids

    def __consolidate(self, kids, hi):
        """Turn shallow nodes into children of deeper ones.

        First argument, kids, is a contiguous chunk of top-level nodes in our
        directory hierarchy (as a tuple); second is one less than the greatest
        depth in this chunk.  All kids with lesser depth shall be relocated into
        suitable neighbour nodes of greater depth.  All kids with depth hi that
        appear before one of depth hi+1 shall likewise be relocated into that
        node.  Returns new max and min depth of surviving top-level nodes in
        this chunk.\n"""

        i, start, stop = 0, kids[0].range.start, kids[-1].range.stop
        back = False    # is kids[i-1] eager to adopt kids ?
        clear = False   #
        while i < len(kids):
            assert not back or i > 0
            if back and kids[i].depth == kids[i-1].depth:
                kid, out = kids[i-1].__adopt(True, kids[i].listing)
                if out: # push back to kids[i]'s end
                    kid, out = kid.__adopt(True, out)
                kids = kids[:i-1] + (kid,) + kids[i:]
                kids[i]._ontidy_()
                if out:
                    kid, out = kids[i].__adopt(False, out)
                    kids = kids[:i] + (kid,) + out + kids[i+1:]
                    if out:
                        back = False
                        i += 1
                        continue
                    assert kids[i].depth > hi or (clear and kids[i].depth == hi)
                else:
                    assert len(kids[i].listing) == 0, 'It just gave away all its kids !'
                    kids = kids[:i] + kids[i+1:]
                    back = len(kids[i-1]) < 12
                    continue

            if kids[i].depth > hi or (clear and kids[i].depth == hi):
                back = len(kids[i]) < 12
                i += 1
                continue

            if back: # easy case
                up = kids[i-1]
                assert i > 0 and up.depth > kids[i].depth
                while up.depth > kids[i].depth + 1:
                    up = up.listing[-1]
                j = i+1
                while j < len(kids) and kids[j].depth == kids[i].depth:
                    j += 1

                out, kids = kids[i:j], kids[:i] + kids[j:]
                up, out = up.__adopt(False, out)
                while out:
                    up, out = up.__bundle(out)
                continue

            raise NotImplementedError # TODO

        return lo, hi # range of values of survivors

    @staticmethod
    def __child_types(kids, ts=None, lo=None, hi=None, set=TypeSet):
        if ts is None: ts = set()
        for kid in kids: ts.update(kid.types)
        return str(ts)

    def __relocate(self, step, kids, Range=Interval):
        """Re-parent some descendant nodes.

        First argument, step, is either +1 or -1, indicating whether nodes are
        to be moved, respectively, away from or towards zero.  All subsequent
        arguments are child nodes of self, when self has decided it's got too
        many children: we need to find a new home for them.\n"""

        # TODO eliminate step; always sweep away from zero
        assert step in (+1, -1) and self.parent is not None
        # Initialize i to force first iteration to move up the directory tree:
        if step < 0: i = 0
        else: i = len(self.listing)
        node, tidy = self, True
        while kids:
            if not tidy or 0 <= i+step < len(node.listing):
                if tidy:
                    i += step # still a valid index in listing
                    down = node.listing[i]
                    if node.parent is None:
                        # Have we run off the end of a contiguous block ?
                        if step < 0:
                            check = lambda k, s=down.span.stop: k.span.start <= s
                        else:
                            check = lambda k, s=down.span.start: k.span.stop >= s
                        if not filter(check, kids): # No kid meets down
                            tidy = False
                            i -= step
                            down = node.listing[i]
                        del check

                elif step < 0: down = node.listing[0]
                else: down = node.listing[-1]

                if filter(lambda x, d=down.depth-1: x.depth >= d, kids):
                    down, kids = down.__adopt(tidy, kids)
                    if not tidy:
                        while kids:
                            down, kids = down.__bundle(kids, step)
                else:
                    node.__revise_span(kids) # kids being added
                    node = down
                    if (step < 0) == tidy:
                        i = len(node.listing) - 1
                    else: i = 0
                del down

            elif node.parent is None: tidy = False # root can't delegate
            else:
                # Onwards and upwards !
                node = node.__revise_span(kids) # kids being removed
                i = node.index
                node = node.parent

    def __revise_span(self, kids, set=TypeSet, Range=Interval):
        """Update span and types as we gain or lose children.

        All arguments are nodes being added to or removed from self, that aren't
        yet reflected in self's children's properties.  Returns the node that
        replaces self after revising its span.\n"""

        if self.parent is None:
            self._ontidy_()
            return # root doesn't record its span anyway.

        types, lo, hi, kids = self._child_union(kids, set()) # from CacheDir

        if self.sign < 0: span = Range(self.span.start + 1 - hi, hi - lo)
        else: span = Range(self.span.start + lo, hi - lo)

        if kids:
            # We've removed the ones in self.listing; the rest are moving in:
            assert all(k.stop is not None for k in kids)
            span = span.meet(*map(lambda k: k.span, kids))
            types = self.__child_types(kids, types)
        else:
            types = str(types)

        return self._update_name_(span, types)

    def __adopt(self, tidy, kids, seq=Ordered):
        """Accept new descendant nodes.

        If first argument, tidy, is true, self should aim to have a sensible
        number of children on return.  Second argument is a sequence of nodes
        self should accept as children.  Each should have depth one less than
        that of self.  The union of the ranges of the given child nodes should
        be contiguous and abut or overlap self.span.

        Adopting these children may, of course, cause self to have (or self may
        already have) too many child nodes: in which case, if tidy is true, self
        should return a tuple of child nodes from self's opposite end, so that
        caller can duly forward them to some other node for adoption.  When tidy
        is false, this function may leave self untidy by adopting all kids and
        returning (); otherwise, it should make self tidy and return a tuple of
        at least six (and ideally at least eight) nodes, either from kids or
        from self's prior children, from the same end of self as the given kids
        abut (this is also the end of the range of self's ancestors all the way
        back to root, where it is the end of a contiguous range).\n"""

        # NB: self may be a freshly-created empty node with no real directory yet.
        assert self.parent is not None
        assert kids or len(self.listing) > 12, 'Pointless !'
        assert not self.span or all(x.depth == self.depth-1 for x in kids)

        for it in kids:
            n = cmp(self.listing[0].span.start, it.span.start)
            if n:
                before = n * self.sign > 0
                break
        else:
            # All kids start at the same place as self (e.g. if self is empty),
            # or there are none: either way, we want to keep .listing[:12].
            before = tidy

        # kids should either all be before listing[0] or all be after listing[-1]:
        assert all(x * self.sign >= 0 for x in
                   map((lambda k, b=self.listing[0].span.start: b - k.span.stop)
                       if before else
                       (lambda k, e=self.listing[-1].span.stop: k.span.start - e),
                       kids))

        all = seq(self.listing)
        for kid in kids: all.append(kid)
        all = tuple(all)

        if self.sign > 0:
            def after(a, b): return a.span > b.span
        else:
            def after(a, b): return a.span < b.span
        # Either way: after(a, b) iff a belongs (wholly) after b in self.listing
        assert all(not after(y, x) for x, y in zip(all[:-1], all[1:])), \
            'Broken sorting in Ordered :-('

        # Where do we want to cut all ?
        n = len(all)
        if before == tidy: # We'll keep all[:cut]
            cut, lo, hi = 12, 6, min(n, 24)
        else: # We'll keep all[cut:]
            cut, lo, hi = n - 12, max(1, n - 24), n - 6

        # Where can we cut all ?
        cs = filter(lambda i, k=all, a=after: a(k[i], k[i-1]), range(lo, hi+1))
        # For c in cs, all[c] is fully after all[c-1]; but a clean cut also
        # needs all i < c-1 to have all[i] before all[c] and all i > c to have
        # all[c-1] before all[i]; so refine initial pass at cs:
        cs = filter(lambda c, k=all, a=after: not(
                filter(lambda p, m=k[c], a=after: not a(m, p), k[:c]) +
                filter(lambda p, m=k[c-1], a=after: not a(p, m), k[c:])),
                    cs)

        if cut in cs: pass
        elif cs: # Make do with the closest cs[i] to cut:
            if cs[0] > cut: cut = cs[0]
            elif cs[-1] < cut: cut = cs[-1]
            else:
                lo, hi = 0, len(cs) - 1
                while lo + 1 < hi:
                    assert cs[lo] < cut < cs[hi]
                    mid = (lo + hi) / 2
                    if cs[mid] < cut: lo = mid
                    else:
                        assert cs[mid] > cut
                        hi = mid
                lo, hi = cs[lo], cs[hi] # Candidate cut-points on either side of cut.
                # Which is closer to cut ?
                gap = cmp(cut - lo, hi - cut)
                if gap > 0 or (gap == 0 and before): cut = hi
                else: cut = lo

        elif tidy: # Ouch !  No valid split-point exists.
            raise NotImplementedError # TODO: create a suitable split-point
        else: # Arrange to keep all and live with the untidiness:
            if before: cut = 0
            else: cut = len(all)
            self._onchange_()

        lo, hi = all[:cut], all[cut:]
        if before == tidy: keep, ans = lo, hi
        else: keep, ans = hi, lo
        assert len(keep) > min(5, len(all))

        ts = self.__child_types(keep)
        span = keep[0].span.meet(*map(lambda k: k.span, keep[1:]))
        peer = self._update_name_(span, ts)

        # NB: relocate *after* _update_name_, to ensure directory exists !
        for kid in kids: kid.relocate(peer)
        # Now forget anything computed based on out-of-date file-system state:
        self._ontidy_()
        peer._ontidy_()

        return peer, ans # so someone else takes them off our hands !

    @staticmethod
    def _child_class_(isfile, mode): # configure __listing
        if isfile: return WriteFile
        return WriteSubDir

    @lazyprop
    def __namelen(self, fmt=nameber.encode):
        if not self.straddles0:
            # len(self.span) is an upper bound on the .span.start of children
            return len(fmt(len(self.span)))
        # Child names use absolute values for starts
        return len(fmt(max(abs(self.listing[0].last),
                           abs(self.listing[-1].last))))

    # annoyance: child_name needs span, but _child_class_() wants sign, hi, lo :-(
    def child_name(self, span, isfile, types, fmt=nameber.encode):
        """Determine name of a child.

        Required arguments:
          span -- range of integers to be described by the new node
          isfile -- true for a file, false for a directory
          types -- [A-Z]+ string indicating application-specific types of data
                   to be stored in the new node.

        Returns a name matching the regex of __listing and padded with enough
        leading 0s to make lexical sorting match numeric order.\n"""

        assert span >= 0 or span <= 0
        assert span.step > 0 or span <= 0
        assert span.step < 0 or span >= 0
        assert span.start * span.step >= 0

        if self.straddles0:
            if span.step < 0: sign = 'N'
            else: sign = 'P'
            name = fmt(span.start * span.step)
        else:
            name = fmt(span.start - self.span.start)

        gap = self.__namelen - len(name)
        if gap > 0: name = '0' * gap + name
        if self.straddles0: name = sign + name

        assert len(types) > 0
        name += types
        name += fmt(len(span))
        if isfile: name += '.py'
        return name

del nameber, Interval, Ordered

class WriteRoot (WriteDir, CacheRoot):
    _child_class_ = WriteDir._child_class_
    __newfile = WriteDir.newfile # q.v. for documentation
    def newfile(self, span, types):
        try: return self.__newfile(span, types)
        except IndexError, what: before, after = what.args

        if self.straddles0:
            # We must set sign, and use absolute start:
            if span > -1: sign = self.sign
            else: sign = -self.sign
            start = abs(span.start)
            assert sign * self.sign * start == span.start
        else:
            if span.step * self.sign < 0: span = span.reversed()
            sign, start = None, span.start - self.span.start

        cls = self._child_class_(True, types)
        return cls(self.child_name(span, True, types),
                    self, types, sign, start, len(span))

    @property
    def contigua(self):
        """Iterator over contiguous chunks of self's children.

        Each yield is a maximal tuple of contiguous top-level children, sorted
        with the ones near zero first.\n"""

        i = 0
        # Initial loop over reversed chunks:
        while i < len(self.listing):
            at = self.listing[i]
            if at.front is not at: break
            j = at.rear.index + 1
            chunk = list(self.listing[i:j])
            chunk.reverse()
            yield tuple(chunk)
            i = j

        # Loop over forward chunks:
        while i < len(self.listing):
            at = self.listing[i]
            assert at.rear is at
            j = at.front.index + 1
            yield tuple(self.listing[i:j])
            i = j

class CacheSubDir (CacheSubNode, CacheDir):
    _contrary = 0

class WriteSubDir (WriteSubNode, CacheSubDir, WriteDir):
    __upinit = WriteSubNode.__init__
    def __init__(self, name, parent, types, start, span, sign=None, replaces=None):
        """Initialize a modifiable directory.

        Arguments are as for SubNode, to which they are forwarded.  The only
        extra complication is that, when replaces is given, the new object needs
        to flag itself as changed if the front of its contiguous block isn't the
        same as that of the node it replaces.  This ensures it gets a chance at
        a tidy() to deal with any over-populated children.\n"""

        if replaces is not None:
            assert isinstance(replaces, WriteSubDir)
            prior = replaces.front

        self.__upinit(name, parent, types, start, span, sign, replaces)

        if replaces is not None and self.front is not prior:
            self._onchange_()
            # If we're an ancestor of prior, it may have surplus children, which
            # it can now relocate; so make sure it gets a chance to do so:
            run = prior.parent
            while run is not None:
                if run is replaces or run is self:
                    prior._onchange_()
                    break
                run = run.parent

    _contrary = 0
    _child_class_ = WriteDir._child_class_

    def _update_name_(self, span=None, types=None,
                      rename=os.rename, mkdir=os.mkdir, listdir=os.listdir,
                      remove=os.unlink, rmdir=os.rmdir, exists=os.path.exists,
                      set=TypeSet):
        """Replace self with a directory covering an altered range.

        Optional arguments (each defaults to None):
          span -- None or a range of integers
          types -- None or a string of type letters, [A-Z]+

        If span is not None, self.span is used.  It specifies the range of
        integers covered by the new directory.  If types is None, self.types is
        used; it specifies the new sub-directory's list of types.  All children
        of self shall be suitably renamed into the new directory and self shall
        be removed.

        Returns an instance of self.parent._child_class_(False, types).  Derived
        classes should over-load this method, taking the returned instance and
        adding appropriate attributes, based on those of self.\n"""

        if types is None: types = self.types

        # Is it sufficient to simply rename self ?
        if span is None or (self.span.subsumes(span) and span.subsumes(self.span)): # i.e. same
            if types == self.types: return self
            if span is None: span = self.span
            alias = True
        else:
            assert self.sign == self.span.step
            assert self.sign * self.span.start >= 0
            if span.step * self.sign < 0: span = span.reversed()
            alias = span.start == self.span.start

        name = self.parent.child_name(span, False, types)
        cls = self.parent._child_class_(False, types)
        if alias:
            # Simple rename
            rename(self.path(), self.parent.path(name))
            self.parent._onchange_()
            if self.parent.straddles0:
                start, sign = span.start, self.sign * self.parent.sign
            else: start, sign = span.start - self.parent.span.start, None
            return cls(name, self.parent, types, start, len(span), sign, self)

        # Heigh ho - self.span.start has to change.  Create new directory, move
        # each child into it, renaming to adjust offsets as it goes.

        sign = self.sign * self.parent.sign
        if self.parent.straddles0: start = span.start * self.parent.sign
        else:
            assert sign == +1
            start, sign = self.sign * (span.start - self.parent.span.start), None
            assert start > 0

        mkdir(name)
        self.parent._onchange_()
        peer = cls(name, self.parent, types, start, len(span), sign, self)
        for kid in self.listing: kid.relocate(peer)
        peer._save_()

        if exists(self.path()):
            remove(self._cache_file) # __init__.py
            # Move any remaining cruft across:
            for name in listdir(self.path()):
                rename(self.path(name), peer.path(name))

            rmdir(self.path())

        return peer

    __newfile = WriteDir.newfile # q.v. for documentation
    def newfile(self, span, types):
        if span.step * self.sign < 0: span = span.reversed()
        try: return self.__newfile(span, types)
        except IndexError, what: before, after = what.args

        assert self.depth == 1
        assert self.sign < 0 or span >= self.start
        assert self.sign > 0 or span <= self.start

        cls = self._child_class_(True, types)
        return cls(self.child_name(span, True, types),
                    self, types, None,
                    span.start - self.span.start, len(span))

del lazyprop, os, TypeSet
