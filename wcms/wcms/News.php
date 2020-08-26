<?php

class News
{
	private $date = 0;	// seconds since the Epoch
	private $expire_date = 0;
	private $content = '';
	private $nid = 0;

	function __construct($date, $expDate, $content, $nid=0) {
		$this->setDate($date);
		$this->setExpDate($expDate);
		$this->setContent($content);
		$this->setNid($nid);
	}

	function setDate($sec) { $this->date = $sec; }
	function setExpDate($sec) { $this->expire_date = $sec; }
	function setContent($s) { $this->content = $s; }
	function setNid($nid) { $this->nid = $nid; }

	function getDate() { return $this->date; }
	function getExpDate() { return $this->expire_date; }
	function getContent() { return $this->content; }
	function getNid() { return $this->nid; }

	function sec2str($sec) {
		return date("Y-m-d H:i", $sec);
	}

	function sec2rus($sec) {
		return date("d.m.Y", $sec);
	}

	function getDateStr() {
		return $this->sec2str($this->getDate());
	}

	function getExpDateStr() {
		return $this->sec2str($this->getExpDate());
	}

	function getDateRus() {
		return $this->sec2rus($this->getDate());
	}
}

?>
