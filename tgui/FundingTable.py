import Config
from Date import Date

class FundingTable:
	def __init__(self, exchanges):
		self.exchanges = list(exchanges)
		self.errorMessages = []

		# fvalues format: {("BTC", "Current"): [f_ex1, f_ex2], ...}
		self.fvalues = {}
		self.fundingTimes = {}  # format: similar to fvalues
		self.updateDates = {}  # format: similar to fvalues

		if not exchanges: self.errorMessages += ["no exchanges given to FundingTable"]

		self._loadFunding()


	def _loadFunding(self):
		exs = self.exchanges
		fs = self.fvalues
		ftimes = self.fundingTimes
		upds = self.updateDates
		fs.clear()
		ftimes.clear()
		upds.clear()

		for i in range(len(exs)):
			ex = exs[i]
			tg = ex.tgui
			rs = tg.execute("""
SELECT * FROM {tbl}
ORDER BY `symbol`
""".format(tbl=ex.tblFunding()), [])

			for r in rs:
				sym = ex.universalSymbolName(r['symbol'])
				if sym not in Config.FUNDING_SYMBOLS: continue
				for (kfs, kr, kttf) in (
					((sym, 'Current'),'fundingRate', 'timestamp'),
					((sym, 'Predicted'),'fundingRatePredicted', 'timestampPredicted'),
				):
					if kfs not in fs.keys():
						fs[kfs] = [None] * len(exs)
					if kfs not in ftimes.keys():
						ftimes[kfs] = [None] * len(exs)
					if kfs not in upds.keys():
						upds[kfs] = [None] * len(exs)

					ftime=Date(r[kttf]) if r[kttf] else None

					fs[kfs][i] = None
					ftimes[kfs][i] = None
					if kfs[1] != 'Predicted' or ex.predictedFRateApplicable():

						fs[kfs][i] = float(r[kr])
						ftimes[kfs][i] = ftime

					upds[kfs][i] = Date(r['last_update'])

		if not len(fs.keys()): self.errorMessages += ["FundingTable found no symbols"]
