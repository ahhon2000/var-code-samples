import Config

def interpolate(x1, y1, x2, y2, x):
	if not(x1 - 1e-10 < x and x < x2 + 1e-10):
		raise Exception("interpolate: x out of range x1={x1}; x={x}; x2={x2}".format(x1=x1, x=x, x2=x2))

	y = (y2 - y1) / (x2 - x1) * (x - x1) + y1

	return y


def extrapolate(x1, y1, x2, y2, x):
	if not(x1 < x2 and x2 < x):
		raise Exception("extrapolate: x out of range x1={x1}; x={x}; x2={x2}".format(x1=x1, x=x, x2=x2))

	y = (y2 - y1) / (x2 - x1) * (x - x1) + y1

	return y

class UniformOrderbook:
	def __init__(self, j):
		"""j can be None, in which case initialisation is skipped"""

		self.uniformLiquidities = {'bids': [], 'asks': []}

		if not j: return

		self._convertJtoU(j)


	def _convertJtoU(self, j):
		# sj is a summed up j. The prices are converted to %. I. e.,
		# the first price is always 100%, the second is 100%-step, ...
		sj = {'bids': [], 'asks': []}

		# 1. Fill out sj

		for direction in ("bids", "asks"):
			rs = j[direction]
			if not len(rs): continue

			szSum = 0
			p0 = float(rs[0][0])
			if not p0: continue

			sjdir = sj[direction]
			p_prev = 0
			for r in rs:
				p = float(r[0])
				percent = abs(p0-p) / p0 * 100
				szSum += float(r[1]) + float(r[2])

				if p_prev:
					if direction == 'bids':
						assert p < p_prev
					elif direction == 'asks':
						assert p > p_prev
					else: assert 0
				p_prev = p

				sjdir += [[percent, szSum]]

		# 2. Calculate the uniform liquidities

		step = Config.UNIFORM_ORDERBOOK_DEPTH_STEP
		for direction in ("bids", "asks"):
			rs = sj[direction]
			if len(rs) < 2: continue

			rsInd = 0
			i = 0
			while True:
				depth = i * step
				if depth > Config.UNIFORM_ORDERBOOK_MAX_DEPTH:
					break

				x = depth

				# increase rsInd until depth is btw 2 rs points
				while rsInd+1 < len(rs):
					if rs[rsInd+1][0] > x - 1e-10: break
					rsInd += 1
				if rsInd+1 >= len(rs):
					# extrapolate one more point and BREAK
					r1 = rs[-2]
					r2 = rs[-1]
					self.uniformLiquidities[direction] += [
						extrapolate(r1[0],r1[1], r2[0],r2[1], x)
					]
					break

				r1 = rs[rsInd]
				r2 = rs[rsInd+1]

				self.uniformLiquidities[direction] += [
					interpolate(r1[0],r1[1], r2[0],r2[1], x)
				]

				i += 1


	def valueByInd(self, direction, depthInd):
		assert direction in ["bids", "asks"]
		assert isinstance(depthInd, int)
		assert depthInd >= 0

		lvs = self.uniformLiquidities[direction]
		if depthInd >= len(lvs): return None
		return lvs[depthInd]


	def valueByDepth(self, direction, depth):
		lvs = self.uniformLiquidities[direction]
		step = Config.UNIFORM_ORDERBOOK_DEPTH_STEP

		i = int(depth / step)
		if i + 1 >= len(lvs): return None

		x = depth
		x1 = i * step
		x2 = (i + 1) * step
		y1 = lvs[i]
		y2 = lvs[i+1]
		#y = (y2 - y1) / (x2 - x1) * (x - x1) + y1
		y = interpolate(x1, y1, x2, y2, x)

		return y


	def isZero(self):
		"""Return True iff the total sizes of bids and asks are 0"""

		for direction in ['bids', 'asks']:
			uls = self.uniformLiquidities[direction]
			for szSum in uls:
				if szSum > 1e-10: return False

		return True


	def _customStr(self, depth=None):
		ret = ""
		for d in ['bids', 'asks']:
			if ret: ret += "\n"
			ret += "\t{d}:\n".format(d=d)

			if depth:
				ret += "\tvalue(depth={depth}%) = {vbd}\n".format(
					depth=depth,
					vbd = self.valueByDepth(d, depth),
				)

			for s in self.uniformLiquidities[d]:
				ret += "\t\t{s}\n".format(s=s)

		return ret
			


	def __str__(self):
		return self._customStr()


	def getMaxDepth(self, direction):
		"""Return the max depth for the current direction (percent pts)
		"""

		lvs = self.uniformLiquidities[direction]

		md = 0
		for i in range(len(lvs)):
			if lvs[i] is None: break
			md = i * Config.UNIFORM_ORDERBOOK_DEPTH_STEP

		return md
