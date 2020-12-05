#!/usr/bin/env python3
# -*- coding: utf8 -*-

import sys
import os
import re
import json
import shlex
import urllib.request
import codecs
import subprocess
import time
import statistics
from datetime import datetime

reader = codecs.getreader("utf-8")

# ############################################################################
#  Helper list
# ############################################################################

# Generated May 21st using:
# cat /path/to/yunohost/data/helpers.d/* | grep  "^ynh_" | tr -d '(){ ' > helperlist
# for HELPER in $(cat helperlist); do REQUIRE=$(grep -whB5 "^$HELPER" /path/to/yunohost/data/helpers.d/* | grep "Requires .* or higher\." | grep -o -E "[0-9].[0-9].[0-9]"); echo "'$HELPER': '$REQUIRE'",; done

official_helpers = {
    'ynh_wait_dpkg_free': '3.3.1',
    'ynh_package_is_installed': '2.2.4',
    'ynh_package_version': '2.2.4',
    'ynh_apt': '2.4.0',
    'ynh_package_update': '2.2.4',
    'ynh_package_install': '2.2.4',
    'ynh_package_remove': '2.2.4',
    'ynh_package_autoremove': '2.2.4',
    'ynh_package_autopurge': '2.7.2',
    'ynh_package_install_from_equivs': '2.2.4',
    'ynh_install_app_dependencies': '2.6.4',
    'ynh_add_app_dependencies': '3.8.1',
    'ynh_remove_app_dependencies': '2.6.4',
    'ynh_install_extra_app_dependencies': '3.8.1',
    'ynh_install_extra_repo': '3.8.1',
    'ynh_remove_extra_repo': '3.8.1',
    'ynh_add_repo': '3.8.1',
    'ynh_pin_repo': '3.8.1',
    'ynh_backup': '2.4.0',
    'ynh_restore': '2.6.4',
    'ynh_restore_file': '2.6.4',
    'ynh_bind_or_cp': '',
    'ynh_store_file_checksum': '2.6.4',
    'ynh_backup_if_checksum_is_different': '2.6.4',
    'ynh_delete_file_checksum': '3.3.1',
    'ynh_backup_before_upgrade': '2.7.2',
    'ynh_restore_upgradebackup': '2.7.2',
    'ynh_add_fail2ban_config': '3.5.0',
    'ynh_remove_fail2ban_config': '3.5.0',
    'ynh_handle_getopts_args': '3.2.2',
    'ynh_get_ram': '3.8.1',
    'ynh_require_ram': '3.8.1',
    'ynh_die': '2.4.0',
    'ynh_print_info': '3.2.0',
    'ynh_no_log': '2.6.4',
    'ynh_print_log': '3.2.0',
    'ynh_print_warn': '3.2.0',
    'ynh_print_err': '3.2.0',
    'ynh_exec_err': '3.2.0',
    'ynh_exec_warn': '3.2.0',
    'ynh_exec_warn_less': '3.2.0',
    'ynh_exec_quiet': '3.2.0',
    'ynh_exec_fully_quiet': '3.2.0',
    'ynh_print_OFF': '3.2.0',
    'ynh_print_ON': '3.2.0',
    'ynh_script_progression': '3.5.0',
    'ynh_return': '3.6.0',
    'ynh_debug': '3.5.0',
    'ynh_debug_exec': '3.5.0',
    'ynh_use_logrotate': '2.6.4',
    'ynh_remove_logrotate': '2.6.4',
    'ynh_mysql_connect_as': '2.2.4',
    'ynh_mysql_execute_as_root': '2.2.4',
    'ynh_mysql_execute_file_as_root': '2.2.4',
    'ynh_mysql_create_db': '2.2.4',
    'ynh_mysql_drop_db': '2.2.4',
    'ynh_mysql_dump_db': '2.2.4',
    'ynh_mysql_create_user': '2.2.4',
    'ynh_mysql_user_exists': '2.2.4',
    'ynh_mysql_drop_user': '2.2.4',
    'ynh_mysql_setup_db': '2.6.4',
    'ynh_mysql_remove_db': '2.6.4',
    'ynh_find_port': '2.6.4',
    'ynh_port_available': '3.8.0',
    'ynh_validate_ip': '2.2.4',
    'ynh_validate_ip4': '2.2.4',
    'ynh_validate_ip6': '2.2.4',
    'ynh_add_nginx_config': '2.7.2',
    'ynh_remove_nginx_config': '2.7.2',
    'ynh_install_n': '2.7.1',
    'ynh_use_nodejs': '2.7.1',
    'ynh_install_nodejs': '2.7.1',
    'ynh_remove_nodejs': '2.7.1',
    'ynh_cron_upgrade_node': '2.7.1',
    'ynh_add_fpm_config': '2.7.2',
    'ynh_remove_fpm_config': '2.7.2',
    'ynh_install_php': '3.8.1',
    'ynh_remove_php': '3.8.1',
    'ynh_get_scalable_phpfpm': '',
    'ynh_psql_connect_as': '3.5.0',
    'ynh_psql_execute_as_root': '3.5.0',
    'ynh_psql_execute_file_as_root': '3.5.0',
    'ynh_psql_create_db': '3.5.0',
    'ynh_psql_drop_db': '3.5.0',
    'ynh_psql_dump_db': '3.5.0',
    'ynh_psql_create_user': '3.5.0',
    'ynh_psql_user_exists': '3.5.0',
    'ynh_psql_database_exists': '3.5.0',
    'ynh_psql_drop_user': '3.5.0',
    'ynh_psql_setup_db': '2.7.1',
    'ynh_psql_remove_db': '2.7.1',
    'ynh_psql_test_if_first_run': '2.7.1',
    'ynh_app_setting_get': '2.2.4',
    'ynh_app_setting_set': '2.2.4',
    'ynh_app_setting_delete': '2.2.4',
    'ynh_app_setting': '',
    'ynh_webpath_available': '2.6.4',
    'ynh_webpath_register': '2.6.4',
    'ynh_permission_create': '3.7.0',
    'ynh_permission_delete': '3.7.0',
    'ynh_permission_exists': '3.7.0',
    'ynh_permission_url': '3.7.0',
    'ynh_permission_update': '3.7.0',
    'ynh_permission_has_user': '3.7.1',
    'ynh_string_random': '2.2.4',
    'ynh_replace_string': '2.6.4',
    'ynh_replace_special_string': '2.7.7',
    'ynh_sanitize_dbid': '2.2.4',
    'ynh_normalize_url_path': '2.6.4',
    'ynh_add_systemd_config': '2.7.1',
    'ynh_remove_systemd_config': '2.7.2',
    'ynh_systemd_action': '3.5.0',
    'ynh_clean_check_starting': '3.5.0',
    'ynh_user_exists': '2.2.4',
    'ynh_user_get_info': '2.2.4',
    'ynh_user_list': '2.4.0',
    'ynh_system_user_exists': '2.2.4',
    'ynh_system_group_exists': '3.5.0',
    'ynh_system_user_create': '2.6.4',
    'ynh_system_user_delete': '2.6.4',
    'ynh_exit_properly': '2.6.4',
    'ynh_abort_if_errors': '2.6.4',
    'ynh_setup_source': '2.6.4',
    'ynh_local_curl': '2.6.4',
    'ynh_render_template': '',
    'ynh_get_debian_release': '2.7.1',
    'ynh_mkdir_tmp': '',
    'ynh_secure_remove': '2.6.4',
    'ynh_get_plain_key': '2.2.4',
    'ynh_read_manifest': '3.5.0',
    'ynh_app_upstream_version': '3.5.0',
    'ynh_app_package_version': '3.5.0',
    'ynh_check_app_version_changed': '3.5.0',
}


