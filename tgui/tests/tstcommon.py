import sys
import os, shutil
import Config


TST_TMP_DIR = "/tmp/.tgui_test_tmp/"

def createTmpDir():
	os.makedirs(TST_TMP_DIR, exist_ok=True)


def delTmpDir():
	shutil.rmtree(TST_TMP_DIR)


def ensure(expr, msg=""):
	if not expr: raise Exception(msg)

def ensureFloat(x, y, msg="", precision=1e-10):
	if abs(x - y) > precision:
		if not msg: msg = "{x} != {y}".format(x=x, y=y)
		raise Exception(msg)


class TstCommon:
	def __enter__(self):
		createTmpDir()

	def __exit__(self, a, b, c):
		delTmpDir()
