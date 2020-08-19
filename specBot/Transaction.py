from Currency import CurrencyPair
import defs
from defs import *
from Date import Date
import Config
from Config import MIN_RATE_CHANGE_TO_UPLOAD

class Transaction:
	def __init__(self, specBot,
		ide = 0,
		status = TRST_UNDEF,
		amount = 0,
		date1 = None,
		date2 = None,
		date1closed = None,
		date2closed = None,
		rate1 = 0,
		rate2 = 0,
		curPair = None,
		wm_tid1 = '',
		wm_tid2 = '',
		row=None,
	):

		self.specBot = specBot
		sb = specBot

		remainder1 = 0
		remainder2 = 0

		if row:
			ide = row['id']
			status = row['status']
			amount = row['amount']

			d1t = row['date1']
			d2t = row['date2']
			date1 = Date(d1t) if d1t else None
			date2 = Date(d2t) if d2t else None

			d1ct = row['date1closed']
			d2ct = row['date2closed']
			date1closed = Date(d1ct) if d1ct else None
			date2closed = Date(d2ct) if d2ct else None

			rate1 = row['rate1']
			rate2 = row['rate2']
			curPair = CurrencyPair(
				sb, row['currency1'], row['currency2']
			)
			wm_tid1 = row['wm_tid1']
			wm_tid2 = row['wm_tid2']
			remainder1 = row['remainder1']
			remainder2 = row['remainder2']

		self.ide = ide
		self.status = status
		self.amount = amount
		self.date1 = date1
		self.date2 = date2
		self.date1closed = date1closed
		self.date2closed = date2closed
		self.rate1 = rate1
		self.rate2 = rate2
		self.curPair = curPair
		self.wm_tid1 = wm_tid1
		self.wm_tid2 = wm_tid2

		if not row:
			remainder1 = amount - self.getCommission1()

		self.remainder1 = remainder1
		self.remainder2 = remainder2


	def save(self):
		sb = self.specBot

		d1txt = self.date1.toText() if self.date1 else ''
		d2txt = self.date2.toText() if self.date2 else ''
		d1ctxt = self.date1closed.toText() if self.date1closed else ''
		d2ctxt = self.date2closed.toText() if self.date2closed else ''

		if self.ide:
			# update existing
			sb.execute("""
				UPDATE transactions SET
					status = ?, amount = ?,
					date1 = ?, date2 = ?,
					date1closed = ?, date2closed = ?,
					rate1 = ?, rate2 = ?,
					currency1 = ?, currency2 = ?,
					wm_tid1 = ?, wm_tid2 = ?,
					remainder1 = ?, remainder2 = ?

				WHERE id = ?
			""", [
				self.status, self.amount,
				d1txt, d2txt,
				d1ctxt, d2ctxt,
				self.rate1, self.rate2,
				self.curPair[0].ide, self.curPair[1].ide,
				self.wm_tid1, self.wm_tid2,
				self.remainder1, self.remainder2,
				self.ide
			])
		else:
			# create new
			sb.execute("""
				INSERT INTO transactions (
					status, amount, date1, date2,
					date1closed, date2closed,
					rate1, rate2, currency1, currency2,
					wm_tid1, wm_tid2,
					remainder1, remainder2
				) VALUES (
					?, ?, ?, ?, ?,
					?, ?,
					?, ?, ?, ?, ?,
					?, ?
				)
			""", [
				self.status, self.amount,
				d1txt, d2txt,
				d1ctxt, d2ctxt,
				self.rate1, self.rate2,
				self.curPair[0].ide, self.curPair[1].ide,
				self.wm_tid1, self.wm_tid2,
				self.remainder1, self.remainder2
			])

			self.ide = self.specBot.lastrowid


	def _generalProfit(self, r1, r2):
		assert r1
		assert r2

		a1 = self.amount

		c1 = defs.calCommission(a1, self.curPair[0])
		a2 = (a1 - c1) * r1
		c2 = defs.calCommission(a2, self.curPair[1])

		p = a1 * (r1 - 1 / r2) * r2 - (c1 * r1 + c2) * r2

		return p


	def getTotalCommission(self, cur):
		"""Return the total commission of a roundtrip transaction in
			the given currency
		"""

		cp = self.curPair

		if not (cur == cp[0]  or  cur == cp[1]): raise Exception("unexpected currency `%s'" % cur)

		aux = self.profit(aux=True)

		a1 = self.amount
		p  = aux['p']
		r1 = aux['r1']
		r2 = aux['r2']

		assert r1
		assert r2
		
		tc = a1 * (r1 - 1 / r2) * r2 - p
		if cur == cp[1]:
			tc *= r1

		return tc


	def profit(self, relative=False, aux=False):
		"""Predict and return the profit of this transaction

		If aux == True then return a dictionary with auxiliary
		parameters (rates used for prediction, profit itself, ...)
		"""

		sb = self.specBot

		r1 = self.rate1
		r2 = self.rate2
		rem1 = self.remainder1
		rem2 = self.remainder2
		com1 = self.getCommission1()

		tar1 = sb.timeAvgRates()[self.curPair]
		tar2 = sb.timeAvgRates()[self.curPair.reverse()]

		# rates used for calculations
		rc1 = 0
		rc2 = 0

		p = 0
		s = self.status
		if s == TRST_UNDEF:
			rc1 = tar1
			rc2 = tar2
		elif s in [TRST_OPEN1, TRST_CLOSED1]:
			#rc1 = r1
			rc1 = (rem2 + rem1 * r1) / (self.amount - com1)
			rc2 = tar2
		elif s in [TRST_OPEN2]:
			rc1 = r1
			#rc2 = r2
			B = rem1 + rem2 * r2
			a2 = (self.amount - com1) * r1
			com2 = defs.calCommission(a2, self.curPair[1])
			rc2 = B / (a2 - com2)
		elif s == TRST_CLOSED2:
			rc1 = r1
			rc2 = r2
		else:
			raise Exception("invalid transaction status = %d" % s)

		p = self._generalProfit(rc1, rc2)

		if relative: p /= self.amount

		if aux:
			dic = {
				'p': p,
				'r1': rc1,
				'r2': rc2,
			}
			return dic

		return p


	def getCommission1(self):
		a1 = self.amount
		return defs.calCommission(a1, self.curPair[0])


	def getCommission2(self):
