<?php


require_once "wcms/Module.php";


class EditKeywords extends Module
{
	private function submit($w) {
		$wcms = $this->wcms;
		$kw = $wcms->Request->getVal("keywords");

		try {
			$wcms->dbExec(<<<EOF
UPDATE wcms_parameters SET `value`=? WHERE `key`=? LIMIT 1;
EOF
				, array($kw, 'keywords'));

			$w->addw(new AdminMsgOk("Ключевые слова сохранены"));
		} catch(Exception $e) {
			$w->addw(new AdminMsgErr( "не удалось сохранить ключевые слова: " . $e->getMessage()));
		}
	}

	private function show($w) {
		$wcms = $this->wcms;

		try {
			$rows = $wcms->dbFetch(<<<EOF
SELECT `value` FROM `wcms_parameters` WHERE `key`='keywords';
EOF
			);

			$kw = $rows[0]['value'];

			$w->addw(new Text("<h1>Ключевые слова сайта</h1>"));

			$w->addw(new AdminMsg("Введите через запятую ключевые фразы:"));

			$w->addw($form = new Form());
			$form->addw(new Input("hidden",
				"keywords_submit", "true"));
			$form->addw(new TextArea($kw, "keywords", 50, 10));
			$form->addw(new Text("<br><br>"));
			$form->addw($b = new SubmitButton("Сохранить"));
			$b->setClass("save_button");
		} catch(Exception $e) {
			$w->addw(new AdminMsgErr( "не удалось получить список ключевых слов: " . $e->getMessage()));
		}
	}

	function run() {
		$wcms = $this->wcms;
		$w = $this->Widget = new Container("keywords_submit");

		$flg = $wcms->Request->getVal("keywords_submit");

		if($flg) {
			$this->submit($w);
		}
		$this->show($w);
	}
}

?>
