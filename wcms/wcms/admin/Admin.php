<?php

require_once("wcms/wcms.php");
require_once("wcms/Module.php");
require_once("wcms/admin/messages.php");


class Admin extends Module
{
	// callbacks
	public $loadSection = "";
	public $saveSection = "";
	public $getSections = "";
	public $getSectionsExcept = "";
	public $getChildSections = "";
	public $addSection = "";
	public $removeSection = "";
	public $setChildren = "";
	public $getMenus = "";
	public $addMenu = "";
	public $setMenuSections = "";
	public $getMenuSections = "";
	public $removeMenu = "";
	public $setMenuFlag = "";
	public $getMenuFlag = "";
	public $getSectionAttrs = "";
	public $setSectionAttrs = "";
	public $getMenuTitle = "";
	public $getSectionOrder = "";
	public $setSectionOrder = "";
	public $addNews = "";
	public $getNews = "";
	public $getNewsByNid = "";
	public $saveNews = "";
	public $removeNews = "";

	function __construct(WCMS $wcms) {
		parent::__construct($wcms);
	}

	private function panelTop() {
		$p = new Container("panel_top");
		$p->addw($m = new Menu());

		$m->addw(new MenuItem("В начало", "admin.php"));
		$m->addw($preview = new MenuItem("Просмотр", "index.php"));
		$m->addw(new MenuItem("Выход", "admin.php?logout=true"));

		$preview->setAnchorAttr("target", "_blank");

		return $p;
	}

	private function panelBottom() {
		$p = new Container("panel_bottom");
		$p->addw($m = new Menu());

		$m->addw(new MenuItem("В начало", "admin.php"));
		$m->addw($preview = new MenuItem("Просмотр", "index.php"));
		$m->addw(new MenuItem("Выход", "admin.php?logout=true"));

		$preview->setAnchorAttr("target", "_blank");

		return $p;
	}

	private function administering() {
		$wcms = $this->wcms;
		$pg = $wcms->getPage();
		$modName = $wcms->Request->getVal("module");

		if($modName == "Editor") {
			$module = $wcms->loadModule("Editor");
		} elseif($modName == "AddSection") {
			$module = $wcms->loadModule("AddSection");
		} elseif($modName == "RemoveSection") {
			$module = $wcms->loadModule("RemoveSection");
		} elseif($modName == "ChangePassword") {
			$module = $wcms->loadModule("ChangePassword");
		} elseif($modName == "EditMenu") {
			$module = $wcms->loadModule("EditMenu");
		} elseif($modName == "AddMenu") {
			$module = $wcms->loadModule("AddMenu");
		} elseif($modName == "RemoveMenu") {
			$module = $wcms->loadModule("RemoveMenu");
		} elseif($modName == "SectionOrder") {
			$module = $wcms->loadModule("SectionOrder");
		} elseif($modName == "EditKeywords") {
			$module = $wcms->loadModule("EditKeywords");
		} elseif($modName == "EditSectionKeywords") {
			$module = $wcms->loadModule("EditSectionKeywords");
		} elseif($modName == "EditNews") {
			$module = $wcms->loadModule("EditNews");
		} elseif($modName == "RemoveNews") {
			$module = $wcms->loadModule("RemoveNews");
		} else {
			# no module was specified
			$module = $wcms->loadModule("ChooseAction");
		}

		$module->run();
		return $module->Widget;
	}

	function run() {
		$wcms = $this->wcms;

		$pg = $wcms->getPage();
		$pg->addStyle("wcms/admin/admin_style.css");
		$pg->addw($wr = new Container("wrapper"));

		$auth = $wcms->loadModule("Auth");
		$widget = NULL;
		if($auth->isAuth()) {
			$widget = $this->administering();
		} else {
			$widget = $auth->Widget;
		}

		$wr->addw($this->panelTop());
		$wr->addw($widget);
		$wr->addw($this->panelBottom());
	}
}

?>
