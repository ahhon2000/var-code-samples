<?php

class Request {
	function getVal($key) {
		if(isset($_REQUEST[$key])) {
			return $_REQUEST[$key];
		} else {
			return "";
		}
	}
}

?>
