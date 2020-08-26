<?php

require_once "wcms/widget/widget.php";
require_once "wcms/Module.php";


class ChooseSection extends Module
{
	function run($buttonTxt, $jscode = "") {
		$this->Widget = new Container("ChooseSection");
		$wcms = $this->wcms;

		$ids = array();
		$titles = array();
		$f = Module::getModule("Admin")->getSections;
		$f($wcms, $ids, $titles, FALSE, TRUE);

		if(count($ids) > 0) {
			$this->Widget->addw($script = new JavaScript());
			$this->Widget->addw($form = new Form());
			$form->addw(new SelectList("sid", $ids, $titles, 2));
			$form->addw(new Text("<br><br>"));
			$form->addw($b = new SubmitButton($buttonTxt));
			if($jscode != "") {
				$form->Tag->setAttr("onSubmit", "return onSubmit()");
				$script->setContent(<<<EOF
function onSubmit()
{
$jscode
}

EOF
				);
			}
		} else {
			$this->Widget->addw(new AdminMsg("Разделов нет"));
		}
	}
}

?>
