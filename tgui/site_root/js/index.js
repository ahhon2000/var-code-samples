
var TGUI_SIJAX_URI = '/';
if(location.host.search('127.0.0.1') < 0 && location.host.search('localhost') < 0) {
	TGUI_SIJAX_URI = 'https://178.62.247.199:8114/';
}
Sijax.requestUri = TGUI_SIJAX_URI;


function scrollToTop() {
	window.setTimeout(function() {
		window.scrollTo(0, 0);
	}, 100);
}
