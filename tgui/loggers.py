import os, sys
import shutil
import subprocess
import re

import Config
from Date import Date
from pathlib import Path


def _rmOldArchives(fn):
	dirn = os.path.dirname(fn)
	fs = os.listdir(dirn)
	now = Date("now")
	for f in fs:
		if f.find(os.path.basename(fn)) < 0: continue
		if not re.search(r'[.][0-9]+[.]bz2$', f): continue

		d = Date(re.sub(r'.*[.]([0-9]+)[.]bz2$', r'\1', f))
		if d.daysEarlier(now) > Config.N_DAYS_TO_KEEP_LOGS:
			p = Path(dirn) / f
			p.unlink()

def _archiveLogFile(fn):
	d = Date("now")
	dt = d.toNiceText()

	fn = os.path.join(
		os.path.abspath(os.path.dirname(sys.argv[0])),
		fn,
	)

	sz = 0
	if os.path.isfile(fn): sz = os.path.getsize(fn)
	if sz > Config.MAX_LOG_SZ:
		f = "{lf}.{d}".format(lf = fn, d = d.toText())
		shutil.copy(fn, f)

		dir0 = os.path.abspath(os.getcwd())
		os.chdir(os.path.dirname(f))
		st = subprocess.call(["/bin/bzip2", f])
		os.chdir(dir0)

		if not st: os.unlink(fn)

	_rmOldArchives(fn)


def genLogFunc(fn):
	def func(msg, stderrFlg=False):
		nonlocal fn
		_archiveLogFile(fn)

		d = Date("now")
		s = "{d} {msg}".format(
			d = d.toNiceText(),
			msg = msg,
		)

		try:
			fp = sys.stdout if not stderrFlg else sys.stderr
			fp.write(s + "\n")

			fn = os.path.join(
				os.path.abspath(os.path.dirname(sys.argv[0])),
				fn,
			)
			with open(fn, "a") as fp:
				fp.write(s + "\n")
		except Exception as e:
			sys.stderr.write("an error occurred while reporting another error: " + str(e) + "\n")

	return func


def genErrorFunc(fn):
	funcl = genLogFunc(fn)
	def func(msg):
		nonlocal funcl
		funcl("Error: " + msg, stderrFlg=True)

	return func


def genWarningFunc(fn):
	funcl = genLogFunc(fn)
	def func(msg):
		nonlocal funcl
		funcl("Warning: " + msg)

	return func


def genLoggers(fn):
	return (genLogFunc(fn), genErrorFunc(fn), genWarningFunc(fn))
