<?php

require_once "wcms/widget/widget.php";

class JavaScript extends TagWidget
{
	function __construct($src="") {
		parent::__construct("script");

		$this->Tag->setAttr("type", "text/javascript");
		$src != ""  and  $this->Tag->setAttr("src", $src);
		# FIXME content should be wrapped by <!-- and //-->
	}
}


class SelectOrder extends Widget
{
	function __construct($varname, $indices, $values, $sel_ind, $id) {
		$input = new Input("hidden", $varname, "");

		$sel = new SelectList("",$indices,$values,$sel_ind,$id);
		$sel->Tag->setAttr("onmousedown", "this.lbp=true");
		$sel->Tag->setAttr("onmouseup", "this.lbp=false");

		$opts = $sel->getChildren();
		foreach($opts as $op) {
			$op->Tag->setAttr("onmouseover",
				"change_order_$id(this)");
		}

		$js = new JavaScript();
		$js->setContent($this->generateJs($varname, $id));

		$this->addw($input);
		$this->addw($sel);
		$this->addw($js);
	}

	private function generateJs($varname, $id) {
		$code = <<<EOF
function select_array_prepare_$id()
{
	var sel = document.getElementById('$id');
	var arr = new Array();
	var i;

	for(i=0; i<sel.options.length; i++) {
		arr.push(sel.options[i].value);
	}
	sel.form.$varname.value = arr.toString();
}

select_array_prepare_$id();

function change_order_$id(opt)
{
	var sel = document.getElementById('$id');

	if(sel.lbp) {
		var i = sel.selectedIndex;
		optSel = sel.options[i];

		var value = optSel.value;
		var text = optSel.text;
		optSel.value = opt.value;
		optSel.text = opt.text;
		opt.value = value;
		opt.text = text;

		select_array_prepare_$id();
	}
}

EOF;
		return $code;
	}
}

?>
