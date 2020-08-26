<?php

require_once "wcms/Module.php";

class Auth extends Module
{
	function askPassword($again = FALSE) {
		$w = $this->Widget = new Container();
		$w->addw(new Text("<h1>Панель управления: вход</h1>"));
		$w->addw($form = new Form("login_form"));

		$form->addw(new Input("hidden", "pw_sent", "true"));

		$fld1 = new TextField("user", "");
		$fld2 = new PasswordField("password", "");
		$b = new SubmitButton("Войти");

		$form->addw(new LabelAndField(
			"Логин:", $fld1
		));
		$form->addw(new LabelAndField(
			"Пароль:", $fld2
		));
		$form->addw(new LabelAndField(
			"", $b
		));

		if($again) {
			$w->addw(new AdminMsgErr("Пароль указан неверно"));
		}
	}

	function isAuth() {
		$wcms = $this->wcms;

		$logout = $wcms->Request->getVal("logout");
		if($logout) $wcms->Session->deauthenticate();

		if($wcms->Session->isAuth()) {
			return 1;
		} else {
			$pw_sent = $wcms->Request->getVal("pw_sent");
			if($pw_sent) {
				$user = $wcms->Request->getVal("user");
				$password = $wcms->Request->getVal("password");

				$st = $wcms->Session->authenticate($user, $password);
				if($st) return 1;
				else {
					$this->askPassword(TRUE);
				}
			} else {
				$this->askPassword();
				return 0;
			}
			// never reached
		}
	}
}

?>
