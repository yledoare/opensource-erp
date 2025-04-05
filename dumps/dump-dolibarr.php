<?php
/*
 * Copyright (C) 2012 Nicolas Villa aka Boyquotes http://informetic.fr
 * Copyright (C) 2013 Florian Henry <forian.henry@open-concept.pro
 * Copyright (C) 2013-2015 Laurent Destailleur <eldy@users.sourceforge.net>
 * Copyright (C) 2025 Yann Le Doaré aka Yledoare https://adn-bzh.org
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 */

/**
 * \file scripts/dump/dump.php
 * \ingroup cron
 * \brief Execute pendings jobs from command line
 */

if (!defined('NOTOKENRENEWAL')) {
	define('NOTOKENRENEWAL', '1'); // Disables token renewal
}
if (!defined('NOREQUIREMENU')) {
	define('NOREQUIREMENU', '1');
}
if (!defined('NOREQUIREHTML')) {
	define('NOREQUIREHTML', '1');
}
if (!defined('NOREQUIREAJAX')) {
	define('NOREQUIREAJAX', '1');
}
if (!defined('NOLOGIN')) {
	define('NOLOGIN', '1');
}
if (!defined('NOSESSION')) {
	define('NOSESSION', '1');
}

// So log file will have a suffix
if (!defined('USESUFFIXINLOG')) {
	define('USESUFFIXINLOG', '_cron');
}

$sapi_type = php_sapi_name();
$script_file = basename(__FILE__);
$path = __DIR__.'/';

// Error if Web mode
if (substr($sapi_type, 0, 3) == 'cgi') {
	echo "Error: You are using PHP for CGI. To execute ".$script_file." from command line, you must use PHP for CLI mode.\n";
	exit(1);
}
if(is_file($path."../../htdocs/master.inc.php"))
{
	# Run from scripts
	require_once $path."../../htdocs/master.inc.php";
}
else
{
	# Run from root, not recommended
	if(is_file($path."./master.inc.php"))
		require_once $path."./master.inc.php";
	else
		die("master.inc.php not found");
}

require_once DOL_DOCUMENT_ROOT."/cron/class/cronjob.class.php";
require_once DOL_DOCUMENT_ROOT.'/user/class/user.class.php';

// Global variables
$version = DOL_VERSION;
$error = 0;

$hookmanager->initHooks(array('cli'));


/*
 * Main
 */

// current date
$now = dol_now();

@set_time_limit(0);
print "***** ".$script_file." (".$version.") pid=".dol_getmypid()." - ".dol_print_date($now, 'dayhourrfc', 'gmt')." - ".gethostname()." *****\n";

// Show TZ of the serveur when ran from command line.
$ini_path = php_ini_loaded_file();
print 'TZ server = '.getServerTimeZoneString()." - set in PHP ini ".$ini_path."\n";

if (!empty($dolibarr_main_db_readonly)) {
	print "Error: instance in read-only mode\n";
	exit(1);
}


$dumpdir= __DIR__ . "/../dumps/";
if(!is_dir($dumpdir))
{
	echo "Create $dumpdir";
	mkdir($dumpdir,0700);
}
if(!is_dir($dumpdir)) exit(1);

$dumpfile=$dumpdir . $dolibarr_main_db_name . "-" . date('dmY') . ".sql";
echo "Dumping $dolibarr_main_db_name ...";
if(is_file($dumpfile.".gz")) unlink(($dumpfile.".gz"));
$mysql_tables="mysql $dolibarr_main_db_name -u $dolibarr_main_db_user -p$dolibarr_main_db_pass -h $dolibarr_main_db_host -N -e 'show tables like \"$dolibarr_main_db_prefix%\"'"; 

$dump = "$mysql_tables | xargs mysqldump -u" . $dolibarr_main_db_user . " -p" . $dolibarr_main_db_pass . " -h" . $dolibarr_main_db_host . " " . $dolibarr_main_db_name . " > " . $dumpfile;
echo exec($dump);
echo exec("gzip $dumpfile");

if(is_file($dumpfile.".gz"))
	echo "Success";
else
	echo "$dump Failed";
//echo $dump;
