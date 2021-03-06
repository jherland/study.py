"""Permutations and related stuff.

Provides:
   Permutation(seq) -- class encapsulating a tuple as a permutation

   permute(seq, ind, ..., dex) -- composes permutations and applies them to seq.
   compose(ind, ..., dex) -- composes permutations (tolerates abbreviation).

   cycle(seq, [by=1]) -- shunts sequence cyclicly rightwards.
   order(seq, [cmp=cmp]) -- returns permutation s for which s(seq) is sorted.
   sorted(seq), sort(seq) -- deploy some of the above.

   unfixed(n) -- number of fixed-point-free permutations of n things; tends to n!/e.

See individual doc strings for further details of these; see Theory sections
of doc-strings for fuller discussion of permutations.  See also: Pascal.py for
factorial(), chose() and other combinatoric toys.

Note that Numeric python's numarray infrastructure provides for quite a lot of
the same things as the following.

See study.LICENSE for copyright and license information.
"""

from study.cache.property import Cached, lazyprop, lazyattr
from study.snake.sequence import Tuple, iterable
class Permutation (Tuple, Cached):
    """Immutable sequence type representing a permutation.

    Provides lazy attributes:
      .inverse -- the inverse of the permutation
      .sign -- the signature, +1 for an even permutation, -1 for an odd one
      .period -- number of times you must repeat self to get back where you started

    Provides methods:
      cycle([by=1]) -- cycle self by the given number of steps
      permute(seq [, seq...]) -- a.k.a. __call__, compose permutations

    Provides (class method) iterators:
      all(size) -- iterate over all permutations of range(size)
      fixed(size, fix) -- all(size) limited to those matching fix in its non-None entries

    Theory
    ======

    In what follows, I'll (orthodoxly treat any natural number as synonymous
    with the collection of smaller ones, effectively n = range(n), and) write
    r@p for permute(r, p):
        r@p = (: r[p[i]] <- i |len(p))

    Theorem (associativity):

        When sequences r, q, p allow formation of the composites (r@q)@p and
        r@(q@p), the two are equal.

        Proof:
            assert len(r@(q@p)) is len(q@p) is len(p) is len((r@q)@p)
            for i in len(p):
                assert ((r@q)@p)[i] is (r@q)[p[i]]
                                    is r[q[p[i]]]
                                    is r[(q@p)[i]]
                                    is (r@(q@p))[i]

            Each `is' just instanciates the definition of @ - QED.

    This simple algebraic truth allows us to skip the brackets and just write
    r@p@q and likewise for longer sequences of sequences, in so far as these
    allow formation of the composite.  Thus permute(row, ind, ..., dex) is
    row@ind@...@dex.  Note, however, that r@q might not be allowed even when
    r@(q@p) is: e.g. when r's length appears as an entry in q, but its
    position in q doesn't appear in p; if all other entries in q are valid
    indices into r, q@p's entries will all be valid indices into r.

    Definition:
        A sequence, p, is described as a permutation if it contains all the
        entries of range(len(p)).

    Note that, given its length, this leaves it with no room to repeat any of
    its entries.  If you ever want to discuss infinite permutations, you'll
    need to define them explicitly as one-to-one mappings; but for finite
    permutations, the `pidgeon-hole principle' makes the above sum up
    `one-to-one' neatly.\n"""

    __upnew = Tuple.__new__ # takes derived type as first arg
    def __new__(cls, perm): # automagically an @staticmethod
        """Create a permutation.

        Single argument must be a sequence of natural numbers in which no number
        is repeated and every natural less than each entry is present in the
        sequence.  Raises ValueError otherwise; see .isa() if you only want to
        test validity.  For convenience constructors, see .identity() and
        .fromSwaps().\n"""
        perm = tuple(perm) # so we only read perm once, in case it's an iterator.
        if not cls.isa(perm):
            raise ValueError('Is not a permutation', perm)
        return cls.__upnew(cls, perm)

    @classmethod
    def identity(cls, n, cycle=0):
        """Construct an identity permutation.

        Required argument, n, is a natural number.  Optional second argument,
        cycle, defaults to 0.  If given, it is the number, c, of steps to
        cycle the identity, to get a cyclic permutation which moves the last c
        entries in a list to the front, so that the (previously) first entry
        ends up at index c.  It is reduced modulo n.

        Returns the identity permutation on naturals less than n, duly cycled
        if requested.\n"""
        seq = range(n)
        if cycle:
            cycle = -cycle % n
            seq = seq[cycle:] + seq[:cycle]
        return cls(seq)

    @classmethod
    def fromSwaps(cls, *ps):
        """Construct a permutation by swapping entries.

        Each argument must be a pair of naturals; an identity permutation is
        constructed and, for each such pair, its entries at the two positions
        indexed by the pair are swapped.\n"""
        ans, n = [], 0
        for i, j in ps:
            if i == j: continue
            if min(i, j) < 0:
                raise ValueError('Invalid permutation index', i, j)

            m = max(i, j) + 1
            if m > n:
                ans += range(n, m)
                n = m

            ans[i], ans[j] = ans[j], ans[i]

        return cls(ans)

    def __call__(self, *seqs):
        """Apply permutation.

        First argument is a list to be permuted; all subsequent arguments are
        permutations (or sequences representating permutations) of this list's
        length; self(row, ind, ..., dex)[i] is
        row[ind[...dex[self[i]]...]]. See permute().  The name permute is
        provided as an alias for function call, mainly for ease of reading
        when a function yields a permutation which is being called;
        order(seq).permute(seq) is more readable, IMO, than order(seq)(seq).\n"""
        return permute(*seqs + (self,)) # forward reference; see after class

    permute = __call__

    @classmethod
    def _permutation_(cls, what):
        """Pseudo-constructor for derived classes to over-ride if needed.

        Used by instance methods of this class to build new instances of this
        class; may be called with the same arguments as __new__ (q.v.).  Any
        derived class whose __init__ or __new__ doesn't accept the same
        signature should over-ride this with something suitable that does.\n"""
        return cls(what)

    @lazyattr
    def inverse(self):
        """Inverts the permutation.

        Computes the inverse of self: that is, if p is a permutation and q =
        p.inverse, then p@q and q@p are the identity permutation, id =
        range(len(p)), of the same length.

        Computed by filling in q[p[i]] as i for each i.  Checking that self is
        a permutation is most readilly done by verifying that the inverse we
        compute does actually get an entry in each position; the pidgeon-hole
        principle then ensures the rest.

        Theory
        ======

        Given a sequence, row, and a permutation, p, of the same length, row@p
        is described as `a permutation of' row: it contains the same entries
        as row but in a different order; any repeated entry in row is repeated
        just as often in a permutation of row; permutations of row have the
        same length as row.  A permutation of a permutation is thus a
        permutation with the same length.

        From the definition of permute, the identity permutation of any given
        length is trivially a right identity: r@id == r for any sequence, r,
        of the given length.  Likewise, for any sequence, p, of entries in id,
        e.g. any permutation of id, id@p == p; thus id is a left identity on
        permutations of id.  Thus, as a binary operator on permutations of
        some given length, @ has, as (both left and right) identity, the range
        of the given length.

        Using q = order(p), p@q is a sorted permutation of p; so, when p is a
        permutation, p@q is sorted and has the same entries as p, which has
        the same entries as id, which is sorted; so p@q == id, making q a
        right-inverse for p.

        Theorem:
            If @ is an associative binary operator closed on some collection,
            P - i.e. for any a, b in P we have a@b in P - having an identity,
            id, in P - i.e. for any a in P, id@a = a = a@id - and (having)
            right-inverses for all elements of P, then these right-inverses
            also serve as left inverses.

            Proof:
                Given p in P, consider its right-inverse, q, and q's
                right-inverse, d: so p@q = id = q@d, whence p = p@id = p@q@d =
                id@d = d, so q@p = id.  QED.

        Our composition, @, meets the preconditions of this, with P the
        collection of permutations with the same length as p, hence order()
        would, on permutations, serve as inversion.  However, the
        implementation here is more efficient than calling order.\n"""

        n = len(self)
        ans = [ None ] * n

        while n > 0:
            n -= 1
            assert 0 <= self[n] < len(self) and ans[self[n]] is None
            ans[self[n]] = n
        # The .isa() check on construction ensures the last and next assertions.
        assert None not in ans

        ans = self._permutation_(ans)
        assert ans(self) == range(len(self)) == self(ans)
        assert ans == order(self)
        assert ans.sign == self.sign
        ans.inverse = self
        return ans

    @lazyprop
    def sign(self):
        """The signature of the permutation.

        The signature homomorphism is the unique non-fatuous mapping from
        permutations to the multiplicative group {+1, -1} which respects the
        group structure (that is, sign(s@t) = sign(s)*sign(t) for all
        permutations s, t; and at least some permutations have sign -1).  Its
        value is entirely determined by the fact that every transposition
        (i.e. a permutation that simply swaps two elements) has sign -1; this
        is used in computing the value.\n"""

        mess, sign, i = list(self), +1, len(self)
        while i > 1:
            i -= 1

            if i != mess[i]:
                sign, j = -sign, mess.index(i)
                assert j < i
                mess[i], mess[j] = mess[j], mess[i]

        assert mess == range(len(self))
        return sign

    @lazyprop
    def period(self):
        """Computes the period of the permutation.

        See http://www.research.att.com/~njas/sequences/A000793 and
        http://mathworld.wolfram.com/LandausFunction.html for Landau's
        function, which gives the maximal period among permutations of each
        length.  This is equally the maximum, over partitions of the length,
        of the lowest common multiple of the lengths of the parts.  Note that
        this method may fail to terminate if self is not actually a
        permutation.\n"""

        q, i = compose(self, self), 1 # Invariant: q = self**(1+i)
        while q != self:
            q, i = compose(q, self), 1+i
        return i # self == self**(1+i) so self**i is an identity

    def cycle(self, by=1):
        return self.identity(len(self), by).permute(self)

    @staticmethod
    def isa(seq):
        """Test whether seq is a permutation.

        Single argument, seq, is a sequence: it must support len() and 'is in'
        tests for its entries.  The result is true precisely if the entries in
        seq are, in some order, the valid (forward) indices into seq.  In
        particular, for each i in seq, seq[i] must be a valid expression.

        Note that this is vastly more efficient than collecting up the outputs
        of .all(len(seq)) and testing whether seq is one of them, even if you
        reuse the collection to do this for many sequences of the same length.\n"""

        check = range(len(seq))
        try:
            for i in seq:
                seq[i] # IndexError on bad entry or TypeError on bad seq

                if i < 0 or check[i] is None: # negative or duplicate
                    return False
                check[i] = None

        except (IndexError, TypeError): # entry that doesn't belong
            return False

        return all(x is None for x in check) # we did hit each entry

    @classmethod
    def fixed(cls, size, fix):
        """Iterator over permutations of a given length with certain fixed entries.

        Required arguments:
          size -- length of the permutations
          fix -- sequence whose non-None entries all permutations should match

        Returns an iterator over all permutations of the given size that can
        be obtained by filling in the None entries of fix and, if its length
        is less than size, extending it to the requested length.\n"""

        fix = tuple(fix)
        js = filter(lambda j: j is not None, fix)
        if js and (max(js) >= size or min(js) < 0):
            raise ValueError('Bad fixed entry in permutation template',
                             filter(lambda i, m=size: i >= m or i < 0, js), fix, size)
        if len(fix) < size: fix += ( None, ) * (size - len(fix))

        # numbers we can use to fill the gaps:
        vs = filter(lambda i, js=js: i not in js, range(size))
        # indices at which the gaps appear:
        ns = filter(lambda n, f=fix: f[n] is None, range(size))

        for perm in cls.all(len(vs)):
            ans = list(fix)
            for n, v in map(lambda *x: x, ns, perm(vs)): ans[n] = v
            assert None not in ans
            yield cls(ans)

    # for a rather elegant application, see queens.py's derived iterator
    @classmethod
    @iterable
    def all(cls, size):
        """Iterator over permutations of given length.

        Single required argument is the length of the permutations.
        Illustrative usage::

            for it in study.maths.permute.Permutation.all(len(word)):
                anagram = ''.join(it(word))
                if dictionary.has_key(anagram): print anagram

        Cycles through all the permutations of [0,...,n-1], a.k.a. range(n),
        for some n; does so in lexicographic order: that is, a permutation p
        shall be yielded sooner than a permutation q precisely if, in the
        first position at which they differ, p[i] is less than q[i].

        Note that collecting up all of the outputs of this may use very large
        amounts of memory.  If all you need to do is test whether some sequence
        is one of these outputs, see .isa() instead.

        Theory
        ======

        To iterate over permutations it suffices to specify a well-ordering of
        permutations - i.e. a choice of one of them as `first', combined with
        a `next' opertion which will, starting from the first, iterate over
        all candidates.  An obvious well-ordering to use is the one obtained
        from `lexicographic order', in which one compares two sequences by
        finding the first entry in which they differ and comparing those.

        Among permutations of any given length, this makes the identity `less
        than' all others, so it's our `first' permutation.  Note that a
        decreasing (reverse-sorted) sequence is later than any other sequence
        with the same entries.  To find the `next' permutation, in the
        lexicographic order, one must change as late a chunk of the permutation
        as possible.

        To this end, find the longest decreasing tail of the permutation: no
        shuffling of only that can yield a later permutation, so our next
        permutation must bring in at least the previous entry.  Since the
        previous entry (by construction) is less than the first entry in the
        decreasing tail, shuffling it into the tail can produce a later
        entry.  A little thought will reveal that we should swap it with the
        smallest entry in the tail bigger than it, then reverse
        (i.e. forward-sort) the thus-amended tail.  This is the step used by
        this iterator.\n"""

        if size < 0: raise StopIteration # Nothing to do :-)

        row = range(size)
        while True:
            yield cls(row)

            i = size - 1
            while i > 0 and row[i - 1] > row[i]: i -= 1
            if i < 1: # row is entirely in decreasing order
                raise StopIteration # yielded all permutaitons already

            i, j = i - 1, size - 1
            assert row[i] < row[i + 1]

            # row[i+1:] is in decreasing order but row[i] < row[i+1]
            # Find smallest row[j] > row[i] with j > i:
            while row[j] < row[i]: j -= 1
            # swap i <-> j:
            row[j], row[i] = row[i], row[j]

            # row[i+1:] is still in decreasing order: reverse it
            i, j = 1 + i, size - 1
            while i < j:
                row[j], row[i] = row[i], row[j]
                i, j = 1 + i, j - 1

    # TODO: devise an alternate-order iterator which ensures each index appears
    # in each position roughly once per n steps.  Useful, e.g., for a "taking
    # turns to chose which chores to do" rota,
    # c.f. http://www.chaos.org.uk/~eddy/when/2009/squalor.html

    # TODO: add random permutation class method
