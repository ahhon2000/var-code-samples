
function updateLTable(onlyTBody=0) {
	var pars = {
		'exchange': orderbookGlobals['exchange'],
		'liquidityFor': orderbookGlobals['liquidityFor'],
		'onlyTBody': onlyTBody,
		'avgInterval1': orderbookGlobals['avgInterval1'],
		'avgInterval2': orderbookGlobals['avgInterval2'],
		'depth': orderbookGlobals['customDepth0'],
		'depth1': orderbookGlobals['customDepth1'],
		'depth2': orderbookGlobals['customDepth2'],
		'tableSortColumn': orderbookGlobals['tableSortColumn'],
	};
	Sijax.requestUri = TGUI_SIJAX_URI;
	Sijax.request('updateLTable', [pars]);
}

function updateLTableOnlyTBody() {
	updateLTable(onlyTBody=1)
}


function inform(s) {
	var msg = document.getElementById('liquidity_table_msg');
	msg.className = "alert alert-info"
	msg.innerHTML = s;
}

function selectContracts(l) {
	orderbookGlobals['liquidityFor'] = l;

	var i;
	var contracts = orderbookGlobals['allContracts'];
	for (i=0; i<contracts.length; i++) {
		var s = contracts[i];
		var e = document.getElementById('btn_contracts_' + s);
		if (s == l) {
			e.className = 'btn btn-primary active';
		} else {
			e.className = 'btn btn-link';
		}
	}

	if (orderbookGlobals['viewType'] == 'table') {
		var tb = document.getElementById('liquidity_table_body');
		tb.innerHTML = '';
	}

	//inform("Loading...");

	updateView();
}


function setAvgIntervalFocus(colNum) {
	window.setTimeout(function() {
		e = document.getElementById('set_avg_interval_input' + colNum);
		e.focus();
	}, 100);
}

function setCustomDepthFocus(colNum) {
	window.setTimeout(function() {
		e = document.getElementById('set_custom_depth_input' + colNum);
		e.focus();
	}, 100);
}

function setAvgInterval(n, m) {
	if (n == 1) {
		if (m == '') {
			var inp = document.getElementById('set_avg_interval_input1');
			m = inp.value;
		}
		orderbookGlobals['avgInterval1'] = m;
	} else if (n == 2) {
		if (m == '') {
			var inp = document.getElementById('set_avg_interval_input2');
			m = inp.value;
		}
		orderbookGlobals['avgInterval2'] = m;
	}

	updateLTable();
}


function setAvgInterval1(m='') {
	setAvgInterval(1, m);
}


function setAvgInterval2(m='') {
	setAvgInterval(2, m);
}

function setCustomDepth(n, d) {
	if (n == 0) {
		if (d == '') {
			var inp = document.getElementById('set_custom_depth_input0');
			d = inp.value;
		}
		orderbookGlobals['customDepth0'] = d;
	} else if (n == 1) {
		if (d == '') {
			var inp = document.getElementById('set_custom_depth_input1');
			d = inp.value;
		}
		orderbookGlobals['customDepth1'] = d;
	} else if (n == 2) {
		if (d == '') {
			var inp = document.getElementById('set_custom_depth_input2');
			d = inp.value;
		}
		orderbookGlobals['customDepth2'] = d;
	}

	updateLTable();
}

function setCustomDepth0(d='') {
	setCustomDepth(0, d);
}

function setCustomDepth1(d='') {
	setCustomDepth(1, d);
}

function setCustomDepth2(d='') {
	setCustomDepth(2, d);
}

function updateView(pars={}) {
	var parsDefault = {
		onlyTBody: false,
		updateGraphInstruments: true,
	};
	pars = Object.assign(parsDefault, pars);

	if (orderbookGlobals['viewType'] == 'table') {
		if (pars['onlyTBody'] == true) {
			updateLTableOnlyTBody();
		} else if (pars['onlyTBody'] == false) {
			updateLTable();
		}
	} else if (orderbookGlobals['viewType'] == 'graph') {
		updateLGraph(pars={
			reinit: false,
			updateGraphInstruments: pars['updateGraphInstruments'],
		});
	}
}

function selectView(v, graphInstrument="") {
	if (v == orderbookGlobals['viewType']) {
		return;
	}

	orderbookGlobals['viewType'] = v;

	var i;
	var vs = orderbookGlobals['allViewTypes'];
	for (i=0; i<vs.length; i++) {
		var s = vs[i];
		var e = document.getElementById('btn_view_' + s);
		if (s == v) {
			e.className = 'btn btn-primary active';
		} else {
			e.className = 'btn btn-link';
		}
	}

	$('#liquidity_table').hide();
	$('#liquidity_table_header').hide();
	$('#liquidity_graph').hide();

	if (orderbookGlobals['viewType'] == 'table') {
		$('#liquidity_table').show();
		$('#liquidity_table_header').show();
	} else if (orderbookGlobals['viewType'] == 'graph') {
		if (graphInstrument) {
			setGraphIns(graphInstrument);
		}
		$('#liquidity_graph').show();
	}

	updateView();
}


function sortTable(col, direction) {
	orderbookGlobals['tableSortColumn'] = [col, direction];
	updateLTable();
}


function switchExchange(exn="") {
	var sel = document.getElementById("exchange_list_id");
	if (exn == "") {
		exn = sel.value;
	} else {
		sel.value = exn;
	}
	
	orderbookGlobals['exchange'] = exn;

	orderbookGlobals['graphInstrumentAll'] = '';
	orderbookGlobals['graphInstrumentFutures'] = '';
	orderbookGlobals['graphInstrumentSwaps'] = '';

	updateView({updateGraphInstruments: true});
}

function toggleThroughList(cur, lst, cb, backwards=false) {
	var ind = 0;
	var i;
	for (i=0; i<lst.length; i++) {
		if (lst[i] == cur) {
			if (backwards) {
				ind = i - 1;
			} else {
				ind = i + 1;
			}
			if (ind >= lst.length) { ind = 0; }
			if (ind < 0) { ind = lst.length - 1; }
			break;
		}
	}
	cb(lst[ind]);
}


function processHotKeyOrderbook(e) {
	if (e.which == 113) {
		// F2
		toggleThroughList(
			orderbookGlobals['exchange'],
			orderbookGlobals['allExchanges'],
			switchExchange,
			e.ctrlKey
		);
	} else if (e.which == 120) {
		// F9
		toggleThroughList(
			orderbookGlobals['liquidityFor'],
			orderbookGlobals['allContracts'],
			selectContracts,
			e.ctrlKey
		);
	} else if (e.which == 119 || e.which == 121) {
		// F8, F10
		toggleThroughList(
			orderbookGlobals['viewType'],
			orderbookGlobals['allViewTypes'],
			selectView,
			e.ctrlKey
		);
	}
}


window.onload = function() {
	updateView();
}

window.setInterval(function() {
	updateView({'onlyTBody': true, 'updateGraphInstruments': false});
}, 15000);

document.addEventListener('keyup', processHotKeyOrderbook, false);
