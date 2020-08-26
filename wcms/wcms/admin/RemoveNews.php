<?php


class RemoveNews extends Module
{
	function run() {
		$wcms = $this->wcms;
		$w = $this->Widget = new Container("remove_news");

		$nid = $wcms->Request->getVal('nid');

		try {
			$f = Module::getModule("Admin")->removeNews;
			$f($wcms, $nid);

			$w->addw(new AdminMsgOk(<<<EOF
Новость удалена
<br>
<a href="?module=EditNews">Возврат</a>
EOF
			));
		} catch(Exception $e) {
			$w->addw(new AdminMsgErr("не удалить новость: " . $e->getMessage()));
		}
	}
}

?>
