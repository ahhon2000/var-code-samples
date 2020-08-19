from flask import render_template, g, request
import flask_sijax
import re
import flask
import traceback

from LiquidityTable import LiquidityTable
from liquidityGraphs import updateLGraph
from errorReporters import updateMsg, updateMsgWarning, updateMsgError
import Config


def _getSortedRowNumbers(instruments, lt, pars):
	sortCol = pars['tableSortColumn']
	assert isinstance(sortCol, list)
	assert len(sortCol) == 2

	lst = list(range(len(instruments)))  # the list to return

	col = sortCol[0]
	direction = sortCol[1]
	if direction == 0: return lst

	if col == 1:
		# sort by instrument
		key = None
		if pars['liquidityFor'] not in ['all', 'futures']:
			key = lambda x: instruments[x].name
		elif pars['liquidityFor'] in ['all', 'futures']:
			sign = -1 if direction == 1 else 1
			key = lambda x: (
				instruments[x].getCoin(),
				sign * {
					"w": 1, "b": 2, "q": 3, "": 4,
				}[instruments[x].getShortAlias()]
			)
		else: raise Exception('invalid liquiditFor')

		lst.sort(key = key, reverse = True if direction == 1 else False)
	elif col == 2:
		# sort by current bid
		lst.sort(key = lambda x:
			lt.liquidities[instruments[x].name].bid,
			reverse = True if direction == 1 else False
		)
	elif col == 3:
		# sort by current ask
		lst.sort(key = lambda x:
			lt.liquidities[instruments[x].name].ask,
			reverse = True if direction == 1 else False
		)
	elif col == 4:
		# sort by avg1 bid
		lst.sort(key = lambda x:
			lt.avgLiquidities[instruments[x].name][0].bid,
			reverse = True if direction == 1 else False
		)
	elif col == 5:
		# sort by avg1 ask
		lst.sort(key = lambda x:
			lt.avgLiquidities[instruments[x].name][0].ask,
			reverse = True if direction == 1 else False
		)
	elif col == 6:
		# sort by avg2 bid
		lst.sort(key = lambda x:
			lt.avgLiquidities[instruments[x].name][1].bid,
			reverse = True if direction == 1 else False
		)
	elif col == 7:
		# sort by avg2 ask
		lst.sort(key = lambda x:
			lt.avgLiquidities[instruments[x].name][1].ask,
			reverse = True if direction == 1 else False
		)
	else: raise Exception("wrong column number")

	return lst


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


