from flask import render_template, g, request
import flask_sijax
import re
import flask
import traceback

from Date import Date
import Config

def restartBackend(tg):
	msgs = []

	st = tg.restartBackend()
	if st: raise Exception("systemctl failed to restart the backend (status = {st})".format(st = st))

	msgs += ["The backend has been restarted"]

	return msgs


def processSettings(tg):
	if request.method != 'POST': return []

	if request.form.get('restartBackend'): return restartBackend(tg)

	depth = request.form.get('default_price_depth', None)
	if depth is None: return []

	depth = float(depth)
	if depth <= 0  or  depth > 100: raise Exception("default depth out of range")

	tg.setSessionPar('DEFAULT_PRICE_DEPTH', float, depth)
	return ["Saved"]


def loadSettings(tg):
	g.default_price_depth = tg.getSessionPar('DEFAULT_PRICE_DEPTH')


def render(tg):
	g.tgui = tg

	if g.sijax.is_sijax_request:
		return ""

	errMsgs = []
	infoMsgs = []

	try:
		infoMsgs += processSettings(tg)
	except Exception as e:
		m = """
Error saving settings: {e}
"""[1:-1].format(e=str(e))
		m += "\n" + str(e) + ": " + "".join(traceback.format_exception(e.__class__, e, e.__traceback__))

		errMsgs += [m]

	try:
		loadSettings(tg)
	except Exception as e:
		m = """
Error loading settings: {e}
"""[1:-1].format(e=str(e))
		m += "\n" + str(e) + ": " + "".join(traceback.format_exception(e.__class__, e, e.__traceback__))

		errMsgs += [m]


	for ms in (infoMsgs, errMsgs):
		for (i, m) in enumerate(ms):
			m = flask.escape(m)
			ms[i] = "\n<br>\n".join(m.split("\n"))

	if errMsgs: g.error_messages = errMsgs
	if infoMsgs: g.info_messages = infoMsgs

	cnt = render_template('settings.html')

	return {'content': cnt, 'pageTitle': 'Settings'}
