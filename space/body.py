# -*- coding: iso-8859-1 -*-
"""The various types of heavenly body.

$Id: body.py,v 1.1 2005-03-12 14:52:15 eddy Exp $
"""

from basEddy.units import Object, Quantity, second, metre, turn, pi

class Body (Object):
    __upinit = Object.__init__
    def __init__(self, name, **what):
        apply(self.__upinit, (), what)
        self.name = name
	try: what['orbit'].centre.satellites.insert(None, self)
	except (KeyError, AttributeError):
            print 'Failed to insert', name, "in satellite list of its orbit's centre"

    def __str__(self): return self.name
    __repr__ = __str__

    def _lazy_get_Bode_(self, ignored, cache=[]):
        try: gen = cache[0]
        except IndexError:
            from space.Bode import Bodalizer
            gen = Bodalizer
            cache.append(gen)

        return gen(self.satellites)

    class _lazy_get_satellites_:
        """Carrier-object for satellites of a heavenly body."""

        def __init__(self, centre, ignored):
            """Construct a new satellite-array.

            All it actually remembers of the centre it serves is a call-back
            method to purge any lazily-computed attributes whose computation
            depends on the satellites.  In practice, the central body's lazy
            reset method is sensible for this, though ideally a more selective
            purge could be used."""

            self.__cb, self.__carry = centre._lazy_reset_, []
            # borrow from carry (in so far as lists have owt to borrow)
            self.borrow(self.__carry)
            # but override insert and append, block reverse and sort.

        def __getitem__(self, ind):
            if ind < 0 or ind >= len(self.__carry): raise IndexError, ind
            return self.__carry[ind]

        # things we should be borrowing from __carry, but py 2.1 doesn't let us:
        def __repr__(self): return `self.__carry`
        def __str__(self): return str(self.__carry)
        def __len__(self): return len(self.__carry)

        def insert(self, ind, what):
            """Inserts what into self: ind is a hint at where to put it.

            Arguments:

              ind -- suggested position for new entry, or None.
              what -- new entry

            Actual position used will ensure that self's entries are ordered by
            entry.orbit.radius in increasing order.  Using an ind of None will
            skip trying to use it as a hint and get straight on with looking for
            the right place to put it."""

            # Look up much-used stuff once:
            row, rad = self.__carry, what.orbit.radius

            if not row or row[0].orbit.radius > rad:
                lo = hi = 0
            else:
                # Prepare for binary chop:
                hi, lo = len(row), 0
                # what belongs at an index i with lo < i <= hi

                if ind is not None:
                    # Use ind as a hint:
                    if hi > ind > 1 and row[ind-1].orbit.radius < rad: lo = ind - 1
                    if hi > ind >= 0 and row[ind].orbit.radius > rad: hi = ind

            # Use binary chop between positions hi and lo in row:
            while lo + 1 < hi:
                mid = (lo + hi) / 2
                if row[mid].orbit.radius > rad: hi = mid
                else: lo = mid

            row.insert(hi, what)
            if isinstance(what, discreteBody):
                self.__cb()

        def append(self, what):
            """Inserts what in self, taking hint that it belongs at end."""
            self.insert(len(self.__carry), what)

        # Don't let anyone mess with the ordering:
        def reverse(self):
            raise ValueError, 'Trying to reverse a rightly-ordered list.'

        def sort(self, func=None):
            raise ValueError, 'Trying to shuffle a neatly-ordered list.'

from space.common import Spin, Orbit

