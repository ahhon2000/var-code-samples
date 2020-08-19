import xml.etree.ElementTree as ET
import Config
import os
import re
from Bid import Bid
from Date import Date
import subprocess
from defs import TRST_OPEN1, TRST_CLOSED1, TRST_OPEN2
from Transaction import Transaction

URLS_HTML = {
	# "USD,RUB": 'https://wm.exchanger.ru/asp/wmlist.asp?exchtype=1',
	# "RUB,USD": 'https://wm.exchanger.ru/asp/wmlist.asp?exchtype=2',
	"USD,RUB": 'https://wm.exchanger.ru/asp/wmlist_old.asp?exchtype=1',
	"RUB,USD": 'https://wm.exchanger.ru/asp/wmlist_old.asp?exchtype=2',
}
URLS_XML = {
	"USD,RUB": 'https://wm.exchanger.ru/asp/XMLWMList.asp?exchtype=1',
	"RUB,USD": 'https://wm.exchanger.ru/asp/XMLWMList.asp?exchtype=2',
	"USD,WMX": 'https://wm.exchanger.ru/asp/XMLWMList.asp?exchtype=33',
	"WMX,USD": 'https://wm.exchanger.ru/asp/XMLWMList.asp?exchtype=34',
	"USD,WMH": 'https://wm.exchanger.ru/asp/XMLWMList.asp?exchtype=79',
	"WMH,USD": 'https://wm.exchanger.ru/asp/XMLWMList.asp?exchtype=80',
}


