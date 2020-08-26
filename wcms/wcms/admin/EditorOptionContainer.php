<?php

require_once "wcms/widget/widget.php";


class EditorOptionContainer extends ContainerCol
{
	function __construct($element, $descr, $id="") {
		parent::__construct($id);
		$this->setAlign("left");
		$this->setValign("center");

		$this->addw($element);
		$this->addw(new AdminLabel($descr));

		$this->setWidths("40%", "60%");
	}
}

?>
