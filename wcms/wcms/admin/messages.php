<?php


class AdminMsg extends Container
{
	function __construct($txt, $id="") {
		parent::__construct($id);
		$this->setContent($txt);
		$this->setClass("admin_message");
	}
}


class AdminMsgOk extends AdminMsg
{
	function __construct($txt, $id="") {
		parent::__construct($txt, $id);
		$this->setClass("admin_message_ok");
	}
}


class AdminMsgErr extends AdminMsg
{
	function __construct($txt, $id="") {
		parent::__construct($txt, $id);
		$this->setClass("admin_message_err");
	}
}


class AdminLabel extends AdminMsg
{
	function __construct($txt, $id="") {
		parent::__construct($txt, $id);
		$this->setClass("admin_label");
	}
}


class AdminTinyLabel extends AdminLabel
{
	function __construct($txt, $id="") {
		parent::__construct($txt, $id);
		$this->setClass("admin_tiny_label");
	}
}


class LabelAndField extends Table
{
	function __construct($descr, $element, $id="") {
		parent::__construct($id);
		$this->Tag->setAttr("width", "100%");

		$this->addw($tr = new TableRow());
		$tr->Tag->setAttr("valign", "center");
		$tr->addw($tdl = new TableCell());
		$tr->addw($tdr = new TableCell());

		$tdl->Tag->setAttr("align", "right");
		$tdr->Tag->setAttr("align", "left");
		$tdl->Tag->setAttr("width", "35%");
		$tdr->Tag->setAttr("width", "65%");

		$tdl->addw(new AdminTinyLabel($descr));
		$tdr->addw($element);
	}
}

?>
