import copy
import re

# transaction statuses
TRST = [
	"TRST_UNDEF",
	"TRST_OPEN1",
	"TRST_CLOSED1",
	"TRST_OPEN2",
	"TRST_CLOSED2",
]
for i in range(len(TRST)):
	exec("%s = %d" % (TRST[i], i))




from Config import WM_COMMISSION, COMMISSION_MAXIMA


def roundUpCent(x):
	centFraction = (100*x - int(100*x)) / 100
	if centFraction > 0:
		x = x - centFraction + 0.01

	return x


def calCommission(am, cur):
	c = WM_COMMISSION * am / (1 + WM_COMMISSION)

	M = COMMISSION_MAXIMA.get(str(cur).upper(), None)
	if M is None: raise Exception("no commission maximum for currency `%s'" % cur)

	if c > M: c = M

	c = roundUpCent(c)

	return c


def trim(x, xmin, xmax):
	assert xmin < xmax

	if x < xmin: return xmin
	if x > xmax: return xmax

	return x


def insideInterval(x, xmin, xmax):
	assert xmin < xmax

	if x < xmin or x > xmax: return False
	return True


def findZero(f, par, x1, x2, maxYError = 1e-10):
	"""Return a solution of the equation f(par, x) == 0 relative to x
	on the interval x1...x2. The solution is returned as a tuple (x, y).

	If no solution can be found return (None, None).

	f must be monotonous.
	"""

	par = copy.copy(par)

	assert x1 < x2	

	maxIter = 1000
	y1 = f(par, x1)
	y2 = f(par, x2)
	(x0, y0) = (None, None)
	for i in range(1, maxIter+1):
		x0 = (x1 + x2) / 2
		y0 = f(par, x0)

		if abs(y0) < maxYError: return (x0, y0)

		if y1 <= 0 and y0 >= 0  or  y1 >= 0 and y0 <= 0:
			x2 = x0
			y2 = y0
		elif y2 <= 0 and y0 >= 0  or  y2 >= 0 and y0 <= 0:
			x1 = x0
			y1 = y0
		else:
			return (None, None)

	return (None, None)


def sqliteToMysql(r):
	# replace all ? placeholders with %s
	rr = ""
	insideQuotes = False
	for x in r:
		if not insideQuotes  and  x == '?': x = "%s"
		if x == "'": insideQuotes = not insideQuotes
		rr += x
	r = rr

	# Fix AUTO_INCREMENT
	r = re.sub(r'^(\s*CREATE\s+TABLE[^;]+INTEGER[^,]+PRIMARY\s+KEY)',
		r'\1 AUTO_INCREMENT ',
		r, flags=re.IGNORECASE)
	r = re.sub(r'^(\s*CREATE\s+TABLE[^;]*)',
		r'\1 AUTO_INCREMENT = 1',
		r, flags=re.IGNORECASE)

	# add a semicolon to terminate the query
	if not re.search(r';\s*$', r): r = r + ';'

	return r


def trapezeAvg(xs, ys):
	if len(xs) != len(ys): raise Exception("the length of xs is not the same as that of ys")

	n = len(xs)
	if n == 0: raise Exception("no points were given for averaging")

	for i in range(1, n):
		if xs[i-1] > xs[i]: raise Exception("unordered xs")

	avg = 0
	if n == 1:
		avg = ys[0]
	else:
		T = 0
		for i in range(1, n):
			y = (ys[i] + ys[i-1]) / 2.
			dx = xs[i] - xs[i-1]
			if dx < 1e-10: raise Exception("2 points have the same x: x1 = %.10f; x2=%.10f" % (xs[i-1], xs[i]))

			avg += y * dx
			T += dx

		avg /= T

	return avg

class NonMatchingCurPurseException(Exception):
	def __init__(self, x):
		Exception.__init__(self, x)
