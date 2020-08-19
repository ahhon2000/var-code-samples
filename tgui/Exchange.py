import pickle
import traceback

import Config
from Date import Date
from Instrument import InstrumentFutures, InstrumentSwaps

class Exchange:
	def __init__(self, tgui, cbLog=None):
		self.tgui = tgui
		self.name = None
		self.instrumentsFutures = []
		self.instrumentsSwaps = []
		self.rawVolumeSymbols = []

		self.cbLog = cbLog

	def log(self, m):
		if self.cbLog:
			f = self.cbLog
			f(self.name + ": " + m)

	def loge(self, m):
		self.log("error: " + m)

	def logw(self, m):
		self.log("warning: " + m)


	def loadInstruments(self):
		tg = self.tgui
		for (instruments, tbl) in (
			(self.instrumentsFutures, self.tblFuturesInstruments()),
			(self.instrumentsSwaps, self.tblSwapsInstruments()),
		):
			instruments.clear()

			rs = tg.execute("""
SELECT * FROM {tbl}
""".format(tbl=tbl))

			for r in rs:
				ins = pickle.loads(r['pickle'])
				instruments += [ins]

		self.sortInstruments()


	def cleanupOldOrderbooks(self):
		tg = self.tgui
		now = Date("now")
		for (tbl, expInt) in (
			(
				self.tblFuturesOrderbooks(),
				Config.ORDERBOOK_EXPIRY_INTERVAL
			), (
				self.tblFuturesUOrderbooks(),
				Config.U_ORDERBOOK_EXPIRY_INTERVAL
			), (
				self.tblSwapsOrderbooks(),
				Config.ORDERBOOK_EXPIRY_INTERVAL
			), (
				self.tblSwapsUOrderbooks(),
				Config.U_ORDERBOOK_EXPIRY_INTERVAL
			),
		):
			d = now.plusHours(-expInt)
			tg.execute("""
DELETE FROM {tbl} WHERE `date` < %s
""".format(tbl=tbl), [d.toText()])


	def connectReconnect(self):
		pass

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

		tg.execute("""
CREATE TABLE IF NOT EXISTS `{tbl}` (
	`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,
	`exchange` VARCHAR(80),
	`symbol` VARCHAR(80),
	`volume` DOUBLE,
	`turnover` DOUBLE,
	`last_update` VARCHAR(32)
)
""".format(tbl=self.tblVolumes()))

		tg.execute("""
CREATE TABLE IF NOT EXISTS `{tbl}` (
	`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,
	`symbol` VARCHAR(80),
	`fundingRate` DOUBLE,
	`fundingRatePredicted` DOUBLE,
	`timestamp` VARCHAR(32),
	`timestampPredicted` VARCHAR(32),
	`last_update` VARCHAR(32)
)
""".format(tbl=self.tblFunding()))


	def downloadInstruments(self):
		raise Exception("redefine this function in children")

	def sortInstruments(self):
		raise Exception("redefine this function in children")


	def pullOrderbooks(self):
		raise Exception("redefine this function in children")

	def tblFuturesOrderbooks(self):
		raise Exception("redefine this function in children")

	def tblSwapsOrderbooks(self):
		raise Exception("redefine this function in children")

	def tblFuturesUOrderbooks(self):
		raise Exception("redefine this function in children")

	def tblSwapsUOrderbooks(self):
		raise Exception("redefine this function in children")

	def tblFuturesInstruments(self):
		raise Exception("redefine this function in children")

	def tblSwapsInstruments(self):
		raise Exception("redefine this function in children")


	def tblVolumes(self):
		tbl = self.name.lower() + "_volumes"
		return tbl


	def tblFunding(self):
		tbl = self.name.lower() + "_funding"
		return tbl


	def allInstrumentsSorted(self):
		"""A sorted list of all instruments for all contract types"""

		instruments = []
		addedSwaps = []
		nf = len(self.instrumentsFutures)
		for i in range(nf):
			ins = self.instrumentsFutures[i]
			instruments += [ins]

			curCoin = ins.getCoin()
			flgAddSwap = False
			if i + 1 < nf:
				nxtCoin = self.instrumentsFutures[i+1].getCoin()
				if curCoin != nxtCoin:
					flgAddSwap = True
			else:
				flgAddSwap = True

			if flgAddSwap:
				for ins2 in self.instrumentsSwaps:
					if ins2.getCoin() == curCoin:
						instruments += [ins2]
						addedSwaps += [ins2]
						break

		# add the swaps for whose coins there are no futures
		for ins in self.instrumentsSwaps:
			flgNew = True
			for ins2 in addedSwaps:
				if ins.name == ins2.name:
					flgNew = False
					break
			if flgNew:
				instruments += [ins]

		return instruments


	def loadOrderbookForIns(self, ins):
		tg = self.tgui

		tbl = None
		if isinstance(ins, InstrumentFutures):
			tbl = self.tblFuturesOrderbooks()
		elif isinstance(ins, InstrumentSwaps):
			tbl = self.tblSwapsOrderbooks()
		else: raise Exception("unsupported Instrument class `{cn}'".format(cn = ins.__class__.__name__))

		rs = tg.execute("""
SELECT * FROM {tbl}
WHERE instrument_id = %s ORDER BY `date` DESC LIMIT 1
""".format(tbl=tbl), [ins.instrument_id])

		for r in rs:
			now = Date("now")
			d = Date(r['date'])
			# TODO adjust the following if...
			if d.secondsEarlier(now) < 15:
				try:
					j = pickle.loads(r['pickle'])
				except Exception as e:
					with open("pickle.dump", "w") as fp:
						fp.write(r['pickle'])

					msg = "{exn}: {e} (dt={dt}; the pickle object is in the file pickle.dump)\n{tb}".format(
						exn = self.name,
						dt = str(d),
						e=e, tb=traceback.format_exc(),
					)
					self.log(msg)
					j = None

				return j

		return None


	def orderbookTblByContracts(self, ctype):
		if ctype == 'futures': return self.tblFuturesOrderbooks()
		elif ctype == 'swaps':  return self.tblSwapsOrderbooks()
		else: raise Exception("unsupported ctype")


	def uorderbookTblByContracts(self, ctype):
		if ctype == 'futures': return self.tblFuturesUOrderbooks()
		elif ctype == 'swaps':  return self.tblSwapsUOrderbooks()
		else: raise Exception("unsupported ctype")


	def saveNewInstruments(self, tbl, instruments):
		tg = self.tgui
		for ins in instruments:
			iid = ins.instrument_id
			rs = tg.execute("""
SELECT * FROM {tbl} WHERE instrument_id = %s LIMIT 1
""".format(tbl=tbl), [iid])

			flgFound = False
			for r in rs:
				ins2 = pickle.loads(r['pickle'])
				if ins.sameAs(ins2): flgFound = True
				break
			if not flgFound:
				b = pickle.dumps(ins)
				tg.execute("""
INSERT INTO {tbl} (instrument_id, pickle) VALUES (%s, %s)
""".format(tbl=tbl), [iid, b])

		# remove the outdated instruments from the db

		rs = tg.execute("""
SELECT * FROM {tbl}
""".format(tbl=tbl))

		for r in rs:
			ins = pickle.loads(r['pickle'])
			flgDel = True
			for ins2 in instruments:
				if ins.sameAs(ins2):
					flgDel = False
					break
			if flgDel:
				tg.execute("""
DELETE FROM {tbl} WHERE `id` = %s
""".format(tbl=tbl), [r['id']])


	def pullVolume(self):
		raise Exception("redefine this function in children")

	def pullFunding(self):
		raise Exception("redefine this function in children")

	def universalSymbolName(self, sym):
		raise Exception("redefine this function in children")

	def getVolumeUnit(self, sym):
		raise Exception("redefine this function in children")


	def predictedFRateApplicable(self):
		return True
