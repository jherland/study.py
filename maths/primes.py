"""Cached prime numbers.

This module provides an object, primes, which masquerades as the infinite list
of all primes, in their proper order.  If you ask it how long it is, it'll be
finite, but if you ask for an element past the `end' you'll still get it
(though you may have to wait).  Ask for its last element and you'll get some
prime: ask whether some bigger prime is in the list and the answer will be
yes, none the less.

Building on that, this module also provides facilities for factorisation and
multiplying back together again:

  Prodict -- dictionary representing product of pow(key, dict[key])

  factorise(numb) -- returns a Prodict, whose int() is numb: its keys are
  irreducible (so generally primes, but -1, at least, may also appear).

See also generic integer manipulators in natural.py (notably eachprime(), a
cheap and cheerful iterator), combinatorial tools in permute.py and
polynomials in polynomial.py: some day, it'd be fun to do some stuff with
prime polynomials ... and there must be such a thing as complex primes.

See study.LICENSE for copyright and license information.
"""

checking = None

from study.snake import prodict
class Prodict (prodict.Prodict):
    """A dictionary that thinks it describes a factorisation.

    Keys are understood as factors; the value of each is understood as its
    multiplicity.  Thus a Prodict represents the integer given by its __long__
    (q.v.).\n"""

    def __long__(self):
        return reduce(lambda a,b: a*b,
                      map(pow, *map(lambda *args: args, *self.items())), 1)

    def __int__(self): return int(long(self))
    def __float__(self): return float(long(self))
    def __complex__(self): return complex(long(self))

    def __setitem__(self, k, v, up=prodict.Prodict.__setitem__):
        if v < 0: raise ValueError('Negative power of factor', v, k)
        up(self, k, v)

    def __mul__(self, other, up=prodict.Prodict.__mul__):
        try: return up(self, other)
        except AttributeError: pass
        # Interpret other as an integer; use its factorisation

        bok = self.copy()
        primes.factorise(other, bok)
        return bok
    __rmul__ = __mul__

    def __div__(self, other, up=prodict.Prodict.__div__):
        try: other.items
        except AttributeError: other = primes.factorise(other)
        return up(self, other)

    def __rdiv__(self, other, up=prodict.Prodict.__rdiv__):
        try: other.items
        except AttributeError: other = primes.factorise(other)
        return up(self, other)

class lazyTuple:
    """Evaluation on demand of a (possibly infinite) tuple.

    Some of what's in this class should be split out into _Prime, below.
    """
    def __init__(self, row=None):
        """Initialises a lazy tuple.

        Optional argument, row, should be a sorted list.
        """
        if row is None: row = []
        self._item_carrier = row

        try: top = row[-1]
        except self._entry_error_: top = 0
        self._ask = 1 + top

    def __repr__(self):
        text = `tuple(self._item_carrier)`
        if len(text) < 3: return text[:-1] + '...' + text[-1:]
        return text[:-1] + ', ...' + text[-1:]

    def __len__(self):
        return len(self._item_carrier)

    def __getitem__(self, key):
        while key >= len(self._item_carrier) and self.grow(): pass
        return self._item_carrier[key]  # raising IndexError if grow failed

    # A list is function from naturals to its entries:
    __call__ = __getitem__

    def __iter__(self):
        i = 0
        while True:
            yield self[i]
            i = 1 + i

    def __getslice__(self, i, j):
        """self[i:j]"""
        # len has already been added if relevant.  Don't do that again.
        if i < 0 or j < 0: raise IndexError
        return self._item_carrier[i:j]

    def __contains__(self, val):
        """Is val in self ?

        Override this in base-classes.
        """
        while val >= self._ask and self.grow(): pass
        return val in self._item_carrier

    def count(self, item):
        if item in self: return 1
        return 0

    def index(self, item):
        if item in self:
            return self._item_carrier.index(item)

        return -1

    def min(self):
        return self._item_carrier[0]

    def max(self):
        return self._item_carrier[-1]

    def grow(self):
        """Extend self._item_carrier, return true on success.

        Over-ride this method in derived classes - don't call this one.
        It implements lazy range(infinity).
        """
        result = self._ask
        self._item_carrier.append(result)
        self._ask = 1 + result
        return result

class list (list):
    # inheriting from list would work better if __getslice__ propagated class ...
    __upgetsl = list.__getslice__
    def __getslice__(self, i, j):
        return self.__class__(self.__upgetsl(i, j))

