from flask import render_template, g, request
import flask_sijax
import re
import flask

from FundingTable import FundingTable
from Date import Date
from errorReporters import updateMsg, updateMsgWarning, updateMsgError
import Config

_supportedExchangeNames = ['BitMEX', 'OKEx']


def _timeToFunding(m):
	"""Return time to funding as a string

	m is the number of minutes (float) to funding
	"""

	n = None
	u = None
	if abs(m) < 1:
		(n, u) = (m * 60, "sec")
	elif abs(m) < 60:
		(n, u) = (m, "min")
	else:
		(n, u) = (m / 60, "h")

	ntxt = str(round(n))
	if u in ("min", "h"):
		if abs(n) < 3: ntxt = "{n:.1f}".format(n=n)

	s = "in {ntxt} {u}".format(ntxt=ntxt, u=u)

	return s


def _getSortedKeys(ft, pars):
	keys = sorted(ft.fvalues.keys(), key=lambda k: (k[0], k[1]))

	sortCol = pars['tableSortColumn']
	assert isinstance(sortCol, list)
	assert len(sortCol) == 2

	rowNumbers = list(range(len(keys)))  # the list of keys indices

	col = sortCol[0]
	direction = sortCol[1]
	if direction == 0: return keys

	if col == 1:
		# sort by symbol
		def sortKeyF(n):
			nonlocal keys, direction
			if direction == 1:
				k1 = keys[n][1]
				if keys[n][1] == 'Current': k1 = 1
				elif keys[n][1] == 'Predicted': k1 = 0
				return (keys[n][0], k1)
			
			return (keys[n][0], keys[n][1])
			
		rowNumbers.sort(key = sortKeyF,
			reverse = True if direction == 1 else False)
	elif col == 2:
		# sort by type
		rowNumbers.sort(key = lambda n: (keys[n][1], keys[n][0]),
			reverse = True if direction == 1 else False)
	else: raise Exception("wrong column number for sorting")

	sortedKeys = list(keys[i] for i in rowNumbers)

	return sortedKeys


def _getSortIcon(sortCol, col):
	"""sortCol format: [COLUMN_NUMBER, DIRECTION]
		DIRECTION: 0 - undefined, 1 - desc, 2 - asc
	"""

	if not isinstance(sortCol, list): raise Exception("the first argument must be a list")
	if not isinstance(col, int): raise Exception("the second argument must be an integer")

	direction = 0  # undefined
	if sortCol[0] == col:
		direction = sortCol[1]

	newDirection = 1 if direction in [0, 2] else 2

	sortTxt = "⇅"
	if direction == 1:
		sortTxt = "⇈"
	elif direction == 2:
		sortTxt = "⇊"

	s = """
&nbsp;<a href="#" class="no_underline" onclick="sortTable({col}, {newDirection}); return false">{sortTxt}</a>
""".format(
	newDirection=newDirection,
	col=col,
	sortTxt=sortTxt,
)

	return s


