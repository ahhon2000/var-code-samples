<?php

require_once 'wcms/widget/widget.php';

class NewsEditor extends Form
{
	function __construct($wcms, $flgNew, $id="") {
		parent::__construct($id);

		$pg = $wcms->getPage();

		$n = NULL;

		$content = $wcms->Request->getVal("ck_content");

		if(!$flgNew) {
			$nid = $wcms->Request->getVal("nid");

			$f = Module::getModule("Admin")->getNewsByNid;
			$f($wcms, $nid, $n);
			if($content == '') $content = $n->getContent();
		} else {
			$t = time();
			$n = new News($t, $t+2592000, "");
		}

		$head = $pg->getHead();
		$head->addw($js = new JavaScript("wcms/editor/ckeditor.js"));

		$this->addw(new Input("hidden", "nid", $nid));
		$this->addw(new Input("hidden","news_submit",'true'));
		$this->addw(new CKEDITOR("ck_content", $content));
		$this->addw(new Br());
		$this->addw(new Br());
		$this->addw(new Br());

		$this->addw(new EditorOptionContainer(
			new DateSelector("year", "month", "day",
				$n->getDate()),
			"С какого времени отображается новость"
		));
		$this->addw(new Br());
		$this->addw(new EditorOptionContainer(
			new DateSelector("exp_year", "exp_month", "exp_day", $n->getExpDate()),
			"С какого времени новость перестанет отображаться"
		));

		$this->addw(new Br());
		$this->addw(new Br());

		if($flgNew) {
			$caption = "Добавить";
			$descr = "Добавить новость";
		} else {
			$caption = "Сохранить";
			$descr = "Сохранить изменения";
		}

		$this->addw(new EditorOptionContainer(
			$b = new SubmitButton($caption),
			$descr
		));
		$b->setClass("save_button");
	}
}


class NewsEditorSubmit
{
	private $wcms = NULL;
	private $flgNew = FALSE;

	function __construct(WCMS $wcms, $flgNew) {
		$this->wcms = $wcms;
		$this->flgNew = $flgNew;
	}

	function exec() {
		$wcms = $this->wcms;
		$flgNew = $this->flgNew;

		$ck_content = $wcms->Request->getVal('ck_content');

		$year = $wcms->Request->getVal('year');
		$month = $wcms->Request->getVal('month');
		$day = $wcms->Request->getVal('day');
		$exp_year = $wcms->Request->getVal('exp_year');
		$exp_month = $wcms->Request->getVal('exp_month');
		$exp_day = $wcms->Request->getVal('exp_day');

		if(!checkdate($month, $day, $year)) throw new Exception("некорректная дата: $year-$month-$day");
		if(!checkdate($exp_month, $exp_day, $exp_year)) throw new Exception("некорректная дата: $exp_year-$exp_month-$exp_day");

		$date = strtotime("$year-$month-$day");
		$expire = strtotime("$exp_year-$exp_month-$exp_day");

		$n = NULL;

		$n = new News($date, $expire, $ck_content);

		if($flgNew) {
			$f = Module::getModule("Admin")->addNews;
		} else {
			$nid = $wcms->Request->getVal('nid');
			$n->setNid($nid);
			$f = Module::getModule("Admin")->saveNews;
		}

		$f($wcms, $n);
	}
}

?>