class risingSet (list):
    __upinit = list.__init__
    def __init__(self, val=None):
        self.__upinit(val or [])

    __upins = list.insert
    def insert(self, val):
        if not self or self[0] > val: self[:0] = [ val ]
        elif self[-1] < val: self.append(val)
        elif val not in self:
            # so self[0] < val < self[-1]
            bot, top = 0, len(self) - 1 # so bot < top
            while bot + 1 < top:
                at = (bot + top) / 2    # midpoint, erring low
                assert bot < at < top, 'arithmetic'
                assert self[bot] < self[at] < self[top], 'prior order'

                if self[at] < val: bot = at
                else: top = at

                assert self[bot] < val < self[top], 'binary chop missed'

            assert bot + 1 == top, 'binary chop mis-terminating'
            # so insert val after bot, before top - ie, at position top
            self.__upins(top, val)

class _Prime(lazyTuple):
    """List of all primes, generated as needed.

    Needs to use a paged-in-and-out item carrier.  Use that to do cacheing.
    """

    _private_doc_ = """

    From lazyTuple, this inherits ._item_carrier in which we store all the
    primes less than ._ask, which is the next number we're going to check to
    see if it's prime.  Any higher primes we've discovered (usually thanks to
    factorise(), see below) are kept in _sparse (in their correct order,
    albeit probably with gaps).  All currently known primes may be listed as
    .known().

    self._ask will be an ordinary integer as long as it can, then switch over
    to being a long one.  Entries in .known() will be ordinary integers most
    of the time, unless they are so big they must be long().  However, some
    entries which could be ordinary may still be long().

    """

    # always initialise this with at least the first entry, 2, in the list.
    def __init__(self, row=None, sparse=None):
        # implementation of .grow() requires row initially non-empty.
        if row is None: row = [ 2 ]
        elif not row: row.append(2)     # complain if it's not a list !
        lazyTuple.__init__(self, row)

        self._sqrt = 2  # Every prime less than _sqrt has square less than _ask.
        self._sparse = risingSet(sparse)

    def __repr__(self):
        return '%s()' % (self.__class__.__name__)
    def __str__(self):
        if len(self) > 20: return '(%s, ..., %s)' % (str(self[:20])[1:-1], self[-1])
        return lazyTuple.__repr__(self)

    def known(self):
        return self._item_carrier + self._sparse

    def ask(self):
        """Returns a number about which self would like to be asked. """
        return self._ask

    def __contains__(self, num):
        # could sensibly check pow(i, num-1, num) == 1 for a few i in range(2, num)
        seen = 0
        while True:
            if num in self._item_carrier[seen:] or num in self._sparse: return num
            if num < self._ask: return None

            for p in self._item_carrier[seen:]:
                if num % p == 0: return None
                # and p < _ask <= num
                seen = len(self._item_carrier)

            p = self._item_carrier[-1]
            if long(p) * p > num: return self._know(num)

            for p in self._sparse:
                if num % p == 0: return None
                if p > num: break

            if not self.get_cache(): break

        while True:
            p = self.grow()
            if num % p == 0: return None
            if long(p) * p > num: return self._know(num)

    def grow(self):
        if self._ask < self[-1]:
            self._ask = 1 + self[-1]
        was = self._ask

        # This method doesn't load cache !  Architecture change needed.

        while self[-1] < was:   # so we exit when we know.
            if self._ask in self._sparse: self._know()
            else:
                for p in self._item_carrier:
                    if self._ask % p == 0:
                        self.__throw()
                        break

                    if p < self._sqrt: continue # skip the square root check

                    if long(p) * p > self._ask:
                        # no prime less than sqrt(_ask) divides _ask
                        self._know()
                        # because: if no prime less than sqrt(_ask) divides it,
                        # _ask is prime.
                        break
                    else: self._sqrt = p + 1

        return self._item_carrier[-1]   # the new prime

    def __throw(self, other=None):
        """Records a non-prime.

        Argument, other, defaults to self._ask: it must not be a prime.  The
        only time it matters is when it's self._ask: which is then stepped
        forward to the next integer.\n"""
        if other in ( None, self._ask ):
            self._ask = 1 + self._ask


    def _know(self, other=None):
        """Records a prime.

        Argument, other, defaults to self._ask: it must be a prime.  If it is
        self._ask, we append it and advance _ask.  Otherwise, if it isn't
        already in self or _sparse, we add it to _sparse in its proper
        place.\n"""

        if not other or other == self._ask:
            # add _ask to self and advance
            self._item_carrier.append(self._ask)
            if self._ask in self._sparse:
                assert self._ask == self._sparse[0], \
                       'sparse primes array disordered at %d' % self._ask
                self._sparse = self._sparse[1:]

            other = self._ask   # we're going to return this
            self._ask = 1 + other

        elif not (other in self._item_carrier or other in self._sparse):
            assert self._ask <= other, 'missed out a prime, %d, in the search' % other

            self._sparse.insert(other)

        return other

    def factorise(self, num, gather=None):
        """Factorises an integer.

        Argument, num, is an integer to be factorised.
        It may be long, but not real.

        Optional argument:

            gather -- dictionary (ideally a Prodict, q.v.) to which to add
                      results, or None (the default) to use a fresh empty
                      Prodict: this is what factorise() returns.

        The result of factorise() is always a Prodict: the number, N, that it
        describes is num times the one gather, treated as a Prodict, described
        when passed in.  The result's keys are primes, -1 or 0 and its values
        are positive integers, indicating multiplicities.  The key -1 is
        present precisely if N is negative, in which case its multiplicity is
        1 (not, for instance, 3 or 5).  The key 0 only appears when N is 0, in
        which case the result is Prodict({0: 1}).  Note that 1 =
        int(Prodict({})) so I don't need to make a special case of 1 ;^)

        If num is a positive integer, factorise(num) is a Prodict whose keys
        are its prime factors: the value for each key is its multiplicity as a
        factor of num.  Thus, int(factorise(num)) is num.

        Zero is a special case (because it is a multiple of every number): its
        given factorisation is { 0: 1 }.  Negative values are factorised as
        the factorisation of the corresponding positive value, with one extra
        key, -1, with multiplicity 1.

        If you want to know the factorisation of the product of a sequence of
        integers, do it by using gather to collect up their several
        factorisations: it's much easier to factorise each of them in turn
        than to factorise their product !

            out = Prodict({})
            for num in sequence: factorise(num, out)

        See also: Factorise() (which is packaging) and Prodict.
        """

        # Only accept integers !
        if num / (1L + abs(num)):
            raise TypeError, ('Trying to factorise a non-integer', num)

        # Can't use {} as gather's default, as we modify it !
        if gather is None: result = {}
        else:
            result = gather
            if result.get(0, 0): num = 0

        if num < 0:
            if result.get(-1, 0) % 2: del result[-1]
            else: result[-1] = 1
            num = -num

        if num == 0:
            result.clear()
            result[0] = 1
        elif num > 1:
            # Keep track of ones we've already seen: in the cache loop,
            # we don't want to repeat all the ones we've seen before.
            seen = 0

            # First, go through the known primes looking for factors:
            while True:
                for p in self.known()[seen:]:
                    count, num = self.__reduce(num, p)
                    if count: result[p] = count + result.get(p, 0)
                    if num < p:
                        assert num == 1 or num > self._item_carrier[-1] + 1, \
                               ('all primes less than p have already been tried', num, p)
                        break
                else:
                    seen = len(self)    # ignore sparse
                    if self.get_cache(): continue
                break

            # Conjecture: hunting outwards from approximately sqrt(num), rather
            # than up from _ask, might be quicker.  Try hunting down from first
            # power of 2 whose square exceeds num.

            # Now go hunting for primes until the job is done:
            while num > 1:
                p = self.grow()
                count, num = self.__reduce(num, p)
                if count: result[p] = count
                if num == 1: pass
                elif long(p) * p > num:
                    # num's a prime !
                    self._know(num)
                    result[num] = 1
                    # job done ;^)
                    num = 1
                else:
                    assert p > 1

        # else: nothing to do
        return result

    def __reduce(self, n, p):
        """Returns c, m with pow(p,c) * m == n and m coprime with p."""
        c = 0   # p's multiplicity as a factor of n
        while n % p == 0:
            self.__throw(n)
            c, n = c + 1, n / p

        return c, n

    def get_cache(self):
        """Hook-in point for cacheing of primes.

        If you can update self._item_carrier from a cache of some kind, do it
        now.  If you can't, return None, or leave it to this base method to do
        so for you.  On a successful update, return some true value: calling
        code can use this to decide whether to try again ...
        """
        return None

