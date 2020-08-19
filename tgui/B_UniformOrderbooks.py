import pickle
import traceback

from UniformOrderbook import UniformOrderbook
from Date import Date

import Config

class B_UniformOrderbooks:
	def __init__(self, ex):
		self.exchange = ex
		self.errorMessage = ""


	def cycle(self):
		ex = self.exchange
		tg = ex.tgui

		for (ctype, instruments) in (
			("futures", ex.instrumentsFutures),
			("swaps", ex.instrumentsSwaps),
		):
			for ins in instruments:
				try:
					self._saveAvgUOrderbook(ctype, ins)
				except Exception as e:
					m = str(e) + ": " + "".join(traceback.format_exception(e.__class__, e, e.__traceback__))
					ex.loge("\tfailed to save average uniform orderbooks for {n} {ctype}: {e}:\n{m}".format(
	n = ins.name,
	ctype = ctype,
	e = str(e),
	m = m,
))
					if self.errorMessage:
						self.errorMessage += "\n"
					self.errorMessage += "failed to save average uniform orderbooks for {n} {ctype}: {e}".format(
	n = ins.name,
	ctype = ctype,
	e = str(e),
)


	def _saveAvgUOrderbook(self, ctype, ins):
		ex = self.exchange
		tg = ex.tgui

		(tbl, utbl) = (None, None)
		if ctype == "futures":
			tbl = ex.tblFuturesOrderbooks()
			utbl = ex.tblFuturesUOrderbooks()
		elif ctype == "swaps":
			tbl = ex.tblSwapsOrderbooks()
			utbl = ex.tblSwapsUOrderbooks()
		else: assert 0

		now = Date("now")

		(au, dlast) = self._getLastAvgUOrderbook(ctype, ins)
		# treat very old uniform records as non-existent
		if dlast  and  dlast.hoursEarlier(now) > Config.U_ORDERBOOK_EXPIRY_INTERVAL:
			dlast = None

		uoi = Config.UNIFORM_ORDERBOOK_INTERVAL
		while not dlast  or  dlast.minutesEarlier(now) > uoi:
			# if there are no records yet:
			if not dlast: dlast = now.plusHours(-uoi/60.)

			d1 = dlast
			d2 = dlast.plusHours(uoi/60.)

			rs = tg.execute("""
SELECT * FROM {tbl} WHERE
`date` >= %s  and  `date` <= %s  and
instrument_id = %s
ORDER BY `date`
""".format(tbl=tbl), [d1.toText(), d2.toText(), ins.instrument_id])

			us = []
			for r in rs:
				j = None
				try:
					j = pickle.loads(r['pickle'])
				except Exception as e:
					m = str(e) + ": " + "".join(traceback.format_exception(e.__class__, e, e.__traceback__))
					ex.logw("\tfailed to load orderbook for {n} {ctype}: {e}:\n{m}".format(
	n = ins.name,
	ctype = ctype,
	e = str(e),
	m = m,
))
				if j is None: continue

				u = UniformOrderbook(j)
				us += [u]

			if us:
				au = self._avgUOrderbook(us)

				if not au.isZero():
					b = pickle.dumps(au)
					tg.execute("""
INSERT INTO {utbl} (`instrument_id`, `date`, `pickle`)
VALUES (%s, %s, %s)
""".format(utbl=utbl), [ins.instrument_id, d2.toText(), b])

			assert dlast < d2
			dlast = d2


	def _getLastAvgUOrderbook(self, ctype, ins):
		ex = self.exchange
		tg = ex.tgui

		utbl = None
		if ctype == "futures":
			utbl = ex.tblFuturesUOrderbooks()
		elif ctype == "swaps":
			utbl = ex.tblSwapsUOrderbooks()
		else: assert 0

		rs = tg.execute("""
SELECT * FROM {utbl}
WHERE instrument_id = %s
ORDER BY `date` DESC LIMIT 1
""".format(utbl=utbl), [ins.instrument_id])

		au = None
		d = None
		for r in rs:
			au = r['pickle']
			d = Date(r['date'])
			break

		return (au, d)


	def _avgUOrderbook(self, us):
		au = UniformOrderbook(None)

		ppm = Config.POINTS_PER_MINUTE_FOR_AVERAGES
		uoi = Config.UNIFORM_ORDERBOOK_INTERVAL
		allowance = Config.INVALID_POINTS_ALLOWANCE_FOR_AVERAGES
		minNPoints = round(ppm * uoi * (1 - allowance))

		for direction in ("bids", "asks"):
			depthInd = 0
			while True:
				s = 0.
				count = 0
				for u in us:
					lv = u.valueByInd(direction, depthInd)
					if lv is None: continue

					s += lv
					count += 1

				if count < minNPoints: break

				au.uniformLiquidities[direction] += [s / count]

				depthInd += 1

		return au
