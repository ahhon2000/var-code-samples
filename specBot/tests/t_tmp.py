#!/usr/bin/python3

import os, sys
sys.path = [".", ".."] + [os.path.dirname(os.path.abspath(sys.argv[0]))] + sys.path

from SpecBot import SpecBot
from Transaction import Transaction
from Config import *
from defs import *
from tstcommon import *

import tstcommon
from tstcommon import TstCommon
from WgetTst import WgetTst

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

	failed = True
	try:
		sb = SpecBot(
			dbFile = tstcommon.TST_DB_FILE,
			dbName = tstcommon.TST_DB_NAME,
			currency1str = "USD",
			currency2str = "RUB",
			readOnly = False,
		)
	except Exception as e:
		failed = False
	if failed: raise Exception("tmpDir safety doesn't work")
