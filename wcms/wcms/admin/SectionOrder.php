<?php

class SectionOrder extends Module
{
	private function show($w) {
		$wcms = $this->wcms;
		$w->addw(new Text("<h1>Порядок разделов</h1>"));
		$w->addw(new AdminMsg("Установите порядок разделов:"));

		try {
			$f = Module::getModule("Admin")->getSectionOrder;
			$f($wcms, $ids, $orders, $titles);

			$w->addw($form = new Form());
			$form->addw(new Input("hidden", "section_order_sent",
				"true"));
			$form->addw($cont = new SelectOrder("orders",
				$orders, $titles, $orders[0], "myselector"));
			$form->addw(new Text("<br><br>"));
			$form->addw($b = new SubmitButton("Сохранить"));
			$b->setClass("save_button");
		} catch(Exception $e) {
			$w->add(new AdminMsgErr("не удалось получить информацию о разделах" . $e->getMessage()));
		}
	}

	private function saveOrder($w) {
		$wcms = $this->wcms;
		$orders = explode(',', $wcms->Request->getVal("orders"));
		try {
			$f = Module::getModule("Admin")->setSectionOrder;
			$f($wcms, $orders);
		} catch(Exception $e) {
			$w->addw(new AdminMsgErr("не удалось установить новый порядок разделов: " . $e->getMessage()));
		}
	}

	function run() {
		$w = $this->Widget = new Container("section_order");
		$wcms = $this->wcms;

		$submit = $wcms->Request->getVal("section_order_sent");
		if($submit) {
			$this->saveOrder($w);
		}
		$this->show($w);
	}
}

?>
