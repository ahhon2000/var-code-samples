from Date import Date

class VolumeTable:
	def __init__(self, exchanges):
		self.exchanges = list(exchanges)
		self.volumes = {}  # format: {"BTCUSD": [vol_ex1, vol_ex2], ...}
		self.turnovers = {}  # format: {"BTCUSD": [to_ex1, to_ex2], ...}
		self.updateDates = {}   # format: similar
		self.errorMessages = []

		if not exchanges: self.errorMessages += ["no exchanges given to VolumeTable"]

		self._loadVolumes()


	def _loadVolumes(self):
		exs = self.exchanges

		vs = self.volumes
		tos = self.turnovers
		upds = self.updateDates
		vs.clear()
		tos.clear()
		upds.clear()

		for i in range(len(exs)):
			ex = exs[i]
			tg = ex.tgui
			rs = tg.execute("""
SELECT * FROM {tbl}
WHERE `exchange` = %s
ORDER BY `symbol`
""".format(tbl=ex.tblVolumes()), [ex.name])

			for r in rs:
				sym = ex.universalSymbolName(r['symbol'])
				if sym not in vs.keys():
					vs[sym] = [None] * len(exs)
				if sym not in tos.keys():
					tos[sym] = [None] * len(exs)
				if sym not in upds.keys():
					upds[sym] = [None] * len(exs)

				vs[sym][i] = float(r['volume'])
				tos[sym][i] = float(r['turnover'])
				upds[sym][i] = Date(r['last_update'])

		if not vs.keys(): self.errorMessages += ["VolumeTable found no symbols"]
