import subprocess
import tstcommon
from tstcommon import *
import shutil
import MarketState
import Config
import re

class WgetTst:
	def __init__(self, default=True):
		self.default = default

		self.marketBids = {}
		self.myBids = []


	def run(self, cmd):
		st = 0

		if self.default:
			st = self._defaultEmul(cmd)
		else:
			st = self._customEmul(cmd)

		return st


	def _defaultEmul(self, cmd):
		tstcommon.createTmpDir()

		mssrc = Config.MARKETSTATE_SOURCE

		arg = list(cmd)
		lnk = arg[-1]
		URLS_HTML = MarketState.URLS_HTML
		URLS_XML = MarketState.URLS_XML
		if lnk in URLS_HTML.values()  or  lnk in URLS_XML.values():
			# Emulate downloading bids
			for cps in ["USD,RUB", "RUB,USD"]:
				dst = "{d}/.specBot_marketState.{cps}".format(
					d = tstcommon.TST_TMP_DIR,
					cps = cps,
				)
				if cps == "USD,RUB" and \
					mssrc == Config.MSSRC_HTML:
					src = "emulator_bids_direct.html"
				elif cps == "RUB,USD" and \
					mssrc == Config.MSSRC_HTML:
					src = "emulator_bids_reverse.html"
				elif cps == "USD,RUB" and \
					mssrc == Config.MSSRC_XML:
					src = "bids_direct.xml"
				elif cps == "RUB,USD" and \
					mssrc == Config.MSSRC_XML:
					src = "bids_reverse.xml"
				else: raise Exception("unpredicted case")

				shutil.copy(src, dst)
		else:
			# Emulate wmexchanger XML interface
			pass


	def _customEmul(self, cmd):
		# obtain the contents of the request file (if any)

		request = ""
		rfn = ""
		for i in range(len(cmd)):
			if not re.search(r'^--post-file', cmd[i]): continue
			if '=' in cmd[i]:
				rfn = re.sub(r'^--post-file=', r'', cmd[i])
			else:
				rfn = cmd[i+1]
			break

		if rfn:
			with open(rfn) as fp:
				ls = fp.readlines()
				request = "".join(ls)

		# process the request depending on the link

		fileReply = tstcommon.TST_TMP_DIR + "/.specBotReply.xml"
		lnk = cmd[-1]

		mssrc = Config.MARKETSTATE_SOURCE

		urls = None
		if mssrc == Config.MSSRC_HTML:
			urls = MarketState.URLS_HTML
		elif mssrc == Config.MSSRC_XML:
			urls = MarketState.URLS_XML

		if lnk in urls.values():
			cps = None
			for (cps2, lnk2) in urls.items():
				if lnk2 == lnk:
					cps = cps2
					break
			dst = "{d}/.specBot_marketState.{cps}".format(
				d = tstcommon.TST_TMP_DIR,
				cps = cps,
			)

			s = ""
			if cps == "USD,RUB":
				s = self._genBidsXML()
			elif cps == "RUB,USD":
				s = self._genBidsXML(reverse=True)
			else: raise Exception("unpredicted cps = `%s'" % cps)

			with open(dst, "w") as fp:
				fp.write(s)

		elif lnk == 'https://wmeng.exchanger.ru/asp/XMLTrustPay.asp':
			tid = ""
			if re.search(r'<inpurse>\s*' + Config.PURSE1 + '\s*</inpurse>', request, flags=re.IGNORECASE):
				tid = '666'
			elif re.search(r'<inpurse>\s*' + Config.PURSE2 + '\s*</inpurse>', request, flags=re.IGNORECASE):
				tid = '999'
			else:
				raise Exception("invalid placeBid request:\n%s" % (request))

			with open(fileReply, "w") as fp:
				s = """
<wm.exchanger.response>
	<retval operid="{tid}">0</retval>
</wm.exchanger.response>
""".format(
	tid = tid,
)
				fp.write(s)
		elif lnk == "https://wmeng.exchanger.ru/asp/XMLWMList2.asp":
			with open(fileReply, "w") as fp:
				bidsLst = ""
				for b in self.myBids:
					bidsLst += """
	<Query id="{tid}" state="{state}" amountin="{amountin}" amountout="{amountout}"/>
""".format(
	tid = b['tid'],
	state = b['state'],
	amountin = b['amountin'],
	amountout = b['amountout'],
)

				s = """
<wm.exchanger.response>
	<retval>0</retval>
	<WMExchangerQuerys wmid="{wmid}">
		{bidsLst}
	</WMExchangerQuerys>
</wm.exchanger.response>
""".format(
	wmid = Config.WMID,
	bidsLst = bidsLst,
)
				fp.write(s)
		elif lnk == "https://wmeng.exchanger.ru/asp/XMLTransIzm.asp":
			with open(fileReply, "w") as fp:
				s = """
<wm.exchanger.response>
	<retval>0</retval>
	<retdesc></retdesc>
</wm.exchanger.response>
"""
				fp.write(s)
		else:
			raise Exception("unsupported link: `%s'" % lnk)

		return 0


	def _genBidsXML(self, reverse = False):
		mssrc = Config.MARKETSTATE_SOURCE
		tstcommon.ensure(mssrc in [Config.MSSRC_HTML, Config.MSSRC_XML], "unknown mssrc = %d" % mssrc)

		if len(self.marketBids) == 0: return ""
		elif len(self.marketBids) != 2: raise Exception("marketBids must be a two element dictionary")

		bs = None
		if not reverse: bs = self.marketBids['direct']
		else: bs = self.marketBids['reverse']

		s = ""

		if mssrc == Config.MSSRC_HTML:
			s = """
<TABLE  class="bidsList" width=100% border="0" cellpadding="3" cellspacing="1">
<tr align="center">
 
<td title="" align='center'   >Номер <BR />заявки</td>
<td title="" align='center'   >Есть сумма <BR />WMZ</td>
<td title="" align='center'   >Нужна сумма <BR />WMR</td>
<td title="" align='center'   >Прямой курс <BR />(WMZ/WMR)</td>
<td title="" align='center'   >Обратный курс <BR />(WMR/WMZ)</td>
<td title="" align='center'   >Всего сумма <BR />WMZ (*)</td>
<td title="" align='center'   >Всего сумма <BR />WMR (*)</td>
<td title="" align='center'   >Дата подачи</td>
</tr>
"""
		elif mssrc == Config.MSSRC_XML  and  not reverse:
			s = """
<?xml version="1.0"?><wm.exchanger.response>
	<BankRate direction="RUR/USD" ratetype="0">57,7832</BankRate>
	<WMExchnagerQuerys amountin="WMZ" amountout="WMR" inoutrate="WMZ/WMR" outinrate="WMR/WMZ">

"""[1:-1]
		elif mssrc == Config.MSSRC_XML  and  reverse:
			s = """
<?xml version="1.0"?><wm.exchanger.response>
	<BankRate direction="RUR/USD" ratetype="0">57,7832</BankRate>
	<WMExchnagerQuerys amountin="WMR" amountout="WMZ" inoutrate="WMR/WMZ" outinrate="WMZ/WMR">

"""[1:-1]
		else: raise Exception("unpredicted case")

		for b in bs:
			a1 = b['amount']
			r = b['rate']
			if reverse: r = 1 / r
			a2 = a1 * r
			
			if mssrc == Config.MSSRC_HTML:
				s += """
<tr    onclick="document.location = 'wmquerysnew.asp?refID=26200929&deststamp=81'" title="Для перехода к просмотру нажмите левую кнопку мыши." >

	<td align='center'   >{tid}</td>
	<td align='right'   >{amount1:.2f}</td>
	<td align='right'   >{amount2:.2f}</td>
	<td align='right'   >1</td>
	<td align='right'   >1</td>
	<td align='right'   >32283,73</td>
	<td align='right'   >1966072,70</td>
	<td align='right'   >04.08.2017 20:39:22</td>

</tr>
""".format(
	tid = b['tid'],
	amount1 = a1,
	amount2 = a2,
)
			elif mssrc == Config.MSSRC_XML:
				s += """
<query id="{tid}" amountin="{amount1:.2f}" amountout="{amount2:.2f}"></query>
""".format(
	tid = b['tid'],
	amount1 = a1,
	amount2 = a2,
)
			else: raise Exception("unpredicted case")

		if mssrc == Config.MSSRC_HTML:
			s += """
</TABLE>
"""
		elif mssrc == Config.MSSRC_XML:
			s += """
	</WMExchnagerQuerys>
</wm.exchanger.response>
"""
		else: raise Exception("unpredicted case")

		return s
