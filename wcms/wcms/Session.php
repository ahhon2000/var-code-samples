<?php

require_once "wcms.php";

class Session
{
	const expir_interval = 604800; # seconds (604800 = a week)
	const sid_characters = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
	const sid_length = 64;

	private $wcms = NULL;
	private $flg_auth = 0;


	function __construct(WCMS $wcms) {
		$this->wcms = $wcms;

		# delete expired sessions from the database

		$sth = $wcms->dbPrepare(<<<EOF
DELETE FROM sessions WHERE expire<?;
EOF
		);
		$res = $sth->execute(array(time()));
		$wcms->dbCheckRes($res);

		# check if the user is authenticated, update expiration date

		if(isset($_COOKIE['session_id'])) {
			$sid = $_COOKIE['session_id'];
			$sth = $wcms->dbPrepare(<<<EOF
SELECT id FROM sessions WHERE id=?;
EOF
			);
			$q = $sth->execute(array($sid));
			$ar = $q->fetchAll(ASSOC);
			if(count($ar)) {
				$this->flg_auth = 1;

				# update expiration date

				$expire = time() + self::expir_interval;
				$sth = $wcms->dbPrepare(<<<EOF
UPDATE sessions SET expire=? WHERE id=? LIMIT 1;
EOF
				);
				$res = $sth->execute(array($expire, $sid));
			} // if
		}// if
	} // __construct()

	function getUser() {
		$wcms = $this->wcms;
		$sid = $_COOKIE['session_id'];

		$sth = $wcms->dbPrepare(<<<EOF
SELECT user FROM sessions WHERE id=?;
EOF
		);
		$q = $sth->execute(array($sid));
		$ar = $q->fetchAll(ASSOC);

		return $ar[0]['user'];
	}

	private function generateSid() {
		$sid = '';
		$chars = self::sid_characters;
		$n = strlen($chars);
		for($i=0; $i<self::sid_length; $i++) {
			$ind = rand() % $n;
			$sid .= $chars[$ind];
		}

		return $sid;
	}

	private function passwordOk($user, $pw) {
		$wcms = $this->wcms;

		$sth = $wcms->dbPrepare(<<<EOF
SELECT name FROM users WHERE name=? and password=?;
EOF
		);
		$q = $sth->execute(array($user, $pw));
		$ar = $q->fetchAll(ASSOC);

		if(count($ar)) {
			return 1;
		} else {
			return 0;
		}
	}

	// try to make the client authenticated, return non-zero on success
	function authenticate($user, $pw) {
		$wcms = $this->wcms;

		if($this->passwordOk($user, $pw)) {
			$sid = $this->generateSid();
			$expire = time() + self::expir_interval;

			$sth = $wcms->dbPrepare(<<<EOF
INSERT INTO sessions SET id=?, expire=?, user=?;
EOF
			);
			$res = $sth->execute(array($sid, $expire, $user));
			$wcms->dbCheckRes($res);

			setcookie("session_id", $sid, time() + 3600*24*30);

			return 1;
		} else {
			return 0;
		}
	}

	function deauthenticate() {
		$wcms = $this->wcms;
		$sid = $_COOKIE['session_id'];

		$sth = $wcms->dbPrepare(<<<EOF
DELETE FROM sessions WHERE id=?;
EOF
		);
		$res = $sth->execute(array($sid));
		$wcms->dbCheckRes($res);

		$this->flg_auth = 0;
	}

	function isAuth() {
		return $this->flg_auth;
	}

	function changePassword($cur, $new) {
		$wcms = $this->wcms;
		$u = $this->getUser();

		# check if the current password is correct

		$sth = $wcms->dbPrepare(<<<EOF
SELECT name FROM users WHERE name=? and password=?;
EOF
		);
		$q = $sth->execute(array($u, $cur));
		$ar = $q->fetchAll(ASSOC);
		if(!count($ar)) throw new Exception("неверный текущий пароль");

		# save the new password

		$sth = $wcms->dbPrepare(<<<EOF
UPDATE users SET password=? WHERE name=? LIMIT 1;
EOF
		);
		$res = $sth->execute(array($new, $u));
		$wcms->dbCheckRes($res);
	}
}

?>
