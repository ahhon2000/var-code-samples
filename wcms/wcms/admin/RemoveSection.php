<?php

class RemoveSection extends Module
{
	private function removing($widget) {
		$wcms = $this->wcms;
		$sid = $wcms->Request->getVal("sid");

		try {
			$f = Module::getModule("Admin")->removeSection;
			$f($wcms, $sid);

			$widget->addw(new AdminMsgOk("раздел удален"));
		} catch(Exception $e) {
			$widget->addw(new AdminMsgErr("раздел не был удален: " . $e->getMessage()));
		}
	}

	function run() {
		$wcms = $this->wcms;
		$sid = $wcms->Request->getVal("sid");
		$widget = $this->Widget = new Container("remove_section");

		if($sid == "") {
			$mod = $wcms->loadModule("ChooseSection");
			$mod->run("Удалить", <<<EOF

return confirm('Вы действительно хотите удалить данный раздел?');
EOF
			);

			$widget->addw(new AdminMsg(
				"Выберите раздел для удаления:"));
			$widget->addw($mod->Widget);
		} else {
			$this->removing($widget);
		}
	}
}

?>
