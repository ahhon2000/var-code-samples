<?php

require_once 'wcms/wcms.php';

function onRequest(WCMS $wcms) {
	$pg = $wcms->getPage();

	$pg->setTitle("Testing Wcms");

	$pg->addw($cont = new ContainerCol("container"));
	$pg->addStyle("style.css");

	$cont->addw($lc = new Container("leftColumn"));
	$cont->addw(new Text("Middle Column"));
	$cont->addw(new Text("Right Column"));
	$cont->setWidths("20%", "60%", "20%");

	$lc->addw($m = new Menu());
	$m->addw(new MenuItem("mail.com", "http://mail.com"));
	$m->addw(new MenuItem("google.com", "http://google.com"));
	$m->addw($mi = new MenuItem("Other Links", ""));

	$mi->addw($mm = new Menu());
	$mm->addw(new MenuItem("mail.ru", "http://mail.ru"));
	$mm->addw(new MenuItem("yandex.ru", "http://yandex.ru"));
}

$wcms = new WCMS();
$wcms->setOnRequest("onRequest");
$wcms->run();

?>