def _updateFTable(rsp, pars):
	tg = g.tgui
	pars = dict(pars)
	pars['onlyTBody'] = bool(pars['onlyTBody'])
	onlyTBody = pars['onlyTBody']

	errorMessages = []

	supportedExs = []
	for exn in _supportedExchangeNames:
		for ex in tg.exchanges:
			if ex.name == exn:
				supportedExs += [ex]
				break
	if not supportedExs: raise Exception("no supported exchanges")

	# define column widths
	coinColWidth = 10  # percent
	typeColWidth = 10  # percent
	funWidth = round((100 - coinColWidth-typeColWidth) / len(supportedExs))
	colWidths = [coinColWidth, typeColWidth] + [funWidth for ex in supportedExs]
	if sum(colWidths) != 100: errorMessages += ["column widths do not add up to 100% ({scw}%)".format(scw=sum(colWidths))]

	ft = FundingTable(supportedExs)
	errorMessages += ft.errorMessages

	# Prepare the table body

	if not ft.fvalues.keys(): errorMessages += ["no rows in the Funding table"]

	sortedKeys = _getSortedKeys(ft, pars)

	cnt_b = ""
	now = Date("now")
	for k in sortedKeys:
		fs = ft.fvalues[k]
		upds = ft.updateDates[k]
		fundingTimes = ft.fundingTimes[k]
		typ = {"Current": "Current", "Predicted": "Predicted"}[k[1]]
		cnt_b += """
<tr>
	<td width="{cw0}%">{sym}</td>
	<td width="{cw1}%">{type}</td>
""".format(
	cw0 = colWidths[0],
	cw1 = colWidths[1],
	sym = k[0],
	type = typ,
)

		for i in range(len(fs)):
			f = fs[i]
			upd = upds[i]
			fundingTime = Date(fundingTimes[i]) if fundingTimes[i] else None
			ex = ft.exchanges[i]
			cw = colWidths[i+2]
			ftxt = "n/a"
			mtf = None  # minutes to funding
			if not(f is None)  and  upd  and  upd.minutesEarlier(now) < 60:  # TODO tune the minutes
				if f > 0: funValCls = "fun_value_positive"
				else: funValCls = "fun_value_negative"

				ftxt = """
<span class="{funValCls}">{f:.4f}%</span>
"""[1:-1].format(
	f = f*100,
	funValCls = funValCls,
)

			if fundingTime: mtf = now.minutesEarlier(fundingTime)

			if upd:
				updMin = upd.minutesEarlier(now)
				if updMin > 2 * Config.FUNDING_UPDATE_PERIOD:
					errorMessages += ["Last funding data update for {exn} {sym} was {updMin} minutes ago".format(
						updMin=round(updMin),
						sym=k[0],
						exn=ex.name,
					)]

			ttf = "&nbsp;" if mtf is None else _timeToFunding(mtf)

			cnt_b += """
	<td class="text-center" width="{cw}%">
		<div class="col-sm-12 text-right">
			<div class="row">
				<div class="col-sm-9 text-right">
					{ftxt}
				</div>
				<div class="col-sm-3 text-right">
					{ttf}
				</div>
			</div>
		</div>
	</td>
""".format(
	cw = round(cw),
	ftxt = ftxt,
	ttf = ttf,
)

		cnt_b += """
</tr>
"""

	# Prepare the table header

	ths_ex = "" # column headers for exchanges (to be inserted into cnt_h)
	for i in range(len(supportedExs)):
		ex = supportedExs[i]
		ths_ex += """
	<th class="fun_table_header align-middle text-center" width="{cw}%">
		{exn}
	</th>
""".format(
	exn = ex.name,
	cw = round(colWidths[i+2]),
)

	sortIcon1 = _getSortIcon(pars['tableSortColumn'], 1)
	sortIcon2 = _getSortIcon(pars['tableSortColumn'], 2)

	cnt_h = """
<tr>
	<th class="fun_table_header align-middle text-center" width="{cw0}%">
		Symbol {sortIcon1}
	</th>
	<th class="fun_table_header align-middle text-center" width="{cw1}%">
		Type {sortIcon2}
	</th>
	{ths_ex}
</tr>

"""[1:-1].format(
	sortIcon1 = sortIcon1,
	sortIcon2 = sortIcon2,
	ths_ex = ths_ex,
	cw0 = round(colWidths[0]),
	cw1 = round(colWidths[1]),
)

	if not errorMessages:
		updateMsg(rsp, "&nbsp;", idBase="funding_table")
	else:
		ms = list(map(flask.escape, errorMessages))
		m = "\n<br>\n".join(ms)
		updateMsgWarning(rsp, m, idBase="funding_table")

	if not onlyTBody:
		rsp.html("#funding_table_header", cnt_h)
	rsp.html("#funding_table_body", cnt_b)


def updateFTable(rsp, pars):
	try:
		_updateFTable(rsp, pars)
	except Exception as e:
		m = """
Couldn't update the table: {e}
"""[1:-1].format(e=str(e))

		m = flask.escape(m)
		updateMsgError(rsp, m, idBase="funding_table")


def render(tg):
	g.tgui = tg

	if g.sijax.is_sijax_request:
		g.sijax.register_callback('updateFTable', updateFTable)
		return ""

	cnt = render_template('funding.html')

	return {'content': cnt, 'pageTitle': 'Funding Rates'}