# ############################################################################
#   Utilities
# ############################################################################

class c:
    HEADER = '\033[94m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    MAYBE_FAIL = '\033[96m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class TestReport:

    def __init__(self, message):
        self.message = message

    def display(self):
        _print(self.style % self.message)

class Warning(TestReport):
    style = c.WARNING + " ! %s " + c.END

class Error(TestReport):
    style = c.FAIL + " ✘ %s" + c.END

class Info(TestReport):
    style = " ⓘ  %s" + c.END

class Success(TestReport):
    style = c.OKGREEN + " ☺  %s ♥" + c.END

class Critical(TestReport):
    style = c.FAIL + " ✘✘✘ %s" + c.END

def header(app):
    _print("""
    [{header}{bold}YunoHost App Package Linter{end}]

 App packaging documentation - https://yunohost.org/#/packaging_apps
 App package example         - https://github.com/YunoHost/example_ynh
 Official helpers            - https://yunohost.org/#/packaging_apps_helpers_en
 Experimental helpers        - https://github.com/YunoHost-Apps/Experimental_helpers

 If you believe this linter returns false negative (warnings / errors which shouldn't happen),
 please report them on https://github.com/YunoHost/package_linter/issues

    Analyzing package {header}{app}{end}"""
    .format(header=c.HEADER, bold=c.BOLD, end=c.END, app=app))


output = "plain"


def _print(*args, **kwargs):
    if output == "plain":
        print(*args, **kwargs)


def print_header(str):
    _print("\n [" + c.BOLD + c.HEADER + str.title() + c.END + "]\n")


def report_warning_not_reliable(str):
    _print(c.MAYBE_FAIL + "?", str, c.END)




def print_happy(str):
    _print(c.OKGREEN + " ☺ ", str, "♥")


def urlopen(url):
    try:
        conn = urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        return {'content': '', 'code': e.code}
    except urllib.error.URLError as e:
        _print('Could not fetch %s : %s' % (url, e))
        return {'content': '', 'code': 0}
    return {'content': conn.read().decode('UTF8'), 'code': 200}


def file_exists(file_path):
    return os.path.isfile(file_path) and os.stat(file_path).st_size > 0


def spdx_licenses():
    cachefile = ".spdx_licenses"
    if os.path.exists(cachefile) and time.time() - os.path.getmtime(cachefile) < 3600:
        return open(cachefile).read()

    url = "https://spdx.org/licenses/"
    content = urlopen(url)['content']
    open(cachefile, "w").write(content)
    return content

tests = {}
tests_reports = {
    "success": [],
    "info": [],
    "warning": [],
    "error": [],
    "critical": [],
}

def test(**kwargs):
    def decorator(f):
        clsname = f.__qualname__.split(".")[0]
        if clsname not in tests:
            tests[clsname] = []
        tests[clsname].append((f,kwargs))
        return f
    return decorator

class TestSuite():

    def run_tests(self):
        for test, options in tests[self.__class__.__name__]:
            if "only" in options and self.name not in options["only"]:
                continue
            if "ignore" in options and self.name in options["ignore"]:
                continue
            self.run_single_test(test)

    def run_single_test(self, test):

        reports = list(test(self))
        for report in reports:
            if output == "plain":
                report.display()
            report_type = report.__class__.__name__.lower()
            test_name = test.__qualname__
            tests_reports[report_type].append((test_name, report))

# ############################################################################
#   Actual high-level checks
# ############################################################################

scriptnames = ["_common.sh", "install", "remove", "upgrade", "backup", "restore"]


class App(TestSuite):

    def __init__(self, path):

        print_header("LOADING APP")
        self.path = path
        self.manifest_ = Manifest(self.path)
        self.manifest = self.manifest_.manifest
        self.scripts = {f: Script(self.path, f) for f in scriptnames}
        self.configurations = Configurations(self)
        self.app_catalog = AppCatalog(self.manifest["id"])

    def analyze(self):

        print_header("MANIFEST")
        self.manifest_.run_tests()

        for script in [self.scripts[s] for s in scriptnames if self.scripts[s].exists]:
            print_header(script.name.upper() + " SCRIPT")
            script.run_tests()

        print_header("GENERAL STUFF, MISC HELPER USAGE")
        self.run_tests()

        print_header("CONFIGURATIONS")
        self.configurations.run_tests()

        print_header("APP CATALOG")
        self.app_catalog.run_tests()

        self.report()

    def report(self):

        # These are meant to be the last stuff running, they are based on
        # previously computed errors/warning/successes
        self.run_single_test(App.qualify_for_level_7)
        self.run_single_test(App.qualify_for_level_8)

        if output == "json":
            print(json.dumps({
                "success": [test for test, _ in tests_reports["success"]],
                "info": [test for test, _ in tests_reports["info"]],
                "warning": [test for test, _ in tests_reports["warning"]],
                "error": [test for test, _ in tests_reports["error"]],
                "critical": [test for test, _ in tests_reports["critical"]],
            }, indent=4))
            return

        if tests_reports["error"] or tests_reports["critical"]:
            sys.exit(1)

    def qualify_for_level_7(self):

        if tests_reports["critical"]:
            _print(" There are some critical issues in this app :(")
        elif tests_reports["error"]:
            _print(" Uhoh there are some errors to be fixed :(")
        elif len(tests_reports["warning"]) > 3:
            _print(" Still some warnings to be fixed :s")
        elif len(tests_reports["warning"]) > 0:
            _print(" Only %s warning remaining! You can do it!" % len(tests_reports["warning"]))
        else:
            yield Success("Not even a warning! Congratz and thank you for keeping that package up to date with good practices! This app qualifies for level 7!")

    def qualify_for_level_8(self):

        successes = [test.split(".")[1] for test, _ in tests_reports["success"]]

        # Level 8 = qualifies for level 7 + maintained + long term good quality
        catalog_infos = self.app_catalog.catalog_infos
        is_maintained = catalog_infos and catalog_infos.get("maintained", True) is True
        if not is_maintained:
            _print(" The app is flagged as not maintained in the app catalog")
        elif "qualify_for_level_7" in successes and "is_long_term_good_quality" in successes:
            yield Success("The app is maintained and long-term good quality, and therefore qualifies for level 8!")

    #########################################
    #   _____                           _   #
    #  |  __ \                         | |  #
    #  | |  \/ ___ _ __   ___ _ __ __ _| |  #
    #  | | __ / _ \ '_ \ / _ \ '__/ _` | |  #
    #  | |_\ \  __/ | | |  __/ | | (_| | |  #
    #   \____/\___|_| |_|\___|_|  \__,_|_|  #
    #                                       #
    #########################################

    @test()
    def mandatory_scripts(app):
        filenames = ("manifest.json", "LICENSE", "README.md",
                     "scripts/install", "scripts/remove",
                     "scripts/upgrade",
                     "scripts/backup", "scripts/restore")

        for filename in filenames:
            if not file_exists(app.path + "/" + filename):
                yield Error("Providing %s is mandatory" % filename)

    @test()
    def change_url_script(app):

        has_domain_arg = any(a["name"] == "is_public" for a in app.manifest["arguments"].get("install", []))
        if has_domain_arg and not file_exists(app.path + "/scripts/change_url"):
            yield Warning("Consider adding a change_url script to support changing where the app is installed")

    @test()
    def badges_in_readme(app):

        id_ = app.manifest["id"]

        if not file_exists(app.path + "/README.md"):
            return

        content = open(app.path + "/README.md").read()

        if not "dash.yunohost.org/integration/%s.svg" % id_ in content:
            yield Warning(
                "Please add a badge displaying the level of the app in the README.  "
                "At least something like :\n   "
                "[![Integration level](https://dash.yunohost.org/integration/%s.svg)](https://dash.yunohost.org/appci/app/%s)\n"
                "  (but ideally you should check example_ynh for the full set of recommendations !)"
                % (id_, id_)
            )



    #######################################
    #  _    _      _                      #
    # | |  | |    | |                     #
    # | |__| | ___| |_ __   ___ _ __ ___  #
    # |  __  |/ _ \ | '_ \ / _ \ '__/ __| #
    # | |  | |  __/ | |_) |  __/ |  \__ \ #
    # |_|  |_|\___|_| .__/ \___|_|  |___/ #
    #               | |                   #
    #               |_|                   #
    #######################################

    @test()
    def helpers_now_official(app):

        cmd = "grep -IhEro 'ynh_\w+ *\( *\)' '%s/scripts' | tr -d '() '" % app.path
        custom_helpers = subprocess.check_output(cmd, shell=True).decode('utf-8').strip().split("\n")
        custom_helpers = [c.split("__")[0] for c in custom_helpers]

        for custom_helper in custom_helpers:
            if custom_helper in official_helpers.keys():
                yield Info("%s is now an official helper since version '%s'" % (custom_helper, official_helpers[custom_helper] or '?'))

    @test()
    def helpers_version_requirement(app):

        cmd = "grep -IhEro 'ynh_\w+ *\( *\)' '%s/scripts' | tr -d '() '" % app.path
        custom_helpers = subprocess.check_output(cmd, shell=True).decode('utf-8').strip().split("\n")
        custom_helpers = [c.split("__")[0] for c in custom_helpers]

        yunohost_version_req = app.manifest.get("requirements", {}).get("yunohost", "").strip(">= ")

        cmd = "grep -IhEro 'ynh_\w+' '%s/scripts'" % app.path
        helpers_used = subprocess.check_output(cmd, shell=True).decode('utf-8').strip().split("\n")
        helpers_used = sorted(set(helpers_used))

        manifest_req = [int(i) for i in yunohost_version_req.split('.')] + [0,0,0]
        def validate_version_requirement(helper_req):
            if helper_req == '':
                return True
            helper_req = [int(i) for i in helper_req.split('.')]
            for i in range(0,len(helper_req)):
                if helper_req[i] == manifest_req[i]:
                    continue
                return helper_req[i] <= manifest_req[i]
            return True

        for helper in [h for h in helpers_used if h in official_helpers.keys()]:
            if helper in custom_helpers:
                continue
            helper_req = official_helpers[helper]
            if not validate_version_requirement(helper_req):
                major_diff = manifest_req[0] > int(helper_req[0])
                minor_diff = helper_req.startswith(yunohost_version_req)  # This is meant to cover the case where manifest says "3.8" vs. the helper requires "3.8.1"
                message = "Using official helper %s implies requiring at least version %s, but manifest only requires %s" % (helper, helper_req, yunohost_version_req)
                yield Error(message) if major_diff else (Info(message) if minor_diff else Warning(message))


    @test()
    def helper_consistency_apt_deps(app):
        """
        check if ynh_install_app_dependencies is present in install/upgrade/restore
        so dependencies are up to date after restoration or upgrade
        """

        install_script = app.scripts["install"]
        if install_script.contains("ynh_install_app_dependencies"):
            for name in ["upgrade", "restore"]:
                if app.scripts[name].exists and not app.scripts[name].contains("ynh_install_app_dependencies"):
                    yield Warning("ynh_install_app_dependencies should also be in %s script" % name)

    @test()
    def helper_consistency_service_add(app):

        occurences = {
            "install": app.scripts["install"].occurences("yunohost service add") if app.scripts["install"].exists else [],
            "upgrade": app.scripts["upgrade"].occurences("yunohost service add") if app.scripts["upgrade"].exists else [],
            "restore": app.scripts["restore"].occurences("yunohost service add") if app.scripts["restore"].exists else [],
        }

        occurences = {k: [sub_v.replace('"$app"', '$app') for sub_v in v] for k, v in occurences.items()}

        all_occurences = occurences["install"] + occurences["upgrade"] + occurences["restore"]
        found_inconsistency = False
        found_legacy_logtype_option = False
        for cmd in all_occurences:
            if any(cmd not in occurences_list for occurences_list in occurences.values()):
                found_inconsistency = True
            if "--log_type systemd" in cmd:
                found_legacy_logtype_option = True

        if found_inconsistency:
            details = [("   %s : " % script + ''.join("\n      " + cmd for cmd in occurences[script] or ["...None?..."]))
                       for script in occurences.keys()]
            details = '\n'.join(details)
            yield Warning("Found some inconsistencies in the 'yunohost service add' commands between install, upgrade and restore:\n%s" % details)

        if found_legacy_logtype_option:
            yield Info("Using option '--log_type systemd' with 'yunohost service add' is not relevant anymore")

        if occurences["install"] and not app.scripts["remove"].contains("yunohost service remove"):
            yield Error(
                "You used 'yunohost service add' in the install script, "
                "but not 'yunohost service remove' in the remove script."
            )

    @test()
    def helper_consistency_firewall(app):
        install_script = app.scripts["install"]
        if install_script.contains("yunohost firewall allow"):
            if not install_script.contains("--needs_exposed_ports"):
                yield Warning("The install script expose a port on the outside with 'yunohost firewall allow' but doesn't use 'yunohost service add' with --needs_exposed_ports ... If your are ABSOLUTELY SURE that the service needs to be exposed on THE OUTSIDE, then add --needs_exposed_ports to 'yunohost service add' with the relevant port number. Otherwise, opening the port leads to a significant security risk and you should keep the damn port closed !")

    @test()
    def references_to_old_php_versions(app):
        if any(script.contains("/etc/php5") or script.contains("php5-fpm") for script in app.scripts.values() if script.exists):
            yield Warning("This app still has references to php5 (from the jessie era !!) which tends to indicate that it's not up to date with recent packaging practices.")


class Configurations(TestSuite):

    def __init__(self, app):

        self.app = app

    ############################
    #    _____             __  #
    #   / ____|           / _| #
    #  | |     ___  _ __ | |_  #
    #  | |    / _ \| '_ \|  _| #
    #  | |___| (_) | | | | |   #
    #   \_____\___/|_| |_|_|   #
    #                          #
    ############################

    @test()
    def check_process_exists(self):

        app = self.app

        check_process_file = app.path + "/check_process"

        if not file_exists(check_process_file):
            yield Warning("You should add a 'check_process' file to properly interface with the continuous integration system")

    @test()
    def check_process_syntax(self):

        app = self.app

        check_process_file = app.path + "/check_process"
        if not file_exists(check_process_file):
            return

        if os.system("grep -q 'Level 5=1' '%s'" % check_process_file) == 0:
            yield Error("Do not force Level 5=1 in check_process...")

        if os.system("grep -q ' *Level [^5]=' '%s'" % check_process_file) == 0:
            yield Info("Setting Level x=y in check_process is obsolete / not relevant anymore")

    @test()
    def check_process_consistency(self):

        app = self.app

        check_process_file = app.path + "/check_process"
        if not file_exists(check_process_file):
            return

        has_is_public_arg = any(a["name"] == "is_public" for a in app.manifest["arguments"].get("install", []))
        if has_is_public_arg:
            if os.system(r"grep -q '^\s*setup_public=1' '%s'" % check_process_file) != 0:
                yield Info("It looks like you forgot to enable setup_public test in check_process ?")

            if os.system(r"grep -q '^\s*setup_private=1' '%s'" % check_process_file) != 0:
                yield Info("It looks like you forgot to enable setup_private test in check_process ?")

        has_path_arg = any(a["name"] == "path" for a in app.manifest["arguments"].get("install", []))
        if has_path_arg:
            if os.system(r"grep -q '^\s*setup_sub_dir=1' '%s'" % check_process_file) != 0:
                yield Info("It looks like you forgot to enable setup_sub_dir test in check_process ?")

        if app.manifest.get("multi_instance") in [True, 1, "True", "true"]:
            if os.system(r"grep -q '^\s*multi_instance=1' '%s'" % check_process_file) != 0:
                yield Info("It looks like you forgot to enable multi_instance test in check_process ?")

        if app.scripts["backup"].exists:
            if os.system(r"grep -q '^\s*backup_restore=1' '%s'" % check_process_file) != 0:
                yield Info("It looks like you forgot to enable backup_restore test in check_process ?")

    @test()
    def misc_legacy_phpini(self):

        app = self.app

        if file_exists(app.path + "/conf/php-fpm.ini"):
            yield Error(
                "Using a separate php-fpm.ini file is deprecated. "
                "Please merge your php-fpm directives directly in the pool file. "
                "(c.f. https://github.com/YunoHost-Apps/nextcloud_ynh/issues/138 )"
            )

    @test()
    def misc_source_management(self):

        app = self.app

        source_dir = os.path.join(app.path, "sources")
        if os.path.exists(source_dir) \
           and len([name for name in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, name))]) > 5:
            yield Error(
                "Upstream app sources shouldn't be stored in this 'sources' folder of this git repository as a copy/paste\n"
                "During installation, the package should download sources from upstream via 'ynh_setup_source'.\n"
                "See the helper documentation. "
                "Original discussion happened here : "
                "https://github.com/YunoHost/issues/issues/201#issuecomment-391549262"
            )

    @test()
    def src_file_checksum_type(self):

        app = self.app
        for filename in os.listdir(app.path + "/conf") if os.path.exists(app.path + "/conf") else []:
            if not filename.endswith(".src"):
                continue

            try:
                content = open(app.path + "/conf/" + filename).read()
            except Exception as e:
                yield Warning("Can't open/read %s : %s" % (filename, e))
                return

            if "SOURCE_SUM_PRG=md5sum" in content:
                yield Info("%s: Using md5sum checksum is not so great for "
                        "security. Consider using sha256sum instead." % filename)


    @test()
    def systemd_config_specific_user(self):

        app = self.app
        for filename in os.listdir(app.path + "/conf") if os.path.exists(app.path + "/conf") else []:
            # Ignore subdirs or filename not containing nginx in the name
            if not filename.endswith(".service"):
                continue

            # Some apps only provide an override conf file, which is different
            # from the full/base service config (c.f. ffsync)
            if "override" in filename:
                continue

            try:
                content = open(app.path + "/conf/" + filename).read()
            except Exception as e:
                yield Warning("Can't open/read %s : %s" % (filename, e))
                return

            matches = re.findall(r"^ *(User|Group)=(\S+)", content, flags=re.MULTILINE)
            if not any(match[0] == "User" for match in matches):
                yield Warning("You should specify a User= directive in the systemd config !")
                return

            if any(match[1] in ["root", "www-data"] for match in matches):
                yield Warning("DO NOT run the app's systemd service as root or www-data ! Use a dedicated system user for this app ! If your app requires administrator priviledges, you should consider adding the user to the sudoers (and restrict the commands it can use !)")

    @test()
    def php_config_specific_user(self):

        app = self.app
        for filename in os.listdir(app.path + "/conf") if os.path.exists(app.path + "/conf") else []:
            # Ignore subdirs or filename not containing nginx in the name
            if not filename.startswith("php") or not filename.endswith(".conf"):
                continue

            try:
                content = open(app.path + "/conf/" + filename).read()
            except Exception as e:
                yield Warning("Can't open/read %s : %s" % (filename, e))
                return

            matches = re.findall(r"^ *(user|group) = (\S+)", content, flags=re.MULTILINE)
            if not any(match[0] == "user" for match in matches):
                yield Warning("You should at least specify a user = directive in your php conf file")
                return

            if any(match[1] in ["root", "www-data"] for match in matches):
                yield Warning("DO NOT run the app php worker as root or www-data ! Use a dedicated system user for this app !")

    @test()
    def misc_nginx_add_header(self):

        app = self.app

        #
        # Analyze nginx conf
        # - Deprecated usage of 'add_header' in nginx conf
        # - Spot path traversal issue vulnerability
        #

        for filename in os.listdir(app.path + "/conf") if os.path.exists(app.path + "/conf") else []:
            # Ignore subdirs or filename not containing nginx in the name
            if not os.path.isfile(app.path + "/conf/" + filename) or "nginx" not in filename:
                continue

            content = open(app.path + "/conf/" + filename).read()
            if "location" in content and "add_header" in content:
                yield Error(
                    "Do not use 'add_header' in the NGINX conf. Use 'more_set_headers' instead. "
                    "(See https://www.peterbe.com/plog/be-very-careful-with-your-add_header-in-nginx "
                    "and https://github.com/openresty/headers-more-nginx-module#more_set_headers )"
                )

    @test()
    def misc_nginx_more_set_headers(self):

        app = self.app

        for filename in os.listdir(app.path + "/conf") if os.path.exists(app.path + "/conf") else []:
            # Ignore subdirs or filename not containing nginx in the name
            if not os.path.isfile(app.path + "/conf/" + filename) or "nginx" not in filename:
                continue

            content = open(app.path + "/conf/" + filename).read()
            if "location" in content and "more_set_headers" in content:

                lines = content.split("\n")
                more_set_headers_lines = [l for l in lines if "more_set_headers" in l]
                def right_syntax(line):
                    return re.search(r"more_set_headers [\"\'][\w-]+\s?: .*[\"\'];", line)

                if any(not right_syntax(line) for line in more_set_headers_lines):
                    yield Warning(
                        "It looks like the syntax for the more_set_headers "
                        "instruction is incorrect in the NGINX conf (N.B. "
                        ": it's different than the add_header syntax!)... "
                        "The syntax should look like: "
                        "more_set_headers \"Header-Name: value\""
                    )

    @test()
    def misc_nginx_path_traversal(self):

        app = self.app
        for filename in os.listdir(app.path + "/conf") if os.path.exists(app.path + "/conf") else []:
            # Ignore subdirs or filename not containing nginx in the name
            if not os.path.isfile(app.path + "/conf/" + filename) or "nginx" not in filename:
                continue
            content = open(app.path + "/conf/" + filename).read()

            #
            # Path traversal issues
            #
            def find_location_with_alias(locationblock):

                if locationblock[0][0] != "location":
                    return

                location = locationblock[0][-1]
                for line in locationblock[1]:
                    instruction = line[0]
                    if instruction == "alias":
                        yield (location, line)
                    elif isinstance(instruction, list) and instruction and instruction[0] == "location":
                        yield from find_location_with_alias(instruction)
                    else:
                        continue

            def find_path_traversal_issue(nginxconf):

                for block in nginxconf:
                    for location, alias in find_location_with_alias(block):
                        # Ignore locations which are regexes..?
                        if location.startswith("^") and location.endswith("$"):
                            continue
                        alias_path = alias[-1]
                        # For path traversal issues to occur, both of those are needed:
                        # - location /foo {          (*without* a / after foo)
                        # -    alias /var/www/foo/   (*with* a / after foo)
                        #
                        # Note that we also consider a positive the case where
                        # the alias folder (e.g. /var/www/foo/) does not ends
                        # with / if __FINALPATH__ ain't used...  that probably
                        # means that the app is not using the standard nginx
                        # helper, and therefore it is likely to be replaced by
                        # something ending with / ...
                        if not location.endswith("/") \
                           and (alias_path.endswith("/") or "__FINALPATH__" not in alias_path):
                            yield location

            do_path_traversal_check = False
            try:
                import pyparsing, six
                do_path_traversal_check = True
            except:
                # If inside a venv, try to magically install pyparsing
                if 'VIRTUAL_ENV' in os.environ:
                    try:
                        _print("(Trying to auto install pyparsing...)")
                        subprocess.check_output("pip3 install pyparsing six", shell=True)
                        import pyparsing
                        _print("Ok!")
                        do_path_traversal_check = True
                    except Exception as e:
                        _print("Failed :[ : %s" % str(e))

            if not do_path_traversal_check:
                _print("N.B.: The package linter need you to run 'pip3 install pyparsing six' if you want it to be able to check for path traversal issue in NGINX confs")

            if do_path_traversal_check:
                from lib.nginxparser import nginxparser
                try:
                    nginxconf = nginxparser.load(open(app.path + "/conf/" + filename))
                except Exception as e:
                    _print("Could not parse NGINX conf...: " + str(e))
                    nginxconf = []

                for location in find_path_traversal_issue(nginxconf):
                    yield Error(
                        "The NGINX configuration (especially location %s) "
                        "appears vulnerable to path traversal issues as explained in\n"
                        "  https://www.acunetix.com/vulnerabilities/web/path-traversal-via-misconfigured-nginx-alias/\n"
                        "  To fix it, look at the first lines of the NGINX conf of the example app : \n"
                        "  https://github.com/YunoHost/example_ynh/blob/master/conf/nginx.conf" % location
                    )

