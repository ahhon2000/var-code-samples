#!/usr/bin/python3

import os, sys, shutil
sys.path = [".", ".."] + [os.path.dirname(os.path.abspath(sys.argv[0]))] + sys.path

from Config import *
import stat

if not os.path.isfile(WM_CERTIFICATE_FILE):
	raise Exception("no certificate file")

if not os.path.isfile(WM_KEY_FILE):
	raise Exception("no key file")

for f in [WM_CERTIFICATE_FILE, WM_KEY_FILE]:
	m = os.stat(f).st_mode
	if not (m & stat.S_IRUSR): raise Exception("file `%s' is not readable by the user" % f)
	if m & (stat.S_IXUSR | stat.S_IWUSR | stat.S_IRWXG | stat.S_IRWXO):
		raise Exception("certificate/key file `%s' has the wrong permissions" % f)
