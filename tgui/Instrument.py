import re

class Instrument:
	def __init__(self, jsonRow):
		r = jsonRow
		if not isinstance(r, dict): raise Exception("jsonRow is not a dictionary")

		for k in ['instrument_id', 'delivery']:
			if k not in r.keys(): raise Exception("can't find key `{k}' in the instrument dict")

		self.instrument_id = r['instrument_id']
		self.delivery = r['delivery']
		self._assignName()


	def getCoin(self):
		if len(self.instrument_id) < 3: return ""

		c = re.sub(r'^(...).*', r'\1', self.instrument_id)
		if re.search(r'^BCHABC', self.instrument_id): c = 'BCHABC'

		return c


	def _assignName(self):
		raise Exception("redefine this function in children")


	def getShortAlias(self):
		return ""


	def sameAs(self, other):
		raise Exception("redefine this function in children")


	def getContractType(self):
		raise Exception("redefine this function in children")
		

class InstrumentFutures(Instrument):
	def __init__(self, jsonRow):
		r = jsonRow

		for k in ['alias']:
			if k not in r.keys(): raise Exception("can't find key `{k}' in the instrument dict".format(k=k))

		self.alias = r['alias']

		Instrument.__init__(self, jsonRow)


	def _assignName(self):
		deliv = re.sub(r'-', r'', self.delivery)

		if deliv  and  len(deliv) < 4: raise Exception("suspicious value of delivery date: " + deliv)
		deliv = re.sub(r'.*(....)$', r'\1', deliv)
		if deliv  and  len(deliv) != 4: raise Exception("suspicious value of delivery date: " + deliv)

		if deliv:
			coin = self.getCoin()
			self.name = """
{coin}-{deliv}
"""[1:-1].format(
	coin = coin,
	deliv = deliv,
)
		else:
			self.name = self.instrument_id


	def getShortAlias(self):
		a = self.alias

		if a == 'this_week': return 'w'
		if a == 'next_week': return 'b'
		if a == 'quarter': return 'q'

		return a


	def sameAs(self, other):
		if self.instrument_id == other.instrument_id:
			if self.delivery == other.delivery:
				if self.alias == other.alias:
					return True
		return False


	def getContractType(self):
		return "futures"


class InstrumentSwaps(Instrument):
	def __init__(self, jsonRow):
		Instrument.__init__(self, jsonRow)


	def _assignName(self):
		if re.search(r'^[A-Z]{6}$', self.instrument_id):
			self.name = self.instrument_id
		elif re.search(r'^[A-Z]{7,}', self.instrument_id):
			self.name = self.instrument_id
		else:
			self.name = self.getCoin() + "-SWAP"


	def sameAs(self, other):
		if self.instrument_id == other.instrument_id:
			if self.delivery == other.delivery:
					return True
		return False


	def getContractType(self):
		return "swaps"
