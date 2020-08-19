function updateFTable(onlyTBody=0) {
	var pars = {
		'onlyTBody': onlyTBody,
		'tableSortColumn': fundingGlobals['tableSortColumn'],
	};
	Sijax.requestUri = TGUI_SIJAX_URI + 'funding';
	Sijax.request('updateFTable', [pars]);
}


function updateFTableOnlyTBody() {
	updateFTable(onlyTBody=1)
}


function sortTable(col, direction) {
	fundingGlobals['tableSortColumn'] = [col, direction];
	updateFTable();
}


function processHotKeyFunding(e) {
}


window.onload = function() {
	updateFTable(false);
}

window.setInterval(function() {
	updateFTable(true);
}, 15000);  // TODO revise this interval

document.addEventListener('keyup', processHotKeyFunding, false);
