import flask
from flask import render_template, g, request
import re
import pickle
import traceback

import Config
from Date import Date
from Liquidity import Liquidity
from errorReporters import updateMsg, updateMsgWarning, updateMsgError


def _genXYPoints(ex, direction, ins, depth, tRange):
	tg = g.tgui

	if not ins: return ""

	if not isinstance(tRange, (int, float)): raise Exception('tRange must be a number')

	if tRange <= 0: raise Exception("tRange cannot be negative")

	ctype = ins.getContractType()

	now = Date("now")
	d1 = now.plusHours(-tRange/60.)

	# load uniform averages

	utbl = ex.uorderbookTblByContracts(ctype)
	rs = tg.execute("""
SELECT * FROM {utbl}
WHERE instrument_id = %s  and  `date` >= %s  and  `date` <= %s
ORDER BY `date`
""".format(utbl=utbl), [
	ins.instrument_id, d1.toText(), now.toText()
])

	xys = []
	for r in rs:
		d = Date(r['date'])

		u = None
		try:
			u = pickle.loads(r['pickle'])
		except Exception as e:
			pass

		if u is None: continue

		x = -d.minutesEarlier(now)
		y = u.valueByDepth(direction, depth)

		xys += [(x, y)]

	# add the latest point

	rs = tg.execute("""
SELECT * FROM {tbl}
WHERE instrument_id = %s
ORDER BY `date` DESC
LIMIT 1
""".format(tbl=ex.orderbookTblByContracts(ctype)), [ins.instrument_id])

	for r in rs:
		d = Date(r['date'])
		l = None
		try:
			l = Liquidity(ins, pickle.loads(r['pickle']), customDepth=depth)
		except Exception as e:
			pass
		if not l: continue

		y = l.bid if direction == 'bids' else l.ask
		x = -d.minutesEarlier(now)
		xys += [(x, y)]

		break

	# generate the x/y pairs

	pts = ""
	for (x, y) in xys:
		if y is None: y = 0
		x = "{x:.1f}".format(x=x)
		y = round(y)
		pts += """
{{x:{x},y:{y}}},
""".format(x=x, y=y)

	return pts

def _updateLGraph(rsp, pars):
	tg = g.tgui

	exn = pars.get('exchange')
	if not exn: raise Exception("an exchange name must be given")
	ex = tg.getExchangeByName(exn)
	if not ex: raise Exception("unsupported exchange: `{exn}'".format(exn=exn))

	liquidityFor = pars['liquidityFor']
	instruments = None
	gik = ""  # graph instrument key
	if liquidityFor == 'all':
		instruments = ex.allInstrumentsSorted()
		gik = "graphInstrumentAll"
	elif liquidityFor == 'futures':
		instruments = ex.instrumentsFutures
		gik = "graphInstrumentFutures"
	elif liquidityFor == 'swaps':
		instruments = ex.instrumentsSwaps
		gik = "graphInstrumentSwaps"
	else: assert 0
	
	graphIns = None
	if pars[gik]:
		iid = pars[gik]
		for ins in instruments:
			if iid == ins.instrument_id:
				graphIns = ins
				break
	elif instruments:
		graphIns = instruments[0]

	insCnt = "" if instruments else "<small><i>No instruments</i></small>"
	for i in range(len(instruments)):
		ins = instruments[i]
		btnCls = "btn btn-link btn-md"
		if graphIns and ins.sameAs(graphIns):
			btnCls = "btn btn-info btn-md"

		if liquidityFor != 'swaps' and i > 0  and  \
			instruments[i-1].getCoin() != ins.getCoin() \
			and (i < 2 or instruments[i-1].getCoin() == instruments[i-2].getCoin()):

			insCnt += """
<br>
"""

		insCnt += """
<div>
	<button type="button" id="graph_ins_btn_{iid}" class="{btnCls}" onclick="setGraphIns('{iid}', this);">
		{n} {a}
	</button>
</div>
""".format(
	n = ins.name,
	iid = ins.instrument_id,
	a = ins.getShortAlias(),
	btnCls = btnCls,
)

	cnt = """
<div class="card">
	<div class="card-body text-muted" title="F4, Ctrl+F4 cycle through instruments">
		<strong>Instruments</strong>
	</div>
</div>
<div class="card">
	<div class="card-body">
		<div class="panel-body text-left pre-scrollable my_pre_scrollable" id="instrument_scrollable_div">
			{insCnt}
		</div>
	</div>
</div>
""".format(insCnt = insCnt)

	if pars['updateGraphInstruments']:
		rsp.html('#liquidity_graph_instruments', cnt)

	pts1 = _genXYPoints(ex, 'bids', graphIns,
		pars['depth'], pars['tRange'])
	pts2 = _genXYPoints(ex, 'asks', graphIns,
		pars['depth'], pars['tRange'])

	title = ""
	iid = ""
	if graphIns:
		title = graphIns.name + " " + graphIns.getShortAlias()
		title += " ({depth:.2f}%)".format(depth = pars['depth'])
		iid = graphIns.instrument_id

	iids = ",".join("'" + ins.instrument_id + "'" for ins in instruments)

	scr = """
orderbookGlobals['allInstruments'] = [{iids}];
orderbookGlobals['{gik}'] = '{iid}';
orderbookGlobals['mainChart'].data.datasets[0].data = [{pts1}];
orderbookGlobals['mainChart'].data.datasets[1].data = [{pts2}];
orderbookGlobals['mainChart'].data.datasets[0].label = 'Bid';
orderbookGlobals['mainChart'].data.datasets[1].label = 'Ask';
orderbookGlobals['mainChart'].options.title.text = '{title}';
orderbookGlobals['mainChart'].update();
""".format(pts1=pts1, pts2=pts2, title=title, iids=iids, gik=gik, iid=iid)

	rsp.script(scr)


def updateLGraph(rsp, pars):
	tg = g.tgui
	try:
		exn = pars.get('exchange')
		tg.loadInstrumentsForExchange(exn)

		_updateLGraph(rsp, pars)
		updateMsg(rsp, "&nbsp;", idBase='liquidity_table')
	except Exception as e:
		
		m = """
Couldn't update the graph: {e}
"""[1:-1].format(e=str(e))
		m += "\n" + str(e) + ": " + "".join(traceback.format_exception(e.__class__, e, e.__traceback__))

		m = flask.escape(m)
		updateMsgError(rsp, m, idBase='liquidity_table')
