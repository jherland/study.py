"""Integration made easy.

$Id: integrate.py,v 1.1 2002-10-06 14:01:04 eddy Exp $
"""

class Integrator:
    """Base class for integrators.

    Provides crude trapezium rule integrator, which derived classes might wish
    to over-ride.  More importantly, defines an API for integrators:
        between(start, stop) -- integrates over an interval
        before(stop) -- as between, but with minus infinity as start
        beyond(start) -- as between, but with plus infinity as stop

    Both before() and beyond() presume that they're integrating a `tail' of a
    distribution: to compute an integral between one side of a distribution's
    mode and infinity on the other side, it is probably wisest to call between()
    on the given bound and a more-or-less arbitrary position on the same side of
    the mode as the infinity in question, then to use before() or beyond() to
    compute the remainder, using between()'s output as offset (see below).

    All three integrator methods take an optional argument, test, following the
    given required arguments; and an optional keyword argument, offset, after
    that.  These are used in deciding when the integral has been determined
    accurately enough: after each iteration, the integrator calls test with the
    change in its estimate of the integral as first argument and, as second
    argument, the new estimate, optionally with offset added to it.  If the
    change is small enough that further refinement is a waste of time, test
    should return true.  The integrator will then return the given estimate
    added to an error bar whose width is the last change.

    By default, the code is geared up to deal with values of class Quantity (see
    basEddy.quantity) and, indeed, the integrators return Quantity()s.  If the
    first estimate at the integral (plus optional offset) has a positive .width
    attribute, it is presumed to be a Quantity() and the default test simply
    compares the change in estimate with the .width of the new estimate; if the
    change is within this existing error bar, it is taken to be small enough.
    In the absence of .width, or if the .width is not positive, the default test
    simply looks to see whether the change in estimate is smaller than 1e-6
    times the estimate (plus optional offset); in the absence of an offset, this
    last test will work poorly if the integral should yield zero. """

    def __init__(self, func, width=None):
	"""Initialises an integrator.

	Required first argument is the function to be integrated.
	This will be stored as self.integrand.

	Optional second argument, width - only needed if .beyond() or .before()
	is liable to be called with bound zero - is a `unit' change in input.
	It should ideally be approximately the difference between highest and
	lowest inputs for which the integrand differs significantly from 0;
	e.g. if func describes a Gaussian distribution with variance 1, a width
	of about 5 would be prudent. """

	self.integrand = func
	if width is not None: self.__unit = abs(width)

    def between(self, start, stop, test=None, offset=None):
	"""Integral over a range.

	Two required arguments, start and stop, give the bounds of the range.
        Also accepts the usual optional tolerance specifiers, test and offset:
        see class doc for details. """

        return self.__between(start,
                              (stop - start) * 1., # avoid integral type gotchas ...
                              (self.integrand(start) + self.integrand(stop)) * .5,
                              test, offset)

    def before(self, stop, test=None, offset=None):
        """Integration from minus infinity.

        Equivalent to between() with start set to a value less than any at which
        self's distribution is distinguishable from zero.  Required argument is
        the upper bound of the integral; also accepts the usual optional
        tolerance specifiers, test and offset: see class doc for details. """

	return -self.__outwards(stop, -self.__step(stop), test, offset)

    def beyond(self, start, test=None, offset=None):
        """Integration to plus infinity.

        As before() but required argument is the lower bound of integration, the
        upper bound being greater than any value at which self's distribution is
        distinguishable from zero. """
	return self.__outwards(start, self.__step(start), test, offset)

    # hairy implementation follows: no further exports.

    from basEddy.quantity import tophat
    def __blur(mid, spread, H=tophat): return mid + H * spread
    del tophat
    # __blur and __gettest will be del'd shortly ... they're *not* methods
    def __gettest(eg,
                  microclose = lambda d, n: abs(d) <= 1e-6 * abs(n),
                  bywidth = lambda d, n: abs(d.best) <= n.width):
        """Returns a sensible tolerance test.

        Where between, below and beyond are not given a tolerance test function,
        this determines one given an example value kindred to the final output
        (plus optional offset) relative to which the tolerance is computed. """

        try:
            w = eg.width
            try:
                while eg is not eg.best: eg = eg.best
            except AttributeError: pass

            if w > 0 * eg: return bywidth

        except AttributeError: pass

        return microclose

    # __sum is also del'd imminently
    def __sum(row, plus=lambda a, b: a+b): return reduce(plus, row)

    def __between(self, start, gap, edge, test, offset,
                  blur=__blur, gettest=__gettest, sum=__sum):

        now = edge * gap # first crude estimate

	# get advertised default for offset:
	if offset is None:
            try: offset = now - now.best
            except AttributeError: offset = now * 0

        # get advertised default test:
        if test is None: test = gettest(offset + now)

        n = 1
	while 1:
	    n, was = 3 * n, now
	    h = gap / n
	    now = (sum(map(lambda i, b=start, s=h, f=self.integrand: f(b+i*s),
			   range(1, n))) + edge) * h

            dif = now - was
            if test(dif, now + offset): return blur(now, dif)

    del __sum

    def __outwards(self, bound, step, test, offset,
                   blur=__blur, gettest=__gettest):
	small = abs(self.integrand(bound)) / 1e3
	while self.__probe(bound, step) < small: step = step / 7.
	while self.__probe(bound, step) > small: step = step * 7
        if test is None: test = gettest(small * step)

        next = bound + step
	total, bound = self.between(bound, next, test, offset=offset), next
        if offset is None:
            try: offset = total - total.best
            except AttributeError: offset = 0 * total

	while 1:
	    step = step * 3
            next = bound + step
	    more = self.between(bound, next, test, offset=total + offset)
	    total, bound = total + more, next
            if test(more, total + offset): return blur(total, more)

    del __blur, __gettest

    # need better initial step than abs(bound) ... bound could be zero.
    def __step(self, bound):
	try: return self.__unit
	except AttributeError: pass
	try: ans = abs(bound.copy(lambda x: 1)) # for Quantity()s
	except (AttributeError, TypeError): ans = abs(bound)
	if ans: self.__unit = ans
	else: raise ValueError, \
	      'Integrator needs a width parameter for .before(0) or .beyond(0)'
	return ans

    import math
    def __probe(self, base, scale,
		samples=[1, math.exp(1/math.pi), math.sqrt(2.0), 2, math.e, 3, math.pi]):
	"""Scale of integrand's values for inputs base + of order scale. """
	return max(map(lambda x, f=self.integrand, s=scale, b=base: abs(f(b + x*s)), samples))
    del math

_rcs_log = """
 $Log: integrate.py,v $
 Revision 1.1  2002-10-06 14:01:04  eddy
 Initial revision

"""