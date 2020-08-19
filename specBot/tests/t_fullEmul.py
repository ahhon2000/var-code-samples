#!/usr/bin/python3

import os, sys
sys.path = [".", ".."] + [os.path.dirname(os.path.abspath(sys.argv[0]))] + sys.path

import subprocess
from SpecBot import SpecBot
from Transaction import Transaction
import Config
from defs import *
import defs
from tstcommon import *

import tstcommon
from tstcommon import TstCommon
from WgetTst import WgetTst


def checkAvgRates(ms, bs):
	p0 = Config.MAX_PLACE_FOR_WEIGHING

	ar1 = ms.avgRates[ms.specBot.curPair]
	ar2 = ms.avgRates[ms.specBot.curPair.reverse()]

	rs = {}
	for typ in ("direct", "reverse"):
		r = 0
		sw = 0
		p = 0
		for b in bs[typ]:
			w = (p0 - p) * b['amount'] / p0
			if w < 0: w = 0

			if b['tid'] in ['666', '999']: continue

			if typ == "direct": r += w * b['rate'] 
			elif typ == "reverse": r += w * 1 / b['rate']
			else: raise Exception("unknown bid type `%s'" % typ)

			sw += w
			p += 1
		r /= sw
		rs[typ] = r

	ensureFloat(ar1, rs['direct'], "ar1 = %.10f calculated incorrectly; must be = %.10f" % (ar1, rs['direct']), precision=1e-5)
	ensureFloat(ar2, rs['reverse'], "ar2 = %.10f calculated incorrectly; must be = %.10f" % (ar2, rs['reverse']), precision=1e-5)


def tst1():
	p0 = Config.MAX_PLACE_FOR_WEIGHING
	sb = SpecBot(
		dbFile = tstcommon.TST_DB_FILE,
		dbName = tstcommon.TST_DB_NAME,
		currency1str = "USD",
		currency2str = "RUB",
		readOnly = False,
		tmpDir = tstcommon.TST_TMP_DIR,
		wget = WgetTst(default=True),
	)

	sb.updateMarketState()
	ms = sb.marketState

	w11 = 200 * (p0 - 0) / p0
	w12 = 100 * (p0 - 1) / p0
	w21 = (p0 - 0) / p0
	w22 = (p0 - 1) / p0

	ar1 = ms.avgRates['USD,RUB']
	ar2 = 1/ms.avgRates['RUB,USD']
	ar1t = (w11 * 60 + w12 * 62 ) / (w11 + w12)
	ar2t = (w21 * 60 + w22 * 58 ) / (w21 + w22)

	dr1 = ar1 - ar1t
	dr2 = ar2 - ar2t

	if abs(dr1) > 10e-6: raise Exception("average rate for emulated direct market state is wrong: %.8f instead of %.8f" % (ar1, ar1t))
	if abs(dr2) > 10e-6: raise Exception("average rate for emulated reverse market state is wrong: %.8f instead of %.8f" % (ar2, ar2t))


class SpecBotTst(SpecBot):
	def sendEmail(self, subject, body, continueOnFailure=True):
		pass


	def updateMarketState(self):
		SpecBot.updateMarketState(self)

		ms = self.marketState
		if ms:
			if '_marketStateDateShift' not in self.__dict__.keys():
				self._marketStateDateShift = 0

			ms.date = ms.date.plusHours(-self._marketStateDateShift)
			self._marketStateDateShift += 1

			ms.save()


