
import Config
from Liquidity import Liquidity
from AvgLiquidity import AvgLiquidity
import time
import pickle
import traceback

from Instrument import InstrumentFutures, InstrumentSwaps
from Date import Date

class LiquidityTable:
	def __init__(self, ex,
		customDepthLst=None,
		liquidityFor="all",
		avgInterval1=None,
		avgInterval2=None,
	):
		self.exchange = ex
		tg = ex.tgui

		if liquidityFor not in ["all", "futures", "swaps"]: raise Exception("invalid liquidityFor")
		self.liquidityFor = liquidityFor

		customDepthLst = list(customDepthLst)
		DEFAULT_PRICE_DEPTH = tg.getSessionPar('DEFAULT_PRICE_DEPTH')
		for i in range(len(customDepthLst)):
			if customDepthLst[i] is None:
				customDepthLst[i] = DEFAULT_PRICE_DEPTH

			if not isinstance(customDepthLst[i], float)  or \
				customDepthLst[i] < -1e-10  or \
				customDepthLst[i] > 100 + 1e-10:
				raise Exception("invalid value of customDepth{i}".format(i=i))
		self.customDepthLst = customDepthLst

		if avgInterval1 is None  or  avgInterval2 is None: raise Exception("invalid avgInterval value")
		self.avgInterval1 = avgInterval1
		self.avgInterval2 = avgInterval2

		self.liquidities = {}  # keys: instrument names; values: Liquidities
		self.avgLiquidities = {}  # keys: instrument names; values: [AvgLiquidity1, AvgLiquidity2]
		self.rows = []
		self.errorMessage = ""


	def _loadOrderbookHistoryForIns(self, colNum, ins):
		ex = self.exchange
		tg = ex.tgui

		if colNum not in [1, 2]: raise Exception("invalid colNum")

		T = None  # minutes
		if colNum == 1: T = self.avgInterval1
		elif colNum == 2: T = self.avgInterval2
		else: assert 0
		assert T > 0

		tbl = None
		if isinstance(ins, InstrumentFutures):
			tbl = ex.tblFuturesUOrderbooks()
		elif isinstance(ins, InstrumentSwaps):
			tbl = ex.tblSwapsUOrderbooks()
		else: assert 0

		d2 = Date("now")
		d1 = d2.plusHours(-T/60.)

		assert d1 < d2

		rs = tg.execute("""
SELECT * FROM {tbl} WHERE
`date` >= %s  and  `date` <= %s and
instrument_id = %s
ORDER BY `date`
""".format(tbl=tbl), [d1.toText(), d2.toText(), ins.instrument_id])

		us = []
		for r in rs:
			u = None
			try:
				u = pickle.loads(r['pickle'])
			except Exception as e:
				m = str(e) + ": " + "".join(traceback.format_exception(e.__class__, e, e.__traceback__))
				if self.errorMessage: self.errorMessage += "\n"
				self.errorMessage += "empty orderbook: {e}:\n{m}".format(
	e = str(e),
	m = m,
)

			if u is None: continue
			us += [u]

		ppm = Config.UNIFORM_POINTS_PER_HOUR / 60

		allowance = Config.INVALID_POINTS_ALLOWANCE_FOR_AVERAGES
		minNPoints = round(ppm * T * (1 - allowance))

		return (us, minNPoints)


	def load(self):
		ex = self.exchange
		tg = ex.tgui

		instruments = None
		if self.liquidityFor == "all":
			instruments = ex.allInstrumentsSorted()
		elif self.liquidityFor == "futures":
			instruments = ex.instrumentsFutures
		elif self.liquidityFor == "swaps":
			instruments = ex.instrumentsSwaps
		else: raise Exception("unexpected liquidityFor")
		if not isinstance(instruments, list): raise Exception("`instruments' must be a list")

		self.liquidities.clear()
		self.avgLiquidities.clear()
		for i in range(len(instruments)):
			ins = instruments[i]

			# current liquidities
			j = ex.loadOrderbookForIns(ins)
			if j is None:
				if self.errorMessage: self.errorMessage += "\n"
				self.errorMessage += "no fresh data for instrument {n}".format(n = ins.name)

			l = Liquidity(ins,j, customDepth=self.customDepthLst[0])
			self.liquidities[ins.name] = l

			# averaged liquidities
			als = []
			self.avgLiquidities[ins.name] = als
			for colNum in [1, 2]:
				(us, minNPoints) = self._loadOrderbookHistoryForIns(colNum, ins)
				al = AvgLiquidity(ins, us,
					customDepth=self.customDepthLst[colNum],
					minNPoints = minNPoints,
				)
				als += [al]

			# collect error messages
			for x in [l] + als:
				if x.errorMessage:
					if self.errorMessage:
						self.errorMessage += "\n"
					self.errorMessage += x.errorMessage