def _genTableRow(instruments,
	lt, rowNumber, trClsState
):

	ins = instruments[rowNumber]
	cnt_r = ""

	n = ins.name
	if n not in lt.liquidities.keys(): return (cnt_r, trClsState)

	l = lt.liquidities[n]
	bid = l.bid
	ask = l.ask

	al1 = lt.avgLiquidities[n][0]
	al2 = lt.avgLiquidities[n][1]
	avg_bid1 = al1.bid
	avg_ask1 = al1.ask
	avg_bid2 = al2.bid
	avg_ask2 = al2.ask

	actualDepth_fmt = """
 <small class="{textClass}">({ad:.2f}%)</small>
"""[1:-1]

	customDepth = lt.customDepthLst[0]

	textClass = ""
	if l.actualDepthBid <= customDepth - 0.005:
		textClass = "text-danger"
	actualDepthBidNfo = actualDepth_fmt.format(
		ad = l.actualDepthBid,
		textClass = textClass,
	)

	textClass = ""
	if l.actualDepthAsk <= customDepth - 0.005:
		textClass = "text-danger"
	actualDepthAskNfo = actualDepth_fmt.format(
		ad = l.actualDepthAsk,
		textClass = textClass,
	)

	td_bid = """
{bid:,}{actualDepthBidNfo}
""".format(
bid = bid,
actualDepthBidNfo = actualDepthBidNfo,
)

	td_ask = """
{ask:,}{actualDepthAskNfo}
""".format(
ask = ask,
actualDepthAskNfo = actualDepthAskNfo,
)

	td_avg_bid1 = """
{avg_bid1:,}
""".format(
avg_bid1 = avg_bid1,
)

	td_avg_ask1 = """
{avg_ask1:,}
""".format(
avg_ask1 = avg_ask1,
)

	td_avg_bid2 = """
{avg_bid2:,}
""".format(
avg_bid2 = avg_bid2,
)

	td_avg_ask2 = """
{avg_ask2:,}
""".format(
avg_ask2 = avg_ask2,
)

	naSpan = '<span class="text text-danger">n&#47;a</span>'
	if l.errorMessage:
		if not bid: td_bid = naSpan
		if not ask: td_ask = naSpan

	if al1.errorMessage:
		if avg_bid1 < 1e-10: td_avg_bid1 = naSpan
		if avg_ask1 < 1e-10: td_avg_ask1 = naSpan
	if al2.errorMessage:
		if avg_bid2 < 1e-10: td_avg_bid2 = naSpan
		if avg_ask2 < 1e-10: td_avg_ask2 = naSpan

	tr_class = ""
	if lt.liquidityFor in ['all', 'futures']:
		if rowNumber > 0 and ins.getCoin() != instruments[rowNumber-1].getCoin():
			trClsState = not trClsState

		if trClsState: tr_class = "liq_table_row_odd"
		else: tr_class = "liq_table_row_even"
	else:
		if rowNumber % 2: tr_class = "liq_table_row_odd"
		else: tr_class = "liq_table_row_even"

	cnt_r += """

<tr class="{tr_class}">
<td class="text-center small" width="16%">
<div class="row">
	<div class="col-sm-3" title="Open chart">
		<a href="#" onclick="selectView('graph', '{instrument_id}')">
			<span class="glyphicon glyphicon-stats"></span>
		</a>
	</div>
	<div class="col-sm-9 text-left">
		{n} <small>{alias}</small>
	</div>
</div>
</td>
<td class="text-right small" width="14%">{td_bid}</td>
<td class="text-right small" width="14%">{td_ask}</td>

<td class="text-right small" width="14%">{td_avg_bid1}</td>
<td class="text-right small" width="14%">{td_avg_ask1}</td>
<td class="text-right small" width="14%">{td_avg_bid2}</td>
<td class="text-right small" width="14%">{td_avg_ask2}</td>
</tr>

"""[1:-1].format(
tr_class = tr_class,
n = n,
alias = ins.getShortAlias(),
instrument_id = ins.instrument_id,
td_bid = td_bid,
td_ask = td_ask,
td_avg_bid1 = td_avg_bid1,
td_avg_ask1 = td_avg_ask1,
td_avg_bid2 = td_avg_bid2,
td_avg_ask2 = td_avg_ask2,
)

	return (cnt_r, trClsState)