class discreteBody (Body):
    def _lazy_get_tidal_(self, ignored, zero = 0 / second**2, Q=Quantity):
        """Returns strength of tidal stresses near self.

        Made up of three terms:
          * tidal stresses due to the body's own satellites (if any).
          * tidal stresses due to whatever the body orbits (if any),
          * ambient tidal stresses, taken as the orbit.centre.tidal

        The last two are provided (as .ambient and .orbital) as attributes of
        the composite, which is obtained by presuming that the various
        contributions are all uncorrelated in phase - i.e. sometimes they
        interfere with one another constructively, sometimes destructively - and
        computed as the largest term plus a `fuzzy' term resembling `+/- each of
        the remaining terms'. """

        row = [] # in which to collect up the contributions

        try: ambient = self.orbit.centre.tidal
        except AttributeError: ambient = zero
        else:
            # but ignore the satellite contribution to this ...
            ambient = ambient.orbital + ambient.ambient
            row.append(ambient)

        try: orbital = self.orbit.tidal
        except AttributeError: orbital = zero
        else: row.append(orbital)

        for moon in self.satellites:
            try: mine = moon.orbit.tidal * moon.mass / self.mass
            except AttributeError: pass
            else: row.append(mine)

        # That's gathered together all contributions.
        if row:
            row.sort()
            row, big = row[:-1], row[-1]
        else: big = zero

        for it in row:
            big = big + Q(zero, sample = (it, -it))

        return Q(big, ambient = ambient, orbital = orbital)

    def _lazy_get_tide_(self, ignored):
        """Returns strength of tidal forces across self.

        This is just the tidal stress times the body-radius.
        """
        return self.tidal * self.surface.radius

    def _lazy_get_density(self, ignored):
        return self.mass / self.surface.volume

    def _lazy_get_binding_(self, ignored):
        """Gravitational binding energy

        To remove a shell of thickness dr from the surface of a body of radius r
        and density rho takes energy dE = 4*dr*pi*r*r*rho*G*M/r where M is
        (4*pi/3)*rho*r**3, so dE = (4*rho*pi)**2 * G/3 * r**4 * dr so shredding
        the body will take the integral of this from 0 to radius,
        i.e. (4*rho*pi)**2 * G/15 * r**5 plus any energy needed to break the
        mass up into the dust assumed by this.

        Substituting back to use M rather than rho we have 3*G*M*M/r/5\n"""

        return .6 * self.mass * self.GM / self.surface.radius

    from const import Cosmos
    def _lazy_get_mass_(self, ignored, G=Cosmos.G):
        return self.GM / G

    def _lazy_get_GM_(self, ignored, G=Cosmos.G, Q=Quantity):
        row = [] # assorted estimates
        try: GM = self.surface._GM
        except AttributeError: pass
        else: row.append(GM)

	for sat in self.satellites:
            if isinstance(sat, discreteBody):
                try: GM = sat.orbit._GM
                except AttributeError: pass
                else: row.append(GM)

        try: mass = self.mass
        except AttributeError: # e.g. thanks to Lazy's recursion detection ...
            try: mass = self.surface.volume * self.density
            except AttributeError: # ditto
                from basEddy.sample import Weighted
                if row: best = Weighted(row).median()
                else: raise AttributeError(ignored, 'no data available from which to infer')
                row.remove(best)
            else: best = mass * G
        else: best = mass * G

	return Q(best, sample=row)

    def _lazy_get_Swarzchild_(self, ignored, S=Cosmos.Swarzchild):
        return self.mass * S

    del Cosmos

    def orbital(self, radius, ecce=0, tp=2*pi):
        """The spin of the relevant orbit.

        Required first argument is the radius of the orbit; optional second
        argument is its eccentricity, defaulting to 0.  Result is a Spin object
        describing the angular velocity of the orbit.

        Present implementation ignores eccentricity, to get: GM/R/R = w.w.R so w
        = sqrt(GM/R/R/R) and T = 2.pi/w.  """

        return Spin(pow(radius**3 / self.GM, .5) / tp)

    def __radius(self, given, time=second, length=metre, angle=turn, tp=2*pi):
        try: given + length # radius
        except TypeError: pass
        else: return given, None

        try: given + time/angle # frequency; convert to period
        except TypeError: pass
        else: given = angle / given

        try: given + time # period
        except TypeError: pass
        else: return (self.GM * (given / tp)**2)**(1./3), given

        raise ValueError('how does that specify an orbit ?', given)

    def orbiter(self, given, **what):
        radius, period = self.__radius(given)
        if period is None:
            return apply(Orbit, (self, radius), what) # accept Orbit's guestimate of spin

        return apply(Orbit, (self, radius, Spin(period)), what)

    def _lazy_get_synchronous_(self, ignored):
	"""Synchronous orbit. """
	name = "Synchronous orbit about %s" % self.name
	return Orbit(self, self.surface._sync, self.surface.spin, 0,
		     name = name,
		     __doc__ = """%s

This is the orbit in which a satellite remains permanently above the same point
on the surface of %s as it rotates. """ % (name, self.name))

    def _lazy_get_Roche_(self, ignored, factor=2.46):
        """The Roche limit

        This is the minimum distance at which a fluid satellite, influenced by
        its own gravitation and that of the central mass, can be in equilibrium.
        For a satellite of zero tensile stress and the same mean density as its
        primary, in a circular orbit around its primary, this critical distance
        is 2.46 times the radius of the primary. [NASA]\n"""

        return self.surface.radius * factor

    class rowbok:
        def __init__(self): self.__bok = {}
        def __getitem__(self, key):
            assert key in "+-"
            try: return self.__bok[key]
            except KeyError: pass
            ans = self.__bok[key] = []
            return ans

    def _lazy_get_Lagrange_(self, ignored, klz = rowbok):
        """Inhabitants of Lagrangian / Trojan points.

        I'm presently using self.Lagrange as a dictionary recording the bodies
        in the Lagrangian / Trojan positions on self's orbit (see NASAtrojan(),
        below).  This may change ...

        Presently, the only keys of self.Lagrange will be '+' and '-' denoting
        the leading and following stable points, respectively.\n"""

        return klz()

    del rowbok

