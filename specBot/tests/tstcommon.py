import sys
import os, shutil
import Config
from WgetTst import WgetTst
from SpecBot import SpecBot

TST_TMP_DIR = "/tmp/.specBot_test_tmp/"
TST_DB_FILE = TST_TMP_DIR + "/.specBot_test.db"
TST_DB_NAME = "specbot_tst"
wgetTst = WgetTst()

def createTmpDir():
	os.makedirs(TST_TMP_DIR, exist_ok=True)


def delTmpDir():
	shutil.rmtree(TST_TMP_DIR)


def dropTables():
	if Config.DB_FORMAT not in [Config.DBF_MARIADB]: return

	import mysql.connector as mariadb
	db = mariadb.connect(
		user = Config.DB_USER,
		password = Config.DB_PASSWORD,
		database = TST_DB_NAME,
	)
	c = db.cursor(buffered=True)

	for tn in ["currencies, marketstates, transactions, pars, bids"]:
		c.execute("""
			DROP TABLE IF EXISTS {tn}
""".format(
			tn = tn,
		))


def ensure(expr, msg):
	if not expr: raise Exception(msg)

def ensureFloat(x, y, msg, precision=1e-10):
	if abs(x - y) > precision: raise Exception(msg)


class TstCommon:
	def __enter__(self):
		createTmpDir()
		dropTables()
		if os.path.isfile(TST_DB_FILE): os.unlink(TST_DB_FILE)

	def __exit__(self, a, b, c):
		dropTables()
		if os.path.isfile(TST_DB_FILE): os.unlink(TST_DB_FILE)
		delTmpDir()