def _updateLTable(rsp, pars):
	tg = g.tgui
	errorMessages = []

	customDepth = pars['depth']
	customDepth1 = pars['depth1']
	customDepth2 = pars['depth2']
	liquidityFor = pars['liquidityFor']
	onlyTBody = pars['onlyTBody']

	for depth_n in ["depth", "depth1", "depth2"]:
		if not isinstance(pars[depth_n], float):
			raise Exception("customDepth must be of type `float'")

		if pars[depth_n] < -1e-10  or  pars[depth_n] > 100 + 1e-10:
			raise Exception("invalid value of customDepth")

	avgInterval1 = 0
	avgInterval2 = 0
	try:
		avgInterval1 = int(pars['avgInterval1'])
	except Exception as e:
		errorMessages += ["avgInterval1 must be an integer"]
	try:
		avgInterval2 = int(pars['avgInterval2'])
	except Exception as e:
		errorMessages += ["avgInterval2 must be an integer"]

	exn = pars.get('exchange')
	if not exn: raise Exception("an exchange name must be given")
	ex = tg.getExchangeByName(exn)
	if not ex: raise Exception("unsupported exchange: `{exn}'".format(exn=exn))

	lt = LiquidityTable(ex,
		customDepthLst = [customDepth, customDepth1, customDepth2],
		liquidityFor=liquidityFor,
		avgInterval1=avgInterval1,
		avgInterval2=avgInterval2,
	)
	lt.load()

	dropdownAvgInterval = """
<span class="dropdown">
	<a href="#" data-toggle="dropdown" class="no_underline" onclick="setAvgIntervalFocus({avgIntCol}); return false;" title="Set Interval">
	<span class="glyphicon glyphicon-time"></span>
	</a>
	&nbsp;
	<ul class="dropdown-menu dropdown-menu-left dropdown_avg_int_ul">
		<li><a href="#" onclick="setAvgInterval{avgIntCol}(1); return false">1 min</a></li>
		<li><a href="#" onclick="setAvgInterval{avgIntCol}(5); return false">5 min</a></li>
		<li><a href="#" onclick="setAvgInterval{avgIntCol}(60); return false">60 min</a></li>
		<li><a href="#" onclick="setAvgInterval{avgIntCol}(240); return false">240 min</a></li>
		<li>
			<form onsubmit="setAvgInterval{avgIntCol}(); return false">
				<input id="set_avg_interval_input{avgIntCol}" type="text" placeholder="Custom..." class="text-right"/>
			</form>
		</li>
	</ul>
</span>
"""[1:-1]

	dropdownDepth = """
<span class="dropdown">
	<a href="#" data-toggle="dropdown" class="no_underline" onclick="setCustomDepthFocus({avgIntCol}); return false;" title="Set Depth">
	%
	</a>
	&nbsp;
	<ul class="dropdown-menu dropdown-menu-left dropdown_avg_int_ul">
		<li><a href="#" onclick="setCustomDepth{avgIntCol}(0.1); return false">0.1%</a></li>
		<li><a href="#" onclick="setCustomDepth{avgIntCol}(0.2); return false">0.2%</a></li>
		<li><a href="#" onclick="setCustomDepth{avgIntCol}(0.5); return false">0.5%</a></li>
		<li>
			<form onsubmit="setCustomDepth{avgIntCol}(); return false">
				<input id="set_custom_depth_input{avgIntCol}" type="text" placeholder="Custom..." class="text-right"/>
			</form>
		</li>
	</ul>
</span>
"""[1:-1]

	dropdownAvgInterval1 = dropdownAvgInterval.format(avgIntCol=1)
	dropdownAvgInterval2 = dropdownAvgInterval.format(avgIntCol=2)
	dropdownDepth0 = dropdownDepth.format(avgIntCol=0)
	dropdownDepth1 = dropdownDepth.format(avgIntCol=1)
	dropdownDepth2 = dropdownDepth.format(avgIntCol=2)

	sortIcon1 = _getSortIcon(pars['tableSortColumn'], 1)
	sortIcon2 = _getSortIcon(pars['tableSortColumn'], 2)
	sortIcon3 = _getSortIcon(pars['tableSortColumn'], 3)
	sortIcon4 = _getSortIcon(pars['tableSortColumn'], 4)
	sortIcon5 = _getSortIcon(pars['tableSortColumn'], 5)
	sortIcon6 = _getSortIcon(pars['tableSortColumn'], 6)
	sortIcon7 = _getSortIcon(pars['tableSortColumn'], 7)

	cnt_h = """
<tr>
	<th rowspan="2" class="liq_table_header align-middle text-center" width="16%">Instrument {sortIcon1}</th>
	<th colspan="2" class="liq_table_header align-middle text-center" width="28%">
	{dropdownDepth0}
	&nbsp;&nbsp;
	Current <small>({customDepth:.2f}%)</small></th>
	<th colspan="2" class="liq_table_header align-middle text-center" width="28%">
	{dropdownDepth1} {dropdownAvgInterval1}
	&nbsp;&nbsp;
	Average #1 <small>({customDepth1:.2f}%)</small>
</th>
	<th colspan="2" class="liq_table_header align-middle text-center" width="28%">
	{dropdownDepth2} {dropdownAvgInterval2}
	&nbsp;&nbsp;
	Average #2 <small>({customDepth2:.2f}%)</small>
</th>
</tr><tr>
	<th class="liq_table_header align-middle text-center">Bid {sortIcon2}</th>
	<th class="liq_table_header align-middle text-center">Ask {sortIcon3}</th>
	<th class="liq_table_header align-middle text-center">
		Bid {avgInterval1}m {sortIcon4}
	</th>
	<th class="liq_table_header align-middle text-center">
		Ask {avgInterval1}m {sortIcon5}
	</th>
	<th class="liq_table_header align-middle text-center">
		Bid {avgInterval2}m {sortIcon6}
	</th>
	<th class="liq_table_header align-middle text-center">
		Ask {avgInterval2}m {sortIcon7}
	</th>
</tr>

"""[1:-1].format(
	customDepth = customDepth,
	customDepth1 = customDepth1,
	customDepth2 = customDepth2,
	dropdownAvgInterval1 = dropdownAvgInterval1,
	dropdownAvgInterval2 = dropdownAvgInterval2,
	avgInterval1 = avgInterval1,
	avgInterval2 = avgInterval2,
	dropdownDepth0 = dropdownDepth0,
	dropdownDepth1 = dropdownDepth1,
	dropdownDepth2 = dropdownDepth2,
	sortIcon1 = sortIcon1,
	sortIcon2 = sortIcon2,
	sortIcon3 = sortIcon3,
	sortIcon4 = sortIcon4,
	sortIcon5 = sortIcon5,
	sortIcon6 = sortIcon6,
	sortIcon7 = sortIcon7,
)

	instruments = None
	if liquidityFor == "all":
		instruments = ex.allInstrumentsSorted()
	elif liquidityFor == "futures": instruments = ex.instrumentsFutures
	elif liquidityFor == "swaps": instruments = ex.instrumentsSwaps
	else: assert 0

	trClsState = False
	cnt_b = ""
	sortedRowNumbers = _getSortedRowNumbers(instruments, lt, pars)
	sortedInstruments = list(instruments[i] for i in sortedRowNumbers)

	for rowNumber in range(len(sortedInstruments)):
		(cnt_r, trClsState) = _genTableRow(
			sortedInstruments,
			lt,
			rowNumber,
			trClsState,
		)
		cnt_b += cnt_r

	m = "\n".join(errorMessages + lt.errorMessage.split("\n"))
	if not m:
		m = "&nbsp;"
		updateMsg(rsp, m, idBase="liquidity_table")
	else:
		m = flask.escape(m)
		m = "\n<br>\n".join(m.split('\n'))
		updateMsgWarning(rsp, m, idBase="liquidity_table")

	if not onlyTBody:
		rsp.html('#liquidity_table_header', cnt_h)
	rsp.html('#liquidity_table_body', cnt_b)


