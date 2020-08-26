<?php

require_once "wcms/News.php";
require_once "wcms/Module.php";
require_once "wcms/admin/NewsEditor.php";

class ChooseNews extends Module
{
	function show($w) {
		$wcms = $this->wcms;
		$w->addw(new Text("<h1>Новости</h1>"));

		$f = Module::getModule("Admin")->getNews;
		$f($wcms, $newsArr);

		if(!count($newsArr)) {
			$w->addw(new AdminMsg("Новостей нет"));
		}

		$w->addw(new Text("<h2>Добавить новость:</h2>"));
		try {
			$w->addw($formNew = new NewsEditor($wcms, TRUE));
		} catch(Exception $e) {
			$w->addw(new AdminMsgErr("ошибка редактора новостей: " . $e->getMessage()));
		}

		if(count($newsArr)) {
			$w->addw(new Br());
			$w->addw(new Text("<hr>"));
			$w->addw(new Br());
			$w->addw(new Text("<h2>Редактировать новости:</h2>"));

			$w->addw($script = new JavaScript());
			$w->addw($form = new Form());

			$form->addw($tbl = new Table("news_table"));
			$tbl->Tag->setAttr("border", "1");
			$tbl->Tag->setAttr("cellpadding", "10px");
			$tbl->Tag->setAttr("cellspacing", "0");

			if($jscode != "") {
				$form->Tag->setAttr("onSubmit", "return onSubmit()");
				$script->setContent(<<<EOF
function onSubmit()
{
$jscode
}

EOF
				);
			}

			$tbl->addw($tr = new TableRow());
			$tr->addw($th1 = new TableHead());
			$tr->addw($th2 = new TableHead());
			$tr->addw($th3 = new TableHead());
			$tr->addw($th4 = new TableHead());
			$th1->setContent("Удалить");
			$th2->setContent("Отображается с");
			$th3->setContent("Отображается по");
			$th4->setContent("Текст");

			foreach($newsArr as $n) {
				$nid = $n->getNid();

				$tbl->addw($tr = new TableRow());

				$tr->addw($td1 = new TableCell());
				$tr->addw($td2 = new TableCell());
				$tr->addw($td3 = new TableCell());
				$tr->addw($td4 = new TableCell());

				$td1->addw($ra = new Anchor("x",
					"?module=RemoveNews&nid=$nid"));
				$ra->setClass("red_remove");
				$ra->Tag->setAttr("onclick", <<<EOF
javascript:return confirm('Вы действительно хотите удалить эту новость?');
EOF
);

				$h = "?module=EditNews&nid=$nid";

				$td2->addw(new Anchor($n->getDateStr(), $h));
				$td3->addw(new Anchor($n->getExpDateStr(), $h));
				$td4->addw(new Anchor($n->getContent(), $h));
			}
		}
	}

	function submit($w) {
		$wcms = $this->wcms;

		try {
			$nes = new NewsEditorSubmit($wcms, TRUE);
			$nes->exec();
		} catch(Exception $e) {
			$w->addw(new AdminMsgErr("не удалось добавить новость: " . $e->getMessage()));
		}
	}

	function run($jscode = "") {
		$wcms = $this->wcms;
		$w = $this->Widget = new Container("choose_news");

		$flg = $wcms->Request->getVal("news_submit");
		if($flg) {
			$this->submit($w);
		}

		$this->show($w);
	}
}

?>