def _tabulate_block(file, block):
    """Writes a sequence of numbers to a file tidily.

    Arguments:

      file -- a file handle, to which to .write() the tabulated numbers

      block -- a sequence of integers (or long integers)

    Begins each line with a space, separates numbers with comma and space,
    limits lines to 80 characters in width (thus only allowing one number per
    line once they are more than 38 characters each).  Ends in a stray comma,
    which python won't mind when it loads the array, but no newline.

    The tabulation algorithm assumes that each entry in block is bigger than
    all previous (specifically, it has at least as many digits), and that
    entries which don't need to be long aren't.  Breaking these assumptions
    will cause no harm beyond making the table messier."""

    across = 80 # Force an initial newline, etc.
    click = 9   # biggest number in current number of digits (initially 1)
    step = 3    # one each for comma and space, plus the current number of digits.
    suffix = 0  # for the trailing L on long items

    for item in block:
        while item > click:
            # item takes up more than step digits: increase step ...
            click = 10 * click + 9
            step += 1
        # That's set step correctly ... now ensure suffix is up to date:
        if not suffix and isinstance(item, long): suffix = 1

        across = across + step + suffix
        if across > 80:
            file.write('\n')
            across = step + suffix

        file.write(' ' + `item` + ',')

from study.snake.lazy import Lazy
class cachePrimes(_Prime, Lazy):
    __upinit = _Prime.__init__
    def __init__(self, row=None, sparse=None,
                 moduledir=None,
                 cachedir=None):
        self.__upinit(row, sparse)
        if moduledir is None:
            from study.maths import __path__
            moduledir = __path__[0]
        self.__prime_module_dir = moduledir
        if cachedir is not None:
            self.prime_cache_dir = cachedir
        self.__step = 1024
        self.__high_water = 0
        return

    def nosuchdir(nom, os):
        try: st = os.stat(nom)
        except os.error: return True
        import stat
        if stat.S_ISDIR(st.st_mode): return False
        raise TypeError(nom, 'exists but is not a directory')

    def _lazy_get_prime_cache_dir_(self, ignored, nodir=nosuchdir):
        import os
        try: ans = os.environ['STUDY_FLATPRIME_PATH']
        except KeyError:
            ans = os.path.join(self.__prime_module_dir, 'primes')
        if nodir(ans, os): os.makedirs(ans)
        return ans

    del nosuchdir

    def _lazy_get__caches_(self, ignored, stem='c'):
        try:
            import os
            loc = self.prime_cache_dir
            row = os.listdir(loc)
        except: return {}

        import string
        def _read_int(text, s=string):
            import string
            if text[-1] == 'L': return s.atol(text, 0)
            else: return s.atoi(text, 0)

        result = {}
        lang = len(stem)
        for name in row:
            if name[:lang] == stem and name[-3:] == '.py' and '-' in name[lang:-3]:
                result[os.path.join(loc, name)
                       ] = map(_read_int, name[lang:-3].split('-'))

        return result

    class Dummy: pass

    def _do_import(self, handle, object=Dummy):
        """Imports data from a file, preparatory to _load()ing."""

        obj = object()
        execfile(handle, obj.__dict__)
        return obj

    del Dummy # Instances of the actual built-in object don't have a __dict__ !

    def get_cache(self):
        """Returns true if it got anything out of the caches."""
        # print 'Getting cache'
        size = len(self._item_carrier)
        for name, pair in self._caches.items():
            if pair[0] <= size:
                del self._caches[name]
                if pair[-1] > size: return self._load(self._do_import(name))

        return None

    def _load(self, found):
        """Loads data that's been imported from a file.

        Argument, found, is the module object as which the file was imported:
        it should have integer attributes, found.at and found.to and list
        attributes found.sparse and found.block, with each member of sparse
        greater than any member of block, and at+len(block)==to.  The given
        block is used as self[at:to], while entries in sparse are added to
        _sparse in their right order.

        The bits of the file we'll examine are variables in the global scope
        with names 'at', 'to', 'sparse' and 'block'.  Most of this function
        checks things, the actual loading is quite brief !\n"""

        size = len(self._item_carrier)
        # Assume found contains the namespace we want to load: if not, convert KeyError.
        try:
            # Test sanity of what we're loading:
            assert found.to == len(found.block) + found.at, 'inconsistent load-file'

            # Check get_cache()'s decision to call _load() was sound ...
            assert found.at <= size, \
                'new slice, [%d:], does not meet up with what we have, [:%d]' % (
                        found.at,                                       size)
            assert size <= found.to, \
                   'mis-ordered loading of cache-files (%d > %d).' % (size, found.to)

            # Expect things in found.sparse to be past the end of found.block,
            # hence of _item_carrier: load them into _sparse (do it here to
            # catch AttributeError if it happens).  If that expectation fails,
            # we'll clear it out shortly.
            for item in found.sparse:
                if item in self._item_carrier + self._sparse: continue
                if checking:
                    # only check it against what we knew before this _load() ...
                    for p in self._item_carrier + self._sparse:
                        assert item % p, 'alleged prime, %d, has a factor, %d' % (item, p)
                # add item to _sparse
                self._know(item)

        except AttributeError, what:
            raise AttributeError('cache-file lacks necessary variable', found, what.args)

        if checking:
            test = self._item_carrier[found.at:]
            assert test == found.block[:len(test)], \
                   "new block of primes doesn't match what I know already"

        # Now the actual loading !
        self._item_carrier[found.at:] = found.block

        # Tidy away anything in _sparse that now doesn't belong there:
        while self._sparse and self._sparse[0] in self._item_carrier:
            self._sparse = self._sparse[1:]

        assert not( self._sparse and self._sparse[0] < self._item_carrier[-1] ), \
               'sparse prime, %d, missed in "full" list' % self._sparse[0]

        return 1

    def _lazy_get__ask_(self, ig):
        return 1 + self._item_carrier[-1]

    def _next_high(self):
        cut = min(self.__high_water >> 3, 1<<22)
        while self.__step < cut: self.__step *= 2
        return self.__high_water + self.__step

    __upgrow = _Prime.grow
    def grow(self):
        # Over-ride _Prime.grow so that we never hold too much uncached.
        ans = self.__upgrow()
        if len(self._item_carrier) > self._next_high():
            self.persist()
        return ans

    def persist(self, name='c', force=None):
        """Records `most' of what the primes module knows in files for later reference.

        Arguments are all optional:

          name -- name-stem for cache files. Default is 'c'.

          force -- flag, default is false.  Normally, persist() trusts files
          already in the cache and doesn't bother re-writing them: set force
          to some true value to make all the files be written anew.

        Updates the cache.  Each cache file contains a sub-list of the known
        primes: small primes are recorded in files with 1024 entries, but
        subsequent sub-lists are longer (by a factor of 2 whenever the
        chunk-size gets bigger than an eighth of the number of primes in all
        earlier cache files).  Each cache-file's name expresses the range of
        indices it contains: this information is also present in the
        cache-file, along with the current value of _sparse.  The block of
        primes stored in the file is formatted to be readable on an 80-column
        display.  The data are stored in the file under the names

          at -- index, in self, of first prime in block

          to -- index, in self, of first prime after block

          sparse -- current _sparse list

          block -- self[at:to]
        """

        # print 'Caching primes'
        import os
        name = os.path.join(self.prime_cache_dir,
                            name) # implicitly tests isabs(name).
        tmpfile = name + '.tmp'

        new = self._next_high()
        while new < len(self._item_carrier):
            outfile = name + `self.__high_water` + '-' + `new` + '.py'
            if force or not os.path.exists(outfile):
                file = open(tmpfile, 'w')
                try:
                    file.writelines([
                    '"""Persistence data for primes module."""',
                    '\nat = ', `self.__high_water`,
                    '\nto = ', `new`,
                    '\nsparse = ', `self._sparse`,
                    '\nblock = ['])
                    _tabulate_block(file,
                                    self._item_carrier[self.__high_water:new])
                    file.write('\n]\n')

                finally: file.close()

                os.rename(tmpfile, outfile)

            self.__high_water = new
            new = self._next_high()