del Cached, lazyprop, lazyattr, iterable

def Iterator(size, P=Permutation): # backward compatibility
    """Redundant alias for Permutation.all"""
    return P.all(size)

def permute(*indices):
    """Returns row permuted by a sequence of indices.

    All arguments must be sequences.  The first is the row to be permuted;
    each subsequent argument will be used to permute the row; entries in each
    argument after the first are read as indices into the preceding argument.

    Returns sequence with
      permute(row, ind, ..., dex)[i] == row[ind[...dex[i]...]],

    which may be understood as the composite of the sequences, read as
    functions (see Theory sections Permutation's doc-strings).\n"""

    indices, ans = indices[:-1], indices[-1] # IndexError if no sequences given !
    classy = isinstance(indices[0], Permutation)

    while indices:
        indices, last = indices[:-1], indices[-1]
        ans = map(lambda i, r=last: r[i], ans)

    if classy:
        try: return Permutation(ans)
        except ValueError: pass

    return ans

def compose(*perms):
    """Composes arbitrarily many permutations.

    Presumes that all arguments are permutations and interprets each as
    coinciding with the identity beyond its length - e.g. (1, 2, 0) is
    implicitly (1, 2, 0, 3, 4, 5, 6, ...) - so as to resolve any differences
    in length.  Otherwise, functionally equivalent to permute, though
    implemented with the two loops rolled out the other way (to implement the
    identity-default behaviour by catching IndexErrors)."""

    try: n = max(map(len, perms))
    except IndexError: n = 0 # Permutation([]) is an implicit identity.

    result, i = [], 0
    while i < n:
        j, k = len(perms), i
        while j > 0:
            j -= 1
            try: k = perms[j][k]
            except IndexError: pass
        result.append(k)
        i += 1

    return Permutation(result)

