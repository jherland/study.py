# -*- coding: iso-8859-1 -*-
"""Planck's units.

$Id: planck.py,v 1.2 2007-03-24 22:42:21 eddy Exp $
"""
from physics import Vacuum, Quantum, Cosmos, Thermal, Object, pi

# Should really define a `system of units' class ...
# Planck's units (c.f. Hartree's in /usr/share/misc/units):
Planck = Object(
    __doc__ = """Planck's units.

When Planck discovered his solution to the problem then known as the
`ultraviolet catastrophe' and hence discovered the physical constant named after
him, he noticed that it, Newton's gravitational constant and the speed of light
were all expressible in terms of units of length, time and mass; yet that no
product of powers of two of them yields a quantity with the same dimensions as
the third.  He thus had three dimensionally independent quantities expressible
in terms of the three primitive units of measurement of classical mechanics:
which necessarily implied there must be a way to invert the `expressed in terms
of' and obtain units of length, time and mass from h, G and c.

It has been common to augment these with the charge on the electron (e,
a.k.a. Millikan's quantum) to produce units of electrodynamic measurement
(charge, current, voltage, etc.); however, G and c arise as constants in the
field equations of gravity and electrodynamics, while h (at least first)
appeared as a constant in a proportionality law (albeit one whose causes
mystified Planck); it would thus be clearly preferable to extend the system to
electromagnetic units by chosing some constant from electromagnetism's *field
equations*, rather than a property of some of the particles *governed by* those
equations.

It so happens that natural candidates present themselves; the permeability,
permittivity and impedance of free space; which of these we chose makes no
difference to our system of units, since combining it suitably with c yields the
other two.  Equally, some constant scaling applied to one of these may be
appropriate; indeed, as argued below, 4*pi times the permittivity provides a
natural candidate (c.f. also Cosmos.qperm).

Much has been said to the effect that the Planck time and length `must
represent' minimal scales of the universe; I treat this with some skepticism,
given that the Planck mass, of order a dozen microgrammes, isn't in any sense
`irreducible' - see Planck.mass.__doc__ for details.  The Planck momentum is of
the same order as the momentum of a full-grown cat running.  The Planck charge,
meanwhile, is of order eight positrons-worth - so manifestly reducible - and the
universe clearly *does* quantise charge (albeit possibly in units of a third
that on the positron) so even when a quantity does have a `minimal scale' this
needn't be the relevant Planck unit.

It should also be noted that one has some choice in the quantities used; hence
the `of order' clauses above.  The speed of light is well established, but: for
the action one may use Planck's constant, h, or Dirac's, h/2/pi, or even argue
for half this (the spin of a fermion); for the constants governing inverse
square laws, one has a choice of a factor of 4*pi according as one uses the
constant from the central-force law or the constant from the equation of
proportionality between divergence and source density (the field equation).
Indeed, as concerns the latter, G is selected from gravity's inverse square law,
so a petty consistency encourages me to select the matching constant from
Coulomb's law, 1/4/pi/epsilon0 = Z0 * c / 4 / pi.

The fine structure constant, alpha = e*e/(4*pi*epsilon0*hbar*c), arises
naturally as a coefficient in perturbation expansions - well, actually, 2*alpha
does - and effectively expresses e in terms of the charge q = sqrt(h/Z0) =
sqrt(2*pi*epsilon0*hbar*c), making e = q * sqrt(2*alpha), i.e. (given 137*alpha
is almost exactly 1) q = e*sqrt(137/2): this would make a more natural unit of
charge, but the above petty consistency obliges me to use 2*q*sqrt(pi) instead.

Since I believe Planck used h, c and G as units, and this object is named after
him, I should be faithful to that choice, as far as it goes: which, with
sqrt(4*pi*h/Z0) as unit of charge, requires that Z0 be 4*pi, hence so is mu0,
while epsilon0 is 1/4/pi.  But for Planck's historical choice, I would prefer to
use the Einstein-Maxwell charge-to-mass ratio (Cosmos.qperm, above) in place of
G, along with Z0 as just justified (in terms of q = sqrt(h/Z0) as unit of
charge); which would be equivalent to replacing G, in the system actually used
here, with its matching Newtonian field-equation unit, 4*pi*G, and using Z0
rather than Z0/4/pi.  However, Planck chose G.\n""",

    # The fabric of space-time:
    speed = Vacuum.c,
    # The quantum of action:
    action = Quantum.h,                 # angular momentum
    # Newton's constant, with suitable powers of c bound into place: # '
    kappa = Cosmos.G / Vacuum.c**3,     # time/mass
    # The electromagnetic field:
    impedance = Vacuum.impedance / 4 / pi)

# obviously, I want to automate the following ... see eddy.science.unit
Planck.also(
    charge   = (Planck.action / Planck.impedance)**.5,  # 29.3446 positrons
    momentum = (Planck.action / Planck.kappa)**.5,      # 8.451 stone foot / second
    length   = (Planck.action * Planck.kappa)**.5)      # very tiny.
# so tiny that a mole of Planck lenghts add up to almost a quarter of an �ngstr�m ...
Planck.also(
    mass = Planck.momentum / Planck.speed, # sqrt(c.h/G)
    energy = Planck.momentum * Planck.speed,
    time = Planck.length / Planck.speed,
    arearate = Planck.length * Planck.speed)    # aka action / mass
Planck.also(
    current = Planck.charge / Planck.time,
    magneton = Planck.charge * Planck.arearate, # aka charge * action / mass
    temperature = Planck.energy / Thermal.k,
    force = Planck.momentum / Planck.time,
    torque = Planck.energy,                     # i.e. force * distance, or action / time
    acceleration = Planck.speed / Planck.time)

Planck.mass.also(__doc__="""The Planck mass.

See general documentation of Planck's units, on object Planck.

Note, for contrast, that amoeba have masses of order 4 micro grams, bacteria of
order a pico gram, individual genes of order 40 atto grams; the Planck mass is
over a dozen times the first of these.  Tardigrades (a.k.a. water bears) are
fully articulated animals with less mass than the Planck mass.  Thus, plenty of
living organisms are smaller than the Planck mass; a cube of water with this
mass has sides over a third of a millimetre long.\n""")