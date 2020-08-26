<?php

require_once 'wcms/widget/widget.php';

class ErrorText extends Text
{
	function __construct($errstr) {
		$file = "errors/$errstr.html";

		$txt = file_get_contents($file);
		parent::__construct($txt);
	}
}

?>