def cycle(row, by=1):
    """Permutes a sequence cyclicly.

    Optional argument, by, has a default of 1: it is the position to which the
    first item in the sequence is to be moved; a portion of this length is
    moved from the end of the sequence to the start; all other entries in the
    list are moved down the list this far.

    For example: cycle((0, 1, 2, 3, 4), 2) yields (3, 4, 0, 1, 2). """

    by = -by % len(row)
    return row[by:] + row[:by]

def order(row, cmp=cmp, key=None, reverse=False):
    """Returns a permutation which will sort a sequence.

    Required argument, row, is a sequence (supporting len() and indexing)
    whose order is to be determined; this function makes no attempt to modify
    it, so it may be immutable.  Takes the same optional parameters as the
    built-in sorted() and list.sort():

      cmp -- comparison function (default: built-in cmp)
      key -- transformation of elements (default: None, to use untransformed)
      reverse -- whether to reverse the result (default: False)

    The result is a permutation of range(len(row)) for which the sequence
    order(row).permute(row) is sorted, contains each entry of row exactly as
    often as it appears in row and has the same length as row.  If order is
    also passed cmp, key and reverse, the same holds but the notion 'sorted'
    is suitably revised.  With rev = -1 if reversed else +1, for any i, j in
    range(len(row)), with seq = order(row, cmp, key, reverse).permute(row):
    when cmp(key(seq[i]), key(seq[j])) is non-zero it is cmp(i, j) * rev.  See
    Permutation.inverse, above, for discussion of what this implies when row
    is a permutation.

    If row has been obtained as r@q, then p = order(row) is a permutation with
    the same length as q and makes r@q@p a sorted list with this same length,
    making q@p a useful replacement for q: it contains the same entries as q,
    but r@(q@p) is sorted.  This is exploited in order()'s recursive calls to
    itself, which model the qsort algorithm.\n"""

    n = len(row)
    if n < 2: return range(n)
    pivot = row[0]
    if key: pivot = key(pivot)
    low, mid, high = [], [ 0 ], []

    # Partition the values:
    while n > 1:
        n -= 1
        here = row[n]
        if key: here = key(here)
        sign = cmp(here, pivot)
        if sign > 0: high.append(n)
        elif sign < 0: low.append(n)
        else: mid.append(n)

    if reverse: low, high = high, low
    if len(low)  > 1: low  = order(permute(row, low),  cmp, key, reverse).permute(low)
    if len(high) > 1: high = order(permute(row, high), cmp, key, reverse).permute(high)
    return Permutation(low + mid + high)