#############################################
#   __  __             _  __          _     #
#  |  \/  |           (_)/ _|        | |    #
#  | \  / | __ _ _ __  _| |_ ___  ___| |_   #
#  | |\/| |/ _` | '_ \| |  _/ _ \/ __| __|  #
#  | |  | | (_| | | | | | ||  __/\__ \ |_   #
#  |_|  |_|\__,_|_| |_|_|_| \___||___/\__|  #
#                                           #
#############################################

class Manifest(TestSuite):

    def __init__(self, path):

        self.path = path
        manifest_path = os.path.join(path, 'manifest.json')
        assert os.path.exists(manifest_path), "manifest.json is missing"

        # Taken from https://stackoverflow.com/a/49518779
        def check_for_duplicate_keys(ordered_pairs):
            dict_out = {}
            for key, val in ordered_pairs:
                if key in dict_out:
                    raise Exception("Duplicated key '%s' in %s" % (key, ordered_pairs))
                else:
                    dict_out[key] = val
            return dict_out

        manifest_path = os.path.join(path, 'manifest.json')
        raw_manifest = open(manifest_path, encoding='utf-8').read()
        try:
            self.manifest = json.loads(raw_manifest, object_pairs_hook=check_for_duplicate_keys)
        except Exception as e:
            print(c.FAIL + "✘ Looks like there's a syntax issue in your manifest ?\n ---> %s" % e)
            sys.exit(1)


    @test()
    def mandatory_fields(self):

        fields = ("name", "id", "packaging_format", "description", "version",
                  "maintainer", "requirements", "multi_instance",
                  "services", "arguments")
        missing_fields = [field for field in fields if field not in self.manifest.keys()]

        if missing_fields:
            yield Critical("The following mandatory fields are missing: %s" % missing_fields)

        fields = ("license", "url")
        missing_fields = [field for field in fields if field not in self.manifest.keys()]

        if missing_fields:
            yield Warning("The following mandatory fields are missing: %s" % missing_fields)

    @test()
    def yunohost_version_requirement(self):

        if not self.manifest.get("requirements", {}).get("yunohost", ""):
            yield Critical("You should add a YunoHost version requirement in the manifest")

    @test()
    def yunohost_version_requirement_superold(app):

        yunohost_version_req = app.manifest.get("requirements", {}).get("yunohost", "").strip(">= ")
        if yunohost_version_req.startswith("2."):
            yield Critical("Your app only requires yunohost >= 2.x, which tends to indicate that your app may not be up to date with recommended packaging practices and helpers.")

    @test()
    def basic_fields_format(self):

        if self.manifest.get("packaging_format") != 1:
            yield Error("packaging_format should be 1")
        if not re.match('^[a-z0-9]((_|-)?[a-z0-9])+$', self.manifest.get("id")):
            yield Error("The app id is not a valid app id")
        if len(self.manifest["name"]) > 22:
            yield Warning("The app name is too long")

    @test()
    def license(self):

        if "license" not in self.manifest:
            return

        # Turns out there may be multiple licenses... (c.f. Seafile)
        licenses = self.manifest["license"].split(",")

        for license in licenses:

            license = license.strip()

            if "nonfree" in license.replace("-", ""):
                yield Warning("'non-free' apps cannot be integrated in YunoHost's app catalog.")
                return

            code_license = '<code property="spdx:licenseId">' + license + '</code>'

            if code_license not in spdx_licenses():
                yield Warning(
                    "The license id '%s' is not registered in https://spdx.org/licenses/." % license
                )
                return

    @test()
    def description(self):

        descr = self.manifest.get("description", "")
        id = self.manifest["id"].lower()
        name = self.manifest["name"].lower()

        if isinstance(descr, dict):
            descr = descr.get("en", "")

        if len(descr) < 5 or len(descr) > 150:
            yield Warning("The description of your app is either missing, too short or too long... Please describe in *consise* terms what the app is/does.")

        if "for yunohost" in descr.lower():
            yield Warning(
                "The 'description' should explain what the app actually does. "
                "No need to say that it is 'for YunoHost' - this is a YunoHost app "
                "so of course we know it is for YunoHost ;-)."
            )
        if descr.lower().startswith(id) or descr.lower().startswith(name):
            yield Warning(
                "Try to avoid starting the description by '$app is' "
                "... explain what the app is/does directly!"
            )

    @test()
    def version_format(self):

        if self.manifest.get("version", "")[-5:-1] != "~ynh":
            yield Error(
                "The 'version' field should match the format <upstreamversion>~ynh<packageversion>. "
                "For example: 4.3-2~ynh3. It is composed of the upstream version number (in the "
                "example, 4.3-2) and an incremental number for each change in the package without "
                "upstream change (in the example, 3). This incremental number can be reset to 1 "
                "each time the upstream version changes."
            )

    @test()
    def multiinstance_format(self):

        if self.manifest["multi_instance"] not in [True, False, 0, 1]:
            yield Error("\"multi_instance\" field should be boolean 'true' or 'false' and not string type")

    @test()
    def url(self):
        if self.manifest.get("url", "").endswith("_ynh"):
            yield Info(
                "'url' is not meant to be the URL of the YunoHost package, "
                "but rather the website or repo of the upstream app itself..."
            )

    @test()
    def install_args(self):

        recognized_types = ("domain", "path", "boolean", "password", "user", "string", "display_text")

        for argument in self.manifest["arguments"].get("install", []):
            if not isinstance(argument.get("optional", False), bool):
                yield Warning(
                    "The key 'optional' value for setting %s should be a boolean (true or false)" % argument["name"]
                )
            if "type" not in argument.keys():
                yield Warning(
                    "You should specify the type of the argument '%s'. "
                    "You can use: %s." % (argument["name"], ', '.join(recognized_types))
                )
            elif argument["type"] not in recognized_types:
                yield Warning(
                    "The type '%s' for argument '%s' is not recognized... "
                    "it probably doesn't behave as you expect? Choose among those instead: %s" % (argument["type"], argument["name"], ', '.join(recognized_types))
                )
            elif argument["type"] == "boolean" and argument.get("default", True) not in [True, False]:
                yield Warning(
                    "Default value for boolean-type arguments should be a boolean... (in particular, make sure it's not a string!)"
                )

            if "choices" in argument.keys():
                choices = [c.lower() for c in argument["choices"]]
                if len(choices) == 2:
                    if ("true" in choices and "false" in choices) or ("yes" in choices and "no" in choices):
                        yield Warning(
                            "Argument %s : you might want to simply use a boolean-type argument. "
                            "No need to specify the choices list yourself." % argument["name"]
                        )

    @test()
    def is_public_help(self):
        for argument in self.manifest["arguments"].get("install", []):
            if argument["name"] == "is_public" and "help" not in argument.keys():
                yield Info(
                    "Consider adding an 'help' key for argument 'is_public' "
                    "to explain to the user what it means for *this* app "
                    "to be public or private :\n"
                    '    "help": {\n'
                    '       "en": "Some explanation"\n'
                    '    }')


