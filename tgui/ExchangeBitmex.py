import requests
import pickle
import os, sys
import time
import json
import re
import traceback

import Config
from Config import BITMEX_CONFIG
from Exchange import Exchange
from Date import Date
from Instrument import InstrumentFutures, InstrumentSwaps
from bitmex_websocket import BitMEXWebsocket


class ExchangeBitmex(Exchange):
	_SUPPORTED_VOLUME_SYMBOLS = [
		"XBTUSD",
		#
		"ETHUSD",
		#
		"ADAXBT",
		"BCHXBT",
		"EOSXBT",
		"LTCXBT",
		"TRXXBT",
		"XRPXBT",
	]

	def __init__(self, tg):
		Exchange.__init__(self, tg)
		self.name = "BitMEX"
		self.ws = None

		self._dateLastMessage = None
		self._pongOk = False
		self._dateLastPullVolume = None
		self._dateLastPullFunding = None

		self._reconnectRequested = False


	def tblFuturesOrderbooks(self):
		return "bitmex_futures_orderbooks"


	def tblSwapsOrderbooks(self):
		return "bitmex_swaps_orderbooks"


	def tblFuturesUOrderbooks(self):
		return "bitmex_futures_uorderbooks"


	def tblSwapsUOrderbooks(self):
		return "bitmex_swaps_uorderbooks"


	def tblFuturesInstruments(self):
		return "bitmex_futures_instruments"


	def tblSwapsInstruments(self):
		return "bitmex_swaps_instruments"


	def pingOk(self, lstForMsg):
		tg = self.tgui
		ws = self.ws

		lstForMsg.clear()

		if ws  and  not ws.exited:
			now = Date("now")
			d = self._dateLastMessage
			if not d  or  d.secondsEarlier(now) > 5:
				self._pongOk = False

				# send ping
				sendOk = False
				try:
					ws.ws.send("ping")
					sendOk = True
				except Exception as e:
					m = "".join(traceback.format_exception(e.__class__, e, e.__traceback__))
					lstForMsg += [m]

				# wait for pong
				if not sendOk: return False
				for i in range(50):
					if self._pongOk: return True
					time.sleep(0.1)
			else:
				return True

		return False


	def _on_pong(self):
		self._pongOk = True
		

	def connectReconnect(self):
		tg = self.tgui
		retMsg = ""

		lstForMsg = []
		pingOk = self.pingOk(lstForMsg)
		retMsg = "\n".join(lstForMsg)

		if not self._reconnectRequested  and  pingOk: return retMsg

		if retMsg: retMsg += "\n"

		parNameLRD = "{exn}_lastReconnectDate".format(exn=self.name)
		now = Date("now")

		if self._reconnectRequested:
			retMsg += "\ta reconnect to {exn} was requested".format(exn=self.name)
			dtxt = tg.getPar(parNameLRD)
			d = Date(dtxt) if dtxt else None
			if d and d.minutesEarlier(now) < 60 / BITMEX_CONFIG['MAX_RECONNECTS_PER_HOUR']:
				
				retMsg += "\n\tskipping (reconnect limit)"

				return retMsg

		if retMsg: retMsg += "\n"
		retMsg += "(re)connecting to {exn}...".format(exn=self.name)

		if self.ws: self.ws.exit()
		self.ws = None

		ws = BitMEXWebsocket(
			#endpoint="wss://testnet.bitmex.com/api/v1",
			#api_key='GA1W_Swiy_uv1duLtxY5gfKg',
			#api_secret='BUgQuwZIqzajqtbGa4d_6Cez5nf7CVxM3OKjzyhizEkaCmP8',
			endpoint="wss://www.bitmex.com/realtime",
			api_key='oPYUv0JJe6hLO1RA7Aq6GJvW',  # account 1
			api_secret='u5QxztZ6PnA4I2UbuR7jYsfTKaQ0nDYS0kFEKxseSDzzBUSw',  # account 1
#			api_key = 'FMQIpxl-A2Ji0ADn3Tg1j0YX',  # account 2
#			api_secret = 'krWXgosAUlvNthCXPkvf3shucre37N-7-5fOiyuu5Txmyi46', # account 2
			symbol="",
		)

		if not ws: raise Exception("could not connect to the exchange's server")
		self.ws = ws

		on_message = ws.ws.on_message
		def myOnMessage(obj, m):
			self._dateLastMessage = Date("now")
			if 'pong' in m:
				self._on_pong()
				return

			return on_message(obj, m)

		ws.ws.on_message = myOnMessage

		self._reconnectRequested = False
		tg.setPar(parNameLRD, now.toText())

		return retMsg


	def bitmexRest(self, arg):
		"""Return the json object containing the server's response"""

		url = "https://www.bitmex.com/api/v1/" + arg

		rsp = requests.get(url,
			headers = {'Content-Type': 'application/json'},
		)

		code = rsp.status_code

		if code != 200: raise Exception("the server responded with code {code}".format(code=code))

		s = rsp.content.decode('utf-8')
		j = json.loads(s)

		return j


	def _convertInstrumentJson(self, r):
		s = r['symbol']

		ret = {
			'instrument_id': s,
			'delivery': '',
			'alias': '',
		}

		return ret


	def _getInsClsById(self, s):
		if re.search(r'^[A-Z]{4}[0-9]{2}$', s):
			return InstrumentFutures
		elif re.search(r'^[A-Z]{6}$', s):
			return InstrumentSwaps

		raise Exception("cannot determine the instrument type of `{s}'".format(s=s))


	def downloadInstruments(self):
		tg = self.tgui

		j = self.bitmexRest("instrument/active")

		self.instrumentsFutures.clear()
		self.instrumentsSwaps.clear()
		CTI = BITMEX_CONFIG['CONTRACTS_TO_IGNORE']
		for rr in j:
			r = self._convertInstrumentJson(rr)
			iid = r['instrument_id']
			if iid.upper() in CTI: continue

			InstrumentClass = self._getInsClsById(iid)
			ins = InstrumentClass(r)

			if ins.getCoin().upper() in Config.COINS[self.name]:
				if isinstance(ins, InstrumentFutures):
					self.instrumentsFutures += [ins]
				elif isinstance(ins, InstrumentSwaps):
					self.instrumentsSwaps += [ins]
				else: assert 0

		for (tbl, instruments) in (
			(self.tblFuturesInstruments(), self.instrumentsFutures),
			(self.tblSwapsInstruments(), self.instrumentsSwaps),
		):
			self.saveNewInstruments(tbl, instruments)

		self.sortInstruments()


	def sortInstruments(self):
		def sortKeyFutures(ins):
			return Config.COINS[self.name].index(ins.getCoin()),

		def sortKeySwaps(ins):
			return Config.COINS[self.name].index(ins.getCoin())

		for (instruments, sortKey) in (
			(self.instrumentsFutures, sortKeyFutures),
			(self.instrumentsSwaps, sortKeySwaps),
		):

			instruments.sort(key = sortKey)


	def pullOrderbooks(self):
		tg = self.tgui
		ws = self.ws
		if 'orderBookL2' not in ws.data.keys(): raise Exception("the orderbook is unavailable")

		# Prepare the ob dictionary

		# ob is a dictonary of the following structure:
		#	instrument_id: {'bids': [...], 'asks': [...]}
		ob = {}
		for ins in self.instrumentsFutures + self.instrumentsSwaps:
			ob[ins.instrument_id] = {
				'bids': [], 'asks': [],
			}

		for rr in ws.data['orderBookL2']:
			sym = rr['symbol']
			if sym not in ob.keys(): continue
			side = rr['side']
			p = float(rr['price'])
			sz = int(rr['size'])

			r = [p, sz, 0]
			if side.lower() == 'sell':
				ob[sym]['asks'] += [r]
			elif side.lower() == 'buy':
				ob[sym]['bids'] += [r]
			else: raise Exception("unsupported `side' value")

		# sort the bids and asks lists by price and limit their size

		MREC = BITMEX_CONFIG['MAX_N_ORDERBOOK_RECORDS']
		for sym in ob.keys():
			ob[sym]['bids'].sort(key=lambda r: r[0], reverse=True)
			ob[sym]['asks'].sort(key=lambda r: r[0])

			# limit the number of price levels

			for direction in ["bids", "asks"]:
				ob[sym][direction] = ob[sym][direction][0:MREC]

		# save the ob data to the DB

		for (instruments, tbl) in (
			(self.instrumentsFutures, self.tblFuturesOrderbooks()),
			(self.instrumentsSwaps, self.tblSwapsOrderbooks()),
		):
			for ins in instruments:
				now = Date("now")
				iid = ins.instrument_id

				j = ob[iid]
				b = pickle.dumps(j)
				tg.execute("""
INSERT INTO {tbl} (`instrument_id`, `date`, `pickle`)
VALUES (%s, %s, %s)
""".format(tbl=tbl), [ins.instrument_id, now.toText(), b])


	def _extractVolumeAndTurnover(self, sym, r):
		sym = sym.upper()
		v = float(r['volume24h'])
		to = float(r['turnover24h']) * 1e-8

		if sym == 'XBTUSD':
			(v, to) = (to, v)

		return (v, to)


	def pullVolume(self):
		tg = self.tgui

		now = Date("now")
		d = self._dateLastPullVolume
		UP = Config.VOLUME24H_UPDATE_PERIOD
		if d  and  d.minutesEarlier(now) < UP:
			self.log("\t\ttoo soon, skipping")
			return

		self.log("\t\tpulling volume data...")
		self._dateLastPullVolume = now

		j = self.bitmexRest("stats")
		self._extractVolumeSymbols(j)

		rvs = self.rawVolumeSymbols
		tbl = self.tblVolumes()
		for r in j:
			rsym = r['rootSymbol']
			cur = r['currency']

			for bcur in ("XBT", "USD"):
				sym = (rsym + bcur).upper()
				if sym not in rvs: continue

				if cur not in ['XBt']: raise Exception('unexpected volume currency: {cur}'.format(cur=cur))

				(v, to) = self._extractVolumeAndTurnover(sym, r)

				# delete the old v, to for the current exch/sym
				tg.execute("""
DELETE FROM {tbl}
WHERE `exchange` = %s and `symbol` = %s
""".format(tbl=tbl), [self.name, sym])

				# save the new values of v, to
				tg.execute("""
INSERT INTO {tbl}
(`exchange`, `symbol`, `volume`, `turnover`, `last_update`)
VALUES (%s, %s, %s, %s, %s)
""".format(tbl=tbl), [self.name, sym, v, to, now.toText()])


	def universalSymbolName(self, sym):
		sym = sym.upper()
		sym = re.sub(r'^XBT', r'BTC', sym)
		sym = re.sub(r'XBT$', r'BTC', sym)

		return sym


	def _extractVolumeSymbols(self, j):
		"""Extract symbols for volume from the json object returned
		by the `stats' endpoint and put them in rawVolumeSymbols
		"""

		# Extract

		syms = ["XBTUSD"]
		for r in j:
			rootSym = r['rootSymbol']

			syms += [(rootSym + "XBT").upper()]
			syms += [(rootSym + "USD").upper()]

		syms = list(filter(
			lambda sym: sym in self._SUPPORTED_VOLUME_SYMBOLS,
			syms
		))
		syms.sort()

		rvs = self.rawVolumeSymbols
		rvs.clear()
		rvs += syms


	def getVolumeUnit(self, sym):
		# NOTE: this function uses 'universal' symbols, not raw

		sym = sym.upper()
		if sym == 'BTCUSD': return "BTC"
		elif sym == 'ETHUSD': return "Contr"
		elif len(sym) >= 6  and  re.search(r'BTC$', sym):
			u = re.sub(r'(.*)BTC$', r'\1', sym)
			if not u: raise Exception("empty unit string for {sym}".format(sym=sym))
			return u

		raise Exception("can't determine the volume unit for {sym}".format(sym=sym))


	def getTurnoverUnit(self, sym):
		# NOTE: this function uses 'universal' symbols, not raw

		sym = sym.upper()
		if sym == 'BTCUSD': return "USD"
		elif sym == 'ETHUSD': return "BTC"
		elif len(sym) >= 6  and  re.search(r'BTC$', sym): return "BTC"

		raise Exception("can't determine the volume unit for {sym}".format(sym=sym))


	def _checkIfFundingRequiresReconnect(self,
		sym, fr, frPr, ts1, ts2
	):
		if self._reconnectRequested: return

		tg = self.tgui
		tbl = self.tblFunding()

		rs = tg.execute("""
SELECT * FROM {tbl}
WHERE `symbol` = %s LIMIT 1
""".format(tbl=tbl), [sym])

		for r in rs:
			d1 = Date(ts1)
			d2 = Date(ts2)
			now = Date("now")
			if abs(r['fundingRate'] - fr) < 1e-10:
				self.log("\t\trequest reconnect: same fundingRate: {fr1} vs {fr2}".format(fr1=r['fundingRate'], fr2=fr))
				self._reconnectRequested = True

			if abs(r['fundingRatePredicted']-frPr) < 1e-10:
				self.log("\t\trequest reconnect: same fundingRatePredicted: {fr1} vs {fr2}".format(fr1=r['fundingRatePredicted'], fr2=frPr))
				self._reconnectRequested = True

			if now.minutesEarlier(d1) < 0:
				self.log("\t\trequest reconnect: negative time1 to funding")
				self._reconnectRequested = True

			if now.minutesEarlier(d2) < 0:
				self.log("\t\trequest reconnect: negative time2 to funding")
				self._reconnectRequested = True

			break
				


	def pullFunding(self):
		tg = self.tgui
		ws = self.ws

		now = Date("now")
		d = self._dateLastPullFunding
		UP = Config.FUNDING_UPDATE_PERIOD
		if d  and  d.minutesEarlier(now) < UP:
			self.log("\t\ttoo soon, skipping")
			return

		#if 'funding' not in ws.data.keys():
		if 'instrument' not in ws.data.keys():
			self.loge("the websocket doesn't have funding data")
			return

		self.log("\t\tpulling funding data...")
		self._dateLastPullFunding = now

		#fs = ws.data['funding']
		fs = ws.data['instrument']

		tbl = self.tblFunding()
		for f in fs:
			sym = f['symbol']
			if self.universalSymbolName(sym) not in \
				Config.FUNDING_SYMBOLS: continue

			ts1 = re.sub(r'[TZ]', r' ',f['fundingTimestamp']).strip()
			ts2 = Date(ts1).plusHours(8).toText()

			self._checkIfFundingRequiresReconnect(
				sym,
				float(f['fundingRate']),
				float(f['indicativeFundingRate']),
				ts1, ts2,
			)
			
			# delete the old values for the current exch/sym
			tg.execute("""
DELETE FROM {tbl}
WHERE `symbol` = %s
""".format(tbl=tbl), [sym])

			tg.execute("""
INSERT INTO {tbl}
(symbol, fundingRate, fundingRatePredicted, timestamp, timestampPredicted, last_update)
VALUES (%s, %s, %s, %s, %s, %s)
""".format(tbl=tbl), [
	sym,
	float(f['fundingRate']),
	float(f['indicativeFundingRate']),
	ts1,
	ts2,
	now.toText(),
])