def tst2():
	"""
	Perform several sb.cycle()'s to emulate a full roundtrip transaction
	"""

	Config.MAXIMUM_AMOUNT1 = 0
	Config.INITIAL_AMOUNT1 = 15000
	Config.MIN_REL_PROFIT = 0.0010

	sb = SpecBotTst(
		dbFile = tstcommon.TST_DB_FILE,
		dbName = tstcommon.TST_DB_NAME,
		currency1str = "USD",
		currency2str = "RUB",
		readOnly = False,
		tmpDir = tstcommon.TST_TMP_DIR,
		wget = WgetTst(default=False),
	)

	wget = sb.wget

	# Cycle 0: check the marketState == None event

	wget.marketBids = {}
	sb.cycle()
	if not(sb.marketState is None):
		raise Exception("sb.marketState is not None")
	sb.setPar("lastMarketstateDownloadDate", '')

	# Cycle 1

	wget.marketBids = {
		'direct': [
			{'tid': '1', 'amount': 100, 'rate': 58,},
			{'tid': '2', 'amount': 100, 'rate': 59,},
			{'tid': '3', 'amount': 100, 'rate': 60,},
			{'tid': '4', 'amount': 100, 'rate': 61,},
			{'tid': '5', 'amount': 100, 'rate': 62,},
		],
		'reverse': [
			{'tid': '6', 'amount': 6000, 'rate': 57,},
			{'tid': '7', 'amount': 6000, 'rate': 56,},
			{'tid': '8', 'amount': 6000, 'rate': 55,},
			{'tid': '9', 'amount': 6000, 'rate': 54,},
			{'tid': '10', 'amount': 6000, 'rate': 53,},
		],
	}
	sb.cycle()
	ts = sb.getTransactions()
	if len(ts) != 1:
		raise Exception("the transaction was not saved to the db")
	t = ts[0]
	att = sb.getAmountToTrade()
	am = att - calCommission(att, sb.curPair[0])
	ensure(t.ide == 1, "wrong transaction id = %d" % t.ide)
	ensure(t.status == TRST_OPEN1,
		"wrong transaction status = %d" % t.status)
	ensureFloat(t.amount, att, "wrong transaction status = %d" % t.status)
	ensure(t.date1, "t.date1 is not set")
	ensure(not (t.date1closed or t.date2 or t.date2closed),
		"wrong transaction dates")
	ensureFloat(t.remainder1, am,
		"t.remainder1 was calculated incorrectly")
	ensureFloat(t.remainder2, 0, "t.remainder2 is not zero")
	ensure(t.wm_tid1 == '666', "expected t.wm_tid1 to be '666'")
	ensure(t.wm_tid2 == '', "expected t.wm_tid2 to be ''")
	ensureFloat(t.rate2, 0, "t.rate2 is not 0")
	ar1 = sb.marketState.avgRates[sb.curPair]
	ensure(58 < ar1 and ar1 < 62, "ar1 out of range")
	ensureFloat(t.rate1, ar1, "the calculated rate1 and the one in the DB differ: t.rate1=%.6f; ar1=%.6f" % (t.rate1, ar1))

	# Cycle 2: same market bids, except that our bid is present

	sb.setPar("lastMarketstateDownloadDate", '')
	wget.marketBids = {
		'direct': [
			{'tid': '1', 'amount': 100, 'rate': 58,},
			{'tid': '2', 'amount': 100, 'rate': 59,},
			{'tid': '666', 'amount': am, 'rate': 59.75,},
			{'tid': '3', 'amount': 100, 'rate': 60,},
			{'tid': '4', 'amount': 100, 'rate': 61,},
			{'tid': '5', 'amount': 100, 'rate': 62,},
		],
		'reverse': [
			{'tid': '6', 'amount': 6000, 'rate': 57,},
			{'tid': '7', 'amount': 6000, 'rate': 56,},
			{'tid': '8', 'amount': 6000, 'rate': 55,},
			{'tid': '9', 'amount': 6000, 'rate': 54,},
			{'tid': '10', 'amount': 6000, 'rate': 53,},
		],
	}
	wget.myBids = [{
		'tid': '666',
		'state': '1',
		'amountin': am,
		'amountout': am * 59.75,
	}]
	sb.cycle()
	ts = sb.getTransactions()
	if len(ts) != 1:
		raise Exception("the number of transaction in the db is not 1")
	t = ts[0]
	ensure(t.ide == 1, "wrong transaction id = %d" % t.ide)
	ensure(t.status == TRST_OPEN1,
		"wrong transaction status = %d" % t.status)
	att = sb.getAmountToTrade()
	am = att - defs.calCommission(att, sb.curPair[0])
	ensureFloat(t.amount, att, "wrong transaction status = %d" % t.status)
	ensure(t.wm_tid1 == '666', "expected t.wm_tid1 to be '666'")
	ar1 = sb.marketState.avgRates[sb.curPair]
	ensure(58 < ar1 and ar1 < 62, "ar1 out of range")
	ensureFloat(t.rate1, ar1, "the calculated rate1 and the one in the DB differ")

	# Cycle 3: avg rate has changed

	sb.setPar("lastMarketstateDownloadDate", '')
	wget.marketBids = {
		'direct': [
			{'tid': '1', 'amount': 100, 'rate': 58,},
			{'tid': '2', 'amount': 100, 'rate': 59,},
			{'tid': '666', 'amount': am, 'rate': 59.75,},
			{'tid': '3', 'amount': 100, 'rate': 60,},
			{'tid': '4', 'amount': 100, 'rate': 61,},
			{'tid': '5', 'amount': 100, 'rate': 70,},
		],
		'reverse': [
			{'tid': '6', 'amount': 6000, 'rate': 57,},
			{'tid': '7', 'amount': 6000, 'rate': 56,},
			{'tid': '8', 'amount': 6000, 'rate': 55,},
			{'tid': '9', 'amount': 6000, 'rate': 54,},
			{'tid': '10', 'amount': 6000, 'rate': 53,},
		],
	}
	sb.cycle()
	t = sb.getTransactions()[0]
	ensure(t.status == TRST_OPEN1, "wrong transaction status")
	ms = sb.marketState
	checkAvgRates(ms, wget.marketBids)
	tar1 = sb.timeAvgRates(recalculate=True)[sb.curPair]
	ensureFloat(t.rate1, tar1, "the calculated rate1 and the one in the DB differ")

	tar1_cycle3 = tar1

	# Cycle 4: someone has bought part of our direct bid

	sb.setPar("lastMarketstateDownloadDate", '')
	att = sb.getAmountToTrade()
	am = att - defs.calCommission(att, sb.curPair[0])
	wget.marketBids = {
		'direct': [
			{'tid': '1', 'amount': 100, 'rate': 58,},
			{'tid': '2', 'amount': 100, 'rate': 59,},
			{'tid': '666', 'amount': am, 'rate': 59.75,},
			{'tid': '3', 'amount': 100, 'rate': 60,},
			{'tid': '4', 'amount': 100, 'rate': 61,},
			{'tid': '5', 'amount': 100, 'rate': 70,},
		],
		'reverse': [
			{'tid': '6', 'amount': 6000, 'rate': 57,},
			{'tid': '7', 'amount': 6000, 'rate': 56,},
			{'tid': '8', 'amount': 6000, 'rate': 55,},
			{'tid': '9', 'amount': 6000, 'rate': 54,},
			{'tid': '10', 'amount': 6000, 'rate': 53,},
		],
	}
	oldAm = am
	am -= 100
	wget.myBids = [{
		'tid': '666',
		'state': '1',
		'amountin': am,
		'amountout': am * tar1_cycle3,
	}]
	sb.cycle()
	t = sb.getTransactions()[0]
	ensure(t.status == TRST_OPEN1, "wrong transaction status")
	ensureFloat(t.remainder1, am, "wrong remainder1 value %.6f (should be %.6f)" % (t.remainder1, am))
	ensureFloat(t.remainder2, (oldAm - am) * tar1_cycle3, "wrong remainder2 value %.6f (should be %.6f)" % (t.remainder2, am))

	tar1_cycle4 = sb.timeAvgRates(recalculate=True)[sb.curPair]

	# Cycle 5: someone has bought the rest of our direct bid

	sb.setPar("lastMarketstateDownloadDate", '')
	att = sb.getAmountToTrade()
	am = att - defs.calCommission(att, sb.curPair[0])
	wget.myBids = [{
		'tid': '999',
		'state': '2',
		'amountin': 0,
		'amountout': 0,
	}]
	sb.cycle()
	ms = sb.marketState
	t = sb.getTransactions()[0]
	tar2 = sb.timeAvgRates(recalculate=True)[sb.curPair.reverse()]

	ensureFloat(t.amount, att, "wrong transaction amount")
	ensure(t.status == TRST_OPEN2, "wrong transaction status")
	ensureFloat(t.remainder1, 0, "wrong remainder1 value %.6f (should be 0)" % (t.remainder1))

	am2 = 100 * tar1_cycle3 + (am - 100) * tar1_cycle4
	am2 -= calCommission(am2, sb.curPair[1])

	ensureFloat(t.remainder2, am2, "wrong remainder2 value %.6f (should be %.6f)" % (t.remainder2, am2))
	ensure(t.wm_tid1 == '666', "wrong wm_tid1=%s instead of %s" % (t.wm_tid1, '666'))
	ensure(t.wm_tid2 == '999', "wrong wm_tid2=%s instead of %s" % (t.wm_tid2, '999'))
	ensure(t.date1 and t.date1closed and t.date2 and not t.date2closed,
		"problems with transaction dates")
	ensureFloat(t.rate2, tar2, "t.rate2 is wrong: t.rate2=%.6f; tar2=%.6f" % (t.rate2, tar2))
	ensure(1/57 < t.rate2 and t.rate2 < 1/53,
		"incorrectly determined t.rate2")
	r1 = (t.remainder2 + t.getCommission2()) / (t.amount-t.getCommission1())
	ensureFloat(t.rate1, r1, "t.rate1 = %.6f instead of %.6f" % (t.rate1, r1))

	r1_cycle5 = t.rate1

	# Cycle 6: reverse market rate has changed

	sb.setPar("lastMarketstateDownloadDate", '')
	wget.marketBids = {
		'direct': [
			{'tid': '1', 'amount': 100, 'rate': 58,},
			{'tid': '2', 'amount': 100, 'rate': 59,},
			{'tid': '3', 'amount': 100, 'rate': 60,},
			{'tid': '4', 'amount': 100, 'rate': 61,},
			{'tid': '5', 'amount': 100, 'rate': 80,},
		],
		'reverse': [
			{'tid': '6', 'amount': 6000, 'rate': 57,},
			{'tid': '7', 'amount': 6000, 'rate': 56,},
			{'tid': '999', 'amount': am, 'rate': 59.75,},
			{'tid': '8', 'amount': 6000, 'rate': 55,},
			{'tid': '9', 'amount': 6000, 'rate': 54,},
			{'tid': '10', 'amount': 6000, 'rate': 50,},
		],
	}
	wget.myBids = [{
		'tid': '999',
		'state': '1',
		'amountin': am2,
		'amountout': 0,
	}]
	sb.cycle()
	ms = sb.marketState
	checkAvgRates(ms, wget.marketBids)
	t = sb.getTransactions()[0]

	ensure(t.status == TRST_OPEN2, "wrong transaction status")
	ensureFloat(t.remainder1, 0, "wrong remainder1 value %.6f (should be 0)" % (t.remainder1))
	ensureFloat(t.remainder2, am2, "wrong remainder2 value %.6f (should be %.6f)" % (t.remainder2, am2))
	ensureFloat(t.rate1, r1_cycle5, "wrong t.rate1")
	tar2 = sb.timeAvgRates(recalculate=True)[sb.curPair.reverse()]
	ensureFloat(t.rate2, tar2, "wrong t.rate2")

	tar2_cycle6 = tar2

	# Cycle 7: someone has bought part of our reverse bid

	sb.setPar("lastMarketstateDownloadDate", '')
	oldAm2 = am2
	am2 -= 10000
	wget.myBids = [{
		'tid': '999',
		'state': '1',
		'amountin': am2,
		'amountout': am2 * tar2_cycle6,
	}]
	sb.cycle()
	ms = sb.marketState
	t = sb.getTransactions()[0]

	ensure(t.status == TRST_OPEN2, "wrong transaction status")
	ensure(t.wm_tid1 == '666', "wrong transaction wm_tid1")
	ensure(t.wm_tid2 == '999', "wrong transaction wm_tid2")
	ensureFloat(t.remainder1, (oldAm2 - am2)*tar2, "wrong remainder1 value %.2f (should be %.2f)" % (t.remainder1, (oldAm2 - am2) * tar2))
	ensureFloat(t.remainder2, am2, "wrong remainder2 value %.2f (should be %.2f)" % (t.remainder2, am2))
	checkAvgRates(ms, wget.marketBids)

	# Cycle 8: someone has bought the rest of our reverse bid

	sb.setPar("lastMarketstateDownloadDate", '')
	att = sb.getAmountToTrade()
	am = att - defs.calCommission(att, sb.curPair[0])
	wget.myBids = [{
		'tid': '999',
		'state': '2',
		'amountin': 0,
		'amountout': 0,
	}]
	sb.cycle()
	ms = sb.marketState
	ts = sb.getTransactions()
	ensure(len(ts) == 2, "len(ts) != 2")

	t = ts[0]
	ensure(t.status == TRST_CLOSED2, "wrong transaction status")
	ensureFloat(t.remainder2, 0, "wrong t.remainder2 value")
	ensure(t.date1 and t.date1closed and t.date2 and t.date2closed,
		"wrong transaction dates")

	ensureFloat(t.profit(), t.remainder1 - t.amount, "t.profit() returned an incorrect result")
	ensure(t.profit() > 0, "negative t.profit()")

	r2 = t.remainder1 / (
		(t.amount - t.getCommission1()) * t.rate1 - t.getCommission2()
	)
	ensureFloat(t.rate2, r2, "t.rate2 = %.6f instead of %.6f" % (t.rate2, r2))

	# Check if the second transaction is ok

	t = ts[1]
	ensure(t.status == TRST_OPEN1, "wrong transaction status")
	ensure(t.date1 and not(t.date1closed or t.date2 or t.date2closed),
		"wrong transaction dates")
	ensure(t.wm_tid1 == '666', 'wrong t.wm_tid1')
	ensure(t.wm_tid2 == '', 'non-empty t.wm_tid2')
	ensureFloat(t.amount, ts[0].remainder1, "capitalization doesn't work")
	ensureFloat(t.remainder1, t.amount - t.getCommission1(), "wrong t.remainder1")
	ensureFloat(t.remainder2, 0, "wrong t.remainder2")


#Config.RATE_SETTING_MODE = Config.RSM_SMART_MIN_PROFIT
#Config.RATE_SETTING_MODE = Config.RSM_MIN_PROFIT
Config.CURRENCY1 = "USD"
Config.CURRENCY2 = "RUB"
Config.PURSE1 = "Z123"
Config.PURSE2 = "R123"

Config.RATE_SETTING_MODE = Config.RSM_SPREAD_AND_MIN_PROFIT
for mssrc in [Config.MSSRC_XML, Config.MSSRC_HTML]:
	Config.MARKETSTATE_SOURCE = mssrc
	for fmt in [Config.DBF_SQLITE3, Config.DBF_MARIADB]:
		Config.DB_FORMAT = fmt
		with TstCommon():
			tst1()

		with TstCommon():
			tst2()
