<?php

require_once "wcms/admin/EditorOptionContainer.php";
require_once "wcms/Module.php";
require_once "wcms/admin/NewsEditor.php";


class EditNews extends Module
{
	private $content = "";

	private function setContent($c) { $this->content = $c; }
	private function getContent($c) { return $this->content; }

	private function submit($w) {
		$wcms = $this->wcms;
		try {
			$nes = new NewsEditorSubmit($wcms, FALSE);
			$nes->exec();
		} catch(Exception $e) {
			$w->addw(new AdminMsgErr("не удалось сохранить новость: " . $e->getMessage()));
		}
	}

	private function show($w) {
		$wcms = $this->wcms;
		$pg = $wcms->getPage();

		$w->addw(new Text("<h1>Редактирование новости</h1>"));

		try {
			$w->addw($formEd = new NewsEditor($wcms, FALSE));
		} catch(Exception $e) {
			$w->addw(new AdminMsgErr("ошибка редактора: " . $e->getMessage()));
		}
	}

	function run() {
		$wcms = $this->wcms;
		$w = $this->Widget = new Container("edit_news");

		$nid = $wcms->Request->getVal("nid");

		if($nid == "") {
			$mod = $wcms->loadModule("ChooseNews");
			$mod->run();

			$w->addw($mod->Widget);
		} else {
			$flg = $wcms->Request->getVal("news_submit");

			if($flg) {
				$this->submit($w);
			}
			$this->show($w);
		}
	}
}

?>
