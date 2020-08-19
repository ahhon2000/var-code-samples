import time
import re

import smtplib
from email.mime.text import MIMEText
import traceback

from loggers import genLoggers
import Config
from TGui import TGui
from LiquidityTable import LiquidityTable
from Date import Date

class Observer:
	def __init__(self):
		self.tgui = TGui(readOnly=True)
		(self.log, self.loge, self.logw) = genLoggers(Config.FILE_OBSERVER_LOG)

	def checkLiquidityTable(self):
		bodies = []

		tg = self.tgui
		for ex in tg.exchanges:
			try:
				lt = LiquidityTable(ex,
					customDepthLst = [0.15, 0.15, 0.15],
					liquidityFor='all',
					avgInterval1=Config.DEFAULT_AVG_INTERVAL1,
					avgInterval2=Config.DEFAULT_AVG_INTERVAL2,
				)
				lt.load()
			except Exception as e:
				msg = "{exn}: {e}\n{tb}".format(
					exn = ex.name,
					e=e, tb=traceback.format_exc(),
				)
				self.logw(msg)
				bodies += [msg]

		m = {
			'subj': "Liquidity table error - {d}".format(d=Date('now')) if bodies else None,
			'body': "\n\n".join(bodies) if bodies else None,
		}

		return m

	def runForever(self):
		self.log('started')
		while True:
			try:
				ms = []

				ms += [ self.checkLiquidityTable() ]
				for m in ms:
					subj = m.get('subj')
					body = m.get('body')
					if subj  and  body:
						self.sendEmail(subj, body)
			except Exception as e:
				self.loge("{e}\n{tb}".format(e=e, tb=traceback.format_exc()))
			time.sleep(Config.OBSERVER_FREQ)

	def sendEmail(self, subject, body, continueOnFailure=True):
		msg = MIMEText(body)

		msg['Subject'] = subject
		msg['From'] = Config.SENDER_EMAIL
		msg['To'] = Config.RECIPIENT_EMAIL

		user = re.sub(r'^(.*)@.*', r'\1', Config.SENDER_EMAIL)
		pw = ""
		with open(Config.PASSWORD_FILE_SMTP) as fp:
			pw = fp.readline().strip()

		# Send the message via our own SMTP server.
		try:
			#s = smtplib.SMTP(Config.SMTP_SERVER, port=Config.SMTP_PORT, timeout=30)
			s = smtplib.SMTP_SSL(Config.SMTP_SERVER, timeout=30)
			s.connect(Config.SMTP_SERVER, port=Config.SMTP_PORT)
			#s.starttls()
			s.login(user, pw)
			s.send_message(msg)
			s.quit()
		except Exception as e:
			self.logw("could not send the email: %s" % e)
			if not continueOnFailure: raise e
