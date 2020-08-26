<?php

require_once 'wcms/widget/widget.php';
require_once 'wcms/widget/table.php';


class Container extends TagWidget
{
	function __construct($id="") {
		parent::__construct("div", $id);
	}
}


class ContainerCol extends Table
{
	private $table_row = NULL;
	private $valign = "top";
	private $align = "left";

	function __construct($id="") {
		parent::__construct($id);

		$this->Tag->setAttr("align", "center");
		$this->Tag->setAttr("width", "100%");
		$this->Tag->setAttr("border", "0");
		$this->Tag->setAttr("cellpadding", "0");
		$this->Tag->setAttr("cellspacing", "0");

		$this->table_row = new TableRow();
		parent::addw($this->table_row);
	}

	function setValign($v) {
		$this->valign = $v;
	}
	
	function setAlign($v) {
		$this->align = $v;
	}

	function addw(Widget $w) {
		$cell = new TableCell();
		$cell->addw($w);
		$cell->Tag->setAttr("align", $this->align);
		$this->table_row->addw($cell);
		$this->table_row->Tag->setAttr("valign", $this->valign);
	}
}

?>
