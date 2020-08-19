#!/usr/bin/python3

import os, sys
sys.path = [".", ".."] + [os.path.dirname(os.path.abspath(sys.argv[0]))] + sys.path

from SpecBot import SpecBot
from Transaction import Transaction
import Config
from defs import *
import defs
from tstcommon import *
from Currency import CurrencyPair
from Date import Date

import tstcommon
from tstcommon import TstCommon
from WgetTst import WgetTst


def doTest(sb=None, am=None, r2=None, st=None, mrp=None, dur=None):
	ms = sb.marketState
	ar1 = ms.avgRates[sb.curPair]
	ar2 = ms.avgRates[sb.curPair.reverse()]

	r1 = 1.01 * r2
	t = Transaction(sb,
		status = st,
		amount = am,
		rate1 = r1,
		rate2 = 1/r2,
		curPair = sb.curPair,
	)
	t.remainder1 = 0
	t.remainder2 = (am - t.getCommission1()) * r1

	t.date2 = Date("now")
	t.date2closed = t.date2.plusHours(dur)

	(t.rate2, rpx) = sb.minProfitRate2(t,
		quiet=True,
	)

	if t.getDuration2() > Config.HOURS_MIN_REL_PROFIT_REVERSE:
		if abs(t.rate2 - ar2) > 1e-9:
			raise Exception("duration protection for minProfitRate2() did not work")
		return

	if not defs.insideInterval(t.rate2,
		ar2 * (1 - Config.MAX_RATE_DEVIATION),
		ar2 * (1 + Config.MAX_RATE_DEVIATION),
	):
		raise Exception("rate2 outside of the allowed interval")

	if t.status == TRST_CLOSED1:
		t.status = TRST_OPEN2
		t.remainder2 -= t.getCommission2()
	rp = t.profit(relative = True)

	r2True = None
	dev = t.rate2 - ar2
	trimmed = False
	if dev / ar2 > Config.MAX_RATE_DEVIATION:
		r2True = ar2 * (1 + Config.MAX_RATE_DEVIATION)
		trimmed = True
	elif dev / ar2 < - Config.MAX_RATE_DEVIATION:
		r2True = ar2 * (1 - Config.MAX_RATE_DEVIATION)
		trimmed = True

	if trimmed and abs(t.rate2 - r2True) > 1e-6:
		raise Exception("inaccurately calculated SpecBot.minProfitRate2(): rate2=%.8f; rate2true=%.8f" % (t.rate2, r2True))

	if not trimmed:
		if abs(ar2 - t.rate2) > 1e-10 \
		and abs(rp - mrp) > 1e-10:
			raise Exception("rate2=%.4f calculated by minProfitRate2() does not result in a minimum profit of %.2f%% and is not equal to ar2=%.4f" % (1/t.rate2, mrp*100, 1/ar2))
		#print("rpx = %f; rp = %f; mrp=%f;   t.rate2-ar2 = %f" % (rpx, rp, mrp, t.rate2-ar2))


#Config.RATE_SETTING_MODE = Config.RSM_SPREAD_AND_MIN_PROFIT
Config.HOURS_MIN_REL_PROFIT_REVERSE = 18
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

		for dur in [1, 3000]:
			for am in [100, 5000, 10000]:
				for mrp in [0.0010, 0.0020, 0.0100, 0.0500]:
					Config.MIN_REL_PROFIT = mrp
					for r2 in [55, 60, 70]:
						for st in [
							TRST_CLOSED1,
							TRST_OPEN2,
						]:
							doTest(sb=sb, am=am,
								mrp=mrp,
								r2=r2, st=st,
								dur=dur,
							)
