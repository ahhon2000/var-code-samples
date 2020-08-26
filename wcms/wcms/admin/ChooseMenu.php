<?php

require_once "wcms/Module.php";


class ChooseMenu extends Module
{
	function run($buttonTxt, $jscode = "") {
		$wcms = $this->wcms;
		$w = $this->Widget = new Container("choose_menu");

		$f = Module::getModule("Admin")->getMenus;
		$f($wcms, $mids, $titles);

		if(count($mids)) {
			$w->addw($script = new JavaScript());
			$w->addw($form = new Form());
			$form->addw(new SelectList("mid",
				$mids, $titles, $mids[0]));
			$form->addw(new Text("<br><br>"));
			$form->addw(new SubmitButton($buttonTxt));
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
			$w->addw(new AdminMsg("не создано ни одного меню"));
		}
	}
}


?>
