class Currency:
	def __init__(self,
		ide = 0,
		name = "",
		row = None,
	):
		if row:
			ide = row['id']
			name = row['name']

		self.ide = ide
		self.name = name


	def __hash__(self):
		return hash(self.name)


	def __str__(self):
		return self.name


	def __eq__(self, other):
		return self.__hash__() == other.__hash__()


class CurrencyPair:
	def __init__(self, sb, c1, c2):
		self.specBot = sb

		self.currency1 = sb.getCurrencyBy(c1)
		self.currency2 = sb.getCurrencyBy(c2)

		assert self.currency1.name  and  self.currency2.name
		assert self.currency1.ide  and  self.currency2.ide


	def __eq__(self, other):
		return self.__hash__() == other.__hash__()


	def __getitem__(self, x):
		if x == 0:
			return self.currency1
		elif x == 1:
			return self.currency2

		raise Exception("wrong index to a currency pair (`%s')" % x)


	def __iter__(self):
		yield self.currency1
		yield self.currency2


	def __str__(self):
		return "%s,%s" % (self.currency1, self.currency2)


	def __hash__(self):
		return hash(str(self))


	def reverse(self):
		"""Return a new currency pair, which is the reversed version
		of this one"""

		cp = CurrencyPair(self.specBot, self.currency2, self.currency1)

		return cp
