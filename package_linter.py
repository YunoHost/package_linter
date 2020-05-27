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

# Taken from https://stackoverflow.com/a/49518779
def check_for_duplicate_keys(ordered_pairs):
    dict_out = {}
    for key, val in ordered_pairs:
        if key in dict_out:
            print_warning("Duplicated key '%s' in %s" % (key, ordered_pairs))
        else:
            dict_out[key] = val
    return dict_out


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


def header(app):
    print("""
    [{header}{bold}YunoHost App Package Linter{end}]

 App packaging documentation - https://yunohost.org/#/packaging_apps
 App package example         - https://github.com/YunoHost/example_ynh
 Official helpers            - https://yunohost.org/#/packaging_apps_helpers_en
 Experimental helpers        - https://github.com/YunoHost-Apps/Experimental_helpers

 If you believe this linter returns false negative (warnings / errors which shouldn't happen),
 please report them on https://github.com/YunoHost/package_linter/issues

    Analyzing package {header}{app}{end}"""
    .format(header=c.HEADER, bold=c.BOLD, end=c.END, app=app))


def print_header(str):
    print("\n [" + c.BOLD + c.HEADER + str.title() + c.END + "]\n")


def print_warning_not_reliable(str):
    print(c.MAYBE_FAIL + "?", str, c.END)


warning_count = 0
def print_warning(str):
    global warning_count
    warning_count += 1
    print(c.WARNING + "!", str, c.END)


error_count = 0
def print_error(str):
    global error_count
    error_count += 1
    print(c.FAIL + "✘", str, c.END)


def print_happy(str):
    print(c.OKGREEN + "☺ ", str, "♥")


def urlopen(url):
    try:
        conn = urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        return {'content': '', 'code': e.code}
    except urllib.error.URLError as e:
        print('URLError')
    return {'content': conn.read().decode('UTF8'), 'code': 200}


def file_exists(file_path):
    return os.path.isfile(file_path) and os.stat(file_path).st_size > 0

def spdx_licenses():
    cachefile = ".spdx_licenses"
    if os.path.exists(cachefile) and time.time() - os.path.getmtime(cachefile) < 3600:
        return open(cachefile).read()

    link = "https://spdx.org/licenses/"
    content = urlopen(link)['content']
    open(cachefile, "w").write(content)
    return content


# ############################################################################
#   Actual high-level checks
# ############################################################################

scriptnames = ["_common.sh", "install", "remove", "upgrade", "backup", "restore"]

