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
        _print(self.style, self.message, c.END)

class Warning(TestReport):
    style = c.WARNING + "!"

class Error(TestReport):
    style = c.FAIL + "✘"

class Info(TestReport):
    style = c.OKBLUE


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
    _print(c.OKGREEN + "☺ ", str, "♥")


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


def app_list():

    cachefile = "./.apps.json"
    if os.path.exists(cachefile) and time.time() - os.path.getmtime(cachefile) < 3600:
        try:
            return json.loads(open(cachefile).read())
        except:
            _print("Uuuuh failed to load apps.json from cache...")

    url = "https://raw.githubusercontent.com/YunoHost/apps/master/apps.json"
    content = urlopen(url)['content']
    open(cachefile, "w").write(content)
    return json.loads(content)


tests = {}
tests_reports = []

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
            reports = list(test(self))
            for report in reports:
                if output == "plain":
                    report.display()
                tests_reports.append((test.__qualname__, report))

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


    def analyze(self):

        print_header("MANIFEST")
        self.manifest_.run_tests()

        for script in [self.scripts[s] for s in scriptnames if self.scripts[s].exists]:
            print_header(script.name.upper() + " SCRIPT")
            script.run_tests()

        print_header("MISC HELPER USAGE / CONSISTENCY")
        self.run_tests()


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
                yield Warning("%s is now an official helper since version '%s'" % (custom_helper, official_helpers[custom_helper] or '?'))

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
                message = "Using official helper %s implies requiring at least version %s, but manifest only requires %s" % (helper, helper_req, yunohost_version_req)
                yield Error(message) if major_diff else Warning(message)


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
        install_script = app.scripts["install"]
        if install_script.contains("yunohost service add"):
            if app.scripts["remove"].exists and not app.scripts["remove"].contains("yunohost service remove"):
                yield Error(
                    "You used 'yunohost service add' in the install script, "
                    "but not 'yunohost service remove' in the remove script."
                )

            if app.scripts["upgrade"].exists and not app.scripts["upgrade"].contains("yunohost service add"):
                yield Warning(
                    "You used 'yunohost service add' in the install script, "
                    "but not in the upgrade script"
                )

            if app.scripts["restore"].exists and not app.scripts["restore"].contains("yunohost service add"):
                yield Warning(
                    "You used 'yunohost service add' in the install script, "
                    "but not in the restore script"
                )

    @test()
    def helper_consistency_firewall(app):
        install_script = app.scripts["install"]
        if install_script.contains("yunohost firewall allow"):
            if not install_script.contains("--needs_exposed_ports"):
                yield Warning("The install script expose a port on the outside with 'yunohost firewall allow' but doesn't use 'yunohost service add' with --needs_exposed_ports ... If your are ABSOLUTELY SURE that the service needs to be exposed on THE OUTSIDE, then add --needs_exposed_ports to 'yunohost service add' with the relevant port number. Otherwise, opening the port leads to a significant security risk and you should keep the damn port closed !")


    ###########################################################
    #    _____             __       __            _           #
    #   / ____|           / _|     / /           (_)          #
    #  | |     ___  _ __ | |_     / /   _ __ ___  _ ___  ___  #
    #  | |    / _ \| '_ \|  _|   / /   | '_ ` _ \| / __|/ __| #
    #  | |___| (_) | | | | |    / /    | | | | | | \__ \ (__  #
    #   \_____\___/|_| |_|_|   /_/     |_| |_| |_|_|___/\___| #
    #                                                         #
    ###########################################################

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
    def check_process_exists(app):

        check_process_file = app.path + "/check_process"

        if not file_exists(check_process_file):
            yield Warning("You should add a 'check_process' file to properly interface with the continuous integration system")

    @test()
    def check_process_syntax(app):

        check_process_file = app.path + "/check_process"
        if not file_exists(check_process_file):
            return

        if os.system("grep -q 'Level 5=1' %s" % check_process_file) == 0:
            yield Error("Do not force Level 5=1 in check_process...")

        if os.system("grep -q ' *Level [^5]=' %s" % check_process_file) == 0:
            yield Warning("Setting Level x=y in check_process is obsolete / not relevant anymore")

    @test()
    def check_process_consistency(app):

        check_process_file = app.path + "/check_process"
        if not file_exists(check_process_file):
            return

        has_is_public_arg = any(a["name"] == "is_public" for a in app.manifest["arguments"].get("install", []))
        if has_is_public_arg:
            if os.system(r"grep -q '^\s*setup_public=1' %s" % check_process_file) != 0:
                yield Warning("It looks like you forgot to enable setup_public test in check_process ?")

            if os.system(r"grep -q '^\s*setup_private=1' %s" % check_process_file) != 0:
                yield Warning("It looks like you forgot to enable setup_private test in check_process ?")

        has_path_arg = any(a["name"] == "path" for a in app.manifest["arguments"].get("install", []))
        if has_path_arg:
            if os.system(r"grep -q '^\s*setup_sub_dir=1' %s" % check_process_file) != 0:
                yield Warning("It looks like you forgot to enable setup_sub_dir test in check_process ?")

        if app.manifest.get("multi_instance") in [True, 1, "True", "true"]:
            if os.system(r"grep -q '^\s*multi_instance=1' %s" % check_process_file) != 0:
                yield Warning("It looks like you forgot to enable multi_instance test in check_process ?")

        if app.scripts["backup"].exists:
            if os.system(r"grep -q '^\s*backup_restore=1' %s" % check_process_file) != 0:
                yield Warning("It looks like you forgot to enable backup_restore test in check_process ?")


    @test()
    def misc_legacy_phpini(app):

        if file_exists(app.path + "/conf/php-fpm.ini"):
            yield Error(
                "Using a separate php-fpm.ini file is deprecated. "
                "Please merge your php-fpm directives directly in the pool file. "
                "(c.f. https://github.com/YunoHost-Apps/nextcloud_ynh/issues/138 )"
            )


    @test()
    def misc_source_management(app):

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
    def misc_nginx_add_header(app):

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
                    "Do not use 'add_header' in the nginx conf. Use 'more_set_headers' instead. "
                    "(See https://www.peterbe.com/plog/be-very-careful-with-your-add_header-in-nginx "
                    "and https://github.com/openresty/headers-more-nginx-module#more_set_headers )"
                )


    @test()
    def misc_nginx_path_traversal(app):
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
                        # For path traversal issues to occur, both of those are needed :
                        # - location /foo {          (*without* a / after foo)
                        # -    alias /var/www/foo/   (*with* a / after foo)
                        #
                        # Note that we also consider a positive the case where
                        # the alias folder (e.g. /var/www/foo/) does not ends
                        # with / if __FINALPATH__ ain't used ...  that probably
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
                _print("N.B.: The package linter need you to run 'pip3 install pyparsing six' if you want it to be able to check for path traversal issue in nginx confs")

            if do_path_traversal_check:
                from lib.nginxparser import nginxparser
                try:
                    nginxconf = nginxparser.load(open(app.path + "/conf/" + filename))
                except Exception as e:
                    _print("Could not parse nginx conf ... : " + str(e))
                    nginxconf = []

                for location in find_path_traversal_issue(nginxconf):
                    yield Error(
                        "The nginx configuration (especially location %s) "
                        "appears vulnerable to path traversal issues as explained in\n"
                        "  https://www.acunetix.com/vulnerabilities/web/path-traversal-via-misconfigured-nginx-alias/\n"
                        "  To fix it, look at the first lines of the nginx conf of the example app : \n"
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
            raise Exception("Looks like there's a syntax issue in your json ? %s" % e)


    @test()
    def mandatory_fields(self):

        fields = ("name", "id", "packaging_format", "description", "version",
                  "maintainer", "requirements", "multi_instance",
                  "services", "arguments")
        missing_fields = [field for field in fields if field not in self.manifest.keys()]

        if missing_fields:
            yield Error("The following mandatory fields are missing: %s" % missing_fields)

        fields = ("license", "url")
        missing_fields = [field for field in fields if field not in self.manifest.keys()]

        if missing_fields:
            yield Warning("The following mandatory fields are missing: %s" % missing_fields)

    @test()
    def yunohost_version_requirement(self):

        if not self.manifest.get("requirements", {}).get("yunohost", ""):
            yield Error("You should add a yunohost version requirement in the manifest")

    @test()
    def yunohost_version_requirement_superold(app):

        yunohost_version_req = app.manifest.get("requirements", {}).get("yunohost", "").strip(">= ")
        if yunohost_version_req.startswith("2."):
            yield Error("Your app only requires yunohost >= 2.x, which tends to indicate that your app may not be up to date with recommended packaging practices and helpers.")

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

        if not "license" in self.manifest:
            return

        def license_mentionned_in_readme():
            readme_path = os.path.join(self.path, 'README.md')
            if os.path.isfile(readme_path):
                return "LICENSE" in open(readme_path).read()
            return False

        license = self.manifest["license"]


        if "nonfree" in license.replace("-", ""):
            yield Warning("'non-free' apps can't be officialized.")


        code_license = '<code property="spdx:licenseId">' + license + '</code>'

        if license == "free" and not license_mentionned_in_readme():
            yield Warning(
                "Setting the license as 'free' implies to write something about it in "
                "the README.md. Alternatively, consider using one of the codes available "
                "on https://spdx.org/licenses/"
            )
        elif code_license not in spdx_licenses():
            yield Warning(
                "The license id '%s' is not registered in https://spdx.org/licenses/. "
                "It can be a typo error. If not, you should replace it by 'free' "
                "or 'non-free' and give some explanations in the README.md." % (license)
            )


    @test()
    def app_in_app_catalog(self):

        if self.manifest["id"] not in app_list():
            yield Warning("This app is not Yunohost's application catalog")

    @test()
    def app_in_github_org(self):

        all_urls = [infos.get("url", "").lower() for infos in app_list().values()]

        repo_org = "https://github.com/YunoHost-Apps/%s_ynh" % (self.manifest["id"])
        repo_brique = "https://github.com/labriqueinternet/%s_ynh" % (self.manifest["id"])

        if repo_org.lower() in all_urls or repo_brique.lower() in all_urls:
            return

        def is_in_github_org():
            return urlopen(repo_org)['code'] != 404
        def is_in_brique_org():
            return urlopen(repo_brique)['code'] != 404

        if not is_in_github_org() and not is_in_brique_org():
            yield Warning("Consider adding your app to the YunoHost-Apps organization to allow the community to contribute more easily")

    @test()
    def description(self):

        descr = self.manifest.get("description", "")
        id = self.manifest["id"].lower()
        name = self.manifest["name"].lower()

        if isinstance(descr, dict):
            descr = descr.get("en", "")

        if len(descr) < 5 or len(descr) > 150:
            yield Warning("The description of your app is either missing, too short or too long... Please describe in *consise* terms what the app is / does.")

        if "for yunohost" in descr.lower():
            yield Warning(
                "The 'description' should explain what the app actually does. "
                "No need to say that it is 'for YunoHost' - this is a YunoHost app "
                "so of course we know it is for YunoHost ;-)."
            )
        if descr.lower().startswith(id) or descr.lower().startswith(name):
            yield Warning(
                "Try to avoid starting the description by '$app is' "
                "... explain what the app is / does directly !"
            )

    @test()
    def version_format(self):

        if self.manifest["version"][-5:-1] != "~ynh":
            yield Error(
                "The 'version' field should match the format <upstreamversion>~ynh<packageversion>. "
                "For example : 4.3-2~ynh3. It is composed of the upstream version number (in the "
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
            yield Warning(
                "'url' is not meant to be the url of the yunohost package, "
                "but rather the website or repo of the upstream app itself..."
            )

    @test()
    def install_args(self):

        recognized_types = ("domain", "path", "boolean", "app", "password", "user", "string", "display_text")

        for argument in self.manifest["arguments"].get("install", []):
            if not isinstance(argument.get("optional", False), bool):
                yield Warning(
                    "The key 'optional' value for setting %s should be a boolean (true or false)" % argument["name"]
                )
            if "type" not in argument.keys():
                yield Warning(
                    "You should specify the type of the argument '%s'. "
                    "You can use : %s." % (argument["name"], ', '.join(recognized_types))
                )
            elif argument["type"] not in recognized_types:
                yield Warning(
                    "The type '%s' for argument '%s' is not recognized... "
                    "it probably doesn't behave as you expect ? Choose among those instead : %s" % (argument["type"], argument["name"], ', '.join(recognized_types))
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
            yield Error("Do not use 'yunohost app setting' directly. Please use 'ynh_app_setting_(set,get,delete)' instead.")
        if self.contains("yunohost app checkurl"):
            yield Error("'yunohost app checkurl' is obsolete!!! Please use 'ynh_webpath_register' instead.")
        if self.contains("yunohost app checkport"):
            yield Error("'yunohost app checkport' is obsolete!!! Please use 'ynh_find_port' instead.")
        if self.contains("yunohost app initdb"):
            yield Error("'yunohost app initdb' is obsolete!!! Please use 'ynh_mysql_setup_db' instead.")

    @test()
    def safe_rm(self):
        if self.contains("rm -rf"):
            yield Error("You should avoid using 'rm -rf', please use 'ynh_secure_remove' instead")

    @test()
    def nginx_restart(self):
        if self.contains("systemctl restart nginx") or self.contains("service nginx restart"):
            yield Error(
                "Restarting nginx is quite dangerous (especially for web installs) "
                "and should be avoided at all cost. Use 'reload' instead."
            )

    @test(only=["install"])
    def argument_fetching(self):

        if self.containsregex(r"^\w+\=\$\{?[0-9]"):
            yield Error(
                "Do not fetch arguments from manifest using variable=$N (e.g."
                " domain=$1 ...) Instead, use name=$YNH_APP_ARG_NAME"
            )


    @test(only=["install"])
    def sources_list_tweaking(self):
        if self.contains("/etc/apt/sources.list") \
        or (os.path.exists(self.app_path + "/scripts/_common.sh") and "/etc/apt/sources.list" in open(self.app_path+"/scripts/_common.sh").read() and "ynh_add_repo" not in open(self.app_path+"/scripts/_common.sh").read()):
            yield Error(
                "Manually messing with apt's sources.lists is strongly discouraged "
                "and should be avoided. Please use ynh_install_extra_app_dependencies is you "
                "need to install dependencies from a custom apt repo."
            )

    @test()
    def exit_ynhdie(self):

        if self.contains(r"\bexit\b"):
            yield Error("'exit' command shouldn't be used. Please use 'ynh_die' instead.")

    @test()
    def old_regenconf(self):
        if self.contains("yunohost service regen-conf"):
            yield Warning("'yunohost tools regen-conf' has been replaced by 'yunohost tools regen-conf'.")

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
            yield Warning("You should avoid using 'sed -i' for substitutions, please use 'ynh_replace_string' instead")

    @test()
    def sudo(self):
        if self.containsregex(r"sudo \w"):  # \w is here to not match sudo -u, legit use because ynh_exec_as not official yet...
            yield Warning(
                "You should not need to use 'sudo', the self is being run as root. "
                "(If you need to run a command using a specific user, use 'ynh_exec_as')"
            )

    @test()
    def chmod777(self):
        if self.containsregex(r"chmod .*777") or self.containsregex(r'chmod .*o\+w'):
            yield Warning(
                "DO NOT use chmod 777 or chmod o+w that gives write permission to every users on the system !!! If you have permission issues, just make sure that the owner and/or group owner is right ..."
            )

    @test()
    def random(self):
        if self.contains("dd if=/dev/urandom") or self.contains("openssl rand"):
            yield Error(
                "Instead of 'dd if=/dev/urandom' or 'openssl rand', you should use ynh_string_random"
            )

    @test(only=["install"])
    def progression(self):
        if not self.contains("ynh_print_info") and not self.contains("ynh_script_progression"):
            yield Warning(
                "Please add a few messages for the user, to explain what is going on "
                "(in friendly, not-too-technical terms) during the installation. "
                "You can use 'ynh_print_info' or 'ynh_script_progression' for this."
            )

    @test()
    def progression_time(self):

        # Usage of ynh_script_prorgression with --time or --weight=1 all over the place...
        if self.containsregex(r"ynh_script_progression.*--time"):
            yield Warning("Using ynh_script_progression --time should only be for calibrating the weight (c.f. --weight). It's not meant to be kept for production versions.")

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
            yield Warning("To have a meaningful progress bar, try to keep the weights in the same range of values, for example [1,10], or [10,100] ... otherwise, if you have super-huge weight differentes, the progress bar rendering will be completely dominated by one or two steps... If these steps are really long, just try to indicated in the message that this will take a while.")

    @test(only=["install", "_common.sh"])
    def php_deps(self):
        if self.containsregex("dependencies.*php-"):
            yield Warning("You should avoid having dependencies like 'php-foobar'. Instead, specify the exact version you want like 'php7.0-foobar'. Otherwise, the *wrong* version of the dependency may be installed if sury is also installed. Note that for Stretch/Buster/Bullseye/... transition, Yunohost will automatically patch your file so there's no need to care about that.")

    @test(only=["backup"])
    def systemd_during_backup(self):
        if self.containsregex("^ynh_systemd_action"):
            yield Warning("Unless you really have a good reason to do so, starting/stopping services during backup has no benefit and leads to unecessary service interruptions when creating backups... As a 'reminder': apart from possibly database dumps (which usually do not require the service to be stopped) or other super-specific action, running the backup script is only a *declaration* of what needs to be backuped. The real copy and archive creation happens *after* the backup script is ran.")

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
    App(app_path).analyze()

    if output == "json":
        print(json.dumps({"warnings": [test for test, report in tests_reports if isinstance(report, Warning)],
                          "errors": [test for test, report in tests_reports if isinstance(report, Error)]}, indent=4))
    else:
        errors = [report for _, report in tests_reports if isinstance(report, Error)]
        warnings = [report for _, report in tests_reports if isinstance(report, Warning)]
        if errors:
            print("Uhoh there are some errors to be fixed :(")
            sys.exit(1)
        elif len(warnings) > 3:
            print("Still some warnings to be fixed :s")
        elif len(warnings) > 0:
            print("Only %s warning remaining! You can do it!" % len(warnings))
        else:
            print_happy("Not even a warning! Congratz and thank you for keeping that package up to date with good practices !")


if __name__ == '__main__':
    main()
