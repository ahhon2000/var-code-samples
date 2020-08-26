<?php

require_once "wcms/widget/widget.php";


class Image extends TagWidget
{
	function __construct($imgsrc, $id="") {
		parent::__construct("img", $id);
		$this->Tag->setAttr("src", $imgsrc);
	}

	function write($lvl=0) {
		$this->Tag->writeOpen($lvl);
	}
}


class Anchor extends TagWidget
{
	function __construct($content, $href, $id="") {
		parent::__construct("a", $id);
		$this->setContent($content);
		$this->Tag->setAttr("href", $href);
	}

	function write($lvl=0) {
		$this->Tag->writeOpenNonl($lvl);
		echo $this->getContent();
		foreach($this->getChildren() as $w) {
			$w->write(0);
		}
		$this->Tag->writeCloseNopad($lvl);
	}
}

class AnchorImg extends Anchor
{
	function __construct($content, $href, $imgsrc, $id="") {
		parent::__construct($content, $href, $id);

		$this->addw(new Image("$imgsrc"));
	}

	function write($lvl=0) {
		$this->Tag->writeOpenNonl($lvl);
		foreach($this->getChildren() as $img) {
			$img->Tag->setAttrNonemp("alt", $this->getContent());
			$img->Tag->setAttrNonemp("title", $this->getContent());
			$img->Tag->writeOpenNonl(0);
		}
		$this->Tag->writeCloseNopad($lvl);
	}
}

class Br extends Text
{
	function __construct($id="") {
		parent::__construct("<br>", $id);
	}
}

?>