class App():

    def __init__(self, path):

        print_header("LOADING APP")
        self.path = path
        self.scripts = {f: Script(self.path, f) for f in scriptnames}

    def analyze(self):

        self.check_manifest()
        self.misc_file_checks()
        self.check_helpers_usage()

        for script in [self.scripts[s] for s in scriptnames if self.scripts[s].exists]:
            script.analyze()

    def check_helpers_usage(self):

        print_header("HELPERS USAGE")

        # Check for custom helpers definition that are now official...
        cmd = "grep -IhEro 'ynh_\w+ *\( *\)' '%s/scripts' | tr -d '() '" % self.path
        custom_helpers = subprocess.check_output(cmd, shell=True).decode('utf-8').strip().split("\n")
        custom_helpers = [c.split("__")[0] for c in custom_helpers]

        for custom_helper in custom_helpers:
            if custom_helper in official_helpers.keys():
                print_warning("%s is now an official helper since version '%s'" % (custom_helper, official_helpers[custom_helper] or '?'))

        # Check for helpers usage that do not match version required in manifest...
        if self.yunohost_version_req:
            cmd = "grep -IhEro 'ynh_\w+' '%s/scripts'" % self.path
            helpers_used = subprocess.check_output(cmd, shell=True).decode('utf-8').strip().split("\n")
            helpers_used = sorted(set(helpers_used))

            manifest_req = [int(i) for i in self.yunohost_version_req.strip(">= ").split('.')] + [0,0,0]
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
                    message = "Using official helper %s implies requiring at least version %s, but manifest only requires %s" % (helper, helper_req, self.yunohost_version_req)
                    if major_diff:
                        print_error(message)
                    else:
                        print_warning(message)


    def misc_file_checks(self):

        print_header("MISC FILE CHECKS")

        #
        # Check for recommended and mandatory files
        #

        filenames = ("manifest.json", "LICENSE", "README.md",
                     "scripts/install", "scripts/remove",
                     "scripts/upgrade",
                     "scripts/backup", "scripts/restore")
        non_mandatory = ("script/backup", "script/restore")

        for filename in filenames:
            if file_exists(self.path + "/" + filename):
                continue
            elif filename in non_mandatory:
                print_warning("Consider adding a file %s" % filename)
            else:
                print_error("Providing a %s is mandatory" % filename)

        #
        # Deprecated php-fpm.ini thing
        #

        if file_exists(self.path + "/conf/php-fpm.ini"):
            print_warning(
                "Using a separate php-fpm.ini file is deprecated. "
                "Please merge your php-fpm directives directly in the pool file. "
                "(c.f. https://github.com/YunoHost-Apps/nextcloud_ynh/issues/138 )"
            )

        #
        # Source management
        #
        source_dir = os.path.join(self.path, "sources")
        if os.path.exists(source_dir) \
           and len([name for name in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, name))]) > 5:
            print_warning(
                "[YEP-3.3] Upstream app sources shouldn't be stored in this 'sources' folder of this git repository as a copy/paste\n"
                "During installation, the package should download sources from upstream via 'ynh_setup_source'.\n"
                "See the helper documentation. "
                "Original discussion happened here : "
                "https://github.com/YunoHost/issues/issues/201#issuecomment-391549262"
            )
        #
        # Analyze nginx conf
        # - Deprecated usage of 'add_header' in nginx conf
        # - Spot path traversal issue vulnerability
        #

        for filename in os.listdir(self.path + "/conf") if os.path.exists(self.path + "/conf") else []:
            # Ignore subdirs or filename not containing nginx in the name
            if not os.path.isfile(self.path + "/conf/" + filename) or "nginx" not in filename:
                continue

            #
            # 'add_header' usage
            #
            content = open(self.path + "/conf/" + filename).read()
            if "location" in content and "add_header" in content:
                print_warning(
                    "Do not use 'add_header' in the nginx conf. Use 'more_set_headers' instead. "
                    "(See https://www.peterbe.com/plog/be-very-careful-with-your-add_header-in-nginx "
                    "and https://github.com/openresty/headers-more-nginx-module#more_set_headers )"
                )

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
                        print("(Trying to auto install pyparsing...)")
                        subprocess.check_output("pip3 install pyparsing six", shell=True)
                        import pyparsing
                        print("Ok!")
                        do_path_traversal_check = True
                    except Exception as e:
                        print("Failed :[ : %s" % str(e))

            if not do_path_traversal_check:
                print("N.B.: The package linter need you to run 'pip3 install pyparsing six' if you want it to be able to check for path traversal issue in nginx confs")

            if do_path_traversal_check:
                from lib.nginxparser import nginxparser
                try:
                    nginxconf = nginxparser.load(open(self.path + "/conf/" + filename))
                except Exception as e:
                    print_warning_not_reliable("Could not parse nginx conf ... : " + str(e))
                    nginxconf = []

                for location in find_path_traversal_issue(nginxconf):
                    print_warning(
                        "The nginx configuration (especially location %s) "
                        "appears vulnerable to path traversal issues as explained in\n"
                        "  https://www.acunetix.com/vulnerabilities/web/path-traversal-via-misconfigured-nginx-alias/\n"
                        "  To fix it, look at the first lines of the nginx conf of the example app : \n"
                        "  https://github.com/YunoHost/example_ynh/blob/master/conf/nginx.conf" % location
                    )

    def check_helper_consistency(self):
        """
        check if ynh_install_app_dependencies is present in install/upgrade/restore
        so dependencies are up to date after restoration or upgrade
        """

        install_script = self.scripts["install"]
        if install_script.exists:
            if install_script.contains("ynh_install_app_dependencies"):
                for name in ["upgrade", "restore"]:
                    if self.scripts[name].exists and not self.scripts[name].contains("ynh_install_app_dependencies"):
                        print_warning("ynh_install_app_dependencies should also be in %s script" % name)

            if install_script.contains("yunohost service add"):
                if self.scripts["remove"].exists and not self.scripts["remove"].contains("yunohost service remove"):
                    print_error(
                        "You used 'yunohost service add' in the install script, "
                        "but not 'yunohost service remove' in the remove script."
                    )


    def check_manifest(self):
        manifest = os.path.join(self.path, 'manifest.json')
        if not os.path.exists(manifest):
            return
        print_header("MANIFEST")
        """
        Check if there is no comma syntax issue
        """

        try:
            with open(manifest, encoding='utf-8') as data_file:
                manifest = json.loads(data_file.read(), object_pairs_hook=check_for_duplicate_keys)
        except:
            print_error("[YEP-2.1] Syntax (comma) or encoding issue with manifest.json. Can't check file.")

        fields = ("name", "id", "packaging_format", "description", "url", "version",
                  "license", "maintainer", "requirements", "multi_instance",
                  "services", "arguments")

        for field in fields:
            if field not in manifest:
                print_warning("[YEP-2.1] \"" + field + "\" field is missing")

        """
        Check values in keys
        """

        if "packaging_format" not in manifest:
            print_error("[YEP-2.1] \"packaging_format\" key is missing")
        elif not isinstance(manifest["packaging_format"], int):
            print_error("[YEP-2.1] \"packaging_format\": value isn't an integer type")
        elif manifest["packaging_format"] != 1:
            print_error("[YEP-2.1] \"packaging_format\" field: current format value is '1'")

        # YEP 1.1 Name is app
        if "id" in manifest:
            if not re.match('^[a-z0-9]((_|-)?[a-z0-9])+$', manifest["id"]):
                print_error("[YEP-1.1] 'id' field '%s' should respect this regex '^[a-z0-9]((_|-)?[a-z0-9])+$'")

        if "name" in manifest:
            if len(manifest["name"]) > 22:
                print_warning(
                    "[YEP-1.1] The 'name' field shouldn't be too long to be able to be with one line in the app list. "
                    "The most current bigger name is actually compound of 22 characters."
                )

        # YEP 1.3 License
        def license_mentionned_in_readme(path):
            readme_path = os.path.join(path, 'README.md')
            if os.path.isfile(readme_path):
                return "LICENSE" in open(readme_path).read()
            return False

        if "license" in manifest:
            for license in manifest['license'].replace('&', ',').split(','):
                code_license = '<code property="spdx:licenseId">' + license + '</code>'
                if license == "nonfree":
                    print_warning("[YEP-1.3] The correct value for non free license in license field is 'non-free' and not 'nonfree'")
                    license = "non-free"
                if license in ["free", "non-free", "dep-non-free"]:
                    if not license_mentionned_in_readme(self.path):
                        print_warning(
                            "[YEP-1.3] The use of '%s' in license field implies "
                            " to write something about the license in your README.md" % (license)
                        )
                    if license in ["non-free", "dep-non-free"]:
                        print_warning(
                            "[YEP-1.3] 'non-free' apps can't be officialized. "
                            " Their integration is still being discussed, especially for apps with non-free dependencies"
                        )
                elif code_license not in spdx_licenses():
                    print_warning(
                        "[YEP-1.3] The license '%s' is not registered in https://spdx.org/licenses/ . "
                        "It can be a typo error. If not, you should replace it by 'free' "
                        "or 'non-free' and give some explanations in the README.md." % (license)
                    )

        # YEP 1.4 Inform if we continue to maintain the app
        # YEP 1.5 Update regularly the app status
        # YEP 1.6 Check regularly the evolution of the upstream

        # YEP 1.2 Put the app in a weel known repo
        # YEP 1.7 - Add an app to the YunoHost-Apps organization
        if "id" in manifest:

            cachefile = "./.apps.json"
            app_list = None
            if os.path.exists(cachefile) and time.time() - os.path.getmtime(cachefile) < 3600:
                try:
                    app_list = open(cachefile).read()
                    app_list = json.loads(app_list)
                except:
                    print("Uuuuh failed to load apps.json from cache...")
                    app_list = None

            if app_list is None:
                app_list_url = "https://raw.githubusercontent.com/YunoHost/apps/master/apps.json"
                app_list = urlopen(app_list_url)['content']
                open(cachefile, "w").write(app_list)
                app_list = json.loads(app_list)

            if manifest["id"] not in app_list:
                print_warning("[YEP-1.2] This app is not registered in our applications list")

            all_urls = [infos.get("url", "").lower() for infos in app_list.values()]

            repo_org = "https://github.com/YunoHost-Apps/%s_ynh" % (manifest["id"])
            repo_brique = "https://github.com/labriqueinternet/%s_ynh" % (manifest["id"])

            if repo_org.lower() not in all_urls and repo_brique.lower() not in all_urls:
                is_not_added_to_org =  urlopen(repo_org)['code'] == 404
                is_not_added_to_brique =  urlopen(repo_brique)['code'] == 404

                if is_not_added_to_org and is_not_added_to_brique:
                    print_warning("[YEP-1.7] You should add your app in the YunoHost-Apps organisation.")

        # YEP 1.8 Publish test request
        # YEP 1.9 Document app
        if "description" in manifest:
            descr = manifest.get("description", "")
            if isinstance(descr, dict):
                descr = descr.get("en", "")

            if len(descr) < 5:
                print_warning(
                    "[YEP-1.9] You should write a good description of the app, "
                    "at least in english (1 line is enough)."
                )

            if len(descr) > 150:
                print_warning(
                    "[YEP-1.9] Please use a shorter description (or the rendering on the webadmin / app list will be messy ...). Just describe in consise terms what the app is / does."
                )

            elif "for yunohost" in descr.lower() :
                print_warning(
                    "[YEP-1.9] The 'description' should explain what the app actually does. "
                    "No need to say that it is 'for YunoHost' - this is a YunoHost app "
                    "so of course we know it is for YunoHost ;-)."
                )
            if descr.lower().startswith(manifest["id"].lower()) or descr.lower().startswith(manifest["name"].lower()):
                print_warning("[YEP-1.9] Try to avoid starting the description by '$app is' ... explain what the app is / does directly !")

        # TODO test a specific template in README.md

        # YEP 1.10 Garder un historique de version propre

        if not "version" in manifest or manifest["version"][-5:-1] != "~ynh":
            print_warning("Please specify a 'version' field in the manifest. It should match the format <upstreamversion>~ynh<packageversion>. For example : 4.3-2~ynh3. It is composed of the upstream version number (in the example, 4.3-2) and an incremental number for each change in the package without upstream change (in the example, 3). This incremental number can be reset to 1 each time the upstream version changes.")

        # YEP 1.11 Cancelled

        # YEP 2.1
        if "multi_instance" in manifest and manifest["multi_instance"] != 1 and manifest["multi_instance"] != 0:
            print_error(
                "[YEP-2.1] \"multi_instance\" field must be boolean type values 'true' or 'false' and not string type")

        if "services" in manifest and self.scripts["install"].exists:

            known_services = ("nginx", "mysql", "uwsgi", "metronome",
                              "php5-fpm", "php7.0-fpm", "php-fpm",
                              "postfix", "dovecot", "rspamd")

            for service in manifest["services"]:
                if service not in known_services:
                    if service == 'postgresql':
                        if not self.scripts["install"].contains('ynh_psql_test_if_first_run')\
                           or not self.scripts["restore"].contains('ynh_psql_test_if_first_run'):
                            print_error("[YEP-2.1?] postgresql service present in the manifest, install and restore scripts must call ynh_psql_test_if_first_run")
                    elif not self.scripts["install"].contains("yunohost service add %s" % service):
                        print_error("[YEP-2.1?] " + service + " service not installed by the install file but present in the manifest")

        if "install" in manifest["arguments"]:

            recognized_types = ("domain", "path", "boolean", "app", "password", "user", "string", "display_text")

            for argument in manifest["arguments"]["install"]:
                if "optional" in argument.keys():
                    if not isinstance(argument["optional"], bool):
                        print_warning("The key 'optional' value for setting %s should be a boolean (true or false)" % argument["name"])
                if "type" not in argument.keys():
                    print_warning(
                        "[YEP-2.1] You should specify the type of the argument '%s'. "
                        "You can use : %s." % (argument["name"], ', '.join(recognized_types))
                    )
                elif argument["type"] not in recognized_types:
                    print_warning(
                        "[YEP-2.1] The type '%s' for argument '%s' is not recognized... "
                        "it probably doesn't behave as you expect ? Choose among those instead : %s" % (argument["type"], argument["name"], ', '.join(recognized_types))
                    )

                if "choices" in argument.keys():
                    choices = [c.lower() for c in argument["choices"]]
                    if len(choices) == 2:
                        if ("true" in choices and "false" in choices) or ("yes" in choices and "no" in choices):
                            print_warning(
                                "Argument %s : you might want to simply use a boolean-type argument. "
                                "No need to specify the choices list yourself." % argument["name"]
                            )

                if argument["name"] == "is_public" and "help" not in argument.keys():
                    print_warning_not_reliable(
                        "Consider adding an 'help' key for argument 'is_public' "
                        "to explain to the user what it means for *this* app "
                        "to be public or private :\n"
                        '    "help": {\n'
                        '       "en": "Some explanation"\n'
                        '    }')


        if "url" in manifest and manifest["url"].endswith("_ynh"):
            print_warning(
                "'url' is not meant to be the url of the yunohost package, "
                "but rather the website or repo of the upstream app itself..."
            )

        self.yunohost_version_req = manifest.get("requirements", {}).get("yunohost", None)


