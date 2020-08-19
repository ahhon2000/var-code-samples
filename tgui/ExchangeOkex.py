import requests
import pickle
import os, sys
import time
import json
import re
from websocket import WebSocket, ABNF
from websocket import WebSocketTimeoutException, WebSocketConnectionClosedException
import queue
import zlib

import Config
from Exchange import Exchange
from Date import Date
from Instrument import InstrumentFutures, InstrumentSwaps


class ExchangeOkex(Exchange):
	def __init__(self, tg):
		Exchange.__init__(self, tg)
		self.name = "OKEx"
		self.ws = None
		self._recvQueue = queue.Queue()
		self._fundingSubscriptions = []
		self._dateLastPullFunding = None
		self._fundingJsonCache = {}  # format: {sym: json, ...}


	def _inflate(self, data):
		decompress = zlib.decompressobj(
			-zlib.MAX_WBITS
		)
		inflated = decompress.decompress(data)
		inflated += decompress.flush()
		return inflated


	def tblFuturesOrderbooks(self):
		return "okex_futures_orderbooks"


	def tblSwapsOrderbooks(self):
		return "okex_swaps_orderbooks"


	def tblFuturesUOrderbooks(self):
		return "okex_futures_uorderbooks"


	def tblSwapsUOrderbooks(self):
		return "okex_swaps_uorderbooks"


	def tblFuturesInstruments(self):
		return "okex_futures_instruments"


	def tblSwapsInstruments(self):
		return "okex_swaps_instruments"


	def okexReq(self, arg):
		"""Return the json object containing the server's response"""

		url = "https://www.okex.com/api/" + arg

		rsp = requests.get(url,
			headers = {'Content-Type': 'application/json'},
		)

		code = rsp.status_code

		if code != 200: raise Exception("the server responded with code {code}".format(code=code))

		s = rsp.content.decode('utf-8')
		j = json.loads(s)

		return j


	def downloadInstruments(self):
		tg = self.tgui
		for (instruments, apiBase, tbl, InstrumentClass) in (
			(
				self.instrumentsFutures,
				'futures/v3/instruments',
				self.tblFuturesInstruments(),
				InstrumentFutures,
			), (
				self.instrumentsSwaps,
				'swap/v3/instruments',
				self.tblSwapsInstruments(),
				InstrumentSwaps,
			),
		):
			instruments.clear()

			j = self.okexReq(apiBase)

			for r in j:
				ins = InstrumentClass(r)
				if ins.getCoin().upper() in Config.COINS[self.name]:
					instruments += [ins]
			self.saveNewInstruments(tbl, instruments)

		self.sortInstruments()


	def sortInstruments(self):
		def sortKeyFutures(ins):
			a = ins.alias
			ao = None
			if a == 'this_week': ao = 0
			elif a == 'next_week': ao = 1
			elif a == 'quarter': ao = 2
			else: ao = 3

			return (
				Config.COINS[self.name].index(ins.getCoin()),
				ao,
			)

		def sortKeySwaps(ins):
			return Config.COINS[self.name].index(ins.getCoin())

		for (instruments, sortKey) in (
			(self.instrumentsFutures, sortKeyFutures),
			(self.instrumentsSwaps, sortKeySwaps),
		):

			instruments.sort(key = sortKey)


	def pullOrderbooks(self):
		for ctype in (
			"futures",
			"swaps",
		):
			self._pullOrderbooks(ctype=ctype)


	def _pullOrderbooks(self, ctype="futures"):
		tg = self.tgui

		apiBase = None
		apiLastWrd = None
		instruments = None
		tbl = None
		if ctype == 'futures':
			apiBase = 'futures/v3/instruments'
			apiLastWrd = "book"
			instruments = self.instrumentsFutures
			tbl = self.tblFuturesOrderbooks()
		elif ctype == 'swaps':
			apiBase = 'swap/v3/instruments'
			apiLastWrd = "depth"
			instruments = self.instrumentsSwaps
			tbl = self.tblSwapsOrderbooks()
		else: raise Exception("wrong ctype")

		bookSize = 200

		pids = []
		sleepSec = 2 / 20.  # time btw requests
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
					j = self.okexReq("{apiBase}/{instrument_id}/{apiLastWrd}?size={sz}".format(
	apiBase = apiBase,
	instrument_id = ins.instrument_id,
	sz = bookSize,
	apiLastWrd = apiLastWrd,
))

					now = Date("now")
					b = pickle.dumps(j)
					tg.execute("""
INSERT INTO {tbl} (`instrument_id`, `date`, `pickle`)
VALUES (%s, %s, %s)
""".format(tbl=tbl), [ins.instrument_id, now.toText(), b])
				except Exception as e:
					sys.stderr.write("error: " + str(e) + "\n")

				sys.exit(0)

		for pid in pids:
			(pid2, st) = os.waitpid(pid, 0)


	def pullVolume(self):
		pass


	def _symToSymOkex(self, sym):
		return re.sub(r'USD', r'-USD-', sym) + "SWAP"


	def _subscribeToFunding(self):
		"""Subscribe to funding rates channels, if necessary"""

		q = self._recvQueue

		for sym in Config.FUNDING_SYMBOLS:
			symOkex = self._symToSymOkex(sym)

			if symOkex in self._fundingSubscriptions: continue

			self.log("\tsubscribing to funding rates for {symOkex}...".format(symOkex=symOkex))

			ch = "swap/funding_rate:{symOkex}".format(
				symOkex = symOkex,
			)
			self._wsSendRequest({
				"op": "subscribe",
				"args": [ch],
			})

			#self._recvUntilTimeout(timeout=2)
			self._recvUntilTimeout(timeout=1)

			success = False
			while not q.empty():
				j = q.get()
				if isinstance(j, dict)  and \
					"event" in j.keys()  and \
					j["event"] == "subscribe"  and \
					j["channel"] == ch:

					self._fundingSubscriptions += [symOkex]
					success = True
					break

				q.put(j)

			if success: self.log("\t\tsuccess")
			else: self.loge("\tno subscription confirmation was received for {symOkex}".format(symOkex=symOkex))


	def _getFundingFromQueue(self, sym):
		"""Find in the queue and return the latest json object for sym

		Return None if no object could be found (even in the cache)
		"""

		symOkex = self._symToSymOkex(sym)
		q = self._recvQueue

		ret = None
		for i in range(q.qsize()):
			j = q.get()
			if isinstance(j, dict) and "table" in j.keys() and \
				j['table'] == 'swap/funding_rate'  and \
				'data' in j.keys()  and \
				len(j['data'])  and \
				j['data'][0]['instrument_id'] == symOkex:

				ret = j
			else:
				q.put(j)

		# in case the server hasn't sent an update, try to use the cache
		if ret is None: ret = self._fundingJsonCache.get(sym, None)
		self._fundingJsonCache[sym] = ret
			
		return ret


	def pullFunding(self):
		tg = self.tgui

		ws = self.ws

		if ws and ws.connected: self._recvUntilTimeout()

		now = Date("now")
		d = self._dateLastPullFunding
		UP = Config.FUNDING_UPDATE_PERIOD
		if d  and  d.minutesEarlier(now) < UP:
			self.log("\t\ttoo soon, skipping")
			return

		if not ws  or  not ws.connected:
			self.logw("\t\tcan't access funding data: websocket connection is closed")
			return

		self._subscribeToFunding()

		# Process the data from the channel

		tbl = self.tblFunding()
		for sym in Config.FUNDING_SYMBOLS:
			j = self._getFundingFromQueue(sym)

			if not isinstance(j, dict): raise Exception("a dict was expected as the funding data container, not {tj} (sym={sym})".format(tj=str(type(j)), sym=sym))
			if not j: raise Exception("no funding data")

			# delete the old values for the current exch/sym
			tg.execute("""
DELETE FROM {tbl}
WHERE `symbol` = %s
""".format(tbl=tbl), [sym])

			f = j['data'][0]

			ts1 = ''
			ts2 = ''
			if 'funding_time' in f.keys():
				ts1 = re.sub(r'[TZ]', r' ',f['funding_time']).strip()
				ts2 = ts1

			tg.execute("""
INSERT INTO {tbl}
(symbol, fundingRate, fundingRatePredicted, timestamp, timestampPredicted, last_update)
VALUES (%s, %s, %s, %s, %s, %s)
""".format(tbl=tbl), [
	sym,
	float(f['funding_rate']),
	float(f['funding_rate']),
	ts1,
	ts2,
	now.toText(),
])
		# END for sym ...

		self._dateLastPullFunding = now


	def universalSymbolName(self, sym):
		sym = sym.upper()
		return sym


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

		self.ws = None

		# empty the queue
		q = self._recvQueue
		while not q.empty(): q.get()

		# clear the subscriptions
		self._fundingSubscriptions.clear()

		# connect
		ws = WebSocket()
		ws.connect("wss://real.okex.com:8443/ws/v3")

		self.ws = ws

		return retMsg


	def _wsSendRequest(self, req):
		ws = self.ws

		b = json.dumps(req).encode('utf-8')
		ws.send(b, opcode = ABNF.OPCODE_TEXT)


	def _recvUntilTimeout(self, timeout=2, max_qsize=0):
		ws = self.ws
		q = self._recvQueue

		flgTimeout = False
		flgConnOk = True
		while True:
			s = None
			try:
				ws.settimeout(timeout)
				data = ws.recv()
				if isinstance(data, str):
					s = data
				else:
					b = self._inflate(data)
					s = b.decode('utf-8')
			except WebSocketTimeoutException:
				flgTimeout = True
			except WebSocketConnectionClosedException:
				flgConnOk = False

			if not flgConnOk: break
			if flgTimeout: break
				
			if re.search(r'[^\s]', s):
				j = json.loads(s)
				q.put(j)

			if max_qsize and q.qsize() > max_qsize: break


	def predictedFRateApplicable(self):
		return False
