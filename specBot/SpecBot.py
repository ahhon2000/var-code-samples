import os, sys
import sqlite3
import re
import subprocess
import shutil
from Config import DB_FILE, LOG_FILE, MAX_LOG_SZ
from Config import WM_CERTIFICATE_FILE, WM_KEY_FILE
from Config import MIN_MINUTES_BTW_REQUESTS
import Config
from Transaction import Transaction
from Currency import Currency, CurrencyPair
from Wallet import Wallet
from MarketState import MarketState
from Date import Date
from Bid import Bid
import xml.etree.ElementTree as ET
import time
import copy
import smtplib
from email.mime.text import MIMEText
import mysql.connector as mariadb

from defs import *
import defs

class SpecBot:
	def __init__(self,
		dbFile="",
		dbName = "",
		currency1str = "",
		currency2str = "",
		readOnly = True,
		tmpDir = "",
		wget = None,
	):
		self.dbFile = dbFile
		self.dbName = dbName
		self.marketState = None
		self.wallet = Wallet(self)
		self.readOnly = readOnly
		self.tmpDir = tmpDir

		dbf = Config.DB_FORMAT

		if not wget: raise Exception("wget parameter was not specified")
		self.wget = wget

		if not tmpDir: raise Exception("tmpDir was not specified")
		if dbf == Config.DBF_SQLITE3 and not dbFile:
			raise Exception("dbFile was not specified")

		if dbf == Config.DBF_MARIADB and not dbName:
			raise Exception("dbName was not specified")

		if dbf == Config.DBF_SQLITE3:
			s = "file:%s" % dbFile
			if readOnly:
				s = "file:%s?mode=ro" % dbFile

			self.db = sqlite3.connect(s, uri=True)
			# to access columns by name:
			self.db.row_factory = sqlite3.Row
			self.cursor = self.db.cursor()
		elif dbf == Config.DBF_MARIADB:
			user = Config.DB_USER
			pw = Config.DB_PASSWORD
			if readOnly:
				user = Config.DB_USER_RO
				pw = Config.DB_PASSWORD_RO

			import mysql.connector as mariadb
			self.db = mariadb.connect(
				user = user,
				password = pw,
				database = dbName,
			)
			self.cursor = self.db.cursor(buffered=True)
		else: raise Exception("unknown DB_FORMAT=%d" % dbf)

		if not readOnly:
			self.createTables()

			pid = self.getPar("specBot_pid")
			if pid:
				pids = [p for p in os.listdir('/proc') if p.isdigit()]
				if pid in pids: raise Exception("another instance is running (pid = %s)" % pid)

			pid = os.getpid()
			self.setPar("specBot_pid", str(pid))

		# Take care of the two currencies in this object and the db

		c1 = self.getCurrencyBy(currency1str)
		c2 = self.getCurrencyBy(currency2str)

		# add the currencies if they don't exist
		for (c, s) in [(c1, currency1str), (c2, currency2str)]:
			if c:
				continue

			self.execute("""
				INSERT INTO currencies (name)
				VALUES (?)
			""", [s])

		c1 = self.getCurrencyBy(currency1str)
		c2 = self.getCurrencyBy(currency2str)

		self.curPair = CurrencyPair(self, c1, c2)
		
		self._dateLastNoMSEmail = None
		self._reasonMSDownloadFailed = ""
		self._last_timeAvgRates = {}


	def getTransactions(self):
		rs = self.execute("""
			SELECT * FROM transactions
			ORDER BY date1
""")

		ts = []
		for r in rs:
			t = Transaction(self, row=r)
			ts += [t]

		return ts


	def getTransactionBy(self, x):
		if isinstance(x, Transaction):
			return x

		if isinstance(x, int):
			rows = self.execute("""
				SELECT * FROM transactions
				WHERE `id` = ?
			""", [x])

			for r in rows:
				c = Transaction(self, row=r)
				return c

		return None


	def getBidBy(self, x):
		if isinstance(x, Bid):
			return x

		if isinstance(x, int):
			rows = self.execute("""
				SELECT * FROM bids
				WHERE `id` = ?
			""", [x])

			for r in rows:
				c = Bid(self, row=r)
				return c

		return None


	def getCurrencyBy(self, x):
		if isinstance(x, Currency):
			return x

		c = None
		if '_currencyCache' in self.__dict__.keys():
			c = self._currencyCache.get(x, None)
			if not(c is None): return c
		else:
			self._currencyCache = {}

		if isinstance(x, int):
			rows = self.execute("""
				SELECT * FROM currencies
				WHERE `id` = ?
			""", [x])

			for r in rows:
				c = Currency(row=r)
				break

		if isinstance(x, str):
			rows = self.execute("""
				SELECT * FROM currencies
				WHERE `name` = ?
			""", [x])

			for r in rows:
				c = Currency(row=r)
				break

		self._currencyCache[x] = c

		return c


	def getMarketStateBy(self, x):
		if isinstance(x, MarketState):
			return x

		if isinstance(x, int):
			rows = self.execute("""
				SELECT * FROM marketstates
				WHERE `id` = ?
			""", [x])

			for r in rows:
				c = MarketState(self, row=r)
				return c

		return None


	def createTables(self):
		self.execute(
			"""
			CREATE TABLE IF NOT EXISTS pars (
				`name` VARCHAR(64) PRIMARY KEY NOT NULL,
				`value` VARCHAR(256) NOT NULL DEFAULT ''
			)
			"""
		)

		self.execute(
			"""
			CREATE TABLE IF NOT EXISTS currencies (
				`id` INTEGER NOT NULL PRIMARY KEY,
				`name` text default ''
			)
			"""
		)

		self.execute(
			"""
			CREATE TABLE IF NOT EXISTS transactions (
				`id` INTEGER NOT NULL PRIMARY KEY,
				`status` INTEGER default 0,
				`amount` real default 0,
				`date1` text default '',
				`date2` text default '',
				`date1closed` text default '',
				`date2closed` text default '',
				`rate1` real default 0,
				`rate2` real default 0,
				`currency1` integer default 0,
				`currency2` integer default 0,
				`wm_tid1` text default '',
				`wm_tid2` text default '',
				`remainder1` real default 0,
				`remainder2` real default 0
			)
			"""
		)

		self.execute(
			"""
			CREATE TABLE IF NOT EXISTS marketstates (
				`id` INTEGER NOT NULL PRIMARY KEY,
				`date` text default ''
			)
			"""
		)

		row_format = ""
		if Config.DB_FORMAT == Config.DBF_MARIADB:
			row_format = "ROW_FORMAT = COMPRESSED"

		self.execute(
			"""
			CREATE TABLE IF NOT EXISTS bids (
				`id` INTEGER NOT NULL PRIMARY KEY,
				`currency1` integer default 0,
				`currency2` integer default 0,
				`amount1` real default 0,
				`amount2` real default 0,
				`place` integer default 0,
				`wm_tid` text not null default '',
				`marketstate` integer default 0
			) {row_format}
			""".format(
				row_format = row_format,
			)
		)


	def setPar(self, n, v):
		if self.execute("SELECT name FROM pars WHERE name=?", [n]):
			self.execute("""
				UPDATE pars SET value=? WHERE name=?
			""", [v, n])
		else:
			self.execute("""
				INSERT INTO pars (name, value)
				VALUES(?, ?)
			""", [n, v])


	def getPar(self, n):
		rows = self.execute("""
			SELECT value FROM pars WHERE name=?
		""", [n])

		v = ""
		if rows: v = rows[0]['value']

		return v


	def execute(self, r, t=[], nocommit=False):
		# execute request r providing it with tuple t
		dbf = Config.DB_FORMAT

		if dbf == Config.DBF_MARIADB:
			r = defs.sqliteToMysql(r)

		db = self.db
		c = self.cursor

		ex = c.execute(r, t)

		rows = None
		if dbf == Config.DBF_SQLITE3:
			rows = ex.fetchall()
		elif dbf == Config.DBF_MARIADB:
			rows = list(c)

		if dbf == Config.DBF_MARIADB  and  rows:
			# convert rows to a key/value format
			newRows = []
			for row in rows:
				row = dict(zip(c.column_names, row))
				newRows += [row]
			rows = newRows
		
		if not nocommit:
			if dbf == Config.DBF_SQLITE3 or \
				dbf == Config.DBF_MARIADB:
				#dbf == Config.DBF_MARIADB and not rows:

				db.commit()

		if isinstance(c.lastrowid, int):
			self.lastrowid = c.lastrowid

		return rows


	def run(self):
		try:
			self._run()
		except KeyboardInterrupt as e:
			self.cleanup()
			self.log("stopped by user")

	def cleanup(self):
		self.setPar("specBot_pid", "")


	def _run(self):
		self.log("*** The loop started ***")
		
		cy = 1
		while True:
			self.log("CYCLE # %d" % cy)
			self.cycle()
			self.log("END OF CYCLE")

			# schedule next cycle

			sec = 60 * MIN_MINUTES_BTW_REQUESTS
			dtxt = self.getPar("lastMarketstateDownloadDate")
			dn = Date("now")
			if dtxt:
				d = Date(dtxt)
				d2 = d.plusHours(MIN_MINUTES_BTW_REQUESTS/60.)

				sec = 60 * dn.minutesEarlier(d2) + 2
			if sec < 1: sec = 1

			d = dn.plusHours(sec / 3600.)
			self.log("next cycle scheduled for %s" % d.toNiceText())

			# wait till next cycle
			time.sleep(sec)

			cy += 1


	def unfinishedTransactions(self):
		"""Return the list of transactions whose status
		is open1, open2, closed1
		"""

		rs = self.execute("""
			SELECT * FROM transactions
			WHERE status = ? or status = ? or status = ?
			ORDER BY date1
		""", [TRST_OPEN1, TRST_OPEN2, TRST_CLOSED1])
		
		ts = []
		for r in rs:
			t = Transaction(self, row=r)
			ts += [t]

		return ts

	def _minProfitRate(self, t, quiet=False):
		"""return a tuple (rate, relativeProfit(rate))"""

		# work on the transaction's copy
		t = copy.copy(t)

		ms = self.marketState
		assert ms
		assert t.amount > 0

		cp = self.curPair
		cpr = self.curPair.reverse()

		if t.status == TRST_UNDEF: t.status = TRST_OPEN1
		elif t.status == TRST_CLOSED1:
			t.status = TRST_OPEN2
			t.remainder2 -= defs.calCommission(t.remainder2, cp[1])
		assert t.status in [TRST_OPEN1, TRST_OPEN2]

		tar1 = self.timeAvgRates()[cp]
		tar2 = self.timeAvgRates()[cpr]

		dur = t.getDuration2()
		if t.status == TRST_OPEN2  and  \
			Config.HOURS_MIN_REL_PROFIT_REVERSE != 0  and \
			dur > Config.HOURS_MIN_REL_PROFIT_REVERSE:

			t.rate2 = tar2
			if not quiet: self.log("minProfitRate() returned tar2 because the duration of the reverse transaction %.2f h exceeded %.2f h" % (
				dur, Config.HOURS_MIN_REL_PROFIT_REVERSE))

			return (tar2, t.profit(relative=True))

		mrp = Config.MIN_REL_PROFIT
		maxRateDev = Config.MAX_RATE_DEVIATION

		r0 = None
		f = None
		if t.status == TRST_OPEN1:
			r0 = tar1
			def f(tt, x):
				tt.rate1 = x
				return tt.profit(relative=True) - mrp
		elif t.status == TRST_OPEN2:
			r0 = tar2
			def f(tt, x):
				tt.rate2 = x
				return tt.profit(relative=True) - mrp
		else:
			raise Exception("unpredicted t.status = %d" % t.status)

		rmin = r0 * (1 - maxRateDev)
		rmax = r0 * (1 + maxRateDev)

		(r, dp) = defs.findZero(f, t, rmin, rmax)
		if r is None:
			assert r0
			r = r0
		else:
			r = defs.trim(r, rmin, rmax)

		if t.status == TRST_OPEN1:
			t.rate1 = r
		elif t.status == TRST_OPEN2:
			t.rate2 = r
		else:
			assert False

		rp = t.profit(relative=True)

		return (r, rp)


	def minProfitRate1(self, t, quiet=False):
		return self._minProfitRate(t, quiet)


	def minProfitRate2(self, t, quiet=False):
		return self._minProfitRate(t, quiet)


	def getAmountToTrade(self):
		a0 = Config.INITIAL_AMOUNT1
		M = Config.MAXIMUM_AMOUNT1

		assert a0 >= 0
		assert M >= 0

		if not a0  and  not M: raise Exception("either INITIAL_AMOUNT1 or MAXIMUM_AMOUNT1 must be positive")

		a = a0 if a0 else M
		if self.getPar('initial_amount1'):
			# if initial_amount1 is present in the DB then
			# try to set `a' to the last closed transaction's
			# remainder1
			rs = self.execute("""
				SELECT * FROM transactions WHERE status = ?
				ORDER BY date2closed DESC LIMIT 1
""", [defs.TRST_CLOSED2])
			for r in rs:
				t = Transaction(self, row=r)
				if t.remainder1: a = t.remainder1
				break
		else:
			# If initial_amount1 is not in the DB then the Config
			# default will be used (either a0 or M -- set above).
			# Here, we save that initial amount to the DB
			if not self.readOnly:
				self.setPar('initial_amount1', str(a))

		# set a to the allowed maximum if a exceeds it
		if M > 0  and  a > M:
			self.log("using the allowed maximum of %.2f as amount1 instead of %.2f" % (M, a))
			a = M

		assert a > 0.01

		return a


	def _checkCurrenciesAndPurses(self):
		specialPurseLetters = {
			"USD": "Z",
			"RUB": "R",
		}

		c1 = Config.CURRENCY1
		c2 = Config.CURRENCY2
		p1 = Config.PURSE1
		p2 = Config.PURSE2

		if str(self.curPair[0]) != c1: raise defs.NonMatchingCurPurseException("the sb currency doesn't match the currency in the Config file")
		if str(self.curPair[1]) != c2: raise defs.NonMatchingCurPurseException("the sb currency doesn't match the currency in the Config file")

		for (c, p) in [(c1, p1), (c2, p2)]:
			if c in specialPurseLetters.keys():
				if specialPurseLetters[c] != p[0]: raise defs.NonMatchingCurPurseException("the purse doesn't match the currency")
			else:
				if c[-1] != p[0]: raise defs.NonMatchingCurPurseException("the purse doesn't match the currency")


	def cycle(self):
		self._checkCurrenciesAndPurses()

		self.setPar("lastCycleDate", Date("now").toText())

		self.updateMarketState()
		ms = self.marketState
		if not ms:
			self._notifyNoMarketState()
			return
		else:
			self._notifyFixedNoMarketState()

		self.timeAvgRates(recalculate=True)
		self.downloadTransactionStatus()

		cp = self.curPair

		# unfinished transactions whose status is open1, open2, closed1
		utrs = self.unfinishedTransactions()

		# no unfinished transactions: try to open a new one
		if not utrs:
			am = self.getAmountToTrade()
			assert am > 0.01

			t = Transaction(
				specBot = self,
				amount = am,
				curPair = cp,
			)

			self.setRate1(t)
			t.placeBid()

		# process unfinished transactions
		for t in utrs:
			st = t.status
			if st == TRST_OPEN1:
				self.setRate1(t)
				t.uploadRate()
			elif st in [TRST_CLOSED1, TRST_OPEN2]:
				self.setRate2(t)
				if st == TRST_CLOSED1:
					t.placeBid(reverse=True)
				else:
					t.uploadRate()
			else: raise Exception("unpredicted transaction status = %d" % st)


	def setRate1(self, t):
		ms = self.marketState
		tar1 = self.timeAvgRates()[self.curPair]
		rsm = Config.RATE_SETTING_MODE
		if rsm == Config.RSM_SPREAD_AND_MIN_PROFIT:
			#
			# Mode `Spread and minimum relative profit'
			#
			t.rate1 = tar1
			rp = t.profit(relative=True)
			if rp < Config.MIN_REL_PROFIT:
				(t.rate1, rp) = self.minProfitRate1(t)
				self.log("used minProfitRate1() to guarantee a minimum profit of %.2f%% at rate1=%.4f" % (rp*100, t.rate1))
			else:
				self.log("used the market average to set rate1=%.4f expecting a profit of %.2f%%" % (t.rate1, rp*100))
			#
		elif rsm == Config.RSM_1TAR_2MIN_PROFIT:
			t.rate1 = tar1
		elif rsm in [
			Config.RSM_MIN_PROFIT, Config.RSM_SMART_MIN_PROFIT,
		]:
			#
			# Mode `Minimum relative profit'
			#     (or `Smart minimum relative profit')
			#
			(t.rate1, rp) = self.minProfitRate1(t)
		else:
			raise Exception("unpredicted value rsm = %d" % (rsm))


	def setRate2(self, t):
		ms = self.marketState
		tar2 = self.timeAvgRates()[self.curPair.reverse()]
		rsm = Config.RATE_SETTING_MODE
		if rsm in [
			Config.RSM_SPREAD_AND_MIN_PROFIT,
			Config.RSM_SMART_MIN_PROFIT,
		]:
			#
			# Mode `Spread and minimum relative profit'
			#
			t.rate2 = tar2
			rp = t.profit(relative=True)
			if rp < Config.MIN_REL_PROFIT:
				(t.rate2, rp) = self.minProfitRate2(t)
				self.log("used minProfitRate2() to guarantee a minimum profit of %.2f%% at rate2=%.4f" % (rp*100, 1/t.rate2))
			#
		elif rsm in [Config.RSM_MIN_PROFIT,Config.RSM_1TAR_2MIN_PROFIT]:
			#
			# Mode `Minimum relative profit'
			#
			(r2, rp) = self.minProfitRate2(t)
			t.rate2 = r2
		else:
			raise Exception("unpredicted value rsm = %d" % (rsm))


	def _wmXmlRequest(self, r, url, outerTag="wm.exchanger.response",
		wgetOptions = [],
		deleteTmpFiles = True,
	):

		qfn = self.tmpDir + "/.specBotRequest.xml"
		rfn = self.tmpDir + "/.specBotReply.xml"

		with open(qfn, "w") as fp:
			fp.write(r + "\n")

		cmd = list(wgetOptions)
		cmd += [
			"--certificate=" + WM_CERTIFICATE_FILE,
			"--private-key=" + WM_KEY_FILE,
			"--post-file=" + qfn,
			"-O", rfn,
			url,
		]
		st = self.wget.run(cmd)

		if st:
			self.logw("could not process wm xml request (wget exit status = %d; the request file is in `%s'; the reply file is in `%s')" % (st, qfn, rfn))
			return None

		if not os.path.isfile(rfn):
			self.logw("could not access the reply file `%s'" % rfn)
			return None

		xmlstr = "".join(open(rfn).readlines())
		for f in [qfn, rfn]:
			if deleteTmpFiles and os.path.isfile(f): os.unlink(f)

		xml = None
		try:
			xml = ET.fromstring(xmlstr)
			if xml is None: raise Exception("failed to create an xml tree object")
		except Exception as e:
			self.logw("xml parser failed (file `%s'): %s" % (rfn, e))
			return None

		if outerTag  and  xml.tag != outerTag:
			self.logw("the xml reply root tag is wrong: `%s' instead of `%s'" % (xml.tag, outerTag))

		return xml


	def updateMarketState(self):
		# TODO delete bids older than one month to save disk space?

		ms = MarketState(self, date = Date("now"))

		st = ms.download(currencyPairs = [self.curPair])

		if st:
			ms.save()
			self.log("the current market state was obtained")
		else:
			self._reasonMSDownloadFailed= ms._reasonMSDownloadFailed
			ms = None
			self.logw("the current market state could NOT be obtained")

		self.marketState = ms


	def downloadTransactionStatus(self):

		# Get opened transactions from the DB

		rs = self.execute("""
			SELECT * FROM transactions
			WHERE status = ? or status = ?
			ORDER BY date1
		""", [TRST_OPEN1, TRST_OPEN2])
		
		ts = []
		for r in rs:
			t = Transaction(self, row=r)
			ts += [t]

		# Update their statuses

		for t in ts:
			st = t.status
			wm_tid = ""
			if st == TRST_OPEN1:
				wm_tid = t.wm_tid1
			elif st == TRST_OPEN2:
				wm_tid = t.wm_tid2
			else: raise Exception("unexpected transaction status = %d" % st)
			assert wm_tid

			r = """
<wm.exchanger.request>
<type>3</type>
<queryid>{wm_tid}</queryid>
</wm.exchanger.request>
"""[1:-1].format(
				wm_tid = wm_tid,
			)

			xml = self._wmXmlRequest(r,
				"https://wmeng.exchanger.ru/asp/XMLWMList2.asp")

			if not xml:
				self.logw("no xml reply")
				continue

			self.log("obtained transaction status data from the server (wm_tid=%s)" % wm_tid)

			# Process the xml reply of a transaction

			rv = xml.find('retval')
			if rv is None:
				self.logw("no retval tag")
				continue

			if rv.text != '0':
				rd = xml.find('retdesc')
				msg = "" if rd is None else rd.text
				self.logw("could not obtain the status of the following transaction: %s\n\tRetval: `%s'\n\tReason: %s" % (t, rv.text, msg))
				continue

			qs = xml.find('WMExchnagerQuerys')
			if qs is None: qs = xml.find('WMExchangerQuerys')
			if qs is None:
				self.logw("could not obtain transaction info from WM for the following transaction: %s" % t)
				continue

			if not len(qs):
				self.logw("no <query/> tag found in the XML reply for the following transaction: %s" % (t))
				continue

			q = qs[0]
			state = q.attrib.get('state', None)
			if state is None:
				self.logw("no `state' attribute in the XML reply for the following transaction: %s" % (t))
				continue

			if state == '0':
				# An unpaid transaction
				self.logw("unpaid transaction detected: %s" % t)
				continue
			elif state == '1':
				# the transaction status persists, do nothing
				pass
			elif state == '2':
				# the transaction has been closed
				ps = t.status  # previous transaction status
				if ps == TRST_OPEN1:
					t.status = TRST_CLOSED1
					t.date1closed = Date("now")
				elif ps == TRST_OPEN2:
					t.status = TRST_CLOSED2
					t.date2closed = Date("now")
				else: assert False

				self.log("transaction id=%d changed its status from %s to %s" % (t.ide, TRST[ps], TRST[t.status]))
			else:
				self.logw("unpredicted value `%s' of the `state' attribute for the following transaction: %s" % (state, t))

			# Deal with the actual exchange rates

			oldRemainder1 = t.remainder1
			oldRemainder2 = t.remainder2

			# sum up all partial sales multiplied by the rate
			ain = float(re.sub(r',', '.',
				q.attrib.get('amountin', '0')))
			if t.status in [TRST_OPEN1, TRST_CLOSED1]:
				dr = t.remainder1 - ain
				t.remainder1 = ain
				t.remainder2 += dr * t.rate1
			elif t.status in [TRST_OPEN2, TRST_CLOSED2]:
				dr = t.remainder2 - ain
				t.remainder2 = ain
				t.remainder1 += dr * t.rate2

			# calculate the actual values of rate1 and rate2
			if t.status == TRST_CLOSED1:
				a1 = t.amount - t.getCommission1()
				t.rate1 = t.remainder2 / a1
			elif t.status == TRST_CLOSED2:
				a2 = t.getAmount2() - t.getCommission2()
				t.rate2 = t.remainder1 / a2

			t.save()

			# Email Reports

			self._emailRemaindersChange(t,
				oldRemainder1, oldRemainder2)

			if t.status == TRST_CLOSED1:
				self._emailClosed1(t)
			elif t.status == TRST_CLOSED2:
				self._emailClosed2(t)


	def _notifyNoMarketState(self):
		if self._reasonMSDownloadFailed == "ban_protection": return

		dn = Date("now")
		d = self._dateLastNoMSEmail 
		if not d  or  d.hoursEarlier(dn) >= Config.NO_MS_NOTIF_INTERVAL:
			self._emailNoMarketState(self)
			self._dateLastNoMSEmail = dn


	def _notifyFixedNoMarketState(self):
		if self._dateLastNoMSEmail:
			self._emailFixedNoMarketState()
			self._dateLastNoMSEmail = None


	def _emailNoMarketState(self, send=True, stdout=False):
		dn = Date("now")

		subj = "Failed to obtain the market state"
		body = """
Date on the server: {d}
"""[1:-1].format(
			d = dn.toNiceText(),
		)

		if send: self.sendEmail(subj, body)
		if stdout:
			print(subj)
			print("")
			print(body)

		return (subj, body)


	def _emailFixedNoMarketState(self, send=True, stdout=False):
		dn = Date("now")

		subj = "Market states are available again"
		body = """
Date on the server: {d}
"""[1:-1].format(
			d = dn.toNiceText(),
		)

		if send: self.sendEmail(subj, body)
		if stdout:
			print(subj)
			print("")
			print(body)

		return (subj, body)


	def _emailOpen1(self, t, send=True, stdout=False):
		rate = t.rate1
		if rate < 1  and  rate: rate = 1 / rate

		subj = "A direct transaction has been opened"
		body = """
Amount = {am:.2f}
Remainder1 = {rem1:.2f}

Profit = {p:+.2f} ({rp:+.2f}%)
Rate = {rate:.4f}

tid = {tid}
"""[1:-1].format(
			am = t.amount,
			rem1 = t.remainder1,
			rate = rate,
			tid = t.wm_tid1,
			p = t.profit(),
			rp = t.profit(relative=True) * 100,
		)

		if send: self.sendEmail(subj, body)
		if stdout:
			print(subj)
			print("")
			print(body)

		return (subj, body)


	def _emailClosed1(self, t, send=True, stdout=False):
		rate = t.rate1
		if rate < 1  and  rate: rate = 1 / rate

		subj = "A direct transaction has been closed"
		body = """
Amount = {am:.2f}
Remainder1 = {rem1:.2f}
Remainder2 = {rem2:.2f}

Profit = {p:+.2f} ({rp:+.2f}%)
Rate = {rate:.4f}

tid = {tid}
"""[1:-1].format(
			am = t.amount,
			rem1 = t.remainder1,
			rem2 = t.remainder2,
			rate = rate,
			tid = t.wm_tid1,
			p = t.profit(),
			rp = t.profit(relative=True) * 100,
		)

		if send: self.sendEmail(subj, body)
		if stdout:
			print(subj)
			print("")
			print(body)

		return (subj, body)


	def _emailOpen2(self, t, send=True, stdout=False):
		rate = t.rate2
		if rate < 1  and  rate: rate = 1 / rate

		subj = "A reverse transaction has been opened"
		body = """
Amount = {am:.2f}
Remainder2 = {rem2:.2f}

Profit = {p:+.2f} ({rp:+.2f}%)
Rate = {rate:.4f}

tid = {tid}
"""[1:-1].format(
			am = t.amount,
			rem2 = t.remainder2,
			rate = rate,
			tid = t.wm_tid2,
			p = t.profit(),
			rp = t.profit(relative=True) * 100,
		)

		if send: self.sendEmail(subj, body)
		if stdout:
			print(subj)
			print("")
			print(body)

		return (subj, body)


	def _emailClosed2(self, t, send=True, stdout=False):
		rate = t.rate2
		if rate < 1  and  rate: rate = 1 / rate

		subj = "A reverse transaction has been closed"
		body = """
Amount = {am:.2f}
Remainder1 = {rem1:.2f}
Remainder2 = {rem2:.2f}

Profit = {p:+.2f} ({rp:+.2f}%)
Rate = {rate:.4f}

tid = {tid}
"""[1:-1].format(
			am = t.amount,
			rem1 = t.remainder1,
			rem2 = t.remainder2,
			rate = rate,
			tid = t.wm_tid2,
			p = t.profit(),
			rp = t.profit(relative=True) * 100,
		)

		if send: self.sendEmail(subj, body)
		if stdout:
			print(subj)
			print("")
			print(body)

		return (subj, body)


	def _emailRemaindersChange(self, t, oldRemainder1, oldRemainder2,
		send=True, stdout=False,
	):
		drem1 = t.remainder1 - oldRemainder1
		drem2 = t.remainder2 - oldRemainder2

		if abs(drem1) < 0.005 and abs(drem2) < 0.005:
			return (None, None)

		rate = abs(drem2 / drem1) if drem1 else 0
		if rate < 1  and  rate: rate = 1 / rate

		subj = "Remainders have changed"
		body = """
remainder1: {orem1:.2f} -> {rem1:.2f} ({drem1:+.2f})
remainder2: {orem2:.2f} -> {rem2:.2f} ({drem2:+.2f})

Profit = {p:+.2f} ({rp:+.2f}%)
Rate = {rate:.4f}

tid1 = {tid1}  tid2 = {tid2}
"""[1:-1].format(
			rem1 = t.remainder1,
			orem1 = oldRemainder1,
			rem2 = t.remainder2,
			orem2 = oldRemainder2,
			drem1 = drem1,
			drem2 = drem2,
			tid1 = t.wm_tid1,
			tid2 = t.wm_tid2,
			rate = rate,
			p = t.profit(),
			rp = t.profit(relative=True) * 100,
		)

		if send: self.sendEmail(subj, body)
		if stdout:
			print(subj)
			print("")
			print(body)

		return (subj, body)


	def sendEmail(self, subject, body, continueOnFailure=True):
		msg = MIMEText(body)

		msg['Subject'] = subject
		msg['From'] = Config.SENDER_EMAIL
		msg['To'] = Config.RECIPIENT_EMAIL

		user = re.sub(r'^(.*)@.*', r'\1', Config.SENDER_EMAIL)
		pw = ""
		with open(Config.PASSWORD_FILE_SMTP) as fp:
			pw = fp.readline().strip()

		# Send the message via our own SMTP server.
		try:
			#s = smtplib.SMTP(Config.SMTP_SERVER, port=465, timeout=30)
			s = smtplib.SMTP_SSL(timeout=30)
			s.connect(Config.SMTP_SERVER, port=465)
			#s.starttls()
			s.login(user, pw)
			s.send_message(msg)
			s.quit()
		except Exception as e:
			self.logw("could not send the email: %s" % e)
			if not continueOnFailure: raise e


	def log(self, msg):
		d = Date("now")
		dt = d.toNiceText()

		sz = 0
		if os.path.isfile(LOG_FILE): sz = os.path.getsize(LOG_FILE)
		if sz > MAX_LOG_SZ:
			f = "{lf}.{d}".format(lf = LOG_FILE, d = d.toText())
			shutil.copy(LOG_FILE, f)
			st = subprocess.call(["bzip2", f])
			if not st: os.unlink(LOG_FILE)

		with open(LOG_FILE, "a") as fp:
			l = "{dt} {msg}\n".format(
				dt = dt,
				msg = msg,
			)

			for f in [sys.stdout, fp]:
				f.write(l)


	def loge(self, msg):
		"""Log an error"""
		self.log("Error: %s" % msg)


	def logw(self, msg):
		"""Log a warning"""
		self.log("Warning: %s" % msg)


	def loadLatestMarketState(self):
		rs = self.execute("""
			SELECT * FROM marketstates
			ORDER BY date DESC
			LIMIT 1
""".format(
		))

		ms = None
		for r in rs:
			ms = MarketState(self, row=r)
			break

		self.marketState = ms

		return ms


	def timeAvgRates(self, recalculate=False):
		"""
		Return the MarketState's average rates averaged over time.

		If recalculate is False then return the last value calculated,
		if there is no such value calculate it and return
		"""

		if not recalculate:
			r = self._last_timeAvgRates
			if len(r) >= 2: return r

		assert Config.RATE_AVG_HOURS > 0

		# Determine d1 as the date of the last marketState

		rows = self.execute("""
			SELECT * FROM marketstates ORDER BY DATE DESC LIMIT 1
""")
		d1 = None
		for row in rows:
			d1 = Date(row['date'])
			break
		if not d1: raise Exception("no marketstates in the DB")

		d0 = d1.plusHours(-Config.RATE_AVG_HOURS)

		rows = self.execute("""
			SELECT * FROM marketstates
			WHERE date >= ?  and  date <= ?
			ORDER BY date
""", [d0.toText(), d1.toText()])
		
		mss = []
		for row in rows:
			ms = MarketState(self, row=row)
			mss += [ms]

		if not mss: raise Exception("timeAvgRates() cannot proceed because the DB does not contain any market states within %s and %s" % (d0.toNiceText(), d1.toNiceText()))

		cp = self.curPair
		cpr = cp.reverse()
		for cpx in (cp, cpr):
			ts = []
			ys = []
			d0 = mss[0].date
			for ms in mss:
				ts += [d0.hoursEarlier(ms.date)]
				ys += [ms.avgRates[cpx]]

			tar = defs.trapezeAvg(ts, ys)

			T = mss[0].date.hoursEarlier(mss[-1].date)

			if len(mss) >= 2: assert T > 1e-10
			assert T < Config.RATE_AVG_HOURS + 1e-10
			assert tar > 1e-10
			assert tar>= min(ms.avgRates[cpx] for ms in mss) - 1e-10
			assert tar<= max(ms.avgRates[cpx] for ms in mss) + 1e-10

			self._last_timeAvgRates[cpx] = tar

		return self._last_timeAvgRates
