<?php

require_once "wcms/wcms.php";

class Module
{
	public $Widget = NULL;
	protected $wcms = NULL;

	static private $loaded_modules = array();
	static private $module_files = array(
		"Admin" => "wcms/admin/Admin.php",
		"Editor" => "wcms/admin/Editor.php",
		"ChooseSection" => "wcms/admin/ChooseSection.php",
		"ChooseAction" => "wcms/admin/ChooseAction.php",
		"AddSection" => "wcms/admin/AddSection.php",
		"RemoveSection" => "wcms/admin/RemoveSection.php",
		"Auth" => "wcms/admin/Auth.php",
		"ChangePassword" => "wcms/admin/ChangePassword.php",
		"ChooseMenu" => "wcms/admin/ChooseMenu.php",
		"EditMenu" => "wcms/admin/EditMenu.php",
		"AddMenu" => "wcms/admin/AddMenu.php",
		"RemoveMenu" => "wcms/admin/RemoveMenu.php",
		"SectionOrder" => "wcms/admin/SectionOrder.php",
		"EditKeywords" => "wcms/admin/EditKeywords.php",
		"EditSectionKeywords" => "wcms/admin/EditSectionKeywords.php",
		"ChooseNews" => "wcms/admin/ChooseNews.php",
		"EditNews" => "wcms/admin/EditNews.php",
		"RemoveNews" => "wcms/admin/RemoveNews.php",
	);

	function __construct(WCMS $wcms) {
		$this->wcms = $wcms;
	}

	static function getModFile($mod) {
		!isset(self::$module_files[$mod]) and
			die("module `$mod' is unavailable");

		return self::$module_files[$mod];
	}

	static function getModule($name) {
		isset(self::$loaded_modules[$name]) or
			die("module `$name' is not loaded");

		return self::$loaded_modules[$name];
	}

	static function load($name, WCMS $wcms) {
		!isset(self::$loaded_modules[$name]) or
			die("module `$name' was loaded earlier");

		$file = self::getModFile($name);
		if(file_exists($file)) {
			require_once "$file";
		} else {
			die("can't load module `$name': file not found");
		}

		$mod = new $name($wcms);
		self::$loaded_modules[$name] = $mod;

		return $mod;
	}

	function setCallbacks($arr) {
		foreach($arr as $cb => $f) {
			isset($this->$cb) or die("no such callback: $cb");
			$this->$cb = $f;
		}
	}
}

?>
