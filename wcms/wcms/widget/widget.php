<?php

require_once 'wcms/widget/container.php';
require_once 'wcms/widget/menu.php';
require_once 'wcms/widget/table.php';
require_once 'wcms/widget/list.php';
require_once 'wcms/widget/paragraph.php';
require_once 'wcms/widget/form.php';
require_once 'wcms/widget/script.php';


class Widget
{
	private $parent = NULL;
	protected $children = array();
	private $id = "";
	private $content = "";

	protected static $identifiers = array();

	protected static function registerId($id) {
		foreach(self::$identifiers as $i) {
			$i == $id and
				die("identifier `$id' already taken");
		}
		self::$identifiers[] = $id;
	}

	function __construct($id="") {
		if($id) { $this->registerId($id); }
		$this->id = $id;
	}

	function getId() {
		return $this->id;
	}

	function getChildren() {
		return $this->children;
	}

	function write($lvl=0) {
		if(!count($this->getChildren())) {
			$this->writeContent();
		}
		foreach ($this->getChildren() as $w) {
			$w->write($lvl+1);
		}
	}

	function getParent() { return $this->parent; }

	function setParent(Widget $p) {
		$this->parent = $p;
	}

	function addw(Widget $w) {
		$w->setParent($this);
		$this->children[] = $w;
	}

	function getContent() { return $this->content; }
	function setContent($s) { $this->content = $s; }
	function appContent($s) { $this->content .= $s; }

	# load content from file
	function setContentFile($f) {
		file_exists($f) or die("can't open file `$f'");
		$this->setContent(file_get_contents($f));
	}

	function writeContent() {
		echo "$this->content\n";
	}
}


class Tag
{
	private $name = "";
	private $attr = NULL;

	function __construct($name, $attr=array()) {
		$this->name = $name;
		$this->attr = $attr;
	}

	function setAttr($key, $val) {
		$this->attr[$key] = $val;
	}

	function setAttrNonemp($key, $val) {
		if($val != "") { $this->setAttr($key, $val); }
	}

	function getAttr($key) {
		isset($this->attr[$key]) or
			die("Tag: attribute `$key' isn't set");

		return $this->attr[$key];
	}

	private function writeAttributes() {
		if(count($this->attr)) {
			foreach($this->attr as $k => $v) {
				echo " $k=\"$v\"";
			}
		}
	}

	function writeOpenNonl($lvl=0) {
		$pad = "";
		for($i=0; $i<$lvl; $i++) { $pad .= "  "; }
		echo "$pad<$this->name";
		$this->writeAttributes();
		echo ">";
	}

	function writeOpen($lvl=0) {
		$this->writeOpenNonl($lvl);
		echo "\n";
	}

	function writeCloseNopad() {
		echo "</$this->name>\n";
	}

	function writeClose($lvl=0) {
		$pad = "";
		for($i=0; $i<$lvl; $i++) { $pad .= "  "; }
		echo "$pad";
		$this->writeCloseNopad();
	}

	function writeEmptyNonl($lvl=0) {
		$pad = "";
		for($i=0; $i<$lvl; $i++) { $pad .= "  "; }
		echo "$pad<$this->name";
		$this->writeAttributes();
		echo "/>";
	}

	function writeEmpty($lvl=0) {
		$this->writeEmptyNonl($lvl);
		echo "\n";
	}
}


class TagWidget extends Widget {
	public $Tag = NULL;
	private $flgEmpty = 0;

	function __construct($tname, $id="") {
		parent::__construct($id);
		$this->Tag = new Tag($tname);
		$this->Tag->setAttrNonemp("id", $id);
	}

	function write($lvl=0) {
		if(!$this->flgEmpty) {
			if(count($this->getChildren()) or
				$this->getContent() != "")
			{
				# if there are some contents or children
				$this->Tag->writeOpen($lvl);
				parent::write($lvl+1);
				$this->Tag->writeClose($lvl);
			} else {
				# there're neither contents nor children
				$this->Tag->writeOpenNonl($lvl);
				$this->Tag->writeCloseNopad();
			}
		} else {
			# TODO turn this check off for performance
			$this->getContent() == "" and
				!count($this->getChildren()) or
				die("can't write empty tag with contents");
			$this->Tag->writeEmpty($lvl);
		}
	}

	function setClass($cl) {
		$this->Tag->setAttr("class", $cl);
	}

	function setEmpty($flg=1) {
		$this->flgEmpty = $flg;
	}
}


class TagWidgetMeta extends TagWidget {
	function __construct() {
		parent::__construct("meta");
		$this->setEmpty();
	}
}


class Text extends Widget
{
	function __construct($txt) {
		parent::__construct();
		$this->setContent($txt);
	}

	function write($lvl=0) {
		$indent = "";
		for($i=0; $i<$lvl; $i++) { $indent .= "  "; }
		echo $indent;
		parent::write($lvl);
	}
}


class Page extends Widget
{
	private $tagHtml = NULL;
	private $head = NULL;
	private $tagBody = NULL;

	private $styles = array();
	private $keywords = '';

	private $favicon = '';

	private $title = "";

	function __construct($id="") {
		parent::__construct($id);

		$h = $this->head = new TagWidget("head");

		# encoding

		$h->addw($metaEnc = new TagWidgetMeta());

		$metaEnc->Tag->setAttr("http-equiv", "Content-Type");
		$metaEnc->Tag->setAttr("content", "text/html; charset=utf-8");
	}

	function getKeywords() { return $this->keywords; }
	function setKeywords($kw) { $this->keywords = $kw; }

	function prependKeywords($kw) {
		if($this->keywords != "") {
			$this->keywords = "$kw, " . $this->keywords;
		} else {
			$this->keywords = $kw;
		}
	}

	function getTitle() { return $this->title; }
	function setTitle($s) { $this->title = $s; }
	function appTitle($s) { $this->title .= $s; }

	function getHead() { return $this->head; }

	function addStyle($href) { $this->styles[] = $href; }
	function addFavicon($href) { $this->favicon = $href; } 

	function writeHeaderOpen() {
		$head = $this->head;
		$this->tagHtml = new Tag("html");
		$this->tagBody = new Tag("body");

		# keywords
		$head->addw($metaKw = new TagWidgetMeta());
		$metaKw->Tag->setAttr("name", "keywords");
		$metaKw->Tag->setAttr("content", $this->getKeywords());

		# stylesheets
		foreach($this->styles as $href) {
			$head->addw($t = new TagWidget("link"));
			$t->Tag->setAttr("href", "$href");
			$t->Tag->setAttr("rel", "stylesheet");
			$t->Tag->setAttr("type", "text/css");
			$t->setEmpty();
		}

		# title
		if($str = $this->getTitle()) {
			$head->addw($t = new TagWidget("title"));
			$t->setContent($str);
		}

		# favicon
		if($this->favicon) {
			$head->addw($t = new TagWidget("link"));
			$t->Tag->setAttr("rel", "shortcut icon");
			$t->Tag->setAttr("href", $this->favicon);
			$t->setEmpty();
		}

		echo <<<EOF
<!DOCTYPE html>

EOF;

		$this->tagHtml->writeOpen();
		$this->head->write();
		$this->tagBody->writeOpen();
	}

	function writeHeaderClose() {
		$this->tagBody->writeClose();
		$this->tagHtml->writeClose();
	}
	
	function write($lvl=0) {
		$this->writeHeaderOpen();
		parent::write($lvl);
		$this->writeHeaderClose();
	}
}

?>
