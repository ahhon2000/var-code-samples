<?php

require_once "wcms/Module.php";

class ChangePassword extends Module
{
	private function pw_form() {
		$this->Widget->addw(new Text("<h1>Смена пароля</h1>"));
		$this->Widget->addw($form = new Form());

		$form->addw(new Input("hidden", "new_password_sent", "true"));

		$fld1 = new PasswordField("current", "");
		$fld2 = new PasswordField("new", "");
		$fld3 = new PasswordField("confirm", "");
		$b = new SubmitButton("Изменить");
		$b->setClass("save_button");

		$form->addw(new LabelAndField(
			"Текущий пароль", $fld1
		));
		$form->addw(new LabelAndField(
			"Новый пароль", $fld2
		));
		$form->addw(new LabelAndField(
			"Подтверждение", $fld3
		));
		$form->addw(new LabelAndField(
			"", $b
		));
	}

	private function onSubmit() {
		$wcms = $this->wcms;
		$w = $this->Widget;

		$cur = $wcms->Request->getVal("current");
		$new = $wcms->Request->getVal("new");
		$conf = $wcms->Request->getVal("confirm");

		try {
			if($new != $conf)
				throw new Exception("неверное подтверждение");
			$wcms->Session->changePassword($cur, $new);

			$w->addw(new AdminMsgOk("Пароль успешно изменен"));
		} catch(Exception $e) {
			$w->addw(new AdminMsgErr("пароль не был изменен: " .
				$e->getMessage()));
		}
	}

	function run() {
		$wcms = $this->wcms;
		$this->Widget = new Container("change_password");

		$new_password_sent = $wcms->Request->getVal("new_password_sent");
		if($new_password_sent) {
			$this->onSubmit();
		} else {
			$this->pw_form();
		}
	}
}

?>
