<?php

require_once "wcms/widget/widget.php";


class ListUl extends TagWidget
{
	function __construct($id="") {
		parent::__construct("ul", $id);
	}
}


class ListItem extends TagWidget
{
	function __construct($id="") {
		parent::__construct("li", $id);
	}
}


?>
