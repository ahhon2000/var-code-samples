#!/usr/bin/python3

import os, sys
sys.path = [".", ".."] + [os.path.dirname(os.path.abspath(sys.argv[0]))] + sys.path

from SpecBot import SpecBot
from Transaction import Transaction
import Config
from defs import *
from tstcommon import *


import tstcommon
from tstcommon import TstCommon
from WgetTst import WgetTst

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
		ms = sb.marketState

		# profit on $100

		t = Transaction(sb,
			status = TRST_CLOSED2,
			amount = 1000,
			rate1 = 61,
			rate2 = 1/60,
			curPair = sb.curPair,
		)

		p = t.profit()
		pr = t.profit(relative=True)

		dp = p - 0.593138
		dpr = pr - 0.0005931384899638
		if abs(dp) > 0.01: raise Exception("incorrectly calculated transaction profit dp=%f; p=%f" % (dp, p))
		if abs(dpr) / pr > 0.01: raise Exception("incorrectly calculated relative transaction profit dpr=%f; pr=%f" % (dpr, pr))

		# profit for a partially exchanged direct transaction

		cp = sb.curPair
		cpr = cp.reverse()

		r1prev = 59
		r1 = 60
		ar2 = ms.avgRates[cpr]

		for am in [100, 1000, 10000]:
			t = Transaction(sb,
				status = TRST_OPEN2,
				amount = am,
				rate1 = r1,
				rate2 = 0,
				curPair = sb.curPair,
			)

			exch = 0.9 * t.remainder1
			t.remainder1 -= exch
			t.remainder2 += exch * r1prev

			pTrue = (t.remainder2 + t.remainder1 * r1 - t.getCommission2()) * ar2 - am
			p = t.profit()

			if abs(p - pTrue) / pTrue > 1e-10:
				raise Exception("inaccurately calculated transaction profit: p=%f; pTrue=%f" % (p, pTrue))

		# profit for a partially exchanged reverse transaction

		r1 = 60
		r2 = 1/61
		r2prev = 1/62
		for am in [100, 1000, 10000]:
			t = Transaction(sb,
				status = TRST_OPEN2,
				amount = am,
				rate1 = r1,
				rate2 = r2,
				curPair = sb.curPair,
			)

			t.remainder1 = 0
			t.remainder2 = (am - t.getCommission1()) * r1
			t.remainder2 -= t.getCommission2()

			exch = 0.9 * t.remainder2
			t.remainder2 -= exch
			t.remainder1 += exch * r2prev

			pTrue = t.remainder1 + t.remainder2 * r2 - am
			p = t.profit()

			if abs(p - pTrue) / pTrue > 1e-10:
				raise Exception("inaccurately calculated transaction profit: p=%f; pTrue=%f" % (p, pTrue))
