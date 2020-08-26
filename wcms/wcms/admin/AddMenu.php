<?php


class AddMenu extends Module
{
	function run() {
		$wcms = $this->wcms;
		$w = $this->Widget = new Container("add_menu");
		$w->addw(new Text("<h1>Создание нового меню</h1>"));
		$mid = $wcms->Request->getVal("mid");

		$menu_title_sent = $wcms->Request->getVal("menu_title_sent");
		if($menu_title_sent) {
			$title = $wcms->Request->getVal("title");
			try {
				$f = Module::getModule("Admin")->addMenu;
				$f($wcms, $title);
				$w->addw(new AdminMsgOk("меню создано"));
			} catch(Exception $e) {
				$w->addw(new AdminMsgErr(
					"меню не было создано: " .
						$e->getMessage()));
			}
		} else {
			$w->addw($form = new Form());
			$form->addw(new Input("hidden",
				"menu_title_sent", "true"));

			$fld = new TextField("title", "");
			$b = new SubmitButton("Создать");
			$b->setClass("save_button");

			$form->addw(new LabelAndField(
				"Название", $fld
			));
			$form->addw(new LabelAndField(
				"", $b
			));
		}
	}
}

?>
