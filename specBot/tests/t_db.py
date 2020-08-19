#!/usr/bin/python3

import os, sys
sys.path = [".", ".."] + [os.path.dirname(os.path.abspath(sys.argv[0]))] + sys.path

from SpecBot import SpecBot
from Transaction import Transaction
from Config import *
from defs import *
from tstcommon import *
from Date import Date
from MarketState import MarketState
from Bid import Bid

import tstcommon
from tstcommon import TstCommon
from WgetTst import WgetTst

def test(fmt, sb):
	if fmt == Config.DBF_SQLITE3  and  \
		not os.path.isfile(tstcommon.TST_DB_FILE):
		raise Exception("could not create the DB file")

	sb2 = SpecBot(
		dbFile = tstcommon.TST_DB_FILE,
		dbName = tstcommon.TST_DB_NAME,
		currency1str = "USD",
		currency2str = "RUB",
		tmpDir = tstcommon.TST_TMP_DIR,
		wget = WgetTst(),
	)

	# Test the read-only mode

	roFailed = True
	try:
		t = Transaction(sb2)
		t.save()
	except Exception as e:
		roFailed = False
	if roFailed: raise Exception("the readonly mode doesn't work for %s" % (Config.DBF[fmt]))


for fmt in [Config.DBF_SQLITE3, Config.DBF_MARIADB]:
	Config.DB_FORMAT = fmt
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

		test(fmt, sb)

# Check if lastrowid works


for fmt in range(len(Config.DBF)):
	Config.DB_FORMAT = fmt
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

		for i in range(5):
			t = Transaction(sb,
				status = TRST_OPEN1,
				rate1 = 59.5,
				rate2 = 58.5,
				curPair = sb.curPair,
				wm_tid1 = '',
				wm_tid2 = '12345',
			)
			t.save()

		if sb.lastrowid != 5: raise Exception("bad lastrowid value %d for %s" % (sb.lastrowid, Config.DBF[fmt]))

# Check if different database formats produce the same results

d1 = Date("2017-08-19 16:54:38")
d2 = Date("2017-08-20 19:54:38")

results = {}  # dbFormat: result
for fmt in range(len(Config.DBF)):
	Config.DB_FORMAT = fmt

	with TstCommon():
		r = {}

		sb = SpecBot(
			dbFile = tstcommon.TST_DB_FILE,
			dbName = tstcommon.TST_DB_NAME,
			currency1str = "USD",
			currency2str = "RUB",
			readOnly = False,
			tmpDir = tstcommon.TST_TMP_DIR,
			wget = WgetTst(),
		)

		t = Transaction(sb,
			status = TRST_OPEN1,
			date1 = d1,
			date2 = d2,
			rate1 = 59.5,
			rate2 = 58.5,
			curPair = sb.curPair,
			wm_tid1 = '',
			wm_tid2 = '12345'
		)
		t.save()
		t = sb.getTransactionBy(sb.lastrowid)

		ms = MarketState(sb, date=d1)
		ms.save()
		ms = sb.getMarketStateBy(sb.lastrowid)

		b = Bid(sb,
			curPair = sb.curPair,
			amount1 = 10000,
			amount2 = 600000,
			place = 4,
			wm_tid = "",
			marketState = ms,
		)
		b.save()
		b = sb.getBidBy(sb.lastrowid)

		bs = []
		for i in range(5):
			b2 = Bid(sb,
				curPair = sb.curPair,
				amount1 = 1 + i,
				amount2 = (i+1)*60,
				place = 4,
				wm_tid = "",
				marketState = ms,
			)
			b2.save()
			b2 = sb.getBidBy(sb.lastrowid)
			bs += [b2]

		assert t
		assert ms
		assert b
		assert bs

		r['t'] = str(t)
		r['ms'] = str(ms)
		r['b'] = str(b)
		r['bs'] = "\n".join(list(str(bs2) for bs2 in bs))

		results[fmt] = r

for fmt1 in range(len(Config.DBF)):
	for fmt2 in range(len(Config.DBF)):
		if fmt1 == fmt2: continue

		r1 = results[fmt1]
		r2 = results[fmt2]

		assert len(r1) == len(r2)

		for k in sorted(r1.keys()):
			s1 = r1[k]
			s2 = r2[k]
			if s1 != s2:
				raise Exception("wrong result for `%s' in the pair %s, %s: `%s' instead of `%s'" % (k, DBF[fmt1], DBF[fmt2], s1, s2))
