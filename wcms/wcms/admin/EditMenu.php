<?php


class EditMenu extends Module
{
	private function show($widget) {
		$wcms = $this->wcms;
		$mid = $wcms->Request->getVal("mid");

		try {
			$f = Module::getModule("Admin")->getMenuTitle;
			$f($wcms, $mid, $title);

			$widget->addw(new Text("<h1>$title</h1>"));
		} catch(Exception $e) {
			$widget->addw(new AdminMsgErr(
				"название данного меню недоступно: " .
					$e->getMessage()));
		}

		$widget->addw($form = new Form());

		try {
			$f= Module::getModule("Admin")->getMenuSections;
			$f($wcms, $mid, $menuSections);

			$f= Module::getModule("Admin")->getSections;
			$f($wcms, $sids, $titles, FALSE, TRUE);

			$form->addw(new Input("hidden", "mid", $mid));
			$form->addw(new Input("hidden",
				"edit_menu_submit", "true"));

			$fld = new SelectListMultiple("sections[]",
				$sids, $titles, $menuSections);
			$b = new SubmitButton("Сохранить");
			$b->setClass("save_button");

			$form->addw(new LabelAndField(<<<EOF
Удерживая клавишу <b>ctrl</b>,<br>
выделите те разделы,<br>
которые должны быть в меню:
EOF
				, $fld
			));
			$form->addw(new LabelAndField(
				"", $b
			));
		} catch(Exception $e) {
			$widget->addw(new AdminMsgErr("ошибка редактора меню: " .
				$e->getMessage()));
		}
	}

	private function editing($widget) {
		$wcms = $this->wcms;
		$mid = $wcms->Request->getVal("mid");
		$edit_menu_submit = $wcms->Request->getVal("edit_menu_submit");

		if($edit_menu_submit) {
			$sections = $wcms->Request->getVal("sections");
			if(!is_array($sections)) $sections = array();
			try {
				$f= Module::getModule("Admin")->setMenuSections;
				$f($wcms, $mid, $sections);
			} catch(Exception $e) {
				$widget->addw(new AdminMsgErr("не удалось сохранить изменения: " . $e->getMessage()));
			}
		}

		$this->show($widget);
	}

	function run() {
		$wcms = $this->wcms;
		$widget = $this->Widget = new Container("edit_menu");
		$mid = $wcms->Request->getVal("mid");

		if($mid == "") {
			$mod = $wcms->loadModule("ChooseMenu");
			$mod->run("Редактировать");

			$widget->addw( new AdminMsg(
				"Выберите меню для редактирования:"));
			$widget->addw($mod->Widget);
		} else {
			$this->editing($widget);
		}
	}
}

?>