#		c1 = self.getCommission1()
#		ct = self.getTotalCommission(self.curPair[0])
#		c2 = ct - c1
#
#		aux = self.profit(aux=True)
#		r1 = aux['r1']
#
#		c2 *= r1
#
#		return c2

		a1 = self.amount
		aux = self.profit(aux=True)
		r1 = aux['r1']
		com1 = self.getCommission1()

		a2 = r1 * (a1 - com1)
		com2 = defs.calCommission(a2, self.curPair[1])

		return com2


	def getAmount2(self):
		aux = self.profit(aux=True)

		a1 = self.amount
		r1 = aux['r1']

		c1 = defs.calCommission(a1, self.curPair[0])
		a2 = (a1 - c1) * r1

		return a2


	def __str__(self):
		d1 = "?"
		d2 = "?"
		d1c = "?"
		d2c = "?"
		if self.date1: d1 = self.date1.toNiceText()
		if self.date2: d2 = self.date2.toNiceText()
		if self.date1closed: dc1 = self.date1closed.toNiceText()
		if self.date2closed: dc2 = self.date2closed.toNiceText()

		s = """
ide = {ide}
amount = {am}
curPair = {cp}
status = {st}
rate1 = {r1:.4f}
rate2 = {r2:.4f}
date1 = {d1}
date2 = {d2}
date1closed = {d1c}
date2closed = {d2c}
remainder1 = {rem1:.2f}
remainder2 = {rem2:.2f}
wm_tid1 = {wm_tid1}
wm_tid2 = {wm_tid2}
"""[1:-1].format(
			ide = self.ide,
			am = self.amount,
			st = self.status,
			r1 = self.rate1,
			r2 = self.rate2,
			d1 = d1,
			d2 = d2,
			d1c = d1c,
			d2c = d2c,
			wm_tid1 = self.wm_tid1,
			wm_tid2 = self.wm_tid2,
			rem1 = self.remainder1,
			rem2 = self.remainder2,
			cp = str(self.curPair),
		)

		return s


	def placeBid(self, reverse=False, deleteTmpFiles=True):
		sb = self.specBot
		if not reverse and self.status != TRST_UNDEF:
			raise Exception("cannot open a direct transaction with status=%d" % self.status)
		if reverse and self.status != TRST_CLOSED1:
			raise Exception("cannot open a reverse transaction with status=%d" % self.status)

		# Prepare the request file

		inpurse = Config.PURSE1 if not reverse else Config.PURSE2
		outpurse = Config.PURSE2 if not reverse else Config.PURSE1

		inAm = 0
		outAm = 0

		if not reverse:
			assert self.rate1
			inAm = self.amount -self.getCommission1()
			outAm = inAm * self.rate1
		else:
			assert self.rate2
			inAm = self.getAmount2() - self.getCommission2()
			outAm = inAm * self.rate2

		assert inAm > 0
		assert outAm > 0

		r = """
<wm.exchanger.request>
	<inpurse>{inpurse}</inpurse>
	<outpurse>{outpurse}</outpurse>
	<inamount>{inamount:.2f}</inamount>
	<outamount>{outamount:.2f}</outamount>
</wm.exchanger.request>
"""[1:-1].format(
			inpurse = inpurse,
			outpurse = outpurse,
			inamount = inAm,
			outamount = outAm,
		)

		# Send the request and retrieve the reply

		xml = sb._wmXmlRequest(r,
			"https://wmeng.exchanger.ru/asp/XMLTrustPay.asp",
			deleteTmpFiles=deleteTmpFiles,
		)

		if not xml:
			sb.logw("no xml reply")
			return

		# Process the xml reply

		rv = xml.find('retval')
		if rv is None:
			sb.logw("no retval tag")
			return

		if rv.text != '0':
			rd = xml.find('retdesc')
			msg = "" if rd is None else rd.text
			sb.logw("failed to open the new transaction (code `%s'): %s" % (rv.text, msg))
			return

		wm_tid = rv.get("operid", "")

		if not wm_tid:
			sb.logw("the new transaction was opened on WM but we could not get its operid")
			return

		# Save to the database

		if not reverse:
			self.status = TRST_OPEN1
			self.wm_tid1 = wm_tid
			self.date1 = Date("now")

			self.remainder1 = self.amount - self.getCommission1()
			self.remainder2 = 0
		else:
			self.status = TRST_OPEN2
			self.wm_tid2 = wm_tid
			self.date2 = Date("now")

			self.remainder2 -= self.getCommission2()

		self.save()

		# Report the opened transaction

		if not reverse:
			a1 = self.amount
			r1 = self.rate1
			com1 = self.getCommission1()

			r1log = self.rate1
			if self.rate1 < 1  and  self.rate1:
				r1log = 1 / self.rate1

			sb.log("opened a direct transaction: wm_tid1 = {wm_tid1}; amount = {a1} (including commission {com1:.2f}); rate = {r1:.4f}".format(
				wm_tid1 = wm_tid,
				a1 = a1,
				r1 = r1log,
				com1 = com1,
			))

			sb._emailOpen1(self)
		else:
			a2 = self.getAmount2()
			com2 = self.getCommission2()

			r2log = self.rate2
			if self.rate2 < 1  and  self.rate2:
				r2log = 1 / self.rate2

			sb.log("opened a reverse transaction: wm_tid2 = {wm_tid2}; amount = {a2} (including commission {com2:.2f}); rate = {r2:.4f}".format(
				wm_tid2 = wm_tid,
				a2 = a2,
				r2 = r2log,
				com2 = com2,
			))

			sb._emailOpen2(self)


	def uploadRate(self, deleteTmpFiles=True):
		sb = self.specBot

		# TODO Store last upload date in the DB.
		# TODO Don't upload if not enough time has passed since then

		wm_tid = ""
		oldRate = 0
		rate = 0
		st = self.status
		curstype = 0
		if st == TRST_OPEN1:
			tt = sb.getTransactionBy(self.ide)
			oldRate = tt.rate1
			dr = abs(oldRate - self.rate1) / oldRate 

			r1log = self.rate1
			if r1log < 1  and  r1log: r1log = 1 / r1log

			oldRateLog = oldRate
			if oldRateLog < 1  and  oldRateLog:
				oldRateLog = 1 / oldRateLog

			if dr < MIN_RATE_CHANGE_TO_UPLOAD:
				sb.log("skipped uploading the new direct rate because it would have only become slightly different (by %.4f%%: %.4f -> %.4f)" % (dr*100, oldRateLog, r1log))
				return

			wm_tid = self.wm_tid1
			rate = self.rate1
			curstype = 1
		elif st == TRST_OPEN2:
			tt = sb.getTransactionBy(self.ide)
			oldRate = tt.rate2
			dr = abs(oldRate - self.rate2) / oldRate

			r2log = self.rate2
			if r2log < 1  and  r2log: r2log = 1 / r2log

			oldRateLog = oldRate
			if oldRateLog < 1  and  oldRateLog:
				oldRateLog = 1 / oldRateLog

			if dr < MIN_RATE_CHANGE_TO_UPLOAD:
				sb.log("skipped uploading the new reverse rate because it would have only become slightly different (by %.4f%%: %.4f -> %.4f)" % (dr*100, oldRateLog, r2log))
				return

			wm_tid = self.wm_tid2
			rate = 1 / self.rate2
			curstype = 0
		else: raise Exception("the transaction's rate can only be updated if it is open but its status is %d" % (st))

		if not wm_tid: raise Exception("wm_tid is an empty string")

		if rate < 1:
			rate = 1 / rate
			curstype = 0 if curstype else 1

		r = """
<wm.exchanger.request>
	<operid>{wm_tid}</operid>
	<curstype>{curstype}</curstype>
	<cursamount>{rate:.4f}</cursamount>
</wm.exchanger.request>
"""[1:-1].format(
			wm_tid = wm_tid,
			rate = rate,
			curstype = curstype,
		)

		xml = sb._wmXmlRequest(r,
			"https://wmeng.exchanger.ru/asp/XMLTransIzm.asp",
			deleteTmpFiles=deleteTmpFiles,
		)
		if not xml:
			sb.logw("no xml reply")
			return

		rv = xml.find('retval')
		if rv is None:
			sb.logw("no retval tag")
			return

		success = False
		if rv.text == '0':
			success = True
		else:
			rd = xml.find('retdesc')
			msg = "" if rd is None else rd.text
			sb.logw("failed to upload the exchange rate (wm_tid=`%s'; retval=`%s'); reason: %s" % (wm_tid, rv.text, msg))

		if success:
			self.save()

		oldRateLog = oldRate
		if oldRate < 1  and  oldRate:
			oldRateLog = 1 / oldRate

		if st == TRST_OPEN1:
			r1 = self.rate1

			r1log = self.rate1
			if self.rate1 < 1  and  self.rate1:
				r1log = 1 / self.rate1

			if success:
				sb.log("updated the rate of the direct transaction wm_tid1 = {wm_tid1}: {r1old:.6f} -> {r1:.6f}".format(
					wm_tid1 = wm_tid,
					r1 = r1log,
					r1old = oldRateLog,
				))
			else:
				sb.logw("could not update the direct transaction's rate (wm_tid1 = {wm_tid1}, old rate1 = {r1old:.6f}, new rate1 = {r1:.6f})".format(
					wm_tid1 = wm_tid,
					r1 = r1log,
					r1old = oldRateLog,
				))
		if st == TRST_OPEN2:
			r2 = self.rate2

			r2log = self.rate2
			if self.rate2 < 1  and  self.rate2:
				r2log = 1 / self.rate2

			if success:
				sb.log("updated the rate of the reverse transaction wm_tid2 = {wm_tid2}; {r2old:.6f} -> {r2:.6f}".format(
					wm_tid2 = wm_tid,
					r2 = r2log,
					r2old = oldRateLog,
				))
			else:
				sb.logw("could not update the reverse transaction's rate (wm_tid2 = {wm_tid2}, old rate2 = {r2old:.6f}, new rate2 = {r2:.6f})".format(
					wm_tid2 = wm_tid,
					r2 = r2log,
					r2old = oldRateLog,
				))


	def getDuration2(self):
		d1 = self.date2
		d2 = self.date2closed

		if not d1: return 0
		if not d2: d2 = Date("now")

		h = d1.hoursEarlier(d2)

		return h


	def getPlace1(self, ms):
		if not self.wm_tid1: return 0

		bs = ms.bids
		cp = self.curPair

		p = 1
		for b in bs:
			if not(cp == b.curPair): continue
			if b.wm_tid == self.wm_tid1: continue

			assert b.amount1
			r1 = b.amount2 / b.amount1

			if self.rate1 < r1: break

			p += 1

		return p


	def getPlace2(self, ms):
		if not self.wm_tid2: return 0

		bs = ms.bids
		cpr = self.curPair.reverse()

		p = 1
		for b in bs:
			if not(cpr == b.curPair): continue
			if b.wm_tid == self.wm_tid2: continue

			assert b.amount2
			#r2 = b.amount1 / b.amount2
			r2 = b.amount2 / b.amount1

			if self.rate2 < r2: break

			p += 1

		assert p > 0

		return p
