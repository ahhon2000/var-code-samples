<?php

require_once "wcms/widget/widget.php";

class Table extends TagWidget {
	function __construct($id="") {
		parent::__construct("table", $id);
	}

	function setWidths() {
		$narg = func_num_args();
		$widths = func_get_args();

		$rows = $this->getChildren();
		foreach($rows as $r) {
			$cells = $r->getChildren();

			count($cells) == $narg  or
				die("number of cells != number of widths");

			foreach($cells as $i => $c) {
				$c->Tag->setAttrNonemp("width", $widths[$i]);
			}
		}
	}
}

class TableRow extends TagWidget
{
	function __construct($id="") {
		parent::__construct("tr", $id);
	}
}

class TableHead extends TagWidget
{
	function __construct($id="") {
		parent::__construct("th", $id);
	}
}

class TableCell extends TagWidget
{
	function __construct($id="") {
		parent::__construct("td", $id);
	}
}

?>
