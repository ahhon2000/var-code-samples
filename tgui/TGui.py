import mysql.connector as mariadb
import Config
import time
import pickle

import os, sys
import subprocess

from Date import Date
from Instrument import InstrumentFutures, InstrumentSwaps
from ExchangeOkex import ExchangeOkex
from ExchangeBitmex import ExchangeBitmex
from ExchangeBitfinex import ExchangeBitfinex
from ExchangeBinance import ExchangeBinance

class TGui:
	exchangeClasses = [
		ExchangeOkex,
		ExchangeBitmex,
		ExchangeBitfinex,
		ExchangeBinance,
	]

	def __init__(self, readOnly=True, skipTests=False):
		self.readOnly = readOnly

		self.db = None
		self._reconnectToDb()
		self.sessionId = ''

		self.exchanges = []

		self._initExchanges()
		self._createTables()
		self._nxtOrderbookCleanupDate = None

		if not skipTests:
			self._testsAfterInit()


	def setSessionPar(self, name, typ, value):
		value = str(value)
		sid = self.sessionId
		if not sid: raise Exception("undefined sessionId")

		typ = {
			float: 'float',
			int: 'int',
			str: 'str',
		}.get(typ, None)
		if typ is None: raise Exception("unsupported session parameter type")

		rs = self.execute("""
SELECT * FROM session_pars WHERE `name`=%s and `sessionId`=%s LIMIT 1
""", [name, sid])

		flgNew = True
		for r in rs:
			flgNew = False
			break

		if flgNew:
			self.execute("""
INSERT INTO session_pars (`name`, `sessionId`, `value`, `type`) VALUES (%s, %s, %s, %s)
""", [name, sid, value, typ])
		else:
			self.execute("""
UPDATE session_pars SET `value`= %s, `type`=%s WHERE `sessionId`=%s and `name` = %s
""", [value, typ, sid, name])


	def getSessionPar(self, name):
		rs = self.execute("""
SELECT * FROM session_pars WHERE `sessionId`=%s and `name`=%s LIMIT 1
""", [self.sessionId, name])

		for r in rs:
			v = r['value']
			typ = r['type']
			if typ == 'float':
				v = float(v)
			elif typ == 'int':
				v = int(v)
			elif typ == 'str':
				v = str(v)
			else: raise Exception("unknown session parameter type")

			return v

		# if the parameter was not found return a default value

		v = {
			'DEFAULT_PRICE_DEPTH': Config.DEFAULT_PRICE_DEPTH,
		}.get(name, None)

		if v is None: raise Exception("unsupported session parameter")

		return v


	def _reconnectToDb(self):
		if self.db:
			self.db.reconnect()
		else:
			import mysql.connector as mariadb
			self.db = mariadb.connect(
				user = Config.DB_USER,
				password = Config.DB_PASSWORD,
				database = Config.DB_NAME,
			)

		self.cursor = self.db.cursor(buffered=True)


	def _initExchanges(self):
		self.exchanges.clear()
		for Cls in self.exchangeClasses:
			self.exchanges += [Cls(self)]


	def _testsAfterInit(self):
		dt = Config.BACKEND_LOOP_INTERVAL
		expi = Config.ORDERBOOK_EXPIRY_INTERVAL
		uexpi = Config.U_ORDERBOOK_EXPIRY_INTERVAL
		if dt <= 0: raise Exception("invalid BACKEND_LOOP_INTERVAL")
		if expi < 1 / 60.: raise Exception("invalid ORDERBOOK_EXPIRY_INTERVAL")
		if uexpi < 10 / 60.: raise Exception("invalid U_ORDERBOOK_EXPIRY_INTERVAL")
		allowance = Config.INVALID_POINTS_ALLOWANCE_FOR_AVERAGES
		if allowance < 0 or allowance > 1: raise Exception("invalid INVALID_POINTS_ALLOWANCE_FOR_AVERAGES")

		for ex in self.exchanges:
			for ex2 in self.exchanges:
				if ex.__class__.__name__==ex2.__class__.__name__:
					continue
				if ex.name == ex2.name: raise Exception("2 exchanges go by the same name")
				
		# TODO put more common sense tests here


	def _createTables(self):
		if self.readOnly: return

		self.execute("""
CREATE TABLE IF NOT EXISTS `pars` (
	`name` VARCHAR(64) PRIMARY KEY NOT NULL,
	`value` VARCHAR(256) NOT NULL DEFAULT ''
)
""")

		self.execute("""
CREATE TABLE IF NOT EXISTS `session_pars` (
	`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,
	`name` VARCHAR(64) NOT NULL,
	`type` VARCHAR(32) NOT NULL DEFAULT 'str',
	`sessionId` VARCHAR(128) NOT NULL DEFAULT '',
	`value` VARCHAR(256) NOT NULL DEFAULT ''
)
""")

		for ex in self.exchanges:
			ex.createTables()


	def execute(self, r, t=[], nocommit=False):
		# execute request r providing it with tuple t
		db = self.db
		if not db.is_connected():
			self._reconnectToDb()

		c = self.cursor

		try:
			ex = c.execute(r, t)
		except Exception as e:
			self.db.disconnect()
			raise e

		rows = list(c)

		if rows:
			# convert rows to a key/value format
			newRows = []
			for row in rows:
				row = dict(zip(c.column_names, row))
				newRows += [row]
			rows = newRows
		
		if not nocommit:
			db.commit()

		if isinstance(c.lastrowid, int):
			self.lastrowid = c.lastrowid

		return rows


	def setPar(self, name, value):
		value = str(value)

		rs = self.execute("""
SELECT * FROM pars WHERE `name`=%s LIMIT 1
""", [name])

		flgNew = True
		for r in rs:
			flgNew = False
			break

		if flgNew:
			self.execute("""
INSERT INTO pars (`name`, `value`) VALUES (%s, %s)
""", [name, value])
		else:
			self.execute("""
UPDATE pars SET `value`= %s WHERE `name` = %s
""", [value, name])


	def  getPar(self, name):
		rs = self.execute("""
SELECT * FROM pars WHERE `name`=%s LIMIT 1
""", [name])

		for r in rs:
			return r['value']

		return ''


	def cleanupOldOrderbooks(self):
		now = Date("now")

		dc = self._nxtOrderbookCleanupDate
		if not dc:
			dc = now
			self._nxtOrderbookCleanupDate = dc
		else:
			if dc > now: return

		for ex in self.exchanges:
			ex.cleanupOldOrderbooks()

		# schedule the next cleanup
		self._nxtOrderbookCleanupDate = now.plusHours(
			0.1 * Config.ORDERBOOK_EXPIRY_INTERVAL
		)


	def getExchangeByName(self, exn):
		if not isinstance(exn, str): raise Exception("an exchange name must be a string")

		for ex in self.exchanges:
			if ex.name.lower() == exn.lower(): return ex

		return None


	def loadInstrumentsForExchange(self, exn):
		if not exn: raise Exception("an exchange name is required")
		ex = self.getExchangeByName(exn)
		if not ex: raise Exception("unsupported exchange: `{exn}'".format(exn=exn))

		ex.loadInstruments()

	def restartBackend(self):
		lrTs = self.getPar('lastBackendRestartTs')
		lrTs = float(lrTs) if lrTs else 0

		sec = time.time() - lrTs
		if sec < Config.BACKEND_RESTART_MAX_FREQ:
			dsec = Config.BACKEND_RESTART_MAX_FREQ - sec
			raise Exception("next restart is only possible in {dsec} seconds (otherwise we may get banned by exchanges)".format(dsec = round(dsec)))

		cmd = "/usr/bin/sudo systemctl restart tguiBackend"
		st = subprocess.call(cmd.split())

		self.setPar('lastBackendRestartTs', round(time.time()))

		return st