########################################
#  _____       _        _              #
# /  __ \     | |      | |             #
# | /  \/ __ _| |_ __ _| | ___   __ _  #
# | |    / _` | __/ _` | |/ _ \ / _` | #
# | \__/\ (_| | || (_| | | (_) | (_| | #
#  \____/\__,_|\__\__,_|_|\___/ \__, | #
#                                __/ | #
#                               |___/  #
#                                      #
########################################


class AppCatalog(TestSuite):

    def __init__(self, app_id):

        self.app_id = app_id

        self._fetch_app_repo()

        try:
            self.app_list = json.loads(open("./.apps/apps.json").read())
        except Exception:
            _print("Failed to read apps.json :/")
            sys.exit(-1)

        self.catalog_infos = self.app_list.get(app_id, {})

    def _fetch_app_repo(self):

        flagfile = "./.apps_git_clone_cache"
        if os.path.exists("./.apps") and os.path.exists(flagfile) and time.time() - os.path.getmtime(flagfile) < 3600:
            return

        if not os.path.exists("./.apps"):
            subprocess.check_call(["git", "clone", "https://github.com/YunoHost/apps", "./.apps", "--quiet"])
        else:
            subprocess.check_call(["git", "-C", "./.apps", "fetch", "--quiet"])
            subprocess.check_call(["git", "-C", "./.apps", "reset", "origin/master", "--hard", "--quiet"])

        open(flagfile, "w").write("")

    @test()
    def is_in_catalog(self):

        if not self.catalog_infos:
            yield Critical("This app is not in YunoHost's application catalog")

    @test()
    def revision_is_HEAD(self):

        if self.catalog_infos and self.catalog_infos.get("revision", "HEAD") != "HEAD":
            yield Error("You should make sure that the revision used in YunoHost's apps catalog is HEAD...")

    @test()
    def state_is_working(self):

        if self.catalog_infos and self.catalog_infos.get("state", "working") != "working":
            yield Critical("The application is not flagged as working in YunoHost's apps catalog")

    @test()
    def has_category(self):
        if self.catalog_infos and not self.catalog_infos.get("category"):
            yield Warning("The application has no associated category in YunoHost's apps catalog")

    @test()
    def is_in_github_org(self):

        repo_org = "https://github.com/YunoHost-Apps/%s_ynh" % (self.app_id)
        repo_brique = "https://github.com/labriqueinternet/%s_ynh" % (self.app_id)

        if self.catalog_infos:
            repo_url = self.catalog_infos["url"]

            all_urls = [infos.get("url", "").lower() for infos in self.app_list.values()]

            if repo_url.lower() not in [repo_org.lower(), repo_brique.lower()]:
                if repo_url.lower().startswith("https://github.com/YunoHost-Apps/"):
                    yield Warning("The URL for this app in the catalog should be %s" % repo_org)
                else:
                    yield Warning("Consider adding your app to the YunoHost-Apps organization to allow the community to contribute more easily")

        else:
            def is_in_github_org():
                return urlopen(repo_org)['code'] != 404

            def is_in_brique_org():
                return urlopen(repo_brique)['code'] != 404

            if not is_in_github_org() and not is_in_brique_org():
                yield Warning("Consider adding your app to the YunoHost-Apps organization to allow the community to contribute more easily")

    @test()
    def is_long_term_good_quality(self):

        #
        # This analyzes the (git) history of apps.json in the past year and
        # compute a score according to the number of period where the app was
        # known + flagged working + level >= 5
        #

        def git(cmd):
            return subprocess.check_output(["git", "-C", "./.apps"] + cmd).decode('utf-8').strip()

        def _time_points_until_today():

            # Prior to April 4th, 2019, we still had official.json and community.json
            # Nowadays we only have apps.json
            year = 2019
            month = 6
            day = 1
            today = datetime.today()
            date = datetime(year, month, day)

            while date < today:
                yield date

                day += 14
                if day > 15:
                    day = 1
                    month += 1

                if month > 12:
                    month = 1
                    year += 1

                date = datetime(year, month, day)

        def get_history(N):

            for t in list(_time_points_until_today())[(-1 * N):]:

                # Fetch apps.json content at this date
                commit = git(["rev-list", "-1", "--before='%s'" % t.strftime("%b %d %Y"), "master"])
                raw_json_at_this_date = git(["show", "%s:apps.json" % commit])
                json_at_this_date = json.loads(raw_json_at_this_date)

                yield (t, json_at_this_date.get(self.app_id))

        # We'll check the history for last 12 months (*2 points per month)
        N = 12 * 2
        history = list(get_history(N))

        # Must have been
        #   known
        # + flagged as working
        # + level > 5
        # for the past 6 months
        def good_quality(infos):
            return bool(infos) and isinstance(infos, dict) \
                and infos.get("state") == "working" \
                and infos.get("level", -1) >= 5

        score = sum([good_quality(infos) for d, infos in history])
        rel_score = int(100 * score / N)
        if rel_score > 90:
            yield Success("The app is long-term good quality in the catalog!")

