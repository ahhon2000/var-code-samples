<?php

class RemoveMenu extends Module
{
	private function removing($widget) {
		$wcms = $this->wcms;
		$mid = $wcms->Request->getVal("mid");

		try {
			$f = Module::getModule("Admin")->removeMenu;
			$f($wcms, $mid);

			$widget->addw(new AdminMsgOk("меню удалено"));
		} catch(Exception $e) {
			$widget->addw(new AdminMsgErr("меню не удалено: " .
				$e->getMessage()));
		}
	}

	function run() {
		$wcms = $this->wcms;
		$widget = $this->Widget = new Container("remove_menu");
		$mid = $wcms->Request->getVal("mid");

		if($mid == "") {
			$mod = $wcms->loadModule("ChooseMenu");
			$mod->run("Удалить", <<<EOF
return confirm('Вы действительно хотите удалить данное меню?');
EOF
			);

			$widget->addw( new AdminMsg(
				"Выберите меню для удаления:"));
			$widget->addw($mod->Widget);
		} else {
			$this->removing($widget);
		}
	}
}

?>
