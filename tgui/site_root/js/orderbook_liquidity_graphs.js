
$.getScript('js/common.js', function() { });
$.getScript('js/Chart/Chart.min.js', function() { });

function updateLGraph(pars={}) {
	var parsDefault = {
		reinit: false,
		updateGraphInstruments: true,
	};
	pars = Object.assign(parsDefault, pars);

	if (pars['reinit'] || orderbookGlobals['mainChart'] === undefined) {
		var data = {
			datasets: [{
				fill: false,
				backgroundColor: 'blue',
				borderColor: 'blue',
				borderWidth: 1,
				data: [
				]
			}, {
				fill: false,
				backgroundColor: 'red',
				borderColor: 'red',
				borderWidth: 1,
				data: [
				]
			}]
		};
		orderbookGlobals['mainChart'] = new Chart('liquidity_graph_canvas', {
			type: 'line',
			data: data,
			options: {
				title: {
					display: true,
					text: '',
				},
				scales: {
					xAxes: [{
						type: 'linear'
					}],
					yAxes: [{
						ticks: {
							callback: function(label, index, labels) {
								return numberWithCommas(label);
							},
						},
					}],
				},
				tooltips: {
					callbacks: {
						title: function(item, data) {
							var v = item[0].label;
							v = Math.round(-parseFloat(v));
							return v + 'm ago';
						},
						label: function(item, data) {
							return numberWithCommas(item.value);
						},
					}
				}
			}
		});
	}

	var sijaxPars = {
		'exchange': orderbookGlobals['exchange'],
		'liquidityFor': orderbookGlobals['liquidityFor'],
		'depth': orderbookGlobals['graphCustomDepth'],
		'depth1': orderbookGlobals['customDepth1'],
		'depth2': orderbookGlobals['customDepth2'],
		'graphInstrumentAll': orderbookGlobals['graphInstrumentAll'],
		'graphInstrumentFutures': orderbookGlobals['graphInstrumentFutures'],
		'graphInstrumentSwaps': orderbookGlobals['graphInstrumentSwaps'],
		'tRange': orderbookGlobals['graphTRange'],
		'updateGraphInstruments': pars['updateGraphInstruments']
	};
	Sijax.requestUri = TGUI_SIJAX_URI;
	Sijax.request('updateLGraph', [sijaxPars]);
}

function setGraphIns(iid, btn=undefined) {
	if (orderbookGlobals['liquidityFor'] == 'all') {
		orderbookGlobals['graphInstrumentAll'] = iid;
	} else if (orderbookGlobals['liquidityFor'] == 'futures') {
		orderbookGlobals['graphInstrumentFutures'] = iid;
	} else if (orderbookGlobals['liquidityFor'] == 'swaps') {
		orderbookGlobals['graphInstrumentSwaps'] = iid;
	}

	var scr = document.getElementById("instrument_scrollable_div");
	if (scr) {
		var btns = scr.getElementsByTagName('button');
		for (i=0; i<btns.length; i++) {
			btns[i].className = 'btn btn-link btn-md';
		}
		if (btn !== undefined) {
			btn.className = "btn btn-info btn-md";
		}
	}

	updateLGraph({'reinit': false, 'updateGraphInstruments': false});
}


function switchTRange(m=0) {
	if (m == 0) {
		var inp = document.getElementById('input_custom_trange');
		m = parseInt(inp.value);
	}
	orderbookGlobals['graphTRange'] = m;

	var i;
	var ranges = [5, 60, 240];
	for (i=0; i<ranges.length; i++) {
		var mm = ranges[i];
		var b = document.getElementById('btn_trange_' + mm + 'm');
		if (mm == m) {
			b.className = 'btn btn-primary active';
		} else {
			b.className = 'btn btn-link';
		}
	}
	
	updateLGraph();
}

function setGraphDepth(d='') {
	if (d == '') {
		var inp = document.getElementById('set_graph_depth_input');
		d = inp.value;
	}
	orderbookGlobals['graphCustomDepth'] = parseFloat(d);

	updateLGraph();
}


function processHotKeyGraphs(e) {
	if (e.which == 115) {
		// F4
		var curIns = undefined;
		var lf = orderbookGlobals['liquidityFor'];
		if (lf == 'futures') {
			curIns = orderbookGlobals['graphInstrumentFutures'];
		} else if (lf == 'swaps') {
			curIns = orderbookGlobals['graphInstrumentSwaps'];
		} else if (lf == 'all') {
			curIns = orderbookGlobals['graphInstrumentAll'];
		}

		var cb = function(iid) {
			var btn = document.getElementById('graph_ins_btn_' + iid);
			setGraphIns(iid, btn);
		}

		toggleThroughList(
			curIns,
			orderbookGlobals['allInstruments'],
			cb,
			e.ctrlKey
		);
	}
}

document.addEventListener('keyup', processHotKeyGraphs, false);
