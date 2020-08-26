<?php


class EditSectionKeywords extends Module
{
	private function submit($w) {
		$wcms = $this->wcms;
		$kw = $wcms->Request->getVal("keywords");
		$sid = $wcms->Request->getVal("sid");

		try {
			$wcms->dbExec(<<<EOF
UPDATE sections SET `keywords`=? WHERE `id`=? LIMIT 1;
EOF
				, array($kw, $sid));

			$w->addw(new AdminMsgOk("Ключевые слова сохранены"));
		} catch(Exception $e) {
			$w->addw(new AdminMsgErr( "не удалось сохранить ключевые слова: " . $e->getMessage()));
		}
	}

	private function show($w) {
		$wcms = $this->wcms;
		$sid = $wcms->Request->getVal("sid");

		try {
			$rows = $wcms->dbFetch(<<<EOF
SELECT `keywords` FROM `sections` WHERE `id`=?;
EOF
				, $sid
			);

			$kw = $rows[0]['keywords'];

			$f = Module::getModule("Admin")->getSectionAttrs;
			$f($wcms, $sid, $title, $title_short, $href);

			$w->addw(new Text("<h1>$title: ключевые слова</h1>"));

			$w->addw(new AdminMsg("Введите через запятую ключевые фразы:"));

			$w->addw($form = new Form());
			$form->addw(new Input("hidden",
				"keywords_submit", "true"));
			$form->addw(new Input("hidden",
				"sid", $sid));
			$form->addw(new TextArea($kw, "keywords", 50, 10));
			$form->addw(new Text("<br><br>"));
			$form->addw($b = new SubmitButton("Сохранить"));
			$b->setClass("save_button");
		} catch(Exception $e) {
			$w->addw(new AdminMsgErr( "не удалось получить список ключевых слов: " . $e->getMessage()));
		}
	}

	function editing(Widget $w) {
		$wcms = $this->wcms;
		$flg = $wcms->Request->getVal("keywords_submit");

		if($flg) {
			$this->submit($w);
		}
		$this->show($w);
	}

	function run() {
		$wcms = $this->wcms;
		$w = $this->Widget = new Container("keywords_submit");

		$sid = $wcms->Request->getVal("sid");

		if($sid == "") {
			$mod = $wcms->loadModule("ChooseSection");
			$mod->run("Выбрать");

			$w->addw( new AdminMsg(
				"В каком разделе нужно обновить ключевые слова?"));
			$w->addw($mod->Widget);
		} else {
			$this->editing($w);
		}
	}
}


?>
