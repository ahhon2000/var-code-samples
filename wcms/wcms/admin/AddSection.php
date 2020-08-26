<?php


class AddSection extends Module
{
	function run() {
		$wcms = $this->wcms;
		$w = $this->Widget = new Container("AddSection");

		$section_title = $wcms->Request->getVal("section_title");
		$section_title_short =
			$wcms->Request->getVal("section_title_short");
		$section_href = $wcms->Request->getVal("section_href");
		$parent = $wcms->Request->getVal("parent");

		if($section_title == "") {
			$w->addw(new Text("<h1>Создание нового раздела</h1>"));
			$w->addw($form = new Form());

			$ids = array();
			$titles = array();
			$f = Module::getModule("Admin")->getSections;
			$f($wcms, $ids, $titles, TRUE);

			$cb = new ComboBox("parent", $ids, $titles, $ids[0]);
			$form->addw(new LabelAndField(
				"Родительский раздел:", $cb
			));

			$fld = new TextField("section_title", "");
			$form->addw(new LabelAndField(
				"Название:", $fld
			));

			$fld = new TextField("section_title_short", "");
			$form->addw(new LabelAndField(
				"Короткое название:", $fld
			));
			# TODO section href validator in javascript
			$fld = new TextField("section_href", "");
			$form->addw(new LabelAndField(
				"Гиперссылка:", $fld
			));
			$b = new SubmitButton("Создать");
			$form->addw(new LabelAndField(
				"", $b
			));
			$b->setClass("save_button");
		} else {
			try {
				$f = Module::getModule("Admin")->addSection;
				$f($wcms, $section_title, $section_title_short,
					$section_href, $parent);
				$w->addw(new
					AdminMsgOk(
					"раздел '$section_title' создан"));
			} catch(Exception $e) {
				$w->addw(new AdminMsgErr(
					"раздел не был создан: " .
						$e->getMessage()));
			} // try
		} // if
	} // function run()
}

?>
