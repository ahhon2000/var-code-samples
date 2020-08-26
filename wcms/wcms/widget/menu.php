<?php

require_once "wcms/widget/widget.php";
require_once "wcms/widget/list.php";
require_once "wcms/widget/paragraph.php";


class Menu extends ListUl
{
	function __construct($id="") {
		parent::__construct($id);
	}
}


class MenuItem extends Widget
{
	private $href = "";
	private $anchor_attr = array();

	function getHref() { return $this->href; }
	function setHref($h) { $this->href = $h; }

	function __construct($cont, $href, $id="") {
		parent::__construct();
		$this->setContent($cont);
		if($href) { $this->setHref($href); }
	}

	function setAnchorAttr($attr, $val) {
		$this->anchor_attr[$attr] = $val;
	}

	function isActive() {
		$r = new Request();
		if($r->getVal('section') == $this->getHref()) return 1;
		else return 0;
	}

	function write($lvl=0) {
		$tagLi = new Tag("li");

		$tagLi->writeOpen($lvl);

		$s = $this->getContent();
		if($s and $this->getHref()) {
			$a = new Anchor("", $this->getHref());
			$a->setContent($s);

			if($this->isActive()) $a->setClass('active');

			foreach($this->anchor_attr as $attr => $v) {
				$a->Tag->setAttr($attr, $v);
			}

			$a->write($lvl+1);
		} elseif($s) {
			$t = new Text($s);
			$t->write($lvl+1);
		}

		foreach ($this->getChildren() as $w) {
			$w->write($lvl+1);
		}

		$tagLi->writeClose($lvl);
	}
}


class MenuItemImage extends Widget
{
	private $href = "";
	private $imgsrc = "";
	private $anchor_attr = array();

	function getHref() { return $this->href; }
	function getImgsrc() { return $this->imgsrc; }
	function setHref($h) { $this->href = $h; }
	function setImgsrc($i) { $this->imgsrc = $i; }

	function __construct($cont, $href, $imgsrc, $id="") {
		parent::__construct();
		$this->setContent($cont);
		if($href) { $this->setHref($href); }
		$this->setImgsrc($imgsrc);
	}

	function setAnchorAttr($attr, $val) {
		$this->anchor_attr[$attr] = $val;
	}

	function write($lvl=0) {
		$tagLi = new Tag("li");

		$tagLi->writeOpen($lvl);

		$s = $this->getContent();
		$imgsrc = $this->getImgsrc();
		if($imgsrc and $this->getHref()) {
			$a = new AnchorImg($s, $this->getHref(), $imgsrc,
				$this->getId());

			foreach($this->anchor_attr as $attr => $v) {
				$a->Tag->setAttr($attr, $v);
			}

			$a->write($lvl+1);
		} elseif($imgsrc) {
			$img = new Image($imgsrc);
			$img->write($lvl+1);
		}

		foreach ($this->getChildren() as $w) {
			$w->write($lvl+1);
		}

		$tagLi->writeClose($lvl);
	}
}


class ComplexMenu extends Menu
{
	private $imgHash = array(
		"first_act" => "",
		"first_pass" => "",
		"last_act" => "",
		"last_pass" => "",
		"delim_act_pass" => "",
		"delim_pass_act" => "",
		"delim_pass_pass" => "",
	);

	function __construct($imgHash, $id="") {
		parent::__construct($id);
		$this->setImgHash($imgHash);
	}

	function setImgHash($h) { $this->imgHash = $h; }
	function getImgHash() { return $this->imgHash; }

	function write($lvl=0) {
		$this->Tag->writeOpen($lvl);

		$imgHash = $this->getImgHash();

		$r = new Request();
		$section = $r->getVal("section");

		$children = $this->getChildren();
		$n = count($children);

		// opening image
		$key = 'first_pass';
		if($n>0 && $children[0]->isActive()) $key = 'first_act';
		$img = new Image($imgHash[$key]);
		$img->write($lvl+1);

		for($i=0; $i<$n; $i++) {
			$ch = $children[$i];
			$ch->write($lvl+1);
			if($i < $n - 1) {
				$chNxt = $children[$i+1];

				$key = 'delim_pass_pass';
				if($ch->isActive()) {
					$key = 'delim_act_pass';
				} elseif($chNxt->isActive()) {
					$key = 'delim_pass_act';
				}

				$img = new Image($imgHash[$key]);
				$img->write($lvl+1);
			}
		}

		// closing image
		$key = 'last_pass';
		if($n>0 && $children[$n-1]->isActive()) $key = 'last_act';
		$img = new Image($imgHash[$key]);
		$img->write($lvl+1);

		$this->Tag->writeClose($lvl);
	}
}


class ComplexMenuItem extends MenuItem
{
	function __construct($cont, $href, $id="") {
		parent::__construct($cont, $href, $id);
	}
}

?>