def sorted(row, cmp=cmp):
    return order(row, cmp).permute(row)

def sort(row, cmp=cmp):
    row[:] = sorted(row, cmp)

# This is number theory, but it's about permutations.
def unfixed(num, cache=[1]): # Need an initial value to seed the iteration.
    # The identity permutation on empty (i.e. 0) has 0 fixed points, so qualifies ...
    """Returns the number of permutations of num without fixed points.

    Subtracting from num!, we get the sum over 0 < i <= num of: the number of
    ways of chosing i things to keep fixed, times the number of ways of
    permuting the remaining (num-i) items without any of these staying
    fixed.  Indeed, num! = sum(: chose(num,i) * unfixed(num-i) <- i :1+num) as
    every permutation of num keeps i items fixed, for some i, while permuting
    the remaining i items without (further) fixed points.  This yields (as
    chose(num,i) = chose(num, num-i) and (1+num| num-i <- i |1+num) is a
    permutation)

        num! = sum(: chose(num, i) * unfixed(i) <- i :1+num)

    Whence, as 1 = chose(num, num)
        unfixed(num) = num! - sum(: chose(num,i) * unfixed(i) <- i :num)

    I find that unfixed(num) * e - factorial(num) gets rapidly close to 0.  We
    get a glitch in the sequence of values at 17 and 19, arising from rounding
    of the floating-point product, between the initial slide towards 0 and the
    subsequent exact zero.  Now, factorial(num) / e is sum(: pow(-1,i) * num!
    / i! <- i :natural) which is, in turn, sum(: pow(-1,i) * num! / i! <- i
    :1+num) plus something smaller than 1.

    So, consider any natural N for which, for each num in N,
        unfixed(num) = sum(: pow(-1,i)*num!/i! <- i :1+num).
    An example would be N = 0, since there is no num in 0 = {}.  In such a
    case,

    unfixed(N)
      = N! - sum(: chose(N,i) * sum(: pow(-1,j)*i!/j! <- j :1+i) <- i :1+N)
        # substitute n = N - i + j, so i = N - n + j:
      = N! - sum(: sum(: N! / (n-j)! * pow(-1,j) / j! <- j :n) <- n-1 :1+N)
      = N! - sum(: N!/n! * sum(: chose(n,j)*pow(-1,j) <- j :n) <- n-1 :N)
      = N! + sum(: N!/n! * pow(-1,n) <- n-1 :N)
      = sum(: pow(-1,i) * N! / i! <- i :1+N)

    Thus unfixed has this form for num=N also, so that 1+N has the same
    property we demanded of N and, inductively, the equation holds for all
    num.  Furthermore, we have unfixed(N) = N*unfixed(N-1) + pow(-1,N) which
    gives us a nice cheap way to evaluate unfixed; which clearly indicates
    that unfixed(N) must grow proportional to factorial in the long run (as
    witnessed in the clue which lead me here, exp(-1) being the constant of
    proportionality).\n"""

    # Deal with boundary case
    if num < 0: return 0
    # Avoid computation when we can
    if num >= len(cache): # Can't just look it up: need to extend cache.
        # Initialise for loop:
        N, last = len(cache), cache[-1]
        if N % 2: sign = -1
        else: sign = 1

        # grow cache until it's long enough
        while num >= N:
            #    u(N) = N * u(N-1) + pow(-1,N)
            next = N * last + sign
            cache.append(next)
            N, sign, last = N+1, -sign, next
        # we should now be happy.

    return cache[num]
