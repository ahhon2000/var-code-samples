from flask import render_template, g, request
import flask_sijax
import re
import flask

from Date import Date
from VolumeTable import VolumeTable
from errorReporters import updateMsg, updateMsgWarning, updateMsgError
import Config

_supportedExchangeNames = ['BitMEX']


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


def _getSortedSyms(vt, pars):
	syms = sorted(vt.volumes.keys())

	sortCol = pars['tableSortColumn']
	assert isinstance(sortCol, list)
	assert len(sortCol) == 2

	rowNumbers = list(range(len(syms)))  # the list of syms indices

	col = sortCol[0]
	direction = sortCol[1]
	if direction == 0: return syms

	if col == 1:
		# sort by symbol
		rowNumbers.sort(reverse = True if direction == 1 else False)
	else: raise Exception("wrong column number")

	sortedSyms = list(syms[i] for i in rowNumbers)

	return sortedSyms


def _updateVTable(rsp, pars):
	tg = g.tgui
	pars = dict(pars)
	pars['onlyTBody'] = bool(pars['onlyTBody'])
	onlyTBody = pars['onlyTBody']

	errorMessages = []

	supportedExs = list(
		ex for ex in tg.exchanges if ex.name in _supportedExchangeNames
	)
	if not supportedExs: raise Exception("no supported exchanges")

	# define column widths
	insColWidth = 16  # percent
	volWidth = round((100 - insColWidth) / len(supportedExs))
	colWidths = [insColWidth] + [volWidth for ex in supportedExs]
	if sum(colWidths) != 100: errorMessages += ["column widths do not add up to 100%"]

	vt = VolumeTable(supportedExs)
	errorMessages += vt.errorMessages

	# Prepare the table body

	if not vt.volumes.keys(): errorMessages += ["no symbols in the volume table"]

	sortedSyms = _getSortedSyms(vt, pars)

	cnt_b = ""
	now = Date("now")
	for sym in sortedSyms:
		vs = vt.volumes[sym]
		tos = vt.turnovers[sym]
		upds = vt.updateDates[sym]
		cnt_b += """
<tr>
	<td>
		<div class="row">
			<div class="col-sm-3">
				&nbsp;
			</div>
			<div class="col-sm-9 text-left">
				{sym}
			</div>
		</div>
	</td>
""".format(
	sym = sym,
)

		for i in range(len(vs)):
			v = vs[i]
			to = tos[i]
			upd = upds[i]
			ex = vt.exchanges[i]
			cw = colWidths[i+1]
			vtxt = "n/a"
			totxt = "n/a"
			utxt = ""
			if not(v is None)  and  upd.minutesEarlier(now) < 60:
				vtxt = "{v:,}".format(v=round(v))
				utxt = ex.getVolumeUnit(sym)

			if not(to is None)  and  upd.minutesEarlier(now) < 60:
				totxt = "Turnover: {to:,}".format(to=round(to))
				totxt += " " + ex.getTurnoverUnit(sym)

			if upd:
				updMin = upd.minutesEarlier(now)
				if updMin > 2 * Config.VOLUME24H_UPDATE_PERIOD:
					errorMessages += ["Last volume data update for {exn} {sym} was {updMin} minutes ago".format(
						updMin=round(updMin),
						sym=sym,
						exn=ex.name,
					)]

			cnt_b += """
	<td class="text-center small" width="{cw}%">
		<div class="col-sm-12 text-right">
			<div class="row">
				<div class="col-sm-9 text-right">
					<span title="{totxt}">{vtxt}</span>
				</div>
				<div class="col-sm-3 text-left">
					<small>{utxt}</small>
				</div>
			</div>
		</div>
	</td>
""".format(
	vtxt = vtxt,
	cw = round(cw),
	utxt = utxt,
	totxt = totxt,
)

		cnt_b += """
</tr>
"""

	# Prepare the table header

	ths_ex = "" # column headers for exchanges (to be inserted into cnt_h)
	for i in range(len(supportedExs)):
		ex = supportedExs[i]
		ths_ex += """
	<th class="vol_table_header align-middle text-center" width="{cw}%">
		{exn}
	</th>
""".format(
	exn = ex.name,
	cw = round(colWidths[i+1]),
)

	sortIcon1 = _getSortIcon(pars['tableSortColumn'], 1)

	cnt_h = """
<tr>
	<th class="vol_table_header align-middle text-center" width="{cw}%">
		Symbol {sortIcon1}
	</th>
	{ths_ex}
</tr>

"""[1:-1].format(
	sortIcon1 = sortIcon1,
	ths_ex = ths_ex,
	cw = round(colWidths[0]),
)

	if not errorMessages:
		updateMsg(rsp, "&nbsp;", idBase="volume_table")
	else:
		ms = list(map(flask.escape, errorMessages))
		m = "\n<br>\n".join(ms)
		updateMsgWarning(rsp, m, idBase="volume_table")

	if not onlyTBody:
		rsp.html("#volume_table_header", cnt_h)
	rsp.html("#volume_table_body", cnt_b)

def updateVTable(rsp, pars):
	try:
		_updateVTable(rsp, pars)
	except Exception as e:
		m = """
Couldn't update the table: {e}
"""[1:-1].format(e=str(e))

		m = flask.escape(m)
		updateMsgError(rsp, m, idBase="volume_table")


def render(tg):
	g.tgui = tg

	if g.sijax.is_sijax_request:
		g.sijax.register_callback('updateVTable', updateVTable)
		return ""

	cnt = render_template('volume.html')

	return {'content': cnt, 'pageTitle': 'Volume (24 Hours)'}
