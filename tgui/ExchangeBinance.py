import requests
import pickle
import os, sys
import time
import json
import re
from websocket import WebSocket
import traceback

import Config
from Exchange import Exchange
from Date import Date
from Instrument import InstrumentFutures, InstrumentSwaps

class ExchangeBinance(Exchange):
	def __init__(self, tg):
		Exchange.__init__(self, tg)
		self.name = "Binance"
		self.ws = None

		# _orderbooks format:
		#	keys:    instrument ids;
		#	values:  {'lastUpdateId', 'bids': {...}, 'asks': {...}}
		#
		# bids and asks are dictionaries of the following format:
		#	keys: price_txt   values: amount (float)
		self._orderbooks = {}

		#iids = list(c + "USD" for c in Config.COINS[self.name])
		iids = list(c + "USDT" for c in Config.COINS[self.name])
		iids += list(c + "BTC" for c in Config.COINS[self.name])
		iids.remove("BTCBTC")
		self._swapInstrumentIds = iids

		streams = [iid.lower() + "@depth"    for iid in iids]
		self._streams = streams


	def tblFuturesOrderbooks(self):
		return "binance_futures_orderbooks"


	def tblSwapsOrderbooks(self):
		return "binance_swaps_orderbooks"


	def tblFuturesUOrderbooks(self):
		return "binance_futures_uorderbooks"


	def tblSwapsUOrderbooks(self):
		return "binance_swaps_uorderbooks"


	def tblFuturesInstruments(self):
		return "binance_futures_instruments"


	def tblSwapsInstruments(self):
		return "binance_swaps_instruments"


	def binanceReq(self, arg):
		"""Return the json object containing the server's response"""

		url = "https://www.binance.com/api/v1/" + arg

		rsp = requests.get(url,
			headers = {'Content-Type': 'application/json'},
		)

		code = rsp.status_code

		if code != 200:
			self.logw("the REST request returned code {code}; url = {url}".format(code=code, url=url))
			return None

		s = rsp.content.decode('utf-8')
		j = json.loads(s)

		return j


	def pingOk(self, lstForMsg):
		lstForMsg.clear()
		if not self.ws  or  not self.ws.connected:
			return False

		return True


	def connectReconnect(self):
		tg = self.tgui
		retMsg = ""

		lstForMsg = []
		pingOk = self.pingOk(lstForMsg)
		retMsg = "\n".join(lstForMsg)

		if pingOk: return retMsg

		if retMsg: retMsg += "\n"
		retMsg += "(re)connecting to {exn}...".format(exn=self.name)

		# (Re)create the websocket object

		if self.ws:
			try:
				self.ws.close()
			except:
				pass

		streams = self._streams

		url = "wss://stream.binance.com:9443/stream?streams="
		url += "/".join(streams)

		self.ws = None
		self.ws = WebSocket()
		self.ws.connect(url)

		self._orderbooks.clear()

		return retMsg


	def downloadInstruments(self):
		tg = self.tgui
		ws = self.ws

		if not self._orderbooks: self._downloadInitialSnapshots()

		self.log("saving the instruments to the db...")
		for (tbl, instruments) in (
			(self.tblFuturesInstruments(), self.instrumentsFutures),
			(self.tblSwapsInstruments(), self.instrumentsSwaps),
		):
			self.saveNewInstruments(tbl, instruments)

		self.log("sorting the instruments...")
		self.sortInstruments()


	def _downloadInitialSnapshots(self):
		self.instrumentsFutures.clear()
		self.instrumentsSwaps.clear()

		self._orderbooks.clear()
		for iid in self._swapInstrumentIds:
			arg = "depth?symbol={s}&limit=1000".format(
				s=iid.upper(),
			)
			j = self.binanceReq(arg)

			if j is None:
				self.logw("symbol {iid} is unavailable".format(iid=iid))
				continue

			ks = ('lastUpdateId', 'bids', 'asks')
			for k in ks:
				if k not in j.keys(): raise Exception("the REST response does not contain keys `{k}'".format(k=k))

			# convert the retrieved data to our orderbook format

			ob = {}
			ob['lastUpdateId'] = int(j['lastUpdateId'])
			for direction in ("bids", "asks"):
				ob[direction] = {}
				for r in j[direction]:
					ptxt  = self._priceToKey(float(r[0]))
					am =  float(r[1])
					ob[direction][ptxt] = am
					
			self._orderbooks[iid] = ob

			# Initialise the Instrument object
			self.instrumentsSwaps += [InstrumentSwaps({
				'instrument_id': iid,
				'delivery': '',
			})]


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
		obs = self._orderbooks
		if not obs:
			self.logw("no initial orderbook snapshots")
			return

		# update the existing orderbooks with data from the server

		ws = self.ws
		self.log("\treceiving updates from the server".format())
		nFailures = 0

		brkFlgs = {iid: False  for iid in obs.keys()}
		# receive and process updates until all of brkFlgs become True
		n_recv = 0
		while not all(v  for v in brkFlgs.values()):
			n_recv += 1
			if n_recv > 100000:
				self.loge("to many reads from the websocket ({n_recv})".format(n_recv))
				break

			j = None
			try:
				# TODO utilise ws.settimeout() here
				j = ws.recv()
			except Exception as e:
				nFailures += 1
				m = str(e) + ": " + "".join(traceback.format_exception(e.__class__, e, e.__traceback__))
				self.loge("\tfailed to retrieve an update from the server".format())

			if nFailures > 3: raise Exception("cannot retrieve update from the server")
			if j is None: raise Exception("the websocket returned no data")
			j = json.loads(j)

			ins = self._getInsByStream(j['stream'])
			data = j['data']

			# checks on the payload for instrument ins:

			if data['e'] != 'depthUpdate': continue
			if data['s'].upper() != ins.instrument_id: raise Exception('the symbol in the payload does not match instrument_id')

			# check if the update is fresh and set the break flag

			U = int(data['U'])
			u = int(data['u'])
			ob = obs[ins.instrument_id]
			if u <= ob['lastUpdateId']: continue
			if U > ob['lastUpdateId'] + 1:
				raise Exception("U > lastUpdateId. Should we download a new initial snapshot at this point and work with it?")

			brkFlgs[ins.instrument_id] = True

			# update/remove the orderbook structure in this object

			for (d, direction) in (("b", "bids"), ("a", "asks")):
				ob['lastUpdateId'] = u
				for r in data[d]:
					ptxt = self._priceToKey(float(r[0]))
					am = float(r[1])

					if abs(am) < 1e-10:
						if ptxt in ob[direction].keys():
							ob[direction].pop(ptxt)
					else:
						ob[direction][ptxt] = am
		# END WHILE

		# save the data to the DB

		for (instruments, tbl) in (
			(self.instrumentsFutures, self.tblFuturesOrderbooks()),
			(self.instrumentsSwaps, self.tblSwapsOrderbooks()),
		):
			for ins in instruments:
				now = Date("now")
				iid = ins.instrument_id

				j = self._assembleInsOrderbook(iid)
				b = pickle.dumps(j)
				tg.execute("""
INSERT INTO {tbl} (`instrument_id`, `date`, `pickle`)
VALUES (%s, %s, %s)
""".format(tbl=tbl), [iid, now.toText(), b])


	def _assembleInsOrderbook(self, iid):
		ob = self._orderbooks
		j = {}
		for direction in ['bids', 'asks']:
			ls = []
			for (ptxt, am) in ob[iid][direction].items():
				p = float(ptxt)
				sz = am
				ls += [[p, sz, 0]]

			flgReverse = True if direction == 'bids' else False
			ls.sort(key=lambda r: r[0], reverse=flgReverse)
				
			j[direction] = ls

		return j


	def _priceToKey(self, p):
		return "%.8f" % p


	def _getInsByStream(self, stream):
		if not re.search(r'^[a-zA-Z]+@depth$', stream): raise Exception("could not recognise stream name `{stream}'".format(stream=stream))

		iid = re.sub(r'^([a-zA-Z]+)@depth$', r'\1', stream).upper()
		for ins in self.instrumentsSwaps:
			if ins.instrument_id == iid: return ins

		raise Exception("unexpected instrument: {iid}".format(iid=iid))


	def pullVolume(self):
		pass


	def pullFunding(self):
		pass
