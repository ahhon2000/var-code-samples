import requests
import pickle
import os, sys
import time
import json
import traceback

from btfxwss import BtfxWss

import Config
from Exchange import Exchange
from Date import Date
from Instrument import InstrumentFutures, InstrumentSwaps

class ExchangeBitfinex3(Exchange):
	def __init__(self, tg):
		Exchange.__init__(self, tg)
		self.name = "Bitfinex"

		# _orderbooks format:
		#	keys:    instrument names;
		#	values:  {'bids': {...}, 'asks': {...}}
		#
		# bids and asks are dictionaries of the following format:
		#	keys: price_txt   values: amount (float)
		self._orderbooks = {}


	def tblFuturesOrderbooks(self):
		return "bitfinex_futures_orderbooks"


	def tblSwapsOrderbooks(self):
		return "bitfinex_swaps_orderbooks"


	def tblFuturesUOrderbooks(self):
		return "bitfinex_futures_uorderbooks"


	def tblSwapsUOrderbooks(self):
		return "bitfinex_swaps_uorderbooks"


	def tblFuturesInstruments(self):
		return "bitfinex_futures_instruments"


	def tblSwapsInstruments(self):
		return "bitfinex_swaps_instruments"


	def createTables(self):
		tg = self.tgui

		for tbl in [
			self.tblFuturesInstruments(),
			self.tblSwapsInstruments(),
		]:
			tg.execute("""
CREATE TABLE IF NOT EXISTS `{tbl}` (
	`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,
	`instrument_id` VARCHAR(80),
	`pickle` BLOB
)
""".format(tbl=tbl))

		for tbl in [
			self.tblFuturesOrderbooks(),
			self.tblSwapsOrderbooks(),
			self.tblFuturesUOrderbooks(),
			self.tblSwapsUOrderbooks(),
		]:
			tg.execute("""
CREATE TABLE IF NOT EXISTS `{tbl}` (
	`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,
	`instrument_id` VARCHAR(80),
	`date` VARCHAR(32),
	`pickle` BLOB
)
""".format(tbl=tbl))


	def bitfinexReq(self, url):

		rsp = requests.get(url,
			headers = {'Content-Type': 'application/json'},
		)

		code = rsp.status_code

		s = rsp.content.decode('utf-8')
		j = json.loads(s)

		if code != 200:
			raise Exception("the REST request returned code {code}; url = {url}; json={j}".format(code=code, url=url, j=str(j)[0:1000]))

		return j


	def downloadInstruments(self):
		tg = self.tgui

		iids = list(c + "USD" for c in Config.COINS[self.name])
		iids += list(c + "BTC" for c in Config.COINS[self.name])
		iids.remove("BTCBTC")

		for (instruments, url, tbl, InstrumentClass) in (
			(
				self.instrumentsSwaps,
				'https://api.bitfinex.com/v2/conf/pub:list:pair:exchange',
				self.tblSwapsInstruments(),
				InstrumentSwaps,
			),
		):
			instruments.clear()

			j = self.bitfinexReq(url)

			if not isinstance(j, list) or not isinstance(j[0], list): raise Exception("unexpected insturment list format")

			for r in j[0]:
				ins = InstrumentClass({
					'instrument_id': r,
					'delivery': '',
				})
				if ins.instrument_id in iids:
					instruments += [ins]
			self.saveNewInstruments(tbl, instruments)

		self.sortInstruments()


	def sortInstruments(self):
		def sortKeyFutures(ins):
			return (
				Config.COINS[self.name].index(ins.getCoin()),
				ins.name,
			)

		def sortKeySwaps(ins):
			return (
				Config.COINS[self.name].index(ins.getCoin()),
				ins.name,
			)

		for (instruments, sortKey) in (
			(self.instrumentsFutures, sortKeyFutures),
			(self.instrumentsSwaps, sortKeySwaps),
		):
			instruments.sort(key = sortKey)


	def pullOrderbooks(self):
		tg = self.tgui

		apiBase = 'https://api-pub.bitfinex.com/v2/book'
		instruments = self.instrumentsSwaps
		tbl = self.tblSwapsOrderbooks()

		pids = []
		sleepSec = 2  # time btw requests  # TODO def from const
		for i in range(len(instruments)):
			ins = instruments[i]

			time.sleep(sleepSec)

			pid = os.fork()
			if pid:
				pids += [pid]
			else:
				try:
					import TGui
					tg = TGui.TGui(readOnly=False)
					j = self.bitfinexReq("{apiBase}/t{instrument_id}/P0?len=100".format(
	apiBase = apiBase,
	instrument_id = ins.instrument_id,
))

					now = Date("now")
					ob = self._assembleOrderbook(j)
					b = pickle.dumps(ob)
					tg.execute("""
INSERT INTO {tbl} (`instrument_id`, `date`, `pickle`)
VALUES (%s, %s, %s)
""".format(tbl=tbl), [ins.instrument_id, now.toText(), b])
				except Exception as e:
					sys.stderr.write("error: " + str(e) + "\n")

				sys.exit(0)

		for pid in pids:
			(pid2, st) = os.waitpid(pid, 0)


	def _assembleOrderbook(self, j):
		ob = {'bids': [], 'asks': []}
		for r in j:
			p = float(r[0])
			am = float(r[2])
			direction = "bids" if am >= 0 else "asks"

			ob[direction] += [[p, abs(am), 0]]

		for direction in ['bids', 'asks']:
			flgRev = True if direction == 'bids' else False
			ob[direction].sort(key=lambda r: r[0], reverse=flgRev)

		return ob
