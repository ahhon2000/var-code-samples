<?php

require_once "wcms.php";

class ClientSession
{
	const expir_interval = 0; # seconds, 0 is infinity
	const sid_characters = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
	const sid_length = 64;

	private $wcms = NULL;
	private $flg_auth = 0;
	private $clientEmail = '';


	function __construct(WCMS $wcms) {
		$this->wcms = $wcms;

		# delete expired client_sessions from the database

		if(self::expir_interval) {
			$sth = $wcms->dbPrepare(<<<EOF
DELETE FROM client_sessions WHERE expire<?;
EOF
			);
			$res = $sth->execute(array(time()));
			$wcms->dbCheckRes($res);
		}

		# check if the user is authenticated, update expiration date

		if(isset($_COOKIE['client_session_id'])) {
			$sid = $_COOKIE['client_session_id'];
			$sth = $wcms->dbPrepare(<<<EOF
SELECT id FROM client_sessions WHERE id=?;
EOF
			);
			$q = $sth->execute(array($sid));
			$ar = $q->fetchAll(ASSOC);
			if(count($ar)) {
				$this->flg_auth = 1;

				# update expiration date

				if(self::expir_interval) {
					$expire = time() + self::expir_interval;
					$sth = $wcms->dbPrepare(<<<EOF
UPDATE client_sessions SET expire=? WHERE id=? LIMIT 1;
EOF
					);
					$res=$sth->execute(array($expire,$sid));
				} // if
			} // if
		}// if
	} // __construct()

	function getClientEmail() {
		$wcms = $this->wcms;

		if($this->clientEmail != '') {
			return $this->clientEmail;
		} else {
			$sid = '';
			if(isset($_COOKIE['client_session_id'])) {
				$sid = $_COOKIE['client_session_id'];
			}

			$sth = $wcms->dbPrepare(<<<EOF
SELECT email FROM client_sessions WHERE id=?;
EOF
			);
			$q = $sth->execute(array($sid));
			$ar = $q->fetchAll(ASSOC);

			if(!count($ar)) throw New Exception("Проблемы с подключением. Неопознанная сессия");

			return $ar[0]['email'];
		}
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

	private function passwordOk($email, $pw) {
		$wcms = $this->wcms;

		$sth = $wcms->dbPrepare(<<<EOF
SELECT email FROM clients WHERE email=? and password=?;
EOF
		);
		$q = $sth->execute(array($email, $pw));
		$ar = $q->fetchAll(ASSOC);

		if(count($ar)) {
			return 1;
		} else {
			return 0;
		}
	}

	// try to make the client authenticated, return non-zero on success
	function authenticate($email, $pw) {
		$wcms = $this->wcms;

		if($this->passwordOk($email, $pw)) {
			$sid = $this->generateSid();

			$expire = 0;
			if(self::expir_interval) {
				$expire = time() + self::expir_interval;
			}

			$sth = $wcms->dbPrepare(<<<EOF
INSERT INTO client_sessions SET id=?, expire=?, email=?;
EOF
			);
			$res = $sth->execute(array($sid, $expire, $email));
			$wcms->dbCheckRes($res);

			setcookie("client_session_id", $sid, time() + 3600*24*365*10);

			$this->clientEmail = $email;
			$this->flg_auth = 1;
			return 1;
		} else {
			$this->flg_auth = 0;
			return 0;
		}
	}

	function deauthenticate() {
		$wcms = $this->wcms;

		if(isset($_COOKIE['client_session_id'])) {
			$sid = $_COOKIE['client_session_id'];

			$sth = $wcms->dbPrepare(<<<EOF
DELETE FROM client_sessions WHERE id=?;
EOF
			);
			$res = $sth->execute(array($sid));
			$wcms->dbCheckRes($res);
		}

		$this->flg_auth = 0;
	}

	function isAuth() {
		return $this->flg_auth;
	}

	function changePassword($cur, $new) {
		$wcms = $this->wcms;
		$u = $this->getClientEmail();

		# check if the current password is correct

		$sth = $wcms->dbPrepare(<<<EOF
SELECT email FROM clients WHERE email=? and password=?;
EOF
		);
		$q = $sth->execute(array($u, $cur));
		$ar = $q->fetchAll(ASSOC);
		if(!count($ar)) throw new Exception("неверный текущий пароль");

		# save the new password

		$sth = $wcms->dbPrepare(<<<EOF
UPDATE clients SET password=? WHERE email=? LIMIT 1;
EOF
		);
		$res = $sth->execute(array($new, $u));
		$wcms->dbCheckRes($res);
	}

	function setMixout($mo) {
		$self->mo = $mo;
	}
}

?>
