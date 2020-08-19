from Currency import CurrencyPair

class Bid:
	def __init__(self,
		sb,
		ide = 0,
		curPair = None,
		amount1 = 0,
		amount2 = 0,
		place = 0,
		wm_tid = "",
		marketState = None,
		row = None,
	):
		if row:
			ide = row['id']

			c1 = sb.getCurrencyBy(row['currency1'])
			c2 = sb.getCurrencyBy(row['currency2'])
			curPair = CurrencyPair(sb, c1, c2)

			amount1 = row['amount1']
			amount2 = row['amount2']
			place = row['place']
			wm_tid = row['wm_tid']

			if not marketState:
				marketState = sb.getMarketStateBy(
					row['marketstate'])

		self.specBot = sb
		self.ide = ide
		self.curPair = curPair
		self.amount1 = amount1
		self.amount2 = amount2
		self.place = place
		self.wm_tid = wm_tid
		self.marketState = marketState


	def save(self, nocommit = False):
		sb = self.specBot

		c1 = self.curPair[0]
		c2 = self.curPair[1]

		if self.ide:
			# update existing
			sb.execute("""
				UPDATE bids SET
					currency1 = ?, currency2 = ?,
					amount1 = ?, amount2 = ?,
					place = ?, wm_tid = ?,
					marketState = ?

				WHERE id = ?
			""", [
					c1.ide, c2.ide,
					self.amount1, self.amount2,
					self.place, self.wm_tid,
					self.marketState.ide,
					self.ide
			])
		else:
			# create new
			sb.execute("""
				INSERT INTO bids (
					currency1, currency2,
					amount1, amount2,
					place, wm_tid,
					marketState
				) VALUES (
					?, ?, ?, ?, ?, ?, ?
				)
			""", [
					c1.ide, c2.ide,
					self.amount1, self.amount2,
					self.place, self.wm_tid,
					self.marketState.ide,
			], nocommit = nocommit)

			self.ide = self.specBot.lastrowid


	def __str__(self):
		s = """
ide = {ide},
curPair = {cp},
amount1 = {a1:.2f},
amount2 = {a2:.2f},
place = {p},
wm_tid = {wm_tid},
marketState = {msid},
"""[1:-1].format(
			ide = self.ide,
			cp = str(self.curPair) if self.curPair else '?',
			a1 = self.amount1,
			a2 = self.amount2,
			p = self.place,
			wm_tid = self.wm_tid,
			msid = self.marketState.ide if self.marketState else 0,
		)

		return s