from study.maths.prime.cache import oldCache
from study.maths import __path__
from os.path import join
def find_factor(n, dir=join(__path__[0], 'primes'), C=oldCache):
    # Much quicker than using a cachePrimes object:
    primes = C(dir)
    for p in primes:
        if p is None: break
        if p * p > n:
            # print n, 'is prime'
            return None
        if n % p:
            last = p
            continue
        # print n, '/', p, '=', n/p
        return p

    # Non-contiguous extras - can't conclude primeness, but can rule it out:
    for p in primes:
        if n % p: continue
        # print n, '/', p, '=', n/p
        return p

    print n, '>', last, ' ** 2'
    raise OverflowError, 'Sorry, I cannot tell'
del oldCache, __path__, join

primes = cachePrimes()
factorise = primes.factorise
# The following should survive as prime.tool:
is_prime = primes.__contains__

def Sisyphus():
    """An iterator that'll ensure primes grows indefinitely.

    If you've got spare clock cycles to burn, and disk you'd be happy to fill
    up by expanding your cache of known primes, iterate Sisyphus.  For
    example:
      for it in Sisyphus: pass
    shall always find more work to do.  Note that this function is called once
    to create one eponymous iterator (making this function inaccessible
    thereafter), so you can interrupt an iteration of it at any point without
    losing (much) state; simply begin iterating it again later and it'll start
    off on the iteration in which you interrupted it.  Just do be aware that
    it may impose significant resource burdens on your computer - the Linux
    OOOM-killer is very likely to interrupt your python process and, quite
    possibly, its parents.

    The iterator this function returns is, in fact, the witness to a proof
    that there is no greatest prime: its i-th iteration takes the product of
    the first i primes, adds one and factorises the result.  Since this cannot
    have any of the first i primes as a factor (it's equal to 1 modulo each of
    them), all of its prime factors must exceed all of the first i
    primes.  This being true for all i, we may infer that, no matter how may
    primes we find, there are always some more to be found.\n"""

    n = 1
    for p in primes:
        n *= p
        yield n+1, primes.factorise(n+1) # all factors are > p
        primes.persist()