##################################
#   _____           _       _    #
#  / ____|         (_)     | |   #
# | (___   ___ _ __ _ _ __ | |_  #
#  \___ \ / __| '__| | '_ \| __| #
#  ____) | (__| |  | | |_) | |_  #
# |_____/ \___|_|  |_| .__/ \__| #
#                    | |         #
#                    |_|         #
##################################
class Script(TestSuite):

    def __init__(self, app_path, name):
        self.name = name
        self.app_path = app_path
        self.path = app_path + "/scripts/" + name
        self.exists = file_exists(self.path)
        if not self.exists:
            return
        self.lines = list(self.read_file())

    def read_file(self):
        with open(self.path) as f:
            lines = f.readlines()

        # Remove trailing spaces, empty lines and comment lines
        lines = [line.strip() for line in lines]
        lines = [line for line in lines if line and not line.startswith('#')]

        # Merge lines when ending with \
        lines = '\n'.join(lines).replace("\\\n", "").split("\n")

        some_parsing_failed = False

        for line in lines:

            try:
                line = shlex.split(line, True)
                yield line
            except Exception as e:
                if not some_parsing_failed:
                    _print("Some lines could not be parsed in script %s. (That's probably not really critical)" % self.name)
                    some_parsing_failed = True
                report_warning_not_reliable("%s : %s" % (e, line))

    def occurences(self, command):
        return [line for line in [' '.join(line) for line in self.lines] if command in line]

    def contains(self, command):
        """
        Iterate on lines to check if command is contained in line

        For instance, "app setting" is contained in "yunohost app setting $app ..."
        """
        return any(command in line
                   for line in [' '.join(line) for line in self.lines])

    def containsregex(self, regex):
        """
        Iterate on lines to check if command is contained in line

        For instance, "app setting" is contained in "yunohost app setting $app ..."
        """
        return any(re.search(regex, line)
                   for line in [' '.join(line) for line in self.lines])


    @test()
    def error_handling(self):

        if self.name in ["backup", "remove", "_common.sh"]:
            present = self.contains("ynh_abort_if_errors") or self.contains("set -eu")
        else:
            present = self.contains("ynh_abort_if_errors")

        if self.name in ["remove", "_common.sh"]:
            if present:
                yield Error(
                    "Do not use set -eu or ynh_abort_if_errors in the remove or _common.sh: "
                    "If a single instruction fails, it will stop the script and is "
                    "likely to leave the system in a broken state."
                )
        elif not present:
            yield Error(
                "You should add 'ynh_abort_if_errors' in this script, "
                "c.f. https://github.com/YunoHost/issues/issues/419"
            )

    # Skip this in common.sh, sometimes custom not-yet-official helpers need this
    @test(ignore=["_common.sh"])
    def raw_apt_commands(self):

        if self.contains("ynh_package_install") or self.contains("apt install") or self.contains("apt-get install"):
            yield Warning(
                "You should not use `ynh_package_install` or `apt-get install`, "
                "use `ynh_install_app_dependencies` instead"
            )

        if self.contains("ynh_package_remove") or self.contains("apt remove") or self.contains("apt-get remove"):
            yield Warning(
                "You should not use `ynh_package_remove` or `apt-get remove`, "
                "use `ynh_remove_app_dependencies` instead"
            )

    @test()
    def obsolete_helpers(self):
        if self.contains("yunohost app setting"):
            yield Critical("Do not use 'yunohost app setting' directly. Please use 'ynh_app_setting_(set,get,delete)' instead.")
        if self.contains("yunohost app checkurl"):
            yield Critical("'yunohost app checkurl' is obsolete!!! Please use 'ynh_webpath_register' instead.")
        if self.contains("yunohost app checkport"):
            yield Critical("'yunohost app checkport' is obsolete!!! Please use 'ynh_find_port' instead.")
        if self.contains("yunohost app initdb"):
            yield Critical("'yunohost app initdb' is obsolete!!! Please use 'ynh_mysql_setup_db' instead.")
        if self.contains("yunohost tools port-available"):
            yield Critical("'yunohost tools port-available is obsolete!!! Please use 'ynh_port_available' instead.")
        if self.contains("yunohost app addaccess") or self.contains("yunohost app removeaccess"):
            yield Warning("'yunohost app addaccess/removeacces' is obsolete. You should use the new permission system to manage accesses.")
        if self.contains("yunohost app list -i") or self.contains("yunohost app list --installed"):
            yield Warning(
                "Argument --installed ain't needed anymore when using "
                "'yunohost app list'. It directly returns the list of installed "
                "apps.. Also beware that option -f is obsolete as well... "
                "Use grep -q 'id: $appname' to check a specific app is installed"
            )

    @test()
    def normalize_url_path(self):
        if self.contains("ynh_normalize_url_path"):
            yield Info("You probably don't need to call 'ynh_normalize_url_path'... this is only relevant for upgrades from super-old versions (like 3 years ago or so...)")

    @test()
    def safe_rm(self):
        if self.contains("rm -r") or self.contains("rm -R") or self.contains("rm -fr") or self.contains("rm -fR"):
            yield Error("You should not be using 'rm -rf', please use 'ynh_secure_remove' instead")

    @test()
    def nginx_restart(self):
        if self.contains("systemctl restart nginx") or self.contains("service nginx restart"):
            yield Error(
                "Restarting NGINX is quite dangerous (especially for web installs) "
                "and should be avoided at all cost. Use 'reload' instead."
            )

    @test()
    def quiet_systemctl_enable(self):

        systemctl_enable = [line
                            for line in [' '.join(line) for line in self.lines]
                            if re.search(r"systemctl.*(enable|disable)", line)]

        if any("-q" not in cmd for cmd in systemctl_enable):
            message = "Please add --quiet to systemctl enable/disable commands to avoid unecessary warnings when the script runs"
            yield Warning(message) if self.name in ["_common.sh", "install"] else Info(message)

    @test()
    def quiet_wget(self):

        wget_cmds = [line
                     for line in [' '.join(line) for line in self.lines]
                     if re.search(r"^wget ", line)]

        if any(" -q " not in cmd and "--quiet" not in cmd and "2>" not in cmd for cmd in wget_cmds):
            message = "Please redirect wget's stderr to stdout with 2>&1 to avoid unecessary warnings when the script runs (yes, wget is annoying and displays a warning even when things are going okay >_> ...)"
            yield Warning(message) if self.name in ["_common.sh", "install"] else Info(message)

    @test(only=["install"])
    def argument_fetching(self):

        if self.containsregex(r"^\w+\=\$\{?[0-9]"):
            yield Critical(
                "Do not fetch arguments from manifest using variable=$N (e.g."
                " domain=$1...) Instead, use name=$YNH_APP_ARG_NAME"
            )

    @test(only=["install"])
    def sources_list_tweaking(self):
        if self.contains("/etc/apt/sources.list") \
        or (os.path.exists(self.app_path + "/scripts/_common.sh") and "/etc/apt/sources.list" in open(self.app_path+"/scripts/_common.sh").read() and "ynh_add_repo" not in open(self.app_path+"/scripts/_common.sh").read()):
            yield Error(
                "Manually messing with apt's sources.lists is strongly discouraged "
                "and should be avoided. Please use 'ynh_install_extra_app_dependencies' if you "
                "need to install dependencies from a custom apt repo."
            )

    @test()
    def exit_ynhdie(self):

        if self.contains(r"\bexit\b"):
            yield Error("'exit' command shouldn't be used. Please use 'ynh_die' instead.")

    @test()
    def old_regenconf(self):
        if self.contains("yunohost service regen-conf"):
            yield Warning("'yunohost service regen-conf' has been replaced by 'yunohost tools regen-conf'.")

    @test()
    def ssowatconf(self):
        # Dirty hack to check only the 10 last lines for ssowatconf
        # (the "bad" practice being using this at the very end of the script, but some apps legitimately need this in the middle of the script)
        oldlines = list(self.lines)
        self.lines = self.lines[-10:]
        if self.contains("yunohost app ssowatconf"):
            yield Warning("You probably don't need to run 'yunohost app ssowatconf' in the app self. It's supposed to be ran automatically after the script.")
        self.lines = oldlines

    @test()
    def sed(self):
        if self.containsregex(r"sed\s+(-i|--in-place)\s+(-r\s+)?s") or self.containsregex(r"sed\s+s\S*\s+(-i|--in-place)"):
            yield Info("You should avoid using 'sed -i' for substitutions, please use 'ynh_replace_string' instead")

    @test()
    def sudo(self):
        if self.containsregex(r"sudo \w"):  # \w is here to not match sudo -u, legit use because ynh_exec_as not official yet...
            yield Info(
                "You should not need to use 'sudo', the script is being run as root. "
                "(If you need to run a command using a specific user, use 'ynh_exec_as' (or 'sudo -u'))"
            )

    @test()
    def chmod777(self):
        if self.containsregex(r"chmod .*777") or self.containsregex(r'chmod .*o\+w'):
            yield Warning(
                "DO NOT use chmod 777 or chmod o+w that gives write permission to every users on the system!!! If you have permission issues, just make sure that the owner and/or group owner is right..."
            )

    @test()
    def random(self):
        if self.contains("dd if=/dev/urandom") or self.contains("openssl rand"):
            yield Error(
                "Instead of 'dd if=/dev/urandom' or 'openssl rand', you should use ynh_string_random"
            )

    @test(only=["install"])
    def progression(self):
        if not self.contains("ynh_script_progression"):
            yield Warning(
                "Please add a few messages for the user using 'ynh_script_progression' "
                "to explain what is going on (in friendly, not-too-technical terms) "
                "during the installation. (and ideally in scripts remove, upgrade and restore too)"
            )

    @test(only=["backup"])
    def progression_in_backup(self):
        if self.contains("ynh_script_progression"):
            yield Info(
                "We recommend to *not* use 'ynh_script_progression' in backup "
                "scripts because no actual work happens when running the script "
                " : YunoHost only fetches the list of things to backup (apart "
                "from the DB dumps which effectively happens during the script...). "
                "Consider using a simple message like this instead: 'ynh_print_info \"Declaring files to be backed up...\"'"
            )


    @test()
    def progression_time(self):

        # Usage of ynh_script_prorgression with --time or --weight=1 all over the place...
        if self.containsregex(r"ynh_script_progression.*--time"):
            yield Info("Using ynh_script_progression --time should only be for calibrating the weight (c.f. --weight). It's not meant to be kept for production versions.")

    @test(ignore=["_common.sh", "backup"])
    def progression_meaningful_weights(self):

        def weight(line):
            match = re.search(r"ynh_script_progression.*--weight=([0-9]+)", ' '.join(line))
            if match:
                try:
                    return int(match.groups()[0])
                except:
                    return -1
            else:
                return 1

        script_progress = [line for line in self.lines if "ynh_script_progression" in line]
        weights = [weight(line) for line in script_progress]

        if not weights:
            return

        if len(weights) > 3 and statistics.stdev(weights) > 50:
            yield Info("To have a meaningful progress bar, try to keep the weights in the same range of values, for example [1,10], or [10,100]... otherwise, if you have super-huge weight differentes, the progress bar rendering will be completely dominated by one or two steps... If these steps are really long, just try to indicated in the message that this will take a while.")

    @test(only=["install", "_common.sh"])
    def php_deps(self):
        if self.containsregex("dependencies.*php-"):
            yield Warning("You should avoid having dependencies like 'php-foobar'. Instead, specify the exact version you want like 'php7.0-foobar'. Otherwise, the *wrong* version of the dependency may be installed if sury is also installed. Note that for Stretch/Buster/Bullseye/... transition, YunoHost will automatically patch your file so there's no need to care about that.")

    @test(only=["backup"])
    def systemd_during_backup(self):
        if self.containsregex("^ynh_systemd_action"):
            yield Warning("Unless you really have a good reason to do so, starting/stopping services during backup has no benefit and leads to unecessary service interruptions when creating backups... As a 'reminder': apart from possibly database dumps (which usually do not require the service to be stopped) or other super-specific action, running the backup script is only a *declaration* of what needs to be backuped. The real copy and archive creation happens *after* the backup script is ran.")

    @test(only=["backup"])
    def check_size_backup(self):
        if self.contains("CHECK_SIZE"):
            yield Warning("There's no need to 'CHECK_SIZE' during backup... This check is handled by the core automatically.")

    @test()
    def helpers_sourcing_after_official(self):
        helpers_after_official = subprocess.check_output("head -n 30 '%s' | grep -A 10 '^ *source */usr/share/yunohost/helpers' | grep '^ *source' | tail -n +2" % self.path, shell=True).decode("utf-8")
        helpers_after_official = helpers_after_official.replace("source", "").replace(" ", "").strip()
        if helpers_after_official:
            helpers_after_official = helpers_after_official.split("\n")
            yield Warning("Please avoid sourcing additional helpers after the official helpers (in this case file %s)" % ", ".join(helpers_after_official))

    @test(only=["backup", "restore"])
    def helpers_sourcing_backuprestore(self):
        if self.contains("source _common.sh") or self.contains("source ./_common.sh"):
            yield Warning("In the context of backup and restore script, you should load _common.sh with \"source ../settings/scripts/_common.sh\"")



def main():
    if len(sys.argv) < 2:
        print("Give one app package path.")
        exit()

    app_path = sys.argv[1]

    global output
    output = "json" if "--json" in sys.argv else "plain"

    header(app_path)
    app = App(app_path)
    app.analyze()

if __name__ == '__main__':
    main()