class MarketState:

	def __init__(self,
		specBot,
		ide = 0,
		date = None,
		row = None,
		nBidsLimit = 0,  # 0 means "no limit"
	):
		if row:
			ide = row['id']
			date = Date(row['date'])

		self.specBot = specBot
		self.ide = ide
		self.date = date
		self.nBidsLimit = nBidsLimit

		# The dictionary of average rates
		# e. g.:    cp: 61.5
		# where cp is a currency pair object
		self.avgRates = {}

		self.bids = []

		if row:
			self._loadBidsFromDB()
			self._calAvgRates()

		self._reasonMSDownloadFailed = ""


	def _loadBidsFromDB(self):
		sb = self.specBot

		limitStr = ""
		if self.nBidsLimit:
			limitStr = "LIMIT %d" % (2*self.nBidsLimit)

		rs = sb.execute("""
			SELECT * FROM bids
			WHERE marketstate = ?
			ORDER BY place
			{limitStr}
""".format(limitStr=limitStr), [self.ide])

		bs = self.bids
		bs.clear()
		for r in rs:
			b = Bid(sb, marketState=self, row=r)
			bs += [b]


	def _calAvgRate(self, bids):
		sb = self.specBot
		from Config import MAX_PLACE_FOR_WEIGHING as p0

		# exclude our open transactions from the average

		rows = sb.execute("""
			SELECT * FROM transactions
			WHERE status = ? or status = ? or status = ?
""", [TRST_OPEN1, TRST_CLOSED1, TRST_OPEN2])

		wm_tids = []
		for row in rows:
			t = Transaction(sb, row=row)
			for wm_tid in [t.wm_tid1, t.wm_tid2]:
				if not wm_tid: continue
				wm_tids += [wm_tid]

		bids2 = []
		for b in bids:
			if len(bids2) >= p0: break
			if b.wm_tid in wm_tids: continue
			bids2 += [b]

		bids = bids2

		# Calculate the average
		
		r1 = 0
		ws = 0
		p = 0
		for b in bids:
			a = b.amount1
			r = b.amount2 / b.amount1

			w = a * (p0 - p) / p0
			ws += w
			r1 += w * r

			p += 1

		r1 /= ws

		return r1


	def _calAvgRates(self):
		ars = self.avgRates
		ars.clear()

		# bids dictionary, e. g.  curPair: bids_for_that_curPair
		bsdic = {}

		for b in self.bids:
			cp = b.curPair
			bs = bsdic.get(cp, None)
			if bs is None:
				bs = []
				bsdic[cp] = bs

			bs += [b]

		for (cp, bs) in bsdic.items():
			ars[cp] = self._calAvgRate(bs)
			

	def download(self,
		currencyPairs = [],
	):
		"""Fill out the MarketState object for the given currency pairs
			with data downloaded from the internet.

		Return True on success, False otherwise
		"""

		for cp in currencyPairs:
			st = self._downloadHTMLs(cp)
			if not st: return False

			st = self._parseHTMLs(cp)
			if not st: return False

		self._calAvgRates()

		return True


	def _getTmpFileName(self, cp):
		sb = self.specBot
		f = "{d}/.specBot_marketState.{cps}".format(
			d = sb.tmpDir,
			cps = str(cp),
		)

		return f


	def _downloadHTMLs(self, cp1):
		"""Download the HTML bid page for currency pair cp1"""

		sb = self.specBot

		# Check here if enough time has passed since the last connect
		# to avoid banning

		dn = Date("now")

		dtxt = sb.getPar("lastMarketstateDownloadDate")
		if dtxt:
			d = Date(dtxt)
			m = d.minutesEarlier(dn)
			if m < Config.MIN_MINUTES_BTW_REQUESTS:
				sb.logw("a marketstate download attempt was made %.2f minutes after the latest instead of the allowed %.2f minutes" % (m, Config.MIN_MINUTES_BTW_REQUESTS))
				self._reasonMSDownloadFailed = "ban_protection"
				return False

		sb.setPar("lastMarketstateDownloadDate", dn.toText())

		# Download

		cp2 = cp1.reverse()
		st = 0
		sb.log("Downloading bids for %s and %s" % (cp1, cp2))
		for cp in (cp1, cp2):
			f = self._getTmpFileName(cp)

			l = None
			k = str(cp[0]) + "," + str(cp[1])
			if Config.MARKETSTATE_SOURCE == Config.MSSRC_HTML:
				l = URLS_HTML[k]
			elif Config.MARKETSTATE_SOURCE == Config.MSSRC_XML:
				l = URLS_XML[k]
			else: raise Exception("unpredicted mssrc")

			sb.log("\t%s from %s..." % (cp, l))
			st = sb.wget.run(["-O", f, l])
			if st:
				sb.logw("downloading bids failed for currency pair %s; (wget's exit status = %d)" % (cp, st))
				break

		sb.log("\tDone!" % (cp))

		return not st


	def _parseHTMLs(self, cp1):
		sb = self.specBot
		bs = self.bids
		cp2 = cp1.reverse()

		for (cp, flgRev) in [(cp1, False), (cp2, True)]:
			f = self._getTmpFileName(cp)

			if not os.path.isfile(f):
				sb.logw("could not find the downloaded HTML file `%s'" % (f))
				return False

			bpars = None
			try:
				mssrc = Config.MARKETSTATE_SOURCE
				if mssrc == Config.MSSRC_HTML:
					bpars = self._extractBidPars_html(f, cp)
				elif mssrc == Config.MSSRC_XML:
					bpars = self._extractBidPars_xml(f, cp)

				if not bpars: raise Exception("bids' parameters extractor returned an empty list for %s" % (cp))
			except Exception as e:
				sb.logw("could not extract bid parameters for currency pair `%s': %s" % (cp, e))
				return False

			assert bpars

			p = 1  # place
			for (ide, a1, a2) in bpars:
				r = a2 / a1
				if flgRev: r = 1 / r

				b = Bid(sb,
					curPair = cp,
					amount1 = a1,
					amount2 = a2,
					place = p,
					wm_tid = str(ide),
					marketState = self,
				)
				bs += [b]

				p += 1

		for cp in [cp1, cp2]:
			f = self._getTmpFileName(cp)
			if os.path.isfile(f): os.unlink(f)

		return True


	def _extractBidPars_xml(self, f, cp):
		sb = self.specBot
		bpars = []

		xmlstr = ""
		with open(f) as fp:
			ls = fp.readlines()
			xmlstr = "".join(ls)

		xml = None
		try:
			xml = ET.fromstring(xmlstr)
			if xml is None: raise Exception("failed to create an xml tree object")
		except Exception as e:
			sb.logw("xml parser failed (file `%s'): %s; file contents:\n%s" % (f, e, xmlstr))
			return bpars

		if xml.tag != "wm.exchanger.response":
			sb.logw("the xml reply root tag is wrong: `%s' instead of `wm.exchanger.response'" % (xml.tag))
			return bpars

		qs = xml.find('WMExchnagerQuerys')
		if qs is None: qs = xml.find('WMExchangerQuerys')
		if qs is None:
			sb.logw("could not obtain the bids list from WM")
			return bpars

		if not len(qs):
			self.logw("no <query/> tag found in the XML reply for the following transaction: %s" % (t))
			return bpars

		cs1 = qs.attrib.get('amountin')
		cs2 = qs.attrib.get('amountout')

		cs1expected = Config.WM_CURRENCY_SYNONYMS[str(cp[0])].upper()
		cs2expected = Config.WM_CURRENCY_SYNONYMS[str(cp[1])].upper()
		if cs1.upper() != cs1expected:
			self.logw("the currency for amoutin is `%s' instead of `%s'" % (cs1, cs1expected))
			return bpars

		if cs2.upper() != cs2expected:
			self.logw("the currency for amoutout is `%s' instead of `%s'" % (cs2, cs2expected))
			return bpars

		inoutrate = qs.attrib.get('inoutrate')
		outinrate = qs.attrib.get('outinrate')

		if inoutrate.upper() != "{cs1}/{cs2}".format(
				cs1 = cs1, cs2 = cs2,).upper():
			self.logw("inoutrate is %s; expected %s/%s" % (inoutrate, cs1, cs2))
			return bpars

		if outinrate.upper() != "{cs2}/{cs1}".format(
				cs1 = cs1, cs2 = cs2,).upper():
			self.logw("outinrate is %s; expected %s/%s" % (inoutrate, cs2, cs1))
			return bpars

		for q in qs:
			if q.tag.lower() != 'query': continue

			ide = q.attrib.get('id')
			amountin = re.sub(r',', '.', q.attrib.get('amountin'))
			amountout = re.sub(r',', '.',q.attrib.get('amountout'))
			a1 = float(amountin)
			a2 = float(amountout)

			assert a1 > 0
			assert a2 > 0
	
			bpars += [(ide, a1, a2)]

		bpars.sort(key = lambda x: x[2] / x[1])

		return bpars
		


	def _extractBidPars_html(self, f, cp):
		ams = []

		with open(f) as fp:
			ls = fp.readlines()

			# Find the beginning and end of the table

			i = 0
			i0 = -1
			i1 = -1
			for l in ls:
				if re.search(r'<TABLE.*class.*bidsList', l):
					i0 = i
				if re.search(r'</TABLE>', l):
					i1 = i
					break

				i += 1

			if i0 < 0: raise Exception("i0 < 0")
			if i1 < 0: raise Exception("i1 < 0")
			if i0 >= i1: raise Exception("i0 >= i1")

			# Parse the table

			flgTr = False
			trind = -1
			tdind = -1
			#
			ide = 0
			amount1 = 0
			amount2 = 0
			for i in range(i0 + 1, i1):
				l = ls[i]

				if re.search(r'^\s*<tr\s', l):
					flgTr = True
					trind += 1
					tdind = -1
					ide = 0
					amount1 = 0
					amount2 = 0
					continue

				if re.search(r'^\s*</tr>', l):
					flgTr = False
					if trind > 0:
						ams += [(ide, amount1, amount2)]

				# skip the first tr with titles
				if flgTr and trind == 0: continue

				# skip everything outside <tr> and </tr>
				if not flgTr: continue

				# from here on only work with <td>
				if re.search(r'^\s*<td\s', l):
					tdind += 1
				else:
					continue

				s = re.sub(r'^\s*<td[^>]+>\s*([^<]*)\s*.*', r'\1', l)
				s = re.sub(r',', '.', s)
				if tdind == 0:
					ide = int(s)
				elif tdind == 1:
					amount1 = float(s)
				elif tdind == 2:
					amount2 = float(s)
					

		return ams


	def save(self):
		sb = self.specBot

		if self.ide:
			# update existing
			sb.execute("""
				UPDATE marketstates SET
					date = ?

				WHERE id = ?
			""", [
					self.date.toText(),
					self.ide
			])
		else:
			# create new
			sb.execute("""
				INSERT INTO marketstates (
					date
				) VALUES (
					?
				)
			""", [
					self.date.toText(),
			])

			self.ide = self.specBot.lastrowid
		

		bs = self.bids

		# save bids in the db
		for b in bs:
			b.save(nocommit=True)

		sb.db.commit()


	def __str__(self):
		ars = self.avgRates

		s = """
Market State at {d}

"""[1:-1].format(
	d = self.date.toNiceText(),
)

		processed = []

		i = 0
		for cp in sorted(ars.keys(), key = lambda x: str(x)):
			c1 = cp[0]
			c2 = cp[1]
			cpr = cp.reverse()

			if str(cp) in processed  or  str(cpr) in processed:
				continue

			processed += [str(cp)]

			if ars[cpr] > ars[cp]:
				(cp, cpr) = (cpr, cp)

			r1 = ars[cp]
			r2r = ars[cpr]
			r2 = 1 / r2r if r2r else 0

			spread = r1 / r2 - 1
			spread_p = spread * 100

			if i > 0: s += "\n\n"

			s += """
	arate1 = {r1:.4f} {c2}/{c1}      arate2 = {r2:.4f} {c2}/{c1}
	spread = {spread_p:.2f}%
"""[1:-1].format(
			r1 = r1,
			r2 = r2,
			c1 = str(c1),
			c2 = str(c2),
			spread_p = spread_p,
)

			i += 1

		return s


	def getAvgRate(self, cp):
		return self.avgRates[cp]


	def getPlace(self, wm_tid):
		if not wm_tid: return 0

		for b in self.bids:
			if b.wm_tid == wm_tid:
				return b.place

		return 0