Sisyphus = Sisyphus()

# Packaging.
def Factorise(args=(), gather=None, cache=True):
        """Factorises an integer or each integer in a tuple.

        Optional arguments:

          args -- an integer, a tuple thereof or (if omitted) the empty tuple.

          gather -- dictionary to which to add results, or None (the default)
          to use a fresh empty dictionary: this is what Factorise() returns.

          cache -- flag, default is True.  By default, Factorise() will do a
          primes.persist() when it is finished: this will slow you down when
          it happens (writing a cache file can take a while once you know a
          lot of primes).  Set cache to some false value to suppress this (and
          remember to run primes.persist() at the end of your session).

        If args is a non-empty tuple, this returns a dictionary whose keys are
        the entries in the tuple, mapped to values which are what you get by
        passing the key to Factorise().  If args is the empty tuple, Factorise
        acts as if it'd been given the smallest natural number that the primes
        module doesn't yet know about.  If args is an integer, Factorise()
        behaves as primes.factorise(), so int(Factorise(())) will be this
        `least unknown', but it'll be known by the time you've evaluated that.

        See also: Prodict and primes.factorise().
        """

        try:
            if len(args) > 1: seq = args
            else:
                seq = args[0]
                # Now raise the right exception if (empty or) not a sequence:
                seq[0], seq[:0]

        except (TypeError, KeyError, IndexError, AttributeError):
            # Numeric argument:
            if args or args == 0: num = args
            else: num = primes.ask()

            if isinstance(num, (float, complex)):
                val = int(num)
                if val != num: raise TypeError('Factorising a non-whole number !', num)
                num = val

            result = primes.factorise(num, gather)

        else:
            # We did get a sequence argument: traverse it.
            if gather is None: result = {}
            else: result = gather
            for num in seq:
                try: result[num]
                except KeyError:
                    result[num] = Factorise(num, cache=False)

        if cache: primes.persist()
        return result

def factors(num):
    """Returns a dictionary whose keys are the factors of num.

    The value this dictionary associates with any factor is the factor's
    multiplicity as a factor of num, except for the key 1 (for which this is
    ill-defined) which gets the maximum of all the values in the
    dictionary. Thus, where defined, pow(k, factors(n)[k]) is a factor of n:
    for k not equal to 1, furthermore, pow(k, 1+factors(n)[k]) is not a factor
    of n.  Notice that factors(n)[n] = 1.

    If num is negative, -1 is listed with multiplicity 1, as is its product
    with each positive factor.  This is not wholly satisfactory, but it's not
    quite clear what's saner.  (Perhaps each negative factor's nominal
    multiplicity should be the largest odd number not greater than the
    matching positive factor's multiplicity.)\n"""

    if num < 0:
        num = -num
        result = {-1: 1}
    else: result = {}
    fact = primes.factorise(num)
    result[1] = max(fact.values())

    for key, val in fact.items():
        q = key
        items = result.items()  # before we enter the inner loop
        for i in range(val):
            top = val / (1+i)   # q is pow(key, 1+i)
            for k, v in items:
                result[k * q] = min(result[k], top)
            try: q = q * key
            except OverflowError: q = long(q) * key

    return result
