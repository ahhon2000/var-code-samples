
def updateMsg(rsp, m, cls="alert", idBase=None):
	if idBase is None: raise Exception("idBase parameter must be specified")
	collapseSz = 80
	mm = m
	if len(m) > collapseSz:
		m1 = m[0:collapseSz]
		mm = """
<div id="{idBase}_msg_short">
	{m1}...
	<a href="#" data-toggle="collapse" data-target="#{idBase}_msg_more" onclick="$('#{idBase}_msg_short').hide(); return false;">more...</a>
</div>

<div id="{idBase}_msg_more" class="collapse">
	{m}
	<a href="#" data-toggle="collapse" data-target="#{idBase}_msg_more" onclick="$('#{idBase}_msg_short').show(); scrollToTop(); return false;">less</a>
</div>
""".format(
	m1 = m1,
	m = m,
	idBase = idBase,
)

	rsp.attr('#{idBase}_msg'.format(idBase=idBase), 'class', cls)
	rsp.html('#{idBase}_msg'.format(idBase=idBase), mm)

def updateMsgWarning(rsp, m, idBase=None):
	updateMsg(rsp, m, cls="alert alert-warning", idBase=idBase)

def updateMsgError(rsp, m, idBase=None):
	updateMsg(rsp, m, cls="alert alert-danger", idBase=idBase)