class Script():

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
                    print("Some lines could not be parsed in script %s. (That's probably not really critical)" % self.name)
                    some_parsing_failed = True
                print_warning_not_reliable("%s : %s" % (e, line))

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

    def analyze(self):

        print_header(self.name.upper() + " SCRIPT")

        self.check_set_usage()
        self.check_helper_usage_dependencies()
        self.check_deprecated_practices()

    def check_set_usage(self):

        if self.name == "_common.sh":
            return

        present = False

        if self.name in ["backup", "remove"]:
            present = self.contains("ynh_abort_if_errors") or self.contains("set -eu")
        else:
            present = self.contains("ynh_abort_if_errors")

        if self.name == "remove":
            # Remove script shouldn't use set -eu or ynh_abort_if_errors
            if present:
                print_error(
                    "[YEP-2.4] set -eu or ynh_abort_if_errors is present. "
                    "If there is a crash, it could put yunohost system in "
                    "a broken state. For details, look at "
                    "https://github.com/YunoHost/issues/issues/419"
                )
        elif not present:
            print_error(
                "[YEP-2.4] ynh_abort_if_errors is missing. For details, "
                "look at https://github.com/YunoHost/issues/issues/419"
            )

    def check_helper_usage_dependencies(self):
        """
        Detect usage of ynh_package_* & apt-get *
        and suggest herlpers ynh_install_app_dependencies and ynh_remove_app_dependencies
        """

        # Skip this in common.sh, sometimes custom not-yet-official helpers need this
        if self.name == "_common.sh":
            return

        if self.contains("ynh_package_install") or self.contains("apt-get install"):
            print_warning(
                "You should not use `ynh_package_install` or `apt-get install`, "
                "use `ynh_install_app_dependencies` instead"
            )

        if self.contains("ynh_package_remove") or self.contains("apt-get remove"):
            print_warning(
                "You should not use `ynh_package_remove` or `apt-get remove`, "
                "use `ynh_remove_app_dependencies` instead"
            )

    def check_deprecated_practices(self):

        if self.contains("yunohost app setting"):
            print_error("Do not use 'yunohost app setting' directly. Please use 'ynh_app_setting_(set,get,delete)' instead.")
        if self.contains("yunohost app checkurl"):
            print_error("'yunohost app checkurl' is obsolete!!! Please use 'ynh_webpath_register' instead.")
        if self.contains("yunohost app checkport"):
            print_error("'yunohost app checkport' is obsolete!!! Please use 'ynh_find_port' instead.")
        if self.contains("yunohost app initdb"):
            print_error("'yunohost app initdb' is obsolete!!! Please use 'ynh_mysql_setup_db' instead.")
        if self.contains("exit"):
            print_warning("'exit' command shouldn't be used. Please use 'ynh_die' instead.")

        if self.contains("yunohost service regen-conf"):
            print_warning("'yunohost tools regen-conf' has been replaced by 'yunohost tools regen-conf'.")

        # Dirty hack to check only the 10 last lines for ssowatconf
        # (the "bad" practice being using this at the very end of the script, but some apps legitimately need this in the middle of the script)
        oldlines = list(self.lines)
        self.lines = self.lines[-10:]
        if self.contains("yunohost app ssowatconf"):
            print_warning("You probably don't need to run 'yunohost app ssowatconf' in the app script. It's supposed to be ran automatically after the script.")
        self.lines = oldlines

        if self.contains("rm -rf"):
            print_error("[YEP-2.12] You should avoid using 'rm -rf', please use 'ynh_secure_remove' instead")

        if self.containsregex(r"sed\s+(-i|--in-place)\s+(-r\s+)?s") or self.containsregex(r"sed\s+s\S*\s+(-i|--in-place)"):
            print_warning("[YEP-2.12] You should avoid using 'sed -i' for substitutions, please use 'ynh_replace_string' instead")
        if self.containsregex(r"sudo \w"):  # \w is here to not match sudo -u, legit use because ynh_exec_as not official yet...
            print_warning(
                "[YEP-2.12] You should not need to use 'sudo', the script is being run as root. "
                "(If you need to run a command using a specific user, use 'ynh_exec_as')"
            )

        if self.containsregex(r"chmod .*777") or self.containsregex(r'chmod .*o\+w'):
            print_warning(
                "DO NOT use chmod 777 or chmod o+w that gives write permission to every users on the system !!! If you have permission issues, just make sure that the owner and/or group owner is right ..."
            )

        if self.contains("dd if=/dev/urandom") or self.contains("openssl rand"):
            print_warning(
                "Instead of 'dd if=/dev/urandom' or 'openssl rand', "
                "you might want to use ynh_string_random"
            )

        if self.contains("systemctl restart nginx") or self.contains("service nginx restart"):
            print_error(
                "Restarting nginx is quite dangerous (especially for web installs) "
                "and should be avoided at all cost. Use 'reload' instead."
            )

        if self.name == "install" and not self.contains("ynh_print_info") and not self.contains("ynh_script_progression"):
            print_warning(
                "Please add a few messages for the user, to explain what is going on "
                "(in friendly, not-too-technical terms) during the installation. "
                "You can use 'ynh_print_info' or 'ynh_script_progression' for this."
            )

        if self.name == "install" and self.containsregex(r"^\w+\=\$\{?[0-9]"):
            print_error(
                "Do not fetch arguments from manifest using variable=$N (e.g."
                " domain=$1 ...) Instead, use name=$YNH_APP_ARG_NAME"
            )

        if self.name == "install":
            if self.contains("/etc/apt/sources.list") \
            or (os.path.exists(self.app_path + "/scripts/_common.sh") and "/etc/apt/sources.list" in open(self.app_path+"/scripts/_common.sh").read() and "ynh_add_repo" not in open(self.app_path+"/scripts/_common.sh").read()):
                print_error(
                    "[YEP-3.7] Manually messing with apt's sources.lists is strongly discouraged "
                    "and should be avoided. Please use ynh_install_extra_app_dependencies is you "
                    "need to install dependencies from a custom apt repo."
                )

        if self.name == "backup":
            if self.containsregex("^ynh_systemd_action"):
                print_warning("Unless you really have a good reason to do so, starting/stopping services during backup has no benefit and leads to unecessary service interruptions when creating backups... As a 'reminder': apart from possibly database dumps (which usually do not require the service to be stopped) or other super-specific action, running the backup script is only a *declaration* of what needs to be backuped. The real copy and archive creation happens *after* the backup script is ran.")

        helpers_after_official = subprocess.check_output("head -n 30 '%s' | grep -A 10 '^ *source */usr/share/yunohost/helpers' | grep '^ *source' | tail -n +2" % self.path, shell=True).decode("utf-8")
        helpers_after_official = helpers_after_official.replace("source", "").replace(" ", "").strip()
        if helpers_after_official:
            helpers_after_official = helpers_after_official.split("\n")
            print_warning("Please avoid sourcing additional helpers after the official helpers (in this case file %s)" % ", ".join(helpers_after_official))

        if self.name in ["backup", "restore"]:
            if self.contains("source _common.sh") or self.contains("source ./_common.sh"):
                print_warning("In the context of backup and restore script, you should load _common.sh with \"source ../settings/scripts/_common.sh\"")

        # Usage of ynh_script_prorgression with --time or --weight=1 all over the place...
        if self.containsregex(r"ynh_script_progression.*--time"):
            print_warning("Using ynh_script_progression --time should only be for calibrating the weight (c.f. --weight). It's not meant to be kept for production versions.")
        if self.containsregex(r"ynh_script_progression.*--weight=1") \
            and not self.containsregex(r"ynh_script_progression.*--weight=([^1]|[1-9][0-9]+)"):
            print_warning("Having only '--weight=1' for ynh_script_progression is useless... Either calibrate the weights with --time once, or don't put any --weight at all.")



def main():
    if len(sys.argv) != 2:
        print("Give one app package path.")
        exit()

    app_path = sys.argv[1]
    header(app_path)
    App(app_path).analyze()

    if error_count > 0:
        sys.exit(1)
    elif warning_count > 3:
        print("Still some warnings to be fixed :s")
    elif warning_count > 0:
        print("Only %s warning remaining! You can do it!" % warning_count)
    else:
        print_happy("Not even a warning! Congratz and thank you for keeping that package up to date with good practices !")



if __name__ == '__main__':
    main()
