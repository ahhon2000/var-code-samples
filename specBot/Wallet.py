import Config
import re

class Wallet:
	def __init__(self, sb):
		self.specBot = sb
		self.currencyAmounts = {}  # {currency_str: amount, ...}


	def __getitem__(self, x):
		return self.currencyAmounts[str(x)]


	def __setitem__(self, x, y):
		self.currencyAmounts[str(x)] = y


	def download(self):

		sb = self.specBot
		self.currencyAmounts.clear()

		reqn = sb.getPar("wallet_request_number")
		reqn = int(reqn) if reqn else 0
		reqn += 1

		r = """
<w3s.request>
    <reqn>{reqn}</reqn>
    <getpurses>
        <wmid>{wmid}</wmid>
    </getpurses>
</w3s.request>
"""[1:-1].format(
			reqn = reqn,
			wmid = Config.WMID,
		)

		sb.setPar("wallet_request_number", str(reqn))

		xml = sb._wmXmlRequest(r,
			"https://w3s.wmtransfer.com/asp/XMLPursesCert.asp",
			outerTag = "w3s.response",
			wgetOptions = ['--no-check-certificate'],
		)
		if not xml:
			sb.logw("no wallet XML")
			return False

		rv = xml.find('retval')
		if rv is None:
			sb.logw("no retval tag")
			return False

		if rv.text != '0':
			rd = xml.find('retdesc')
			msg = "" if rd is None else rd.text
			sb.logw("could not download wallet contents; retval: `%s'\n\tReason: %s" % (rv.text, msg))
			return False

		ps = xml.find('purses')
		if ps is None:
			sb.logw("<purses/> tag missing in XML reply")
			return False

		a1 = None
		a2 = None
		n1 = ""
		n2 = ""
		for p in ps:
			if p.tag != 'purse': continue

			try:
				n = p.find('pursename').text
				a = float(re.sub(r',', '.',
					p.find('amount').text))
			except Exception as e:
				sb.logw("could not parse purses XML: %s" % e)
				return False

			if n == Config.PURSE1:
				a1 = a
				n1 = n
				self.currencyAmounts[Config.CURRENCY1] = a
			elif n == Config.PURSE2:
				a2 = a
				n2 = n
				self.currencyAmounts[Config.CURRENCY2] = a

		if a1 is None  or  a2 is None:
			sb.logw("could not determine wallet amounts from the downloaded XML")
			return False

		sb.log("downloaded amounts for purses %s (%.2f) and %s (%.2f)" % (n1, a1, n2, a2))

		return True


	def __str__(self):
		ca = self.currencyAmounts

		i = 0
		s = ""
		for (c, a) in sorted(ca.items(), key = lambda it: it[0]):
			if i > 0: s += "; "
			s += "%s: %.2f" % (c, a)

			i += 1

		return s