def updateLTable(rsp, pars):
	tg = g.tgui
	pars = dict(pars)

	try:
		pars['onlyTBody'] = int(pars['onlyTBody'])
		DEFAULT_PRICE_DEPTH = tg.getSessionPar('DEFAULT_PRICE_DEPTH')

		exn = pars.get('exchange')
		tg.loadInstrumentsForExchange(exn)

		for depth_n in ["depth", "depth1", "depth2"]:
			if isinstance(pars[depth_n], str) and re.search(r'^[\s]*$', pars[depth_n]):
				pars[depth_n] = DEFAULT_PRICE_DEPTH
			pars[depth_n] = float(pars[depth_n])

			if pars['liquidityFor'] not in ["all", "futures", "swaps"]: raise Exception("invalid liquidityFor")

		try:
			_updateLTable(rsp, pars)
		except Exception as e:
			raise Exception("_updateLTable() failed: {e}".format(
				e = str(e),
			))
	except Exception as e:
		tb = traceback.format_exc()
		m = """
Couldn't update the table: {e}
{tb}
"""[1:-1].format(e=str(e), tb=tb)

		m = flask.escape(m)
		m = "\n<br>\n".join(m.split("\n"))
		updateMsgError(rsp, m, idBase='liquidity_table')


def render(tg):
	g.tgui = tg
	g.default_price_depth = tg.getSessionPar('DEFAULT_PRICE_DEPTH')
	g.default_avg_interval1 = Config.DEFAULT_AVG_INTERVAL1
	g.default_avg_interval2 = Config.DEFAULT_AVG_INTERVAL2
	g.default_graph_time_range = Config.DEFAULT_GRAPH_TIME_RANGE
	g.default_exchange = Config.DEFAULT_EXCHANGE

	if g.sijax.is_sijax_request:
		g.sijax.register_callback('updateLTable', updateLTable)
		g.sijax.register_callback('updateLGraph', updateLGraph)
		return ""

	cnt = render_template('orderbook_liquidity.html')

	return {'content': cnt, 'pageTitle': 'Orderbook Liquidity'}
