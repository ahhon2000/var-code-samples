<?php

# TODO class autoload

set_include_path(get_include_path() . PATH_SEPARATOR . "PEAR" . PATH_SEPARATOR . "../PEAR/share/pear");
require_once 'wcms/Optimizer.php';
require_once 'wcms/Session.php';
require_once 'wcms/ClientSession.php';
require_once 'wcms/Error.php';
require_once 'wcms/Request.php';
require_once 'wcms/Module.php';
require_once 'wcms/widget/widget.php';
require_once 'PEAR.php';
require_once 'MDB2.php';

define("ASSOC", MDB2_FETCHMODE_ASSOC);

# TODO write development functions that facilitate tuning css properties via gui
class WCMS {
	private $Page = NULL;

	public $Request = NULL;
	public $Session = NULL;
	public $ClientSession = NULL;
	public $Optimizer = NULL;
	public $mo = NULL;	// mix-out, or "super object"

	public $Database = NULL;
	private $dsn = "";

	private $on_request = NULL;

	private $disable_output = false;

	function __destruct() {
		if($this->Database && !PEAR::isError($this->Database)) {
			$this->Database->disconnect();
		}
	}

	// TODO move all db* methods to database.php ?

	function dbCheckRes($res) {
		if(PEAR::isError($res)) {
			throw new Exception($res->getMessage() . ', ' .  $res->getDebugInfo());
		}
	}

	function dbSetDsn($dsn) {
		$this->dsn = $dsn;
	}

	function dbQuery($s) {
		$res = $this->Database->query($s);
		$this->dbCheckRes($res);
		return $res;
	}

	function dbPrepare($s) {
		$sth = $this->Database->prepare($s);
		$this->dbCheckRes($sth);
		return $sth;
	}

	// execute query (don't fetch anything)
	function dbExec($query, $params=array()) {
		$sth = $this->dbPrepare($query);
		$q = $sth->execute($params);
		$this->dbCheckRes($q);
		return $q;
	}

	// return rows fetched as a result of the query
	function dbFetch($query, $params=array()) {
		$sth = $this->dbPrepare($query);
		$q = $sth->execute($params);
		$this->dbCheckRes($q);
		$rows = $q->fetchAll(ASSOC);
		return $rows;
	}

	function setOnRequest($cb) {
		$this->on_request = $cb;
	}
	
	function getPage() {return $this->Page;}

	function loadModule($name) {
		return Module::load($name, $this);
	}

	function getModule($name) {
		return Module::getModule($name);
	}

	function run($module="") {
		$this->Page = new Page();

		$this->Request = new Request();

		# connect to db
		$options = array(
			'portability' => MDB2_PORTABILITY_ALL ^ MDB2_PORTABILITY_EMPTY_TO_NULL,
		);
		$res= MDB2::connect($this->dsn, $options);
		$this->dbCheckRes($res);
		$this->Database = $res;

		$this->dbQuery("SET NAMES UTF8;");

		# create objects to be in WCMS

		$this->Session = new Session($this);
		$this->ClientSession = new ClientSession($this);
		$this->Optimizer = new Optimizer($this);

		# execute user supplied handler
		$f = $this->on_request;
		!empty($f)  and  $f($this);

		# output
		if(!$this->disable_output) $this->Page->write();
	}

	function setMixout($mo) {
		$this->mo = $mo;
	}

	function run_cl($module="") {
		$this->disable_output = true;
		$this->run($module);
	}
}

?>
