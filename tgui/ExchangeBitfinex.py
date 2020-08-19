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

class ExchangeBitfinex(Exchange):
	def __init__(self, tg):
		Exchange.__init__(self, tg)
		self.name = "Bitfinex"
		self.ws = None

		# _orderbooks format:
		#	keys:    instrument names;
		#	values:  {'bids': {...}, 'asks': {...}}
		#
		# bids and asks are dictionaries of the following format:
		#	keys: price_txt   values: amount (float)
		self._orderbooks = {}
		self._activeSubscriptions = []  # a list of instrument_id's


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


	def pingOk(self, lstForMsg):
		lstForMsg.clear()
		if not self.ws  or  not self.ws.conn.isAlive():
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
				self.ws.stop()
			except:
				pass

		self.ws = None
		self._activeSubscriptions.clear()

		ws = BtfxWss()
		self.ws = ws
		ws.start()

		flgNoConnection = True
		for i in range(10):
			if ws.conn.connected.is_set():
				flgNoConnection = False
				break
			time.sleep(1)

		if flgNoConnection: raise Exception("failed to establish connection")

		# Initialise orderbooks

		self._orderbooks.clear()

		return retMsg


	def _updateOrderbook(self, iid, r):
		if not isinstance(r, list): raise Exception("a list was expected")

		if len(r) < 3: raise Exception("wrong list size")

		if not isinstance(r[0], (str, int, float)): raise Exception("r[0] must be a string or a number, not " + str(r[0]))
		p = float(r[0])
		nOrders = int(r[1])
		am = float(r[2])

		assert p > 0
		assert nOrders >= 0

		# determine the direction
		direction = None
		if am > 0: direction = "bids"
		else: direction = "asks"

		# add/update/remove price levels

		ob = self._orderbooks[iid][direction]
		ptxt = self._priceToKey(p)
		if nOrders > 0:
			# add/update the price level
			ob[ptxt] = abs(am)
		elif nOrders == 0:
			# remove the price level
			ob.pop(ptxt, None)
		else: assert 0


	def _priceToKey(self, p):
		return "%.6f" % p


	def _subscribeIfNecessary(self, iids):
		"""Subscribe to orderbooks, if necessary"""

		ws = self.ws
		for iid in iids:
			if iid in self._activeSubscriptions: continue

			try:
				self.log("\tsubscribing to {iid}...".format(iid=iid))
				ws.subscribe_to_order_book(
					iid,
					prec = "P0",
					len = "100",
				)
				self._activeSubscriptions += [iid]
			except Exception as e:
				m = str(e) + ": " + "".join(traceback.format_exception(e.__class__, e, e.__traceback__))
				self.loge("\tfailed to subscribe to {iid}: {m}".format(iid=iid, m=m))

			# get the initial orderbook snapshot

			self._orderbooks[iid] = {
				'bids': {}, 'asks': {},
			}

			self.log("\tretrieving the initial orderbook for {iid}...".format(iid=iid))
			g = None
			try:
				self.log("\t\tcall to ws.books()...")
				books = ws.books(iid)
				flgNoData = True
				for i in range(100):
					if not books.empty():
						flgNoData = False
						break
					time.sleep(0.05)

				if flgNoData:
					self.loge("\t\tthe queue is empty")
				else:
					self.log("\t\tcall to books.get()..")
					g = books.get()
			except Exception as e:
				m = str(e) + ": " + "".join(traceback.format_exception(e.__class__, e, e.__traceback__))
				self.loge("\tfailed to retrieve the initial orderbook for {iid}: {m}".format(iid=iid, m=m))

			if not g:
				self.loge("\tthe websocket failed to retrieve initial data")
				self.log("\tunsubscribing from {iid}".format(iid=iid))
				self.unsubscribeFromOrderbook(iid)

				continue

			if not g[0]  or  not g[0][0]: raise Exception("unexpected format of initial orderbook data")

			self.log("\tsaving initial orderbook data for {iid}".format(iid=iid))
			for r in g[0][0]:
				self._updateOrderbook(iid, r)

	
	def unsubscribeFromOrderbook(self, iid):
		ws = self.ws
		try:
			self._activeSubscriptions.remove(iid)
			ws.unsubscribe_from_order_book(iid)
		except Exception as e:
			m = str(e) + ": " + "".join(traceback.format_exception(e.__class__, e, e.__traceback__))
			self.loge("\t\tcould not unsubscribe from {iid}: {m}".format(iid=iid, m=m))



	def downloadInstruments(self):
		tg = self.tgui
		ws = self.ws
		self.instrumentsFutures.clear()
		self.instrumentsSwaps.clear()

		iids = list(c + "USD" for c in Config.COINS[self.name])
		iids += list(c + "BTC" for c in Config.COINS[self.name])
		iids.remove("BTCBTC")

		self.log("subscribing to instruments...")
		self._subscribeIfNecessary(iids)
		for iid in self._activeSubscriptions:
			# Initialise the Instrument object
			self.instrumentsSwaps += [InstrumentSwaps({
				'instrument_id': iid,
				'delivery': '',
			})]

		# Save and sort the instruments

		self.log("saving the instruments to the db...")
		for (tbl, instruments) in (
			(self.tblFuturesInstruments(), self.instrumentsFutures),
			(self.tblSwapsInstruments(), self.instrumentsSwaps),
		):
			self.saveNewInstruments(tbl, instruments)

		self.log("sorting the instruments...")
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


	def pullOrderbooks(self):
		tg = self.tgui
		ws = self.ws

		# retrieve data for each instrument

		for ins in self.instrumentsSwaps:
			books = ws.books(ins.instrument_id)
			
			for i in range(100000):
				if books.empty(): break
				g = books.get()
				if not g: raise Exception("the websocket failed to retrieve any data")
				if not g  or  not g[0]  or  not g[0][0]: raise Exception("unexpected format of orderbook data")

				self._updateOrderbook(ins.instrument_id,g[0][0])

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


	def pullVolume(self):
		pass


	def pullFunding(self):
		pass
