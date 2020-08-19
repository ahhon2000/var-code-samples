import time
import datetime
import dateutil.parser
import copy

class Date:
	def __init__(self, s):
		dt = None

		if s.__class__.__name__ == 'Date':
			dt0 = s.datetime
			dt = datetime.datetime(
				year = dt0.year,
				month = dt0.month,
				day = dt0.day,
				hour = dt0.hour,
				minute = dt0.minute,
				second = dt0.second,
				microsecond = dt0.microsecond,
			)
		elif s.__class__.__name__ == 'datetime':
			dt = copy.copy(s)
		elif s == "now":
			dt = datetime.datetime.now()
		elif s == "today":
			dt = datetime.datetime.today()
			dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
		elif s == "yesterday" or s == "yest":
			dt = datetime.datetime.today()
			dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
			dt -= datetime.timedelta(days=1)
		elif s == "inf" or s == "infinity":
			dt = dateutil.parser.parse("9999-12-31 23:59")
		elif s == "":
			raise Exception("an empty string given as the Date initializer")
		else:
			dt = dateutil.parser.parse(s)

		self.datetime = dt


	def getDatetime(self):
		return self.datetime


	def toText(self):
		t = self.getDatetime().strftime("%Y%m%d%H%M%S")
		return t

	def toNiceText(self):
		t = self.getDatetime().strftime("%Y-%m-%d %H:%M:%S")
		return t

	def toRusTxt(self):
		t = self.getDatetime().strftime("%d.%m.%Y")
		return t


	def same(self, other):
		if self.toText() == other.toText():
			return True
		else:
			return False


	def nextDay(self):
		date = Date(self.toText())
		date.datetime += datetime.timedelta(days=1)
		return date

	def previousWeek(self):
		txt = self.toText()
		date = Date(txt)

		date.datetime -= datetime.timedelta(days=7)

		return date


	def __gt__(self, other):
		return self.toText() > other.toText()

	def __lt__(self, other):
		return self.toText() < other.toText()


	def daysEarlier(self, other):
		# return the number of days since self until other

		td = other.getDatetime() - self.getDatetime()

		nd = td.days + td.seconds/(60.*60.*24.)

		return nd


	def hoursEarlier(self, other):
		# return the number of hours since self until other

		td = other.getDatetime() - self.getDatetime()

		nd = td.days*24. + td.seconds/(60.*60.)

		return nd


	def minutesEarlier(self, other):
		# return the number of minutes since self until other

		td = other.getDatetime() - self.getDatetime()

		nd = td.days*24.*60. + td.seconds/(60.)

		return nd


	def plusHours(self, n):
		"""Return a date that is n hours later than self
		"""

		d = Date(self.toText())
		d.datetime += datetime.timedelta(hours=n)

		return d


	def plusDays(self, n):
		"""Return a date that is n days later than self
		"""

		d = Date(self.toText())
		d.datetime += datetime.timedelta(days=n)

		return d


	def toNiceTextDateOnly(self):
		t = self.getDatetime().strftime("%Y-%m-%d")
		return t

	def toNiceTextTimeOnly(self):
		t = self.getDatetime().strftime("%H:%M")
		return t


	def midnight(self):
		d = Date(self)
		d.datetime += datetime.timedelta(
			days = 0,
			hours = - self.datetime.hour,
			minutes = - self.datetime.minute,
			seconds = - self.datetime.second,
			microseconds = - self.datetime.microsecond,
		)

		return d


	def __str__(self):
		return self.toNiceText()


	def nextDayMidnight(self):
		date = Date(self)
		date.datetime += datetime.timedelta(
			days = 1,
			hours = - self.datetime.hour,
			minutes = - self.datetime.minute,
			seconds = - self.datetime.second,
			microseconds = - self.datetime.microsecond,
		)

		return date


	def __lt__(self, other):
		x = self.datetime
		y = other.datetime

		xs = (x.year, x.month, x.day,
			x.hour, x.minute, x.second, x.microsecond)
		ys = (y.year, y.month, y.day,
			y.hour, y.minute, y.second, y.microsecond)

		for i in range(0, 7):
			a = xs[i]
			b = ys[i]

			if a < b: return True
			elif a > b: return False

		return False


	def __gt__(self, other):
		return other < self


	def __ge__(self, other):
		return not(self < other)

	def __le__(self, other):
		return not(self > other)
