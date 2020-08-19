function updateVTable(onlyTBody=0) {
	var pars = {
		'onlyTBody': onlyTBody,
		'tableSortColumn': volumeGlobals['tableSortColumn'],
	};
	Sijax.requestUri = TGUI_SIJAX_URI + 'volume';
	Sijax.request('updateVTable', [pars]);
}


function updateVTableOnlyTBody() {
	updateVTable(onlyTBody=1)
}


function sortTable(col, direction) {
	volumeGlobals['tableSortColumn'] = [col, direction];
	updateVTable();
}


function processHotKeyVolume(e) {
}


window.onload = function() {
	updateVTable(false);
}

window.setInterval(function() {
	updateVTable(true);
}, 60000);

document.addEventListener('keyup', processHotKeyVolume, false);