del Spin

del Object, Quantity, second, metre, turn, pi
from space.common import Round

class Hoop (Body, Round):
    # used for gaps and ring arcs, and as base for Ring.
    __upinit = Body.__init__
    def __init__(self, name, centre, radius, tilt=0, eccentricity=0, **what):
        # Assume rings move circularly, since Saturn's rings look like they do ...
        if tilt: tilt = tilt * tophat
        o = what['orbit'] = Orbit(centre, radius, None, eccentricity, tilt)
        # It's important that we pass orbit via what ...
        apply(self.__upinit, (name,), what)
        self.borrow(o)

del Orbit, Round

class Ring (Hoop):
    __upinit = Hoop.__init__
    def __init__(self, name, centre, inner, outer, tilt=0, eccentricity=0, **what):
        apply(self.__upinit, (name, centre,
                              (inner.best + outer.best) * .5 + (outer.high - inner.low) * tophat,
                              eccentricity, tilt),
              what)

class Planetoid (discreteBody):
    # any vaguely spherical object that orbits a star

    def _lazy_get_iBode_(self, ignored):
        return self.orbit.iBode

class Asteroid (Planetoid):
    __upinit = Planetoid.__init__
    def __init__(self, name, orbit, mass, **what):
        what.update({'orbit': orbit, 'mass': mass})
        apply(self.__upinit, (name,), what)

class Planet (Planetoid):
    """A major satellite of the sun.

    There is some debate about where we should draw the boundary between planets
    and other detritus in the solar system.  Sedna's discoverers advocate that,
    to qualify as a planet, a body should have to have more mass than all the
    other bodies in orbits of kindred radius.  This would knock Pluto off the
    list and leave us with only the eight planets out to Neptune.  They regard
    Pluto, like Quaoar, as a Kuiper belt object.\n"""

    __upinit = Planetoid.__init__
    def __init__(self, name, surface, orbit, **what):
        """Initialises a Planet object during creation.

        Required arguments:
            name -- name of the planet
            surface -- a Surface object describing the planet's surface
            orbit -- an Orbit object describing its orbit

        Further data may be supplied in name=value form, to taste; these
        will be added to the Planet's namespace.  Likewise, name, surface
        and orbit will be stored as self.name, self.surface and self.orbit.

        Initialisation ensures that orbit.centre notices that the new Planet
        is one of its satellites. """

        what.update({'orbit': orbit, 'surface': surface})
        apply(self.__upinit, (name,), what)
        # give surface.gravity an error bar (where feasible):
        try: g, r, m = surface.gravity, surface.radius, self.GM
        except AttributeError: pass
        else: g.observe(m/r**2)

_rcs_log = """
$Log: body.py,v $
Revision 1.1  2005-03-12 14:52:15  eddy
Initial revision

"""