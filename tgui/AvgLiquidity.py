from Liquidity import Liquidity

class AvgLiquidity:
	def __init__(self, ins, us, customDepth = None, minNPoints=0):
		if not isinstance(customDepth, (float, int))  or \
			customDepth < -1e-10  or  customDepth > 100 + 1e-10:
			raise Exception("invalid value of customDepth: {cd}".format(cd=customDepth))
		self.customDepth = customDepth

		if minNPoints <= 0: raise Exception("a positive minNPoints must be specified")

		self.instrument = ins
		self.errorMessage = ""
		self.minNPoints = minNPoints

		self.bid = 0
		self.ask = 0

		n = ins.name

		if not isinstance(us, list):
			raise Exception("`us' must be a list")
		if not us: return

		try:
			self._processUOrderbooks(us)
		except Exception as e:
			if self.errorMessage:
				self.errorMessage += "\n"
			self.errorMessage += """
failed to calculate averages for {n}: {m}
"""[1:-1].format(
	n = n,
	m=str(e),
)


	def _processUOrderbooks(self, us):
		ins = self.instrument
		customDepth = self.customDepth
		minNPoints = self.minNPoints
		
		lenus = len(us)
		if not lenus: raise Exception("no records for the average")
		if lenus < minNPoints: raise Exception("not enough valid records for the {n} average: {lenus} instead of {minNPoints} required".format(
	n = self.instrument.name,
	lenus = lenus,
	minNPoints = self.minNPoints,
))

		assert minNPoints > 0


		avgs = {
			'bids': {'sum': 0., 'count': 0},
			'asks': {'sum': 0., 'count': 0},
		}
		for u in us:
			for direction in ("bids", "asks"):
				lv = u.valueByDepth(direction, customDepth)
				if not(lv is None):
					avgs[direction]['sum'] += lv
					avgs[direction]['count'] += 1

		for direction in ("bids", "asks"):
			s = avgs[direction]['sum']
			count = avgs[direction]['count']

			if count >= self.minNPoints:
				a = round(s / count)
				if direction == "bids": self.bid = a
				elif direction == "asks": self.ask = a
				else: assert 0
			else:
				if self.errorMessage: self.errorMessage += "\n"
				self.errorMessage += "not enough valid records for the {n} {direction} average: {count} instead of at least {Nm}".format(
	n = self.instrument.name,
	direction = direction,
	count = count,
	Nm = self.minNPoints,
)
