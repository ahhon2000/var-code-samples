import Config

class Liquidity:
	def __init__(self, ins, j, customDepth=None):
		self.askm = 0
		self.bidm = 0
		self.ask = 0
		self.bid = 0
		self.actualDepthAsk = 0
		self.actualDepthBid = 0
		self.actualDepthAskm = 0
		self.actualDepthBidm = 0

		self.instrument = ins
		self.errorMessage = ""

		if not isinstance(customDepth, (float, int))  or \
			customDepth < -1e-10  or  customDepth > 100 + 1e-10:
			raise Exception("invalid value of customDepth: {cd}".format(cd=customDepth))
		self.customDepth = customDepth

		n = ins.name

		if not j: return

		for d in ("asks", "bids"):
			try:
				self._process_json(j, d)
			except Exception as e:
				if self.errorMessage:
					self.errorMessage += "\n"
				self.errorMessage += """
failed to retrieve {n} {d} data: {m}
"""[1:-1].format(
	d = d,
	n = n,
	m=str(e),
)


	def _calcLiquidity(self, j, direction, depth=None):
		"""If depth is None use the maximum available depth"""
		
		ins = self.instrument
		d = direction
		n = ins.name

		if d not in j.keys():
			raise Exception("no `{d}' in the json object for {instrument_id}".format(d=d, instrument_id=ins.instrument_id))

		rs = j[d]
		if len(rs) == 0:
			raise Exception("no {d} available for {n}".format(
	d = d,
	n = n,
))

		r0 = rs[0]
		p0 = float(r0[0])
		sz0 = int(r0[1])
		if p0 <= 0: raise Exception("non-positive price")

		szSum = 0
		actualDepth = 0
		p_prev = None
		for r in rs:
			p = float(r[0])
			sz = int(r[1])
			liquidatedOrders = int(r[2])
			dp = abs(p - p0)

			if p_prev:
				if direction == 'bids':
					assert p < p_prev
				elif direction == 'asks':
					assert p > p_prev
				else: assert 0

			assert sz >= -1e-10
			assert liquidatedOrders >= -1e-10
			szSum += sz + liquidatedOrders

			actualDepth = dp / p0 * 100

			if depth is None:
				# sum over all the records (the maximum depth)
				pass
			else:
				# only sum up to a custom depth
				if dp / p0 * 100 > depth - 1e-10: break

			p_prev = p

		return (szSum, actualDepth)


	def _process_json(self, j, direction):
		d = direction
		depth = self.customDepth

		(szm, actualDepth_m) = self._calcLiquidity(j, direction, depth=None)
		(sz, actualDepth) = self._calcLiquidity(j, direction, depth=depth)

		if d == 'asks':
			self.askm = szm
			self.ask = sz
			self.actualDepthAskm = actualDepth_m
			self.actualDepthAsk = actualDepth
		elif d == 'bids':
			self.bidm = szm
			self.bid = sz
			self.actualDepthBidm = actualDepth_m
			self.actualDepthBid = actualDepth
		else:
			raise Exception("unknown order type: `%s'" % (d))


	def bidCustomDepthAvailable(self):
		assert isinstance(self.customDepth, (float, int))
		assert self.actualDepthBid >= -1e-10

		if self.customDepth <= 0: return True

		if self.actualDepthBid > self.customDepth - 1e-10:
			return True

		return False


	def askCustomDepthAvailable(self):
		assert isinstance(self.customDepth, (float, int))
		assert self.actualDepthAsk >= -1e-10

		if self.customDepth <= 0: return True

		if self.actualDepthAsk > self.customDepth -1e-10:
			return True

		return False
