"""Cardan's solution of the cubic.
"""

_rcs_id_ = """
$Id: cardan.py,v 1.2 2003-07-26 12:46:24 eddy Exp $
"""

from math import cos, acos, pi
def Cardan(cube, square, linear, constant):
    """Solves a cubic polynomial equation.

    Takes four arguments, the coefficients of the cube, square, linear and
    constant terms in the cubic, respectively.  Finds all the inputs at which
    that cubic yields zero as output; returns these as a tuple.  Repeated roots
    are appropriately repeated.  Raises ValueError if there are no roots (or if
    *every* input yields zero output - i.e. all arguments are zero); this can
    only happen if the first argument is zero.

    To be specific: all entries in
        map(lambda x: ((a*x +b)*x +c)*x +d, Cardan(a, b, c, d))
    will be tiny.  See cardan(), which wraps Cardan and asserts this.
"""

    #print 'Cardan(%s, %s, %s, %s)' % (cube, square, linear, constant)

    if not cube:
        # deal with degenerate cases
        if not square:
            try: return (-constant * 1. / linear)
            except ZeroDivisionError:
                raise ValueError, 'Constant cubic has no roots (or everything)'
        disc = linear**2 -4. * square * constant
        if disc < 0:
            raise ValueError, 'Positive definite quadratic has no real roots'
        mid, gap = -linear * 1. / square, disc**.5 / square
        return mid+gap, mid-gap

    # deal with easy special case:
    if not constant:
        return (0,) + Cardan(0, cube, square, linear)

    # canonicalise:
    # u*x**3 +s*x**2 +i*x +c == 0 iff
    # x**3 +(s/u)*x**2 +(i/u)*x +(c/u) == 0 iff, with y = x +s/u/3, x = y - s/u/3,
    # (y - s/u/3)**3 +(s/u)*(y - s/u/3)**2 +(i/u)*(y - s/u/3) +c/u == 0 iff
    # y**3 +3*y*(s/u/3)**2 -(s/u/3)**3 -6*y*(s/u/3)**2 +3*(s/u/3)**3 +y*i/u -i*s/u/u/3 +c/u == 0 iff
    # y**3 -3*y*((s/u/3)**2 -i/u/3) +2*(s/u/3)**3 -i*s/u/u/3 +c/u == 0
    offset = square / 3. / cube # y = x + offset
    E = offset**2 - linear / 3. / cube
    F = linear * square / 3. / cube**2 -2 * offset**3 - constant * 1. / cube
    # so cube*(y**3 -3*E*y -F) = ((cube*x +square)*x +linear)*x +constant;
    # now solve y**3 -3*E*y -F = 0 and subtract offset from each y to get x.
    #print 'E, F = %s, %s' % (E, F)

    # deal with two more easy cases:
    if not F: # 0 = y**3 -3*E*y = y*(y**2 -3*E)
        if E < 0: return -offset, # only one
        E = (3*E)**.5
        return -offset, -E-offset, E-offset
    if not E: # y**3 = F
        return F**(1./3) - offset,

    disc = F**2 -4 * E**3
    if disc > 0: # only one root
        disc = disc**.5
        p, q = .5 * (F + disc), .5 * (F - disc)
        p, q = p**(1./3), q**(1./3)
        return p+q - offset,

    assert E > 0
    E = E**.5
    if disc < 0: # three roots; 
        a = acos(.5 * F / E**3) / 3
        #print 'angle:', a * 180 / pi
        return 2*E*cos(a) - offset, 2*E*cos(a + 2*pi/3) - offset, 2*E*cos(a + 4*pi/3) - offset

    # disc == 0, two roots, one repeated
    if F < 0:
        F = E - offset
        return F, F, -E-offset

    F = -E - offset
    return E-offset, F, F

def cardan(u, s, i, c):
    # debug wrapper on the above, doing the assertion
    ans = Cardan(u, s, i, c)

    for x, v in map(lambda x, u=u, s=s, i=i, c=c: (x, ((u*x +s)*x +i)*x +c), ans):
        if v:
            print '%s -> %s' % (x, v)
            assert abs(v) < 1e-14, '%s -> %s' % (x, v)

    return ans

_rcs_log_ = """
$Log: cardan.py,v $
Revision 1.2  2003-07-26 12:46:24  eddy
Refined the assertion.

Initial Revision 1.1  2003/07/26 12:37:25  eddy
"""