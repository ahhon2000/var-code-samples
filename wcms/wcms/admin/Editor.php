<?php

require_once "wcms/admin/EditorOptionContainer.php";
require_once "wcms/widget/widget.php";
require_once "wcms/Module.php";


class Editor extends Module
{
	private $content = "";

	function getContent() { return $this->content; }
	function setContent($s) { $this->content = $s; }

	private function show_editor($widget) {
		$wcms = $this->wcms;
		$pg = $wcms->getPage();

		$sid = $wcms->Request->getVal("sid");

		$head = $pg->getHead();
		$head->addw($js = new JavaScript("wcms/editor/ckeditor.js"));

		try {
			$f = Module::getModule("Admin")->getSectionAttrs;
			$f($wcms, $sid, $title, $title_short, $section_href);

			$widget->addw(new Text("<h1>$title</h1>"));
		} catch(Exception $e) {
			$widget->addw(new AdminMsgErr(
				"свойства данного раздела недоступны: " .
					$e->getMessage()));
		}

		$widget->addw($formEd = new Form());
		$formEd->addw(new Input("hidden", "sid", $sid));
		$formEd->addw(new Input("hidden", "editor_submit", "true"));
		$formEd->addw(new CKEDITOR("ck_content", $this->getContent()));
		$formEd->addw(new Text("<br>"));

		$formEd->addw(new EditorOptionContainer(
			new TextField("section_title", $title),
			"Название данного раздела"
		));

		$formEd->addw(new EditorOptionContainer(
			new TextField("section_title_short", $title_short),
			<<<EOF
Короткое название, используется в меню. (Это поле можно оставить пустым.)
EOF
		));

		$formEd->addw(new EditorOptionContainer(
			new TextField("section_href", $section_href),
			<<<EOF
Гиперссылка используется для доступа к странице данного раздела.
EOF
		));

		try {
			# choose child sections

			$ids = array();
			$childIds = array();
			$titles = array();

			$f = Module::getModule("Admin")->getChildSections;
			$f($wcms, $childIds, $titles, $sid);

			$f = Module::getModule("Admin")->getSectionsExcept;
			$f($wcms, $ids, $titles, array($sid), FALSE, TRUE);

			$el = new SelectListMultiple("children[]",
				$ids, $titles, $childIds, $id="");
			$descr = <<<EOF
Выберите разделы, которые нужно добавить в данный. (Чтобы выбрать несколько
разделов, нажмите одновременно клавишу <b>ctrl</b> и левую кнопку мыши.)"
EOF;
			$cont = new EditorOptionContainer($el, $descr);
			$formEd->addw($cont);
		} catch(Exception $e) {
			$formEd->addw(new AdminMsgErr(
				"не удается отобразить список подразделов: " .  $e->getMessage()));
		}

		$formEd->addw(new Text("<br>"));
		try {
		       $f = Module::getModule("Admin")->getMenuFlag;
		       $f($wcms, $sid, $checked);

		       $el = new Container();
		       $el->addw(new CheckBox("menu_item", "true", $checked));
		       $el->addw(new Text("Пункт меню"));
		       $descr = <<<EOF
Если галочка стоит, данный раздел будет отображаться в меню
EOF;
			$formEd->addw(new EditorOptionContainer($el, $descr));
		} catch(Exception $e) {
		       $formEd->addw(new AdminMsgErr("не удалось получить статус меню: " . $e->getMessage()));
		}

		$formEd->addw(new Text("<br><hr><br>"));

		$b = new SubmitButton("Сохранить");
		$b->setClass("save_button");
		$descr = <<<EOF
Сохранить все изменения, включая текст раздела
EOF;
		$formEd->addw(new EditorOptionContainer($b, $descr));
	}

	private function editing($widget) {
		$wcms = $this->wcms;
		$sid = $wcms->Request->getVal("sid");

		$submit = $wcms->Request->getVal("editor_submit");
		$ck_content = $wcms->Request->getVal("ck_content");
		$ck_content = stripslashes($ck_content);

		try {
			if($submit) {
				$this->setContent($ck_content);
				$f = Module::getModule("Admin")->saveSection;
				$f($wcms, $sid, $ck_content);
			} else {
				$f = Module::getModule("Admin")->loadSection;
				$f($wcms, $sid, $ck_content);
			}
			$this->setContent($ck_content);
			# FIXME separate saving content from saving other
			# attributes, options, ...

			if($submit) {
				$children = $wcms->Request->getVal("children");
				if(!is_array($children)) $children = array();
				$f = Module::getModule("Admin")->setChildren;
				$f($wcms, $sid, $children);

				$menu_item= $wcms->Request->getVal("menu_item");
				$f = Module::getModule("Admin")->setMenuFlag;
				$f($wcms, $sid, $menu_item);

				$title = $wcms->Request->getVal(
					"section_title");
				$title_short = $wcms->Request->getVal(
					"section_title_short");
				$href = $wcms->Request->getVal("section_href");

				$f= Module::getModule("Admin")->setSectionAttrs;
				$f($wcms, $sid, $title, $title_short, $href);
			}

			$this->show_editor($widget);
		} catch(Exception $e) {
			$widget->addw(new AdminMsgErr("ошибка редактора: " . $e->getMessage()));
		}

		return $widget;
	}

	function run() {
		$wcms = $this->wcms;
		$sid = $wcms->Request->getVal("sid");
		$widget = $this->Widget = new Container("Editor");

		if($sid == "") {
			$mod = $wcms->loadModule("ChooseSection");
			$mod->run("Редактировать");

			$widget->addw( new AdminMsg(
				"Выберите раздел для редактирования:"));
			$widget->addw($mod->Widget);
		} else {
			$this->editing($widget);
		}
	}
}

?>
