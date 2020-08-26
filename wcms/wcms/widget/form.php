<?php


class Form extends TagWidget
{
	function __construct($id="") {
		parent::__construct("form", $id);
		$this->Tag->setAttr("method", "post");
	}
}


class FormElement extends TagWidget
{
	function __construct($elname, $varname, $varvalue, $id="") {
		parent::__construct($elname, $id);
		$this->Tag->setAttrNonemp("name", $varname);
		$this->Tag->setAttrNonemp("value", $varvalue);
	}
}


class Input extends FormElement
{
	function __construct($type, $varname, $varvalue, $id="") {
		parent::__construct("input", $varname, $varvalue, $id);
		$this->Tag->setAttr("type", $type);
	}
}


class Button extends Input
{
	function __construct($value, $id="") {
		parent::__construct("button", "", $value, $id);
		$this->setEmpty();
	}
}


class SubmitButton extends Input
{
	function __construct($value, $id="") {
		parent::__construct("submit", "", $value, $id);
		$this->setEmpty();
		$this->setClass("submit_button");
	}
}


class _Select extends FormElement
{
	function __construct($varname, $indices, $values, $sel_arr, $id="") {
		parent::__construct("select", $varname, "", $id);
		foreach($indices as $i => $ind) {
			$this->addw($op = new FormElement("option", "", $ind));
			$op->setContent($values[$i]);

			foreach($sel_arr as $sel_ind) {
				if($ind == $sel_ind)
					$op->Tag->setAttr("selected", "true");
			}
		}
	}
}


class ComboBox extends _Select
{
	function __construct($varname, $indices, $values, $sel_ind, $id="") {
		parent::__construct($varname,
			$indices, $values, array($sel_ind), $id);
		$this->setClass("combo_box");
	}
}


class SelectList extends _Select
{
	function __construct($varname, $indices, $values, $sel_ind, $id="") {
		parent::__construct($varname,
			$indices, $values, array($sel_ind), $id);
		$sz = count($indices);
		if($sz < 2) $sz = 2;
		$this->Tag->setAttr("size", $sz);
		$this->setClass("select_list");
	}
}


class SelectListMultiple extends _Select
{
	function __construct($varname, $indices, $values, $sel_arr, $id="") {
		parent::__construct($varname, $indices, $values, $sel_arr, $id);

		$sz = count($indices);
		if($sz < 2) $sz = 2;
		$this->Tag->setAttr("size", $sz);
		$this->Tag->setAttr("multiple", "true");
		$this->setClass("select_list_multiple");
	}
}


class Radio extends Container
{
	function __construct($varname, $indices, $values, $sel_ind, $id="") {
		parent::__construct($id);
		foreach($indices as $i => $ind) {
			$content = $values[$i];

			$inp = new Input("radio", $varname, $ind, $id);
			$inp->setContent($content);

			if($ind == $sel_ind) {
				$inp->Tag->setAttr("checked", "true");
			}

			$this->addw($inp);
			$this->addw(new Text("<br>"));
		}
		$this->setClass("radio");
	}
}


class TextField extends Input
{
	function __construct($varname, $varvalue, $id="") {
		parent::__construct("text", $varname, $varvalue, $id);
		$this->setClass("text_field");
	}
}


class TextArea extends TagWidget
{
	function __construct($txt, $varname, $cols, $rows, $id="") {
		parent::__construct("textarea", $id);
		$this->setContent($txt);
		$this->Tag->setAttrNonemp("name", $varname);
		$this->Tag->setAttrNonemp("cols", $cols);
		$this->Tag->setAttrNonemp("rows", $rows);
	}

	function write($lvl=0) {
		$this->Tag->writeOpenNonl($lvl);
		echo $this->getContent();
		$this->Tag->writeCloseNopad($lvl);
	}
}


class CKEDITOR extends Widget
{
	function __construct($varname, $content) {
		parent::__construct();

		$this->addw($ta = new FormElement("textarea", $varname, "", "ckeditor"));
		$this->addw($scr = new JavaScript());

		$ta->setContent($content);
		$scr->setContent("CKEDITOR.replace('$varname');");
	}
}


class PasswordField extends Input
{
	function __construct($varname, $varvalue, $id="") {
		parent::__construct("password", $varname, $varvalue, $id);
		$this->setClass("password_field");
	}
}


class CheckBox extends Input
{
	function __construct($varname, $varvalue, $checked, $id="") {
		parent::__construct("checkbox", $varname, $varvalue, $id);
		if($checked) {
			$this->Tag->setAttr("checked", "true");
		}
		$this->setClass("check_box");
	}
}


class DateSelector extends Container
{
	function __construct($varYear, $varMonth, $varDay, $seconds, $id="") {
		parent::__construct($id);

		$years = array();
		$months = array();
		$days = array();

		$ymin = min( date("Y", time()) - 10, date("Y", $seconds) );
		$ymax = max( date("Y", time()) + 10, date("Y", $seconds) );
		for($i=$ymin; $i<=$ymax; $i++) {
			$years[] = $i;
		}

		for($i=1; $i<=12; $i++) {
			$months[] = $i;
		}

		for($i=1; $i<=31; $i++) {
			$days[] = $i;
		}

		$y = date("Y", $seconds);
		$m = date("m", $seconds);
		$d = date("d", $seconds);

		$this->addw(new AdminTinyLabel("год:"));
		$this->addw($c1 = new ComboBox($varYear, $years, $years, $y));
		$this->addw(new AdminTinyLabel("месяц:"));
		$this->addw($c2 =new ComboBox($varMonth, $months, $months, $m));
		$this->addw(new AdminTinyLabel("день:"));
		$this->addw($c3 = new ComboBox($varDay, $days, $days, $d));

		$c1->setClass("date_digit");
		$c2->setClass("date_digit");
		$c3->setClass("date_digit");
	}
}

?>
