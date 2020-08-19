import traceback
import time
import json
import pickle
from websocket import WebSocket, ABNF, WebSocketTimeoutException
import queue

import Config
from Date import Date
from ExchangeBitfinex import ExchangeBitfinex

class ExchangeBitfinex2(ExchangeBitfinex):
	def __init__(self, tg):
		ExchangeBitfinex.__init__(self, tg)
		self._recvQueue = queue.Queue()
		self._channelIds = {}

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
		self._activeSubscriptions.clear()

		# empty the queue
		q = self._recvQueue
		while not q.empty(): q.get()

		# connect
		ws = WebSocket()
		ws.connect("wss://api.bitfinex.com/ws/")

		self.ws = ws

		# receive connection confirmation
		self._recvUntilTimeout(timeout=2)
		rsp = q.get()
		if not isinstance(rsp, dict)  or  'event' not in rsp.keys() or \
			rsp['event'] != 'info':
			raise Exception("failed to establish connection")

		# Initialise orderbooks
		self._orderbooks.clear()

		return retMsg


	def _subscribeIfNecessary(self, iids):
		"""Subscribe to orderbooks, if necessary"""

		ws = self.ws
		for iid in iids:
			if iid in self._activeSubscriptions: continue

			try:
				self.log("\tsubscribing to {iid}...".format(iid=iid))
				self._subscribeToOrderbook(iid)
			except Exception as e:
				m = str(e) + ": " + "".join(traceback.format_exception(e.__class__, e, e.__traceback__))
				self.loge("\tfailed to subscribe to {iid}: {m}".format(iid=iid, m=m))

			if iid not in self._activeSubscriptions: continue

			# get the initial orderbook snapshot

			self._orderbooks[iid] = {
				'bids': {}, 'asks': {},
			}

			self.log("\tretrieving the initial orderbook for {iid}...".format(iid=iid))
			g = None
			try:
				self._recvUntilTimeout(stopOnInsId=iid)
				g = self._getOrderbookItem(iid)
			except Exception as e:
				m = str(e) + ": " + "".join(traceback.format_exception(e.__class__, e, e.__traceback__))
				self.loge("\tfailed to retrieve the initial orderbook for {iid}: {m}".format(iid=iid, m=m))

			if not g:
				self.loge("\tthe websocket failed to retrieve initial data")
				self.log("\tunsubscribing from {iid}".format(iid=iid))
				self.unsubscribeFromOrderbook(iid)

				continue

			if not isinstance(g, list): raise Exception("a list was expected as the initial snapshot")
			if len(g) < 2: raise Exception("expected at least 2 elements in the initial snapshot list")

			if not isinstance(g[1], list): raise Exception("unexpected format of initial orderbook data")

			self.log("\tsaving initial orderbook data for {iid}".format(iid=iid))
			for r in g[1]:
				self._updateOrderbook(iid, r)


	def _sendRequest(self, req):
		ws = self.ws

		# empty the queue
		q = self._recvQueue
		while not q.empty(): q.get()

		b = json.dumps(req).encode('utf-8')
		ws.send(b, opcode = ABNF.OPCODE_BINARY)


	def _recvUntilTimeout(self, timeout=2, max_qsize=0, stopOnInsId=""):
		ws = self.ws
		q = self._recvQueue

		flgTimeout = False
		while True:
			s = None
			try:
				print("debug recv [...")
				ws.settimeout(timeout)
				s = ws.recv()
				print("debug ]")
			except WebSocketTimeoutException:
				flgTimeout = True

			if flgTimeout: break
				
			j = json.loads(s)
			q.put(j)
			print("debug qsz=", q.qsize())

			if stopOnInsId  and  isinstance(j, list)  and  \
				j[0] == self._channelIds[stopOnInsId]:
				break
			if max_qsize and q.qsize() > max_qsize: break


	def _subscribeToOrderbook(self, iid):
		ws = self.ws

		req = {
			"event": "subscribe",
			"channel": "book",
			"symbol": iid,
			"freq": "F1",  # updates every 2 seconds
#			"prec": "P0",
			"prec": "P2",
			"len": "100",
		}
		self._sendRequest(req)

		q = self._recvQueue
		nRetriesToGetRsp = 100
		while True:
			if q.empty():
				if nRetriesToGetRsp <= 0: raise Exception("exceeded the number of retries to get subscription confirmation")
				nRetriesToGetRsp -= 1
				self._recvUntilTimeout(max_qsize=100)

			rsp = q.get()
			if not isinstance(rsp, dict): continue
			if 'event' not in rsp.keys(): continue

			if rsp['event'] == 'error':
				raise Exception("the server returned code {code}: {msg}".format(code=rsp['code'], msg=rsp['msg']))
			elif rsp['event'] == 'subscribed':
				if rsp['pair'] != iid: raise Exception("sent a request to subscribe to `{iid}' but the server subsribed us to `{ch}' instead".format(iid=iid, ch=rsp['pair']))
				self._channelIds[iid] = rsp['chanId']
				self._activeSubscriptions += [iid]
				return

		raise Exception("no server response on subscription")



	def _getOrderbookItem(self, iid):
		"""Get one item of orderbook data from the queue

		(either an initial snapshot or one update)
		"""

		chid = self._channelIds[iid]

		q = self._recvQueue
		qsz = q.qsize()

		for i in range(qsz):
			g = q.get()
			if isinstance(g, list)  and  g[0] == chid:
				return g
			q.put(g)

		return None
	
	def unsubscribeFromOrderbook(self, iid):
		ws = self.ws
		try:
			self._activeSubscriptions.remove(iid)
			chid = self._channelIds.pop(iid)

			self._sendRequest({
				'event': 'unsubscribe',
				'chanId': chid,
			})
		except Exception as e:
			m = str(e) + ": " + "".join(traceback.format_exception(e.__class__, e, e.__traceback__))
			self.loge("\t\tcould not unsubscribe from {iid}: {m}".format(iid=iid, m=m))


	def pullOrderbooks(self):
		tg = self.tgui
		ws = self.ws
		q = self._recvQueue

		# retrieve data for each instrument

		N = 500 * len(Config.COINS[self.name])
		self._recvUntilTimeout(timeout=1, max_qsize=N)
		# trim the queue: drop older items
		while q.qsize() > N: q.get()

		for ins in self.instrumentsSwaps:
			iid = ins.instrument_id
			while True:
				g = self._getOrderbookItem(iid)
				if g is None: break

				if not isinstance(g, list) or len(g) < 3:
					continue

				self._updateOrderbook(iid, g)

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
