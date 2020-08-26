<?php

class ModuleMenu extends Menu
{
	function __construct($actions, $id="") {
		parent::__construct($id);
		foreach($actions as $module => $descr) {
			$href = "?module=$module";
			$this->addw(new MenuItem($descr, $href));
		}
	}
}

class ChooseAction extends Module
{
	function run() {
		$w = $this->Widget = new Container("ChooseAction");
		$wcms = $this->wcms;

		$menus = array();

		$menus[] = new ModuleMenu(array(
			"Editor" => "Редактировать раздел",
			"AddSection" => "Добавить раздел",
			"EditSectionKeywords" => "Ключевые слова раздела",
			"RemoveSection" => "Удалить раздел",
		));

		if(!file_exists(".news_lock")) {
			$menus[]= new ModuleMenu(array(
				"EditNews" => "Новости",
			));
		}

		$menus[] = new ModuleMenu(array(
			"EditMenu" => "Редактировать меню",
			"AddMenu" => "Добавить меню",
			"RemoveMenu" => "Удалить меню",
			"SectionOrder" => "Порядок разделов",
		));

		$menus[] = new ModuleMenu(array(
			"EditKeywords" => "Ключевые слова сайта",
			"ChangePassword" => "Сменить пароль",
		));

		foreach($menus as $m) {
			$m->setClass("main_menu");
			$w->addw($m);
		}

		$w->addw($mLast = new Menu());
		$mLast->setClass("main_menu");
		$mLast->addw(new MenuItem("Выход", "?logout=true"));
	}
}

?>
