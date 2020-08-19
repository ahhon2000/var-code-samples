#!/usr/bin/python3

import os, sys
sys.path = [".", ".."] + [os.path.dirname(os.path.abspath(sys.argv[0]))] + sys.path

from SpecBot import SpecBot
from Transaction import Transaction
import Config
import defs
from defs import *
from Currency import CurrencyPair
from tstcommon import *
import tstcommon
from tstcommon import TstCommon
from WgetTst import WgetTst


def doTest(sb=None, am=None, r1=None, st=None, mrp=None):
	ms = sb.marketState
	ar1 = ms.avgRates[sb.curPair]

	t = Transaction(sb,
		status = st,
		amount = am,
		rate1 = r1,
		curPair = sb.curPair,
	)

	(t.rate1, rp) = sb.minProfitRate1(t,
		quiet = True,
	)

	if not defs.insideInterval(t.rate1,
		ar1 * (1 - Config.MAX_RATE_DEVIATION),
		ar1 * (1 + Config.MAX_RATE_DEVIATION),
	):
		raise Exception("rate1 outside of the allowed interval")

	t.status = TRST_OPEN1
	rp = t.profit(relative = True)

	r1True = None
	dev = t.rate1 - ar1
	trimmed = False
	if dev / ar1 > Config.MAX_RATE_DEVIATION:
		r1True = ar1 * (1 + Config.MAX_RATE_DEVIATION)
		trimmed = True
	elif dev / ar1 < - Config.MAX_RATE_DEVIATION:
		r1True = ar1 * (1 - Config.MAX_RATE_DEVIATION)
		trimmed = True

	if trimmed and abs(t.rate1 - r1True) > 1e-6:
		raise Exception("inaccurately calculated SpecBot.minProfitRate1(): rate1=%.8f; rate1true=%.8f" % (t.rate1, r1True))

	if not trimmed:
		if abs(ar1 - t.rate1) > 1e-10 \
		and abs(rp - mrp) > 1e-10:
			raise Exception("rate1=%.4f calculated by minProfitRate1() does not result in a minimum profit of %.2f%% and is not equal to ar1=%.4f" % (t.rate1, mrp*100, ar1))



for mssrc in range(len(Config.MSSRC)):
	Config.MARKETSTATE_SOURCE = mssrc

	with TstCommon():
		sb = SpecBot(
			dbFile = tstcommon.TST_DB_FILE,
			dbName = tstcommon.TST_DB_NAME,
			currency1str = "USD",
			currency2str = "RUB",
			readOnly = False,
			tmpDir = tstcommon.TST_TMP_DIR,
			wget = WgetTst(),
		)

		sb.updateMarketState()

		for am in [100, 5000, 10000]:
			for mrp in [0.0010, 0.0020, 0.0100, 0.5000]:
				for r1 in [1, 60, 1000]:
					for st in [TRST_UNDEF, TRST_OPEN1]:
						Config.MIN_REL_PROFIT = mrp
						doTest(sb=sb, am=am, mrp=mrp,
							r1=r1, st=st,
						)
