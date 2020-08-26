<?php

require_once "wcms/wcms.php";

class Optimizer
{
	private $wcms = NULL;

	function __construct(WCMS $wcms) {
		$this->wcms = $wcms;

		# TODO each page must have its own keywords (fld in `sections`)
		$rows = $wcms->dbFetch(<<<EOF
SELECT `value` FROM wcms_parameters WHERE `key`='keywords';
EOF
		);
		$kw = $rows[0]['value'];

		$wcms->getPage()->setKeywords($kw);
	}
}

?>
