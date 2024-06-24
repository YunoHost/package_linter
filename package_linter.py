#!/usr/bin/env python3
# -*- coding: utf8 -*-

import copy
import sys
import os
import re
import json
import shlex
import urllib.request
import subprocess
import time
import statistics
from datetime import datetime

try:
    import toml
except Exception:
    os.system("pip3 install toml")
    import toml

try:
    import jsonschema
except Exception:
    os.system("pip3 install jsonschema")
    import jsonschema


# ############################################################################
#  Helper list
# ############################################################################

# Generated May 20 2024 using:
# cat /path/to/yunohost/data/helpers.d/* | grep  "^ynh_" | tr -d '(){ ' > helperlist 2>/dev/null
# for HELPER in $(cat helperlist); do REQUIRE=$(grep -whB5 "^$HELPER" /path/to/yunohost/data/helpers.d/* 2>/dev/null | grep "Requires .* or higher\." | grep -o -E "[0-9].[0-9].[0-9]"); echo "'$HELPER': '$REQUIRE'",; done | tr "'" '"'

official_helpers = {
    "ynh_install_apps": "",
    "ynh_remove_apps": "",
    "ynh_spawn_app_shell": "",
    "ynh_wait_dpkg_free": "3.3.1",
    "ynh_package_is_installed": "2.2.4",
    "ynh_package_version": "2.2.4",
    "ynh_apt": "2.4.0",
    "ynh_package_update": "2.2.4",
    "ynh_package_install": "2.2.4",
    "ynh_package_remove": "2.2.4",
    "ynh_package_autoremove": "2.2.4",
    "ynh_package_autopurge": "2.7.2",
    "ynh_package_install_from_equivs": "2.2.4",
    "ynh_install_app_dependencies": "2.6.4",
    "ynh_add_app_dependencies": "3.8.1",
    "ynh_remove_app_dependencies": "2.6.4",
    "ynh_install_extra_app_dependencies": "3.8.1",
    "ynh_install_extra_repo": "3.8.1",
    "ynh_remove_extra_repo": "3.8.1",
    "ynh_add_repo": "3.8.1",
    "ynh_pin_repo": "3.8.1",
    "ynh_backup": "2.4.0",
    "ynh_restore": "2.6.4",
    "ynh_restore_file": "2.6.4",
    "ynh_store_file_checksum": "2.6.4",
    "ynh_backup_if_checksum_is_different": "2.6.4",
    "ynh_delete_file_checksum": "3.3.1",
    "ynh_backup_archive_exists": "",
    "ynh_backup_before_upgrade": "2.7.2",
    "ynh_restore_upgradebackup": "2.7.2",
    "ynh_app_config_get_one": "",
    # Commenting out config panel helpers
    # that may legitimately be overwritten from config script
    # "ynh_app_config_get": "",
    # "ynh_app_config_show": "",
    # "ynh_app_config_validate": "",
    "ynh_app_config_apply_one": "",
    # "ynh_app_config_apply": "",
    # "ynh_app_action_run": "",
    # "ynh_app_config_run": "",
    "ynh_add_fail2ban_config": "4.1.0",
    "ynh_remove_fail2ban_config": "3.5.0",
    "ynh_handle_getopts_args": "3.2.2",
    "ynh_go_try_bash_extension": "",
    "ynh_use_go": "",
    "ynh_install_go": "",
    "ynh_remove_go": "",
    "ynh_cleanup_go": "",
    "ynh_get_ram": "3.8.1",
    "ynh_require_ram": "3.8.1",
    "ynh_die": "2.4.0",
    "ynh_print_info": "3.2.0",
    "ynh_print_log": "3.2.0",
    "ynh_print_warn": "3.2.0",
    "ynh_print_err": "3.2.0",
    "ynh_exec_err": "3.2.0",
    "ynh_exec_warn": "3.2.0",
    "ynh_exec_warn_less": "3.2.0",
    "ynh_exec_quiet": "3.2.0",
    "ynh_exec_fully_quiet": "3.2.0",
    "ynh_exec_and_print_stderr_only_if_error": "",
    "ynh_print_OFF": "3.2.0",
    "ynh_print_ON": "3.2.0",
    "ynh_script_progression": "3.5.0",
    "ynh_return": "3.6.0",
    "ynh_use_logrotate": "2.6.4",
    "ynh_remove_logrotate": "2.6.4",
    "ynh_multimedia_build_main_dir": "",
    "ynh_multimedia_addfolder": "",
    "ynh_multimedia_addaccess": "",
    "ynh_mysql_connect_as": "2.2.4",
    "ynh_mysql_execute_as_root": "2.2.4",
    "ynh_mysql_execute_file_as_root": "2.2.4",
    "ynh_mysql_create_db": "2.2.4",
    "ynh_mysql_drop_db": "2.2.4",
    "ynh_mysql_dump_db": "2.2.4",
    "ynh_mysql_create_user": "2.2.4",
    "ynh_mysql_user_exists": "2.2.4",
    "ynh_mysql_drop_user": "2.2.4",
    "ynh_mysql_setup_db": "2.6.4",
    "ynh_mysql_remove_db": "2.6.4",
    "ynh_find_port": "2.6.4",
    "ynh_port_available": "3.8.0",
    "ynh_validate_ip": "2.2.4",
    "ynh_validate_ip4": "2.2.4",
    "ynh_validate_ip6": "2.2.4",
    "ynh_add_nginx_config": "4.1.0",
    "ynh_remove_nginx_config": "2.7.2",
    "ynh_change_url_nginx_config": "11.1.9",
    "ynh_use_nodejs": "2.7.1",
    "ynh_install_nodejs": "2.7.1",
    "ynh_remove_nodejs": "2.7.1",
    "ynh_cron_upgrade_node": "2.7.1",
    "ynh_permission_create": "3.7.0",
    "ynh_permission_delete": "3.7.0",
    "ynh_permission_exists": "3.7.0",
    "ynh_permission_url": "3.7.0",
    "ynh_permission_update": "3.7.0",
    "ynh_permission_has_user": "3.7.1",
    "ynh_legacy_permissions_exists": "4.1.2",
    "ynh_legacy_permissions_delete_all": "4.1.2",
    "ynh_add_fpm_config": "4.1.0",
    "ynh_remove_fpm_config": "2.7.2",
    "ynh_get_scalable_phpfpm": "",
    "ynh_composer_exec": "",
    "ynh_install_composer": "",
    "ynh_psql_connect_as": "3.5.0",
    "ynh_psql_execute_as_root": "3.5.0",
    "ynh_psql_execute_file_as_root": "3.5.0",
    "ynh_psql_create_db": "3.5.0",
    "ynh_psql_drop_db": "3.5.0",
    "ynh_psql_dump_db": "3.5.0",
    "ynh_psql_create_user": "3.5.0",
    "ynh_psql_user_exists": "3.5.0",
    "ynh_psql_database_exists": "3.5.0",
    "ynh_psql_drop_user": "3.5.0",
    "ynh_psql_setup_db": "2.7.1",
    "ynh_psql_remove_db": "2.7.1",
    "ynh_psql_test_if_first_run": "2.7.1",
    "ynh_redis_get_free_db": "",
    "ynh_redis_remove_db": "",
    "ynh_use_ruby": "",
    "ynh_install_ruby": "",
    "ynh_remove_ruby": "",
    "ynh_cleanup_ruby": "",
    "ynh_ruby_try_bash_extension": "",
    "ynh_app_setting_get": "2.2.4",
    "ynh_app_setting_set": "2.2.4",
    "ynh_app_setting_delete": "2.2.4",
    "ynh_app_setting": "",
    "ynh_webpath_available": "2.6.4",
    "ynh_webpath_register": "2.6.4",
    "ynh_string_random": "2.2.4",
    "ynh_replace_string": "2.6.4",
    "ynh_replace_special_string": "2.7.7",
    "ynh_sanitize_dbid": "2.2.4",
    "ynh_normalize_url_path": "2.6.4",
    "ynh_add_systemd_config": "4.1.0",
    "ynh_remove_systemd_config": "2.7.2",
    "ynh_systemd_action": "3.5.0",
    "ynh_clean_check_starting": "3.5.0",
    "ynh_user_exists": "2.2.4",
    "ynh_user_get_info": "2.2.4",
    "ynh_user_list": "2.4.0",
    "ynh_system_user_exists": "2.2.4",
    "ynh_system_group_exists": "3.5.0",
    "ynh_system_user_create": "2.6.4",
    "ynh_system_user_delete": "2.6.4",
    "ynh_exec_as": "4.1.7",
    "ynh_exit_properly": "2.6.4",
    "ynh_abort_if_errors": "2.6.4",
    "ynh_setup_source": "2.6.4",
    "ynh_local_curl": "2.6.4",
    "ynh_add_config": "4.1.0",
    "ynh_replace_vars": "4.1.0",
    "ynh_read_var_in_file": "",
    "ynh_write_var_in_file": "",
    "ynh_render_template": "",
    "ynh_get_debian_release": "2.7.1",
    "ynh_secure_remove": "2.6.4",
    "ynh_read_manifest": "3.5.0",
    "ynh_app_upstream_version": "3.5.0",
    "ynh_app_package_version": "3.5.0",
    "ynh_check_app_version_changed": "3.5.0",
    "ynh_compare_current_package_version": "3.8.0",
}

deprecated_helpers_in_v2 = [
    ("ynh_clean_setup", "(?)"),
    ("ynh_abort_if_errors", "nothing, handled by the core, just get rid of it"),
    ("ynh_backup_before_upgrade", "nothing, handled by the core, just get rid of it"),
    ("ynh_restore_upgradebackup", "nothing, handled by the core, just get rid of it"),
    ("ynh_system_user_create", "the system_user resource"),
    ("ynh_system_user_delete", "the system_user resource"),
    ("ynh_webpath_register", "the permission resource"),
    ("ynh_webpath_available", "the permission resource"),
    ("ynh_permission_update", "the permission resource"),
    ("ynh_permission_create", "the permission resource"),
    ("ynh_permission_exists", "the permission resource"),
    ("ynh_legacy_permissions_exists", "the permission resource"),
    ("ynh_legacy_permissions_delete_all", "the permission resource"),
    ("ynh_install_app_dependencies", "the apt resource"),
    ("ynh_install_extra_app_dependencies", "the apt source"),
    ("ynh_remove_app_dependencies", "the apt resource"),
    ("ynh_psql_test_if_first_run", "the database resource"),
    ("ynh_mysql_setup_db", "the database resource"),
    ("ynh_psql_setup_db", "the database resource"),
    ("ynh_mysql_remove_db", "the database resource"),
    ("ynh_psql_remove_db", "the database resource"),
    ("ynh_find_port", "the port resource"),
    (
        "ynh_send_readme_to_admin",
        "the doc/POST_INSTALL.md or POST_UPGRADE.md mechanism",
    ),
]

# Default to 1, set to 2 automatically if a toml manifest is found
app_packaging_format = None

# ############################################################################
#   Utilities
# ############################################################################


class c:
    HEADER = "\033[94m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    MAYBE_FAIL = "\033[96m"
    FAIL = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class TestReport:
    def __init__(self, message):
        self.message = message

    def display(self, prefix=""):
        _print(prefix + self.style % self.message)


class Warning(TestReport):
    style = c.WARNING + " ! %s " + c.END


class Error(TestReport):
    style = c.FAIL + " ✘ %s" + c.END


class Info(TestReport):
    style = " - %s" + c.END


class Success(TestReport):
    style = c.OKGREEN + " ☺  %s ♥" + c.END


class Critical(TestReport):
    style = c.FAIL + " ✘✘✘ %s" + c.END


output = "plain"


def _print(*args, **kwargs):
    if output == "plain":
        print(*args, **kwargs)


def report_warning_not_reliable(str):
    _print(c.MAYBE_FAIL + "?", str, c.END)


def print_happy(str):
    _print(c.OKGREEN + " ☺ ", str, "♥")


def urlopen(url):
    try:
        conn = urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        return {"content": "", "code": e.code}
    except urllib.error.URLError as e:
        _print("Could not fetch %s : %s" % (url, e))
        return {"content": "", "code": 0}
    return {"content": conn.read().decode("UTF8"), "code": 200}


def file_exists(file_path):
    return os.path.isfile(file_path) and os.stat(file_path).st_size > 0


def cache_file(cachefile: str, ttl_s: int):
    def cache_is_fresh():
        return (
            os.path.exists(cachefile)
            and time.time() - os.path.getmtime(cachefile) < ttl_s
        )

    def decorator(function):
        def wrapper(*args, **kwargs):
            if not cache_is_fresh():
                with open(cachefile, "w+") as outfile:
                    outfile.write(function(*args, **kwargs))
            return open(cachefile).read()

        return wrapper

    return decorator


@cache_file(".spdx_licenses", 3600)
def spdx_licenses():
    return urlopen("https://spdx.org/licenses/")["content"]


@cache_file(".manifest.v2.schema.json", 3600)
def manifest_v2_schema():
    return urlopen(
        "https://raw.githubusercontent.com/YunoHost/apps/master/schemas/manifest.v2.schema.json"
    )["content"]


@cache_file(".tests.v1.schema.json", 3600)
def tests_v1_schema():
    return urlopen(
        "https://raw.githubusercontent.com/YunoHost/apps/master/schemas/tests.v1.schema.json"
    )["content"]


@cache_file(".config_panel.v1.schema.json", 3600)
def config_panel_v1_schema():
    return urlopen(
        "https://raw.githubusercontent.com/YunoHost/apps/master/schemas/config_panel.v1.schema.json"
    )["content"]


def validate_schema(name: str, schema, data):
    v = jsonschema.Draft7Validator(schema)

    for error in v.iter_errors(data):
        try:
            error_path = " > ".join(error.path)
        except:
            error_path = str(error.path)

        yield Info(
            f"Error validating {name} using schema: in key {error_path}\n       {error.message}"
        )


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
        tests[clsname].append((f, kwargs))
        return f

    return decorator


class TestSuite:
    def run_tests(self):

        reports = []

        for test, options in tests[self.__class__.__name__]:
            if "only" in options and self.name not in options["only"]:
                continue
            if "ignore" in options and self.name in options["ignore"]:
                continue

            this_test_reports = list(test(self))
            for report in this_test_reports:
                report.test_name = test.__qualname__

            reports += this_test_reports

        # Display part

        def report_type(report):
            return report.__class__.__name__.lower()

        if any(report_type(r) in ["warning", "error", "critical"] for r in reports):
            prefix = c.WARNING + "! "
        elif any(report_type(r) in ["info"] for r in reports):
            prefix = "ⓘ "
        else:
            prefix = c.OKGREEN + "✔ "

        _print(" " + c.BOLD + prefix + c.OKBLUE + self.test_suite_name + c.END)

        if len(reports):
            _print("")

        for report in reports:
            report.display(prefix="   ")

        if len(reports):
            _print("")

        for report in reports:
            tests_reports[report_type(report)].append((report.test_name, report))

    def run_single_test(self, test):

        reports = list(test(self))

        def report_type(report):
            return report.__class__.__name__.lower()

        for report in reports:
            report.display()
            test_name = test.__qualname__
            tests_reports[report_type(report)].append((test_name, report))


# Defined in packaging module
# See https://github.com/pypa/packaging/blob/20cd09e00917adbc4afeaa753be831a6bc2740f7/packaging/version.py#L225
VERSION_PATTERN = r"""
    v?
    (?:
        (?:(?P<epoch>[0-9]+)!)?                           # epoch
        (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?P<pre>                                          # pre-release
            [-_\.]?
            (?P<pre_l>(a|b|c|rc|alpha|beta|pre|preview))
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>                                         # post release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                [-_\.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>                                          # dev release
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
    (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
"""

# ############################################################################
#   Actual high-level checks
# ############################################################################

scriptnames = ["_common.sh", "install", "remove", "upgrade", "backup", "restore"]


class App(TestSuite):
    def __init__(self, path):

        _print("  Analyzing app %s ..." % path)
        self.path = path
        self.manifest_ = Manifest(self.path)
        self.manifest = self.manifest_.manifest
        self.scripts = {f: Script(self.path, f) for f in scriptnames}
        self.configurations = Configurations(self)
        self.app_catalog = AppCatalog(self.manifest["id"])

        self.test_suite_name = "General stuff, misc helper usage"

        _print()

    def analyze(self):

        self.manifest_.run_tests()

        for script in [self.scripts[s] for s in scriptnames if self.scripts[s].exists]:
            script.run_tests()

        self.run_tests()
        self.configurations.run_tests()
        self.app_catalog.run_tests()

        self.report()

    def report(self):

        _print(" =======")

        # These are meant to be the last stuff running, they are based on
        # previously computed errors/warning/successes
        self.run_single_test(App.qualify_for_level_7)
        self.run_single_test(App.qualify_for_level_8)
        self.run_single_test(App.qualify_for_level_9)

        if output == "json":
            print(
                json.dumps(
                    {
                        "success": [test for test, _ in tests_reports["success"]],
                        "info": [test for test, _ in tests_reports["info"]],
                        "warning": [test for test, _ in tests_reports["warning"]],
                        "error": [test for test, _ in tests_reports["error"]],
                        "critical": [test for test, _ in tests_reports["critical"]],
                    },
                    indent=4,
                )
            )
            return

        if tests_reports["error"] or tests_reports["critical"]:
            sys.exit(1)

    def qualify_for_level_7(self):

        if tests_reports["critical"]:
            _print(" There are some critical issues in this app :(")
        elif tests_reports["error"]:
            _print(" Uhoh there are some errors to be fixed :(")
        elif len(tests_reports["warning"]) >= 3:
            _print(" Still some warnings to be fixed :s")
        elif len(tests_reports["warning"]) == 2:
            _print(" Only 2 warnings remaining! You can do it!")
        elif len(tests_reports["warning"]) == 1:
            _print(" Only 1 warning remaining! You can do it!")
        else:
            yield Success(
                "Not even a warning! Congratz and thank you for keeping this package up to date with good practices! This app qualifies for level 7!"
            )

    def qualify_for_level_8(self):

        successes = [test.split(".")[1] for test, _ in tests_reports["success"]]

        # Level 8 = qualifies for level 7 + maintained + long term good quality
        catalog_infos = self.app_catalog.catalog_infos
        antifeatures = catalog_infos and catalog_infos.get("antifeatures", [])

        if any(
            af in antifeatures
            for af in [
                "package-not-maintained",
                "deprecated-software",
                "alpha-software",
                "replaced-by-another-app",
            ]
        ):
            _print(
                " In the catalog, the app is flagged as not maintained / deprecated / alpha or replaced by another app, therefore does not qualify for level 8"
            )
        elif (
            "qualify_for_level_7" in successes
            and "is_long_term_good_quality" in successes
        ):
            yield Success(
                "The app is maintained and long-term good quality, and therefore qualifies for level 8!"
            )

    def qualify_for_level_9(self):

        if self.app_catalog.catalog_infos.get("high_quality", False):
            yield Success("The app is flagged as high-quality in the app catalog")

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
    def v1packaging(app):
        if app_packaging_format <= 1:
            if datetime.today() >= datetime(2025, 2, 1):
                yield Error(
                    "This app is still using packaging v1 which is now hard-deprecated. Packaging v2 was released more than two years ago. You should really have a look at https://yunohost.org/en/packaging_v2."
                )
            elif datetime.today() >= datetime(2024, 2, 1):
                yield Warning(
                    "This app is still using packaging v1 which is now softly-deprecated. Packaging v2 was released more than one year ago and is now used by 75% of the app catalog with many other v1->v2 app transition ongoing. We encourage you to convert this app to packaging v2 following the recommendations described in https://yunohost.org/en/packaging_v2. This warning will turn into an error on February 1st, 2025."
                )

    @test()
    def mandatory_scripts(app):
        filenames = (
            "LICENSE",
            "README.md",
            "scripts/install",
            "scripts/remove",
            "scripts/upgrade",
            "scripts/backup",
            "scripts/restore",
        )

        for filename in filenames:
            if not file_exists(app.path + "/" + filename):
                yield Error("Providing %s is mandatory" % filename)

        if file_exists(app.path + "/LICENSE"):
            license_content = open(app.path + "/LICENSE").read()
            if "File containing the license of your package" in license_content:
                yield Error("You should put an actual license in LICENSE...")

    @test()
    def doc_dir(app):

        if not os.path.exists(app.path + "/doc"):
            if app_packaging_format <= 1:
                yield Warning(
                    """READMEs are to be automatically generated using https://github.com/YunoHost/apps/tree/master/tools/README-generator.
    - You are encouraged to create a doc/DISCLAIMER.md file, which should contain any important information to be presented to the admin before installation. Check https://github.com/YunoHost/example_ynh/blob/master/doc/DISCLAIMER.md for more details (it should be somewhat equivalent to the old 'Known limitations' and 'Specific features' section). (It's not mandatory to create this file if you're absolutely sure there's no relevant info to show to the user)
    - If relevant for this app, screenshots can be added in a doc/screenshots/ folder."""
                )
            elif app_packaging_format >= 2:
                yield Error(
                    """Having a doc/ folder is now mandatory in packaging v2 and is expected to contain :
    - (recommended) doc/DESCRIPTION.md : a long description of the app, typically around 5~20 lines, for example to list features
    - (recommended) doc/screenshots/ : a folder containing at least one .png (or .jpg) screenshot of the app
    - (if relevant) doc/ADMIN.md : an admin doc page meant to provide general info about adminstrating this app, will be available in yunohost's webadmin
    - (if relevant) doc/SOME_OTHER_PAGE.md : an arbitrarily named admin doc page meant to provide info on a specific topic, will be available in yunohost's webadmin
    - (if relevant) doc/PRE_INSTALL.md, POST_INSTALL.md : important informations to display to the user before/after the install (similar mechanism exists for upgrade)
"""
                )

        if os.path.exists(os.path.join(app.path, "doc/screenshots")):
            du_output = subprocess.check_output(
                ["du", "-sb", app.path + "/doc/screenshots"], shell=False
            )
            screenshots_size = int(du_output.split()[0])
            if screenshots_size > 512000:
                yield Info(
                    "Consider keeping the content of doc/screenshots under ~512Kb for better UI/UX once the screenshots will be integrated in the webadmin app's catalog (to be discussed with the team)"
                )

            for _, _, files in os.walk(os.path.join(app.path, "doc/screenshots")):
                for file in files:
                    if file == ".gitkeep":
                        continue
                    if all(
                        not file.lower().endswith(ext)
                        for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]
                    ):
                        yield Warning(
                            "In the doc/screenshots folder, only .jpg, .jpeg, .png, .webp and .gif are accepted"
                        )
                        break

    @test()
    def doc_dir_v2(app):

        if app_packaging_format <= 1:
            return

        if os.path.exists(app.path + "/doc") and not os.path.exists(
            app.path + "/doc/DESCRIPTION.md"
        ):
            yield Error(
                "A DESCRIPTION.md is now mandatory in packaging v2 and is meant to contains an extensive description of what the app is and does. Consider also adding a '/doc/screenshots/' folder with a few screenshots of what the app looks like."
            )
        elif (
            os.system(
                rf'grep -inrq "Some long and extensive description\|lorem ipsum dolor sit amet\|Ut enim ad minim veniam" {app.path}/doc/DESCRIPTION.md'
            )
            == 0
        ):
            yield Error("It looks like DESCRIPTION.md just contains placeholder texts")

        if os.path.exists(app.path + "/doc/DISCLAIMER.md"):
            yield Warning(
                """The whole thing about doc/DISCLAIMER.md is refactored again in v2 (sorry about that :/) to improve the UX - basically people shouldnt have to actively go read the READMEs to get those infos

    You are encouraged to split its infos into:

    - Integration-related infos (eg. LDAP/SSO support, arch support, resource usage, ...)
        -> neant to go in the 'integration' section of the manifest.toml

    - Antifeatures-related infos (eg. alpha/deprecated software, arbitrary limiations, ...)
        -> these are now formalized using the 'antifeatures' mechanism in the app catalog directly : cf https://github.com/YunoHost/apps/blob/master/antifeatures.yml and the 'antifeatures' key in apps.json

    - Important infos that the admin should be made aware of *before* or *after* the install
        -> infos *before* the install are meant to go in 'doc/PRE_INSTALL.md'
        -> infos *after* the install are meant to go in 'doc/POST_INSTALL.md' (mostly meant to replace ynh_send_readme_to_admin, typically tips about how to login for the first time on the app / finish the install, ...).
        -> these will be shown to the admin before/after the install (and the post_install notif will also be available in the app info page)
        -> note that in these files, the __FOOBAR__ syntax is supported and replaced with the corresponding 'foobar' setting.

    - General admin-related infos (eg. how to access the admin interface of the app, how to install plugin, etc)
        -> meant to go in 'doc/ADMIN.md' which shall be made available in the app info page in the webadmin after installation.
        -> if relevant, you can also create custom doc page, just create 'doc/WHATEVER.MD' and this will correspond to a specific documentation tab in the webadmin.
        -> note that in these files, the __FOOBAR__ syntax is supported and replaced with the corresponding 'foobar' setting.
"""
            )

    @test()
    def disclaimer_wording_or_placeholder(app):
        if os.path.exists(app.path + "/doc"):
            if (
                os.system(
                    r"grep -nr -q 'Any known limitations, constrains or stuff not working, such as\|Other infos that people should be' %s/doc/"
                    % app.path
                )
                == 0
            ):
                yield Warning(
                    "In DISCLAIMER.md: 'Any known limitations [...] such as' and 'Other infos [...] such as' are supposed to be placeholder sentences meant to explain to packagers what is the expected content, but is not an appropriate wording for end users :/"
                )
            if (
                os.system(
                    r"grep -nr -q 'This is a dummy\|Ceci est une fausse' %s/doc/"
                    % app.path
                )
                == 0
            ):
                yield Warning(
                    "The doc/ folder seems to still contain some dummy, placeholder messages in the .md markdown files. If those files are not useful in the context of your app, simply remove them."
                )

    @test()
    def change_url_script(app):

        if app_packaging_format <= 1:
            args = app.manifest["arguments"].get("install", [])
        else:
            keyandargs = copy.deepcopy(app.manifest["install"])
            for key, infos in keyandargs.items():
                infos["name"] = key
            args = keyandargs.values()

        has_domain_arg = any(a["name"] == "domain" for a in args)

        if has_domain_arg and not file_exists(app.path + "/scripts/change_url"):
            yield Info(
                "Consider adding a change_url script to support changing where the app can be reached"
            )

    @test()
    def config_panel(app):

        if file_exists(app.path + "/config_panel.json"):
            yield Error(
                "JSON config panels are not supported anymore, should be replaced by a toml version"
            )

        if file_exists(app.path + "/config_panel.toml"):
            if (
                os.system(
                    "grep -q 'version = \"0.1\"' '%s'"
                    % (app.path + "/config_panel.toml")
                )
                == 0
            ):
                yield Error(
                    "Config panels version 0.1 are not supported anymore, should be adapted for version 1.0"
                )
            elif (
                os.path.exists(app.path + "/scripts/config")
                and os.system(
                    "grep -q 'YNH_CONFIG_\\|yunohost app action' '%s'"
                    % (app.path + "/scripts/config")
                )
                == 0
            ):
                yield Error(
                    "The config panel is set to version 1.x, but the config script is apparently still using some old code from 0.1 such as '$YNH_CONFIG_STUFF' or 'yunohost app action'"
                )

            yield from validate_schema(
                "config_panel",
                json.loads(config_panel_v1_schema()),
                toml.load(app.path + "/config_panel.toml"),
            )

    @test()
    def badges_in_readme(app):

        id_ = app.manifest["id"]

        if not file_exists(app.path + "/README.md"):
            return

        content = open(app.path + "/README.md").read()

        if (
            "This README was automatically generated" not in content
            or not "dash.yunohost.org/integration/%s.svg" % id_ in content
        ):
            yield Warning(
                "It looks like the README was not generated automatically by https://github.com/YunoHost/apps/tree/master/tools/README-generator. "
                "Note that nowadays you are not suppose to edit README.md, the yunohost bot will usually automatically update it if your app is hosted in the YunoHost-Apps org ... or you can also generate it by running the README-generator yourself."
            )

        superoldstuff = [
            "%20%28Apps%29",
            "%20%28Community%29",
            "/jenkins/job",
            "ci-buster",
            "ci-stretch",
            "ci-apps-arm",
        ]
        if any(oldstuff in content for oldstuff in superoldstuff):
            yield Error(
                "The README contains references to super-old build status (such as old jenkins job or ci-apps-arm or ci-stretch...) which are not relevant anymore. Please consider switching to the new auto-generated README format which contains the standard CI badge at the top."
            )

    @test()
    def placeholder_help_string(self):
        if (
            os.system(
                "grep -q 'Use the help field' %s/manifest.json 2>/dev/null" % self.path
            )
            == 0
        ):
            yield Warning(
                "Sounds like your manifest.json contains some default placeholder help string ('Use the help field to...') ... either replace it with an actually helpful explanation, or remove the help string entirely if you don't use it."
            )

        if (
            os.system(
                "grep -q 'Explain in *a few (10~15) words* the purpose of the app\\|Expliquez en *quelques* (10~15) mots' %s/manifest.json 2>/dev/null"
                % self.path
            )
            == 0
        ):
            yield Error(
                "Sounds like your manifest.json contains the default description string ('Explain in *a few (10~15 words) [...]') ... Please replace it with an actual description."
            )

    @test()
    def remaining_replacebyyourapp(self):
        if os.system("grep -I -qr 'REPLACEBYYOURAPP' %s 2>/dev/null" % self.path) == 0:
            yield Error("You should replace all occurences of REPLACEBYYOURAPP.")

    @test()
    def supervisor_usage(self):
        if os.system("grep -I -qr '^\s*supervisorctl' %s 2>/dev/null" % self.path) == 0:
            yield Warning(
                "Please don't rely on supervisor to run services. YunoHost is about standardization and the standard is to use systemd units..."
            )

    @test()
    def bad_encoding(self):

        cmd = (
            "file --mime-encoding $(find %s/ -type f) | grep 'iso-8859-1\\|unknown-8bit' || true"
            % self.path
        )
        bad_encoding_files = (
            subprocess.check_output(cmd, shell=True).decode("utf-8").strip().split("\n")
        )
        for file_ in bad_encoding_files:
            if not file_:
                continue
            file_ = file_.split()[0]
            yield Error(
                "%s appears to be encoded as latin-1 / iso-8859-1. Please convert it to utf-8 to avoid funky issues. Something like 'iconv -f iso-8859-1 -t utf-8 SOURCE > DEST' should do the trick."
                % file_
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

        cmd = "grep -IhEro 'ynh_\\w+ *\\( *\\)' '%s/scripts' | tr -d '() '" % app.path
        custom_helpers = (
            subprocess.check_output(cmd, shell=True).decode("utf-8").strip().split("\n")
        )
        custom_helpers = [c.split("__")[0] for c in custom_helpers]

        for custom_helper in custom_helpers:
            if custom_helper in official_helpers.keys():
                yield Info(
                    "%s is now an official helper since version '%s'"
                    % (custom_helper, official_helpers[custom_helper] or "?")
                )

    @test()
    def git_clone_usage(app):
        cmd = f"grep -I 'git clone' '{app.path}'/scripts/install '{app.path}'/scripts/_common.sh 2>/dev/null | grep -qv 'xxenv\|rbenv\|oracledb'"
        if os.system(cmd) == 0:
            yield Info(
                "Using 'git clone' is not recommended ... most forge do provide the ability to download a proper archive of the code for a specific commit. Please use the 'sources' resource in the manifest.toml in combination with ynh_setup_source."
            )

    @test()
    def helpers_version_requirement(app):

        cmd = "grep -IhEro 'ynh_\\w+ *\\( *\\)' '%s/scripts' | tr -d '() '" % app.path
        custom_helpers = (
            subprocess.check_output(cmd, shell=True).decode("utf-8").strip().split("\n")
        )
        custom_helpers = [c.split("__")[0] for c in custom_helpers]

        if app_packaging_format <= 1:
            yunohost_version_req = (
                app.manifest.get("requirements", {}).get("yunohost", "").strip(">= ")
            )
        else:
            yunohost_version_req = (
                app.manifest.get("integration", {}).get("yunohost", "").strip(">= ")
            )

        cmd = "grep -IhEro 'ynh_\\w+' '%s/scripts'" % app.path
        helpers_used = (
            subprocess.check_output(cmd, shell=True).decode("utf-8").strip().split("\n")
        )
        helpers_used = sorted(set(helpers_used))

        manifest_req = [int(i) for i in yunohost_version_req.split(".")] + [0, 0, 0]

        def validate_version_requirement(helper_req):
            if helper_req == "":
                return True
            helper_req = [int(i) for i in helper_req.split(".")]
            for i in range(0, len(helper_req)):
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
                message = (
                    "Using official helper %s implies requiring at least version %s, but manifest only requires %s"
                    % (helper, helper_req, yunohost_version_req)
                )
                yield Error(message) if major_diff else Warning(message)

    @test()
    def helpers_deprecated_in_v2(app):

        if app_packaging_format <= 1:
            return

        cmd = f"grep -IhEro 'ynh_\\w+' '{app.path}/scripts/install' '{app.path}/scripts/remove' '{app.path}/scripts/upgrade' '{app.path}/scripts/backup' '{app.path}/scripts/restore' || true"
        helpers_used = (
            subprocess.check_output(cmd, shell=True).decode("utf-8").strip().split("\n")
        )
        helpers_used = sorted(set(helpers_used))

        deprecated_helpers_in_v2_ = {k: v for k, v in deprecated_helpers_in_v2}

        for helper in [
            h for h in helpers_used if h in deprecated_helpers_in_v2_.keys()
        ]:
            yield Warning(
                f"Using helper {helper} is deprecated when using packaging v2 ... It is replaced by: {deprecated_helpers_in_v2_[helper]}"
            )

    @test()
    def helper_consistency_apt_deps(app):
        """
        Check if ynh_install_app_dependencies is present in install/upgrade/restore
        so dependencies are up to date after restoration or upgrade
        """

        install_script = app.scripts["install"]
        if install_script.contains("ynh_install_app_dependencies"):
            for name in ["upgrade", "restore"]:
                if app.scripts[name].exists and not app.scripts[name].contains(
                    "ynh_install_app_dependencies"
                ):
                    yield Warning(
                        "ynh_install_app_dependencies should also be in %s script"
                        % name
                    )

        cmd = (
            'grep -IhEr "install_extra_app_dependencies" %s/scripts | grep -v "key" | grep -q "http://"'
            % app.path
        )
        if os.system(cmd) == 0:
            yield Warning(
                "When installing dependencies from extra repository, please include a `--key` argument (yes, even if it's official debian repos such as backports - because systems like Raspbian do not ship Debian's key by default!"
            )

    @test()
    def helper_consistency_service_add(app):

        occurences = {
            "install": (
                app.scripts["install"].occurences("yunohost service add")
                if app.scripts["install"].exists
                else []
            ),
            "upgrade": (
                app.scripts["upgrade"].occurences("yunohost service add")
                if app.scripts["upgrade"].exists
                else []
            ),
            "restore": (
                app.scripts["restore"].occurences("yunohost service add")
                if app.scripts["restore"].exists
                else []
            ),
        }

        occurences = {
            k: [sub_v.replace('"$app"', "$app") for sub_v in v]
            for k, v in occurences.items()
        }

        all_occurences = (
            occurences["install"] + occurences["upgrade"] + occurences["restore"]
        )
        found_inconsistency = False
        found_legacy_logtype_option = False
        for cmd in all_occurences:
            if any(
                cmd not in occurences_list for occurences_list in occurences.values()
            ):
                found_inconsistency = True
            if "--log_type systemd" in cmd:
                found_legacy_logtype_option = True

        if found_inconsistency:
            details = [
                (
                    "   %s : " % script
                    + "".join(
                        "\n      " + cmd
                        for cmd in occurences[script] or ["...None?..."]
                    )
                )
                for script in occurences.keys()
            ]
            details = "\n".join(details)
            yield Warning(
                "Some inconsistencies were found in the 'yunohost service add' commands between install, upgrade and restore:\n%s"
                % details
            )

        if found_legacy_logtype_option:
            yield Warning(
                "Using option '--log_type systemd' with 'yunohost service add' is not relevant anymore"
            )

        if occurences["install"] and not app.scripts["remove"].contains(
            "yunohost service remove"
        ):
            yield Error(
                "You used 'yunohost service add' in the install script, "
                "but not 'yunohost service remove' in the remove script."
            )

    @test()
    def references_to_superold_stuff(app):
        if any(
            script.contains("jessie")
            for script in app.scripts.values()
            if script.exists
        ):
            yield Error(
                "The app still contains references to jessie, which could probably be cleaned up..."
            )
        if any(
            script.contains("/etc/php5") or script.contains("php5-fpm")
            for script in app.scripts.values()
            if script.exists
        ):
            yield Error(
                "This app still has references to php5 (from the jessie era!!) which tends to indicate that it's not up to date with recent packaging practices."
            )
        if any(
            script.contains("/etc/php/7.0") or script.contains("php7.0-fpm")
            for script in app.scripts.values()
            if script.exists
        ):
            yield Error(
                "This app still has references to php7.0 (from the stretch era!!) which tends to indicate that it's not up to date with recent packaging practices."
            )
        if any(
            script.contains("/etc/php/7.3") or script.contains("php7.3-fpm")
            for script in app.scripts.values()
            if script.exists
        ):
            yield Error(
                "This app still has references to php7.3 (from the buster era!!) which tends to indicate that it's not up to date with recent packaging practices."
            )

    @test()
    def conf_json_persistent_tweaking(self):
        if (
            os.system(
                "grep -nr '/etc/ssowat/conf.json.persistent' %s | grep -vq '^%s/doc' 2>/dev/null"
                % (self.path, self.path)
            )
            == 0
        ):
            yield Error("Don't do black magic with /etc/ssowat/conf.json.persistent!")

    @test()
    def bad_final_path_location(self):
        if (
            os.system(
                f"grep -q -nr 'ynh_webpath_register' {self.path}/scripts/install 2>/dev/null"
            )
            == 0
            and os.system(
                f"grep -q -nr 'final_path=/opt' {self.path}/scripts/install  {self.path}/scripts/_common.sh 2>/dev/null"
            )
            == 0
        ):
            yield Info(
                "Web applications are not supposed to be installed in /opt/ ... They are supposed to be installed in /var/www/$app :/"
            )

    @test()
    def app_data_in_unofficial_dir(self):

        allowed_locations = [
            "/home/yunohost.app",
            "/home/yunohost.conf",
            "/home/yunohost.backup",
            "/home/yunohost.multimedia",
        ]
        cmd = (
            "grep -IhEro '/home/yunohost[^/ ]*/|/home/\\$app' %s/scripts || true"
            % self.path
        )
        home_locations = (
            subprocess.check_output(cmd, shell=True).decode("utf-8").strip().split("\n")
        )

        forbidden_locations = set(
            [
                location
                for location in home_locations
                if location and location.rstrip("/") not in allowed_locations
            ]
        )

        if forbidden_locations:
            yield Warning(
                "The app seems to be storing data in the 'forbidden' locations %s. The recommended pratice is rather to store data in /home/yunohost.app/$app or /home/yunohost.multimedia (depending on the use case)"
                % ", ".join(forbidden_locations)
            )


class Configurations(TestSuite):
    def __init__(self, app):

        self.app = app
        self.test_suite_name = "Configuration files"

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
    def tests_toml(self):

        app = self.app

        if app_packaging_format <= 1:
            check_process_file = app.path + "/check_process"
            if not file_exists(check_process_file):
                yield Warning(
                    "You should add a 'check_process' file to properly interface with the continuous integration system"
                )
        else:
            tests_toml_file = app.path + "/tests.toml"
            if not file_exists(tests_toml_file):
                yield Error(
                    "The 'check_process' file that interfaces with the app CI has now been replaced with 'tests.toml' format and is now mandatory for apps v2."
                )
            else:
                yield from validate_schema(
                    "tests.toml",
                    json.loads(tests_v1_schema()),
                    toml.load(app.path + "/tests.toml"),
                )

    @test()
    def check_process_syntax(self):

        app = self.app

        check_process_file = app.path + "/check_process"
        if not file_exists(check_process_file):
            return

        if os.system("grep -q 'Level 5=1' '%s'" % check_process_file) == 0:
            yield Error("Do not force Level 5=1 in check_process...")
        elif os.system("grep -qE ' *Level \\d=' '%s'" % check_process_file) == 0:
            yield Error(
                "Setting Level x=y in check_process is obsolete / not relevant anymore"
            )

    @test()
    def check_process_consistency(self):

        app = self.app

        if app_packaging_format <= 1:
            args = app.manifest["arguments"].get("install", [])
        else:
            keyandargs = copy.deepcopy(app.manifest["install"])
            for key, infos in keyandargs.items():
                infos["name"] = key
            args = keyandargs.values()

        check_process_file = app.path + "/check_process"
        if not file_exists(check_process_file):
            return

        has_is_public_arg = any(a["name"] == "is_public" for a in args)
        if has_is_public_arg:
            if (
                os.system(r"grep -q '^\s*setup_public=1' '%s'" % check_process_file)
                != 0
            ):
                yield Info(
                    "It looks like you forgot to enable setup_public test in check_process?"
                )

            if (
                os.system(r"grep -q '^\s*setup_private=1' '%s'" % check_process_file)
                != 0
            ):
                yield Info(
                    "It looks like you forgot to enable setup_private test in check_process?"
                )

        has_path_arg = any(a["name"] == "path" for a in args)
        if has_path_arg:
            if (
                os.system(r"grep -q '^\s*setup_sub_dir=1' '%s'" % check_process_file)
                != 0
            ):
                yield Info(
                    "It looks like you forgot to enable setup_sub_dir test in check_process?"
                )

        if (
            app.manifest.get("multi_instance") in [True, 1, "True", "true"]
            or app.manifest.get("integration", {}).get("multi_instance") is True
        ):
            if (
                os.system(r"grep -q '^\s*multi_instance=1' '%s'" % check_process_file)
                != 0
            ):
                yield Info(
                    "It looks like you forgot to enable multi_instance test in check_process?"
                )

        if app.scripts["backup"].exists:
            if (
                os.system(r"grep -q '^\s*backup_restore=1' '%s'" % check_process_file)
                != 0
            ):
                yield Info(
                    "It looks like you forgot to enable backup_restore test in check_process?"
                )

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
    def encourage_extra_php_conf(self):

        app = self.app

        if file_exists(app.path + "/conf/php-fpm.conf"):
            yield Info(
                "For the php configuration, consider getting rid of php-fpm.conf "
                "and using the --usage and --footprint option of ynh_add_fpm_config. "
                "This will use an auto-generated php conf file."
                "Additionally you can provide a conf/extra_php-fpm.conf for custom PHP settings "
                "that will automatically be appended to the autogenerated conf. "
                " (Feel free to discuss this on the chat with other people, the whole thing "
                "with --usage/--footprint is legitimately a bit unclear ;))"
            )

    @test()
    def misc_source_management(self):

        app = self.app

        source_dir = os.path.join(app.path, "sources")
        if (
            os.path.exists(source_dir)
            and len(
                [
                    name
                    for name in os.listdir(source_dir)
                    if os.path.isfile(os.path.join(source_dir, name))
                ]
            )
            > 5
        ):
            yield Error(
                "Upstream app sources shouldn't be stored in this 'sources' folder of this git repository as a copy/paste\n"
                "During installation, the package should download sources from upstream via 'ynh_setup_source'.\n"
                "See the helper documentation. "
                "Original discussion happened here: "
                "https://github.com/YunoHost/issues/issues/201#issuecomment-391549262"
            )

    @test()
    def src_file_checksum_type(self):

        app = self.app
        for filename in (
            os.listdir(app.path + "/conf") if os.path.exists(app.path + "/conf") else []
        ):
            if not filename.endswith(".src"):
                continue

            try:
                content = open(app.path + "/conf/" + filename).read()
            except Exception as e:
                yield Warning("Can't open/read %s: %s" % (filename, e))
                return

            if "SOURCE_SUM_PRG=md5sum" in content:
                yield Error(
                    "%s: Using md5sum checksum is not so great for "
                    "security. Consider using sha256sum instead." % filename
                )

    @test()
    def systemd_config_specific_user(self):

        app = self.app
        for filename in (
            os.listdir(app.path + "/conf") if os.path.exists(app.path + "/conf") else []
        ):
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

            if "[Unit]" not in content:
                continue

            if re.findall(r"^ *Type=oneshot", content, flags=re.MULTILINE):
                Level = Info
            else:
                Level = Warning

            matches = re.findall(r"^ *(User)=(\S+)", content, flags=re.MULTILINE)
            if not any(match[0] == "User" for match in matches):
                yield Level(
                    "You should specify a 'User=' directive in the systemd config !"
                )
                return

            if any(match[1] in ["root", "www-data"] for match in matches):
                yield Level(
                    "DO NOT run the app's systemd service as root or www-data! Use a dedicated system user for this app! If your app requires administrator priviledges, you should consider adding the user to the sudoers (and restrict the commands it can use!)"
                )

    @test()
    def systemd_config_harden_security(self):

        app = self.app
        for filename in (
            os.listdir(app.path + "/conf") if os.path.exists(app.path + "/conf") else []
        ):
            # Ignore subdirs or filename not containing nginx in the name
            if not filename.endswith(".service"):
                continue

            if (
                os.system(
                    f"grep -q '^ *CapabilityBoundingSet=' '{app.path}/conf/{filename}'"
                )
                != 0
                or os.system(f"grep -q '^ *Protect.*=' '{app.path}/conf/{filename}'")
                != 0
                or os.system(
                    f"grep -q '^ *SystemCallFilter=' '{app.path}/conf/{filename}'"
                )
                != 0
                or os.system(f"grep -q '^ *PrivateTmp=' '{app.path}/conf/{filename}'")
                != 0
            ):

                yield Info(
                    f"You are encouraged to harden the security of the systemd configuration {filename}. You can have a look at https://github.com/YunoHost/example_ynh/blob/master/conf/systemd.service#L14-L46 for a baseline."
                )

    @test()
    def php_config_specific_user(self):

        app = self.app
        for filename in (
            os.listdir(app.path + "/conf") if os.path.exists(app.path + "/conf") else []
        ):
            # Ignore subdirs or filename not containing nginx in the name
            if not filename.startswith("php") or not filename.endswith(".conf"):
                continue

            try:
                content = open(app.path + "/conf/" + filename).read()
            except Exception as e:
                yield Warning("Can't open/read %s : %s" % (filename, e))
                return

            matches = re.findall(
                r"^ *(user|group) = (\S+)", content, flags=re.MULTILINE
            )
            if not any(match[0] == "user" for match in matches):
                yield Error(
                    "You should at least specify a 'user =' directive in your PHP conf file"
                )
                return

            if any(
                match[1] == "root" or match == ("user", "www-data") for match in matches
            ):
                yield Error(
                    "DO NOT run the app PHP worker as root or www-data! Use a dedicated system user for this app!"
                )

    @test()
    def nginx_http_host(self):

        app = self.app

        if os.path.exists(app.path + "/conf/nginx.conf"):
            content = open(app.path + "/conf/nginx.conf").read()
            if "$http_host" in content:
                yield Info(
                    "In nginx.conf : please don't use $http_host but $host instead. C.f. https://github.com/yandex/gixy/blob/master/docs/en/plugins/hostspoofing.md"
                )

    @test()
    def nginx_https_redirect(self):

        app = self.app

        for filename in (
            os.listdir(app.path + "/conf") if os.path.exists(app.path + "/conf") else []
        ):
            # Ignore subdirs or filename not containing nginx in the name
            if (
                not os.path.isfile(app.path + "/conf/" + filename)
                or "nginx" not in filename
            ):
                continue

            content = open(app.path + "/conf/" + filename).read()
            if "if ($scheme = http)" in content and "rewrite ^ https" in content:
                level = Info if app_packaging_format <= 1 else Warning
                yield level(
                    "Since Yunohost 4.3, the http->https redirect is handled by the core, "
                    "therefore having an if ($scheme = http) { rewrite ^ https://... } block "
                    "in the nginx config file is deprecated. (This helps with supporting Yunohost-behind-reverse-proxy use case)"
                )

    @test()
    def misc_nginx_add_header(self):

        app = self.app

        #
        # Analyze nginx conf
        # - Deprecated usage of 'add_header' in nginx conf
        # - Spot path traversal issue vulnerability
        #

        for filename in (
            os.listdir(app.path + "/conf") if os.path.exists(app.path + "/conf") else []
        ):
            # Ignore subdirs or filename not containing nginx in the name
            if (
                not os.path.isfile(app.path + "/conf/" + filename)
                or "nginx" not in filename
            ):
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

        for filename in (
            os.listdir(app.path + "/conf") if os.path.exists(app.path + "/conf") else []
        ):
            # Ignore subdirs or filename not containing nginx in the name
            if (
                not os.path.isfile(app.path + "/conf/" + filename)
                or "nginx" not in filename
            ):
                continue

            content = open(app.path + "/conf/" + filename).read()
            if "location" in content and "more_set_headers" in content:

                lines = content.split("\n")
                more_set_headers_lines = [
                    zzz for zzz in lines if "more_set_headers" in zzz
                ]

                def right_syntax(line):
                    return re.search(
                        r"more_set_headers +[\"\'][\w-]+\s?: .*[\"\'];", line
                    )

                lines = [
                    line.strip()
                    for line in more_set_headers_lines
                    if not right_syntax(line)
                ]
                if lines:
                    yield Error(
                        "It looks like the syntax for the 'more_set_headers' "
                        "instruction is incorrect in the NGINX conf (N.B. "
                        ": it's different than the 'add_header' syntax!)... "
                        "The syntax should look like: "
                        'more_set_headers "Header-Name: value"'
                        f"\nOffending line(s) [{lines}]"
                    )

    @test()
    def misc_nginx_check_regex_in_location(self):
        app = self.app
        for filename in (
            os.listdir(app.path + "/conf") if os.path.exists(app.path + "/conf") else []
        ):
            # Ignore subdirs or filename not containing nginx in the name
            if (
                not os.path.isfile(app.path + "/conf/" + filename)
                or "nginx" not in filename
            ):
                continue

            cmd = 'grep -q -IhEro "location ~ __PATH__" %s' % (
                app.path + "/conf/" + filename
            )

            if os.system(cmd) == 0:
                yield Warning(
                    "When using regexp in the nginx location field (location ~ __PATH__), start the path with ^ (location ~ ^__PATH__)."
                )

    @test()
    def misc_nginx_path_traversal(self):

        app = self.app
        for filename in (
            os.listdir(app.path + "/conf") if os.path.exists(app.path + "/conf") else []
        ):
            # Ignore subdirs or filename not containing nginx in the name
            if (
                not os.path.isfile(app.path + "/conf/" + filename)
                or "nginx" not in filename
            ):
                continue

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
                    elif (
                        isinstance(instruction, list)
                        and instruction
                        and instruction[0] == "location"
                    ):
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

                        # Ugly hack to ignore cases where aliasing to a specific file (e.g. favicon.ico or foobar.html)
                        if "." in alias_path[-5:]:
                            continue

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
                        if not location.strip("'").endswith("/") and (
                            alias_path.endswith("/")
                            or "__FINALPATH__" not in alias_path
                        ):
                            yield location

            do_path_traversal_check = False
            try:
                import pyparsing, six

                do_path_traversal_check = True
            except Exception:
                # If inside a venv, try to magically install pyparsing
                if "VIRTUAL_ENV" in os.environ:
                    try:
                        _print("(Trying to auto install pyparsing...)")
                        subprocess.check_output(
                            "pip3 install pyparsing six", shell=True
                        )
                        import pyparsing

                        _print("OK!")
                        do_path_traversal_check = True
                    except Exception as e:
                        _print("Failed :[ : %s" % str(e))

            if not do_path_traversal_check:
                _print(
                    "N.B.: The package linter needs you to run 'pip3 install pyparsing six' if you want it to be able to check for path traversal issue in NGINX confs"
                )

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
                        "  https://github.com/YunoHost/example_ynh/blob/master/conf/nginx.conf"
                        % location
                    )

    @test()
    def bind_public_ip(self):
        app = self.app
        for path, subdirs, files in (
            os.walk(app.path + "/conf") if os.path.exists(app.path + "/conf") else []
        ):
            for filename in files:
                try:
                    content = open(os.path.join(path, filename)).read()
                except Exception as e:
                    yield Warning(
                        "Can't open/read %s: %s" % (os.path.join(path, filename), e)
                    )
                    return

                for number, line in enumerate(content.split("\n"), 1):
                    comment = ("#", "//", ";", "/*", "*")
                    if (
                        "0.0.0.0" in line or "::" in line
                    ) and not line.strip().startswith(comment):
                        for ip in re.split("[ \t,='\"(){}\[\]]", line):
                            if ip == "::" or ip.startswith("0.0.0.0"):
                                yield Info(
                                    f"{os.path.relpath(path, app.path)}/{filename}:{number}: "
                                    "Binding to '0.0.0.0' or '::' can result in a security issue "
                                    "as the reverse proxy and the SSO can be bypassed by knowing "
                                    "a public IP (typically an IPv6) and the app port. "
                                    "Please be sure that this behavior is intentional. "
                                    "Maybe use '127.0.0.1' or '::1' instead."
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
        self.test_suite_name = "manifest"

        global app_packaging_format
        manifest_path = os.path.join(path, "manifest.toml")
        if os.path.exists(manifest_path):
            app_packaging_format = 2
        else:
            app_packaging_format = 1
            manifest_path = os.path.join(path, "manifest.json")
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

        self.raw_manifest = open(manifest_path, encoding="utf-8").read()
        try:
            if app_packaging_format == 1:
                self.manifest = json.loads(
                    self.raw_manifest, object_pairs_hook=check_for_duplicate_keys
                )
            else:
                self.manifest = toml.loads(self.raw_manifest)
        except Exception as e:
            print(
                c.FAIL
                + "✘ Looks like there's a syntax issue in your manifest?\n ---> %s" % e
            )
            sys.exit(1)

    @test()
    def mandatory_fields(self):

        base_fields = [
            "packaging_format",
            "id",
            "name",
            "description",
            "version",
        ]

        if app_packaging_format == 1:
            fields = base_fields + [
                "maintainer",
                "requirements",
                "multi_instance",
                "services",
                "arguments",
            ]
        else:
            fields = base_fields + [
                "maintainers",
                "upstream",
                "integration",
                "install",
                "resources",
            ]

        missing_fields = [
            field for field in fields if field not in self.manifest.keys()
        ]

        if missing_fields:
            yield Critical(
                "The following mandatory fields are missing: %s" % missing_fields
            )

        if app_packaging_format == 1:
            fields = ("license", "url")
            missing_fields = [
                field for field in fields if field not in self.manifest.keys()
            ]

            if missing_fields:
                yield Error(
                    "The following mandatory fields are missing: %s" % missing_fields
                )
        else:
            if "license" not in self.manifest.get("upstream"):
                yield Error("The license key in the upstream section is missing")

    @test()
    def maintainer_sensible_values(self):
        if "maintainers" in self.manifest.keys():
            for value in self.manifest["maintainers"]:
                if not value.strip():
                    yield Warning("Please don't put empty string as a maintainer x_x")
                elif "," in value:
                    yield Warning(
                        "Please don't use comma in maintainers value, this is supposed to be a list such as ['foo', bar'], not ['foo, bar'] x_x"
                    )

    @test()
    def upstream_fields(self):
        if "upstream" not in self.manifest.keys():
            yield Warning(
                """READMEs are to be automatically generated using https://github.com/YunoHost/apps/tree/master/tools/README-generator.
        - You are encouraged to add an 'upstream' section in the manifest, filled with the website, demo, repo, license of the upstream app, as shown here: https://github.com/YunoHost/example_ynh/blob/7b72b7334964b504e8c901637c73ce908204d38b/manifest.json#L11-L18 . (Not all infos are mandatory, you can remove irrelevant entries)"""
            )

    @test()
    def upstream_placeholders(self):
        if "upstream" in self.manifest.keys():
            if "yunohost.org" in self.manifest["upstream"].get("admindoc", ""):
                yield Error(
                    "The field 'admindoc' should point to the **official** admin doc, not the YunoHost documentation. If there's no official admin doc, simply remove the admindoc key entirely."
                )
            if "github.com" in self.manifest["upstream"].get("website", ""):
                yield Warning(
                    "The field 'website' is not meant to point to a code repository ... this is to be handled by the 'code' key ... If the app has no proper website, just remove the 'website' key entirely"
                )
            if "yunohost.org" in self.manifest["upstream"].get("userdoc", ""):
                yield Warning(
                    "The field 'userdoc' should point to the **official** user doc, not the YunoHost documentation. (The default auto-generated README already includes a link to the yunohost doc page for this app). If there's no official user doc, simply remove the userdoc key entirely."
                )
            if "example.com" in self.manifest["upstream"].get(
                "demo", ""
            ) or "example.com" in self.manifest["upstream"].get("website", ""):
                yield Error(
                    "It seems like the upstream section still contains placeholder values such as 'example.com' ..."
                )

    @test()
    def FIXMEs(self):
        if "FIXME" in self.raw_manifest:
            yield Warning("There are still some FIXMEs remaining in the manifest")

    @test()
    def yunohost_version_requirement(self):

        if app_packaging_format >= 2:
            return

        if not self.manifest.get("requirements", {}).get("yunohost", ""):
            yield Critical(
                "You should add a YunoHost version requirement in the manifest"
            )

    @test()
    def yunohost_version_requirement_superold(app):

        if app_packaging_format >= 2:
            yunohost_version_req = (
                app.manifest.get("integration", {}).get("yunohost", "").strip(">= ")
            )
        else:
            yunohost_version_req = (
                app.manifest.get("requirements", {}).get("yunohost", "").strip(">= ")
            )
        if yunohost_version_req.startswith("2.") or yunohost_version_req.startswith(
            "3."
        ):
            yield Critical(
                "Your app only requires YunoHost >= 2.x or 3.x, which tends to indicate that it may not be up to date with recommended packaging practices and helpers."
            )
        elif (
            yunohost_version_req.startswith("4.0")
            or yunohost_version_req.startswith("4.1")
            or yunohost_version_req.startswith("4.2")
        ):
            yield Critical(
                "Your app only requires yunohost >= 4.0, 4.1 or 4.2, which tends to indicate that it may not be up to date with recommended packaging practices and helpers."
            )
        # elif yunohost_version_req.startswith("4.3"):
        #    yield Warning(
        #        "Your app only requires yunohost >= 4.3, which tends to indicate that it may not be up to date with recommended packaging practices and helpers."
        #    )

    @test()
    def basic_fields_format(self):

        if self.manifest.get("packaging_format") != app_packaging_format:
            yield Error(f"packaging_format should be {app_packaging_format}")
        if not re.match("^[a-z0-9]((_|-)?[a-z0-9])+$", self.manifest.get("id")):
            yield Error("The app id is not a valid app id")
        elif self.manifest.get("id").endswith("_ynh"):
            yield Warning("The app id is not supposed to end with _ynh :| ...")
        if len(self.manifest["name"]) > 22:
            yield Error("The app name is too long")

        if app_packaging_format <= 1:
            if self.manifest.get("url", "").endswith("_ynh"):
                yield Info(
                    "'url' is not meant to be the URL of the YunoHost package, "
                    "but rather the website or repo of the upstream app itself..."
                )
            if self.manifest["multi_instance"] not in [True, False, 0, 1]:
                yield Error(
                    "\"multi_instance\" field should be boolean 'true' or 'false', and not string type"
                )
            return

        keys = {
            "yunohost": (
                lambda v: isinstance(v, str) and re.fullmatch(r"^>=\s*[\d\.]+\d$", v),
                "Expected something like '>= 4.5.6'",
            ),
            "architectures": (
                lambda v: v == "all"
                or (
                    isinstance(v, list)
                    and all(subv in ["i386", "amd64", "armhf", "arm64"] for subv in v)
                ),
                "'all' or a list of values in ['i386', 'amd64', 'armhf', 'arm64']",
            ),
            "multi_instance": (
                lambda v: isinstance(v, bool),
                "Expected a boolean (true or false, no quotes!)",
            ),
            "ldap": (
                lambda v: isinstance(v, bool) or v == "not_relevant",
                "Expected a boolean (true or false, no quotes!) or 'not_relevant'",
            ),
            "sso": (
                lambda v: isinstance(v, bool) or v == "not_relevant",
                "Expected a boolean (true or false, no quotes!) or 'not_relevant'",
            ),
            "disk": (lambda v: isinstance(v, str), "Expected a string"),
            "ram": (
                lambda v: isinstance(v, dict)
                and isinstance(v.get("build"), str)
                and isinstance(v.get("runtime"), str),
                "Expected to find ram.build and ram.runtime with string values",
            ),
        }

        for key, validator in keys.items():
            if key not in self.manifest.get("integration", {}):
                yield Error(f"Missing key in the integration section: {key}")
                continue
            value = self.manifest["integration"][key]
            if not validator[0](value):
                yield Error(
                    f"Error found with key {key} in the 'integration' section: {validator[1]}, got: {value}"
                )

        if not self.manifest.get("upstream", {}).get("license"):
            yield Error("Missing 'license' key in the upstream section")

    @test()
    def license(self):

        if app_packaging_format <= 1:
            if "license" not in self.manifest:
                return

            if (
                "upstream" in self.manifest
                and "license" in self.manifest["upstream"]
                and self.manifest["upstream"]["license"] != self.manifest["license"]
            ):
                yield Warning(
                    "The content of 'license' in the 'upstream' block should be the same as 'license' (yes sorry, this is duplicate info, this is transitional for the manifest v2 ...)"
                )

            # Turns out there may be multiple licenses... (c.f. Seafile)
            licenses = self.manifest["license"].split(",")
        else:
            # Turns out there may be multiple licenses... (c.f. Seafile)
            licenses = self.manifest.get("upstream", {}).get("license", "").split(",")

        for license in licenses:

            license = license.strip()

            if "nonfree" in license.replace("-", ""):
                yield Warning(
                    "'non-free' apps cannot be integrated in YunoHost's app catalog."
                )
                return

            code_license = '<code property="spdx:licenseId">' + license + "</code>"

            if code_license not in spdx_licenses():
                yield Warning(
                    "The license id '%s' is not registered in https://spdx.org/licenses/."
                    % license
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
            yield Warning(
                "The description of your app is either missing, too short or too long... Please describe in *consise* terms what the app is/does."
            )

        if "for yunohost" in descr.lower():
            yield Error(
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
        if not re.match(
            r"^" + VERSION_PATTERN + r"~ynh[0-9]+$",
            self.manifest.get("version", ""),
            re.VERBOSE,
        ):
            yield Error(
                "The 'version' field should match the format <upstreamversion>~ynh<packageversion>. "
                "For example: 4.3-2~ynh3. It is composed of the upstream version number (in the "
                "example, 4.3-2) and an incremental number for each change in the package without "
                "upstream change (in the example, 3). This incremental number can be reset to 1 "
                "each time the upstream version changes."
            )

    @test()
    def install_args(self):

        recognized_types = (
            "string",
            "text",
            "select",
            "tags",
            "email",
            "url",
            "date",
            "time",
            "color",
            "password",
            "path",
            "boolean",
            "domain",
            "user",
            "group",
            "number",
            "range",
            "display_text",
            "alert",
            "markdown",
            "file",
            "app",
        )

        if app_packaging_format <= 1:
            args = self.manifest["arguments"].get("install", [])
        else:
            keyandargs = copy.deepcopy(self.manifest["install"])
            for key, infos in keyandargs.items():
                infos["name"] = key
            args = keyandargs.values()

        for argument in args:
            if not isinstance(argument.get("optional", False), bool):
                yield Warning(
                    "The key 'optional' value for setting %s should be a boolean (true or false)"
                    % argument["name"]
                )
            if "type" not in argument.keys():
                yield Warning(
                    "You should specify the type of the argument '%s'. "
                    "You can use: %s." % (argument["name"], ", ".join(recognized_types))
                )
            elif argument["type"] not in recognized_types:
                yield Warning(
                    "The type '%s' for argument '%s' is not recognized... "
                    "it probably doesn't behave as you expect? Choose among those instead: %s"
                    % (argument["type"], argument["name"], ", ".join(recognized_types))
                )
            elif argument["type"] == "display_text":
                yield Info(
                    "Question type 'display_text' is deprecated. You might want to use 'markdown' or 'alert' instead."
                )
            elif argument["type"] == "boolean" and argument.get(
                "default", True
            ) not in [True, False]:
                yield Warning(
                    "Default value for boolean-type arguments should be a boolean... (in particular, make sure it's not a string!)"
                )
            elif argument["type"] in ["domain", "user", "password"]:
                if argument.get("default"):
                    yield Info(
                        "Default value for argument %s is superfluous, will be ignored"
                        % argument["name"]
                    )
                if argument.get("example"):
                    yield Info(
                        "Example value for argument %s is superfluous, will be ignored"
                        % argument["name"]
                    )

            if "choices" in argument.keys():
                choices = [c.lower() for c in argument["choices"]]
                if len(choices) == 2:
                    if ("true" in choices and "false" in choices) or (
                        "yes" in choices and "no" in choices
                    ):
                        yield Warning(
                            "Argument %s : you might want to simply use a boolean-type argument. "
                            "No need to specify the choices list yourself."
                            % argument["name"]
                        )

    @test()
    def obsolete_or_missing_ask_strings(self):

        ask_string_managed_by_the_core = [
            ("domain", "domain"),
            ("path", "path"),
            ("admin", "user"),
            ("is_public", "boolean"),
            ("password", "password"),
            ("init_main_permission", "group"),
        ]

        if app_packaging_format <= 1:
            args = self.manifest["arguments"].get("install", [])
        else:
            keyandargs = copy.deepcopy(self.manifest["install"])
            for key, infos in keyandargs.items():
                infos["name"] = key
            args = keyandargs.values()

        for argument in args:

            if (
                argument.get("ask")
                and (argument.get("name"), argument.get("type"))
                in ask_string_managed_by_the_core
            ):
                yield Warning(
                    "'ask' string for argument %s is superfluous / will be ignored. Since 4.1, the core handles the 'ask' string for some recurring arg name/type for consistency and easier i18n. See https://github.com/YunoHost/example_ynh/pull/142"
                    % argument.get("name")
                )

            elif (
                not argument.get("ask")
                and (argument.get("name"), argument.get("type"))
                not in ask_string_managed_by_the_core
            ):
                yield Warning(
                    "You should add 'ask' strings for argument %s"
                    % argument.get("name")
                )

    @test()
    def old_php_version(self):

        if app_packaging_format <= 1:
            return

        resources = self.manifest["resources"]

        if "apt" in list(resources.keys()):
            packages = str(list(resources["apt"].get("packages", "")))
            if "php7.4-" in packages:
                yield Warning(
                    "The app currently runs on php7.4 which is pretty old (unsupported by the PHP group since January 2023). Ideally, upgrade it to at least php8.2."
                )
            elif "php8.0-" in packages:
                yield Warning(
                    "The app currently runs on php8.0 which is pretty old (unsupported by the PHP group since January 2024). Ideally, upgrade it to at least php8.2."
                )
            elif "php8.1-" in packages:
                yield Info(
                    "The app currently runs on php8.1 which is deprecated since January 2024. Ideally, upgrade it to at least php8.2."
                )

    @test()
    def resource_consistency(self):

        if app_packaging_format <= 1:
            return

        resources = self.manifest["resources"]

        if "database" in list(resources.keys()):
            if "apt" not in list(resources.keys()):
                yield Warning(
                    "Having an 'apt' resource is mandatory when using a 'database' resource, to also install postgresql/mysql if needed"
                )
            else:
                if list(resources.keys()).index("database") < list(
                    resources.keys()
                ).index("apt"):
                    yield Warning(
                        "The 'apt' resource should be placed before the 'database' resource, to install postgresql/mysql if needed *before* provisioning the database"
                    )

                dbtype = resources["database"]["type"]

                apt_packages = resources["apt"].get("packages", [])
                if isinstance(apt_packages, str):
                    apt_packages = [
                        value.strip() for value in re.split(" |,", apt_packages)
                    ]

                if dbtype == "mysql" and "mariadb-server" not in apt_packages:
                    yield Warning(
                        "When using a mysql database, you should add mariadb-server in apt dependencies. Even though it's currently installed by default in YunoHost installations, it might not be in the future !"
                    )
                if dbtype == "postgresql" and "postgresql" not in apt_packages:
                    yield Warning(
                        "When using a postgresql database, you should add postgresql in apt dependencies."
                    )

        main_perm = self.manifest["resources"].get("permissions", {}).get("main", {})
        if (
            isinstance(main_perm.get("url"), str)
            and "init_main_permission" not in self.manifest["install"]
            and not main_perm.get("allowed")
        ):
            yield Warning(
                "You should add a 'init_main_permission' question, or define `allowed` for main permission to have the app ready to be accessed right after installation."
            )

        @test()
        def manifest_schema(self):
            if app_packaging_format <= 1:
                return
            yield from validate_schema(
                "manifest", json.loads(manifest_v2_schema()), self.manifest
            )


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
        self.test_suite_name = "Catalog infos"

        self._fetch_app_repo()

        try:
            self.app_list = toml.loads(open("./.apps/apps.toml").read())
        except Exception:
            _print("Failed to read apps.toml :/")
            sys.exit(-1)

        self.catalog_infos = self.app_list.get(app_id, {})

    def _fetch_app_repo(self):

        flagfile = "./.apps_git_clone_cache"
        if (
            os.path.exists("./.apps")
            and os.path.exists(flagfile)
            and time.time() - os.path.getmtime(flagfile) < 3600
        ):
            return

        if not os.path.exists("./.apps"):
            subprocess.check_call(
                [
                    "git",
                    "clone",
                    "https://github.com/YunoHost/apps",
                    "./.apps",
                    "--quiet",
                ]
            )
        else:
            subprocess.check_call(["git", "-C", "./.apps", "fetch", "--quiet"])
            subprocess.check_call(
                ["git", "-C", "./.apps", "reset", "origin/master", "--hard", "--quiet"]
            )

        open(flagfile, "w").write("")

    @test()
    def is_in_catalog(self):

        if not self.catalog_infos:
            yield Critical("This app is not in YunoHost's application catalog")

    @test()
    def revision_is_HEAD(self):

        if self.catalog_infos and self.catalog_infos.get("revision", "HEAD") != "HEAD":
            yield Error(
                "You should make sure that the revision used in YunoHost's apps catalog is HEAD..."
            )

    @test()
    def state_is_working(self):

        if (
            self.catalog_infos
            and self.catalog_infos.get("state", "working") != "working"
        ):
            yield Error(
                "The application is not flagged as working in YunoHost's apps catalog"
            )

    @test()
    def has_category(self):
        if self.catalog_infos and not self.catalog_infos.get("category"):
            yield Warning(
                "The application has no associated category in YunoHost's apps catalog"
            )

    @test()
    def is_in_github_org(self):

        repo_org = "https://github.com/YunoHost-Apps/%s_ynh" % (self.app_id)
        repo_brique = "https://github.com/labriqueinternet/%s_ynh" % (self.app_id)

        if self.catalog_infos:
            repo_url = self.catalog_infos["url"]

            if repo_url.lower() not in [repo_org.lower(), repo_brique.lower()]:
                if repo_url.lower().startswith("https://github.com/YunoHost-Apps/"):
                    yield Warning(
                        "The URL for this app in the catalog should be %s" % repo_org
                    )
                else:
                    yield Info(
                        "Consider adding your app to the YunoHost-Apps organization to allow the community to contribute more easily"
                    )

        else:

            def is_in_github_org():
                return urlopen(repo_org)["code"] != 404

            def is_in_brique_org():
                return urlopen(repo_brique)["code"] != 404

            if not is_in_github_org() and not is_in_brique_org():
                yield Info(
                    "Consider adding your app to the YunoHost-Apps organization to allow the community to contribute more easily"
                )

    @test()
    def is_long_term_good_quality(self):

        #
        # This analyzes the (git) history of apps.json in the past year and
        # compute a score according to the time when the app was
        # known + flagged working + level >= 5
        #

        def git(cmd):
            return (
                subprocess.check_output(["git", "-C", "./.apps"] + cmd)
                .decode("utf-8")
                .strip()
            )

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

            for t in list(_time_points_until_today())[(-1 * N) :]:

                # Fetch apps.json content at this date
                commit = git(
                    [
                        "rev-list",
                        "-1",
                        "--before='%s'" % t.strftime("%b %d %Y"),
                        "master",
                    ]
                )
                if (
                    os.system(
                        f"git -C ./.apps  cat-file -e {commit}:apps.json 2>/dev/null"
                    )
                    == 0
                ):
                    raw_catalog_at_this_date = git(["show", f"{commit}:apps.json"])
                    loader = json

                elif os.system(f"git -C ./.apps  cat-file -e {commit}:apps.toml") == 0:
                    raw_catalog_at_this_date = git(["show", f"{commit}:apps.toml"])
                    loader = toml
                else:
                    raise Exception("No apps.json/toml at this point in history?")

                try:
                    catalog_at_this_date = loader.loads(raw_catalog_at_this_date)
                # This can happen in stupid cases where there was a temporary syntax error in the json..
                except json.decoder.JSONDecodeError:
                    _print(
                        "Failed to parse apps.json/toml history for at commit %s / %s ... ignoring "
                        % (commit, t)
                    )
                    continue
                yield (t, catalog_at_this_date.get(self.app_id))

        # We'll check the history for last 12 months (*2 points per month)
        N = 12 * 2
        history = list(get_history(N))

        # Must have been
        #   known
        # + flagged as working
        # + level > 5
        # for the past 6 months
        def good_quality(infos):
            return (
                bool(infos)
                and isinstance(infos, dict)
                and infos.get("state") == "working"
                and infos.get("level", -1) >= 5
            )

        score = sum([good_quality(infos) for d, infos in history])
        rel_score = int(100 * score / N)
        if rel_score > 80:
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
        self.test_suite_name = "scripts/" + self.name

    def read_file(self):
        with open(self.path) as f:
            lines = f.readlines()

        # Remove trailing spaces, empty lines and comment lines
        lines = [line.strip() for line in lines]
        lines = [line for line in lines if line and not line.startswith("#")]

        # Merge lines when ending with \
        lines = "\n".join(lines).replace("\\\n", "").split("\n")

        some_parsing_failed = False

        for line in lines:

            try:
                line = shlex.split(line, True)
                yield line
            except Exception as e:

                ignore_pattern = [
                    "/etc/cron",
                    "admin_panel=",
                    'echo "',
                    "__PRE_TAG",
                    "__URL_TAG",
                    "maintenance.$app.conf",
                    "mail_message=",
                    "maintenance.$app.html",
                    "> mail_to_send",
                ]
                if str(e) == "No closing quotation" and any(
                    pattern in line for pattern in ignore_pattern
                ):
                    continue

                if not some_parsing_failed:
                    _print(
                        "Some lines could not be parsed in script %s. (That's probably not really critical)"
                        % self.name
                    )
                    some_parsing_failed = True

                report_warning_not_reliable("%s : %s" % (e, line))

    def occurences(self, command):
        return [
            line for line in [" ".join(line) for line in self.lines] if command in line
        ]

    def contains(self, command):
        """
        Iterate on lines to check if command is contained in line

        For instance, "app setting" is contained in "yunohost app setting $app ..."
        """
        return any(command in line for line in [" ".join(line) for line in self.lines])

    def containsregex(self, regex):
        """
        Iterate on lines to check if command is contained in line

        For instance, "app setting" is contained in "yunohost app setting $app ..."
        """
        return any(
            re.search(regex, line) for line in [" ".join(line) for line in self.lines]
        )

    @test()
    def error_handling(self):

        if app_packaging_format == 2:
            if (
                self.contains("ynh_abort_if_errors")
                or self.contains("set -eu")
                or self.contains("set -u")
            ):
                yield Error(
                    "ynh_abort_if_errors or set -eu is now handled by YunoHost core in packaging v2, you should not have to add it to your script !"
                )

            return

        if self.name in ["backup", "remove", "_common.sh"]:
            present = (
                self.contains("ynh_abort_if_errors")
                or self.contains("set -eu")
                or self.contains("set -u")
            )
        else:
            present = self.contains("ynh_abort_if_errors")

        if self.name in ["remove", "_common.sh"]:
            if present:
                yield Error(
                    "Do not use 'set -eu' or 'ynh_abort_if_errors' in the remove or _common.sh scripts: "
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

        if (
            self.contains("ynh_package_install")
            or self.contains("apt install")
            or self.contains("apt-get install")
        ):
            yield Error(
                "You should not use `ynh_package_install` or `apt-get install`, "
                "use `ynh_install_app_dependencies` instead"
            )

        if (
            self.contains("ynh_package_remove")
            or self.contains("apt remove")
            or self.contains("apt-get remove")
        ):
            yield Error(
                "You should not use `ynh_package_remove` or `apt-get remove`, "
                "use `ynh_remove_app_dependencies` instead"
            )

    @test()
    def obsolete_helpers(self):
        if self.contains("yunohost app setting"):
            yield Critical(
                "Do not use 'yunohost app setting' directly. Please use 'ynh_app_setting_(set,get,delete)' instead."
            )
        if self.contains("yunohost app checkurl"):
            yield Critical(
                "'yunohost app checkurl' is obsolete!!! Please use 'ynh_webpath_register' instead."
            )
        if self.contains("yunohost app checkport"):
            yield Critical(
                "'yunohost app checkport' is obsolete!!! Please use 'ynh_find_port' instead."
            )
        if self.contains("yunohost app initdb"):
            yield Critical(
                "'yunohost app initdb' is obsolete!!! Please use 'ynh_mysql_setup_db' instead."
            )
        if self.contains("yunohost tools port-available"):
            yield Critical(
                "'yunohost tools port-available is obsolete!!! Please use 'ynh_port_available' instead."
            )
        if self.contains("yunohost app addaccess") or self.contains(
            "yunohost app removeaccess"
        ):
            yield Error(
                "'yunohost app addaccess/removeacces' is obsolete. You should use the new permission system to manage accesses."
            )
        if self.contains("yunohost app list -i") or self.contains(
            "yunohost app list --installed"
        ):
            yield Error(
                "Argument --installed ain't needed anymore when using "
                "'yunohost app list'. It directly returns the list of installed "
                "apps.. Also beware that option -f is obsolete as well... "
                "Use grep -q 'id: $appname' to check a specific app is installed"
            )
        if self.contains("--others_var"):
            yield Error(
                "Option --others_var is deprecated / irrelevant since 4.2, and will be removed in Bullseye. YunoHost now manages conf using ynh_add_config which automatically replace all __FOOBAR__ by $foobar"
            )
        if self.contains("ynh_webpath_available"):
            yield Warning(
                "Calling 'ynh_webpath_available' is quite probably pointless: in the install script, just call ynh_webpath_register, and in the restore script, there's no need to check/register the webpath. (Also the helper always return exit code 0, so 'ynh_webpath_available || ynh_die' is useless :/"
            )
        if self.contains("ynh_print_ON") or self.contains("ynh_print_OFF"):
            yield Error(
                "Please refrain from using 'ynh_print_ON/OFF' ... YunoHost already integrates a mecanism to automatically redact variables with names ending with : pwd, pass, passwd, password, passphrase, key, token, and any variable with 'secret' in its name. Using 'ynh_print_ON/OFF' is cumbersome and may have the unintended effect of defeating Yunohost's autoredacting mecanism ... If you noticed that Yunohost's mecanism doesn't work or cover your specific case, please contact the dev team about it."
            )
        if self.contains("ynh_add_app_dependencies"):
            yield Error(
                "ynh_add_app_dependencies is supposed to be an internal helper and will soon be deprecated. Consider using ynh_install_app_dependencies or ynh_install_extra_app_dependencies instead."
            )
        if self.contains("ynh_detect_arch"):
            yield Warning(
                "(Requires yunohost 4.3) Using ynh_detect_arch is deprecated, since Yunohost 4.3, an $YNH_ARCH variable is directly available in the global context. Its value directly corresponds to `dpkg --print-architecture` which returns a value among : amd64, i386, armhf, arm64 and armel (though armel is probably not used at all?)"
            )

    @test(only=["install"])
    def admin_has_to_finish_install(self):
        cmd = 'grep -B10 -IhEr "send_readme_to_admin" %s | grep -q db_pwd' % self.path
        if os.system(cmd) == 0:
            yield Warning(
                "It looks like this app requires the admin to finish the install by entering DB credentials. Unless it's absolutely not easily automatizable, this should be handled automatically by the app install script using curl calls, or (CLI tools provided by the upstream maybe ?)."
            )

    @test(only=["install", "upgrade"])
    def deprecated_replace_string(self):
        cmd1 = "grep -Ec 'ynh_replace_string' '%s' || true" % self.path
        cmd2 = "grep -Ec 'ynh_replace_string.*__\\w+__' '%s' || true" % self.path

        count1 = int(subprocess.check_output(cmd1, shell=True).decode("utf-8").strip())
        count2 = int(subprocess.check_output(cmd2, shell=True).decode("utf-8").strip())

        if count2 > 0 or count1 >= 5:
            yield Info(
                "Please consider using 'ynh_add_config' to handle config files instead of gazillions of manual cp + 'ynh_replace_string' + chmod"
            )

    @test()
    def bad_ynh_exec_syntax(self):
        cmd = (
            'grep -q -IhEro "ynh_exec_(err|warn|warn_less|quiet|fully_quiet) (\\"|\').*(\\"|\')$" %s'
            % self.path
        )
        if os.system(cmd) == 0:
            yield Warning(
                "(Requires Yunohost 4.3) When using ynh_exec_*, please don't wrap your command between quotes (typically DONT write ynh_exec_warn_less 'foo --bar --baz')"
            )

    @test()
    def ynh_setup_source_keep_with_absolute_path(self):
        cmd = 'grep -q -IhEro "ynh_setup_source.*keep.*final_path" %s' % self.path
        if os.system(cmd) == 0:
            yield Info(
                "The --keep option of ynh_setup_source expects relative paths, not absolute path ... you do not need to prefix everything with '$final_path' in the --keep arg ..."
            )

    @test()
    def ynh_npm_global(self):
        if self.containsregex(r"ynh_npm.*install.*global"):
            yield Warning(
                "Please don't install stuff on global scope with npm install --global é_è"
            )

    @test()
    def ynh_add_fpm_config_deprecated_package_option(self):
        if self.containsregex(r"ynh_add_fpm_config .*package=.*"):
            yield Error(
                "(Requires Yunohost 4.3) Option --package for ynh_add_fpm_config is deprecated : please use 'ynh_install_app_dependencies' with **all** your apt dependencies instead (no need to define a special 'extra_php_dependencies'). YunoHost will automatically install any phpX.Y-fpm / phpX.Y-common if needed."
            )

    @test()
    def set_is_public_setting(self):
        if self.containsregex(r"ynh_app_setting_set .*is_public.*"):
            if self.name == "upgrade":
                yield Error(
                    "permission system: it should not be needed to save is_public with ynh_app_setting_set ... this setting should only be used during installation to initialize the permission. The admin is likely to manually tweak the permission using YunoHost's interface later."
                )
            else:
                yield Warning(
                    "permission system: it should not be needed to save is_public with ynh_app_setting_set ... this setting should only be used during installation to initialize the permission. The admin is likely to manually tweak the permission using YunoHost's interface later."
                )

    @test(only=["_common.sh"])
    def default_php_version_in_common(self):
        if self.contains("YNH_DEFAULT_PHP_VERSION"):
            yield Warning(
                "Do not use YNH_DEFAULT_PHP_VERSION in _common.sh ... _common.sh is usually sourced *before* the helpers, which define the version of YNH_DEFAULT_PHP_VERSION (hence it gets replaced with empty string). Instead, please explicitly state the PHP version in the package, e.g. dependencies='php8.2-cli php8.2-imagemagick'"
            )

    @test(ignore=["install", "_common.sh"])
    def get_is_public_setting(self):
        if self.contains("is_public=") or self.contains("$is_public"):
            yield Warning(
                "permission system: there should be no need to fetch or use $is_public ... is_public should only be used during installation to initialize the permission. The admin is likely to manually tweak the permission using YunoHost's interface later."
            )

    @test(only=["upgrade"])
    def temporarily_enable_visitors_during_upgrade(self):
        if self.containsregex(
            "ynh_permission_update.*add.*visitors"
        ) and self.containsregex("ynh_permission_update.*remove.*visitors"):
            yield Warning(
                "permission system: since Yunohost 4.3, there should be no need to temporarily add 'visitors' to the main permission. ynh_local_curl will temporarily enable visitors access if needed"
            )

    @test()
    def set_legacy_permissions(self):
        if self.containsregex(
            r"ynh_app_setting_set .*protected_uris"
        ) or self.containsregex(r"ynh_app_setting_set .*skipped_uris"):
            yield Error(
                "permission system: it looks like the app is still using super-legacy (un)protected/skipped_uris settings. This is now completely deprecated. Please check https://yunohost.org/packaging_apps_permissions for a documentation on how to migrate the app to the new permission system."
            )

        elif self.containsregex(
            r"ynh_app_setting_set .*protected_"
        ) or self.containsregex(r"ynh_app_setting_set .*skipped_"):
            yield Warning(
                "permission system: it looks like the app is still using the legacy permission system (unprotected/protected/skipped uris/regexes setting). Please check https://yunohost.org/packaging_apps_permissions for a documentation on how to migrate the app to the new permission system."
            )

    @test()
    def normalize_url_path(self):
        if self.contains("ynh_normalize_url_path"):
            yield Warning(
                "You probably don't need to call 'ynh_normalize_url_path'... this is only relevant for upgrades from super-old versions (like 3 years ago or so...)"
            )

    @test()
    def safe_rm(self):
        if (
            self.contains("rm -r")
            or self.contains("rm -R")
            or self.contains("rm -fr")
            or self.contains("rm -fR")
        ):
            yield Error(
                "You should not be using 'rm -rf', please use 'ynh_secure_remove' instead"
            )

    @test()
    def nginx_restart(self):
        if self.contains("systemctl restart nginx") or self.contains(
            "service nginx restart"
        ):
            yield Error(
                "Restarting NGINX is quite dangerous (especially for web installs) "
                "and should be avoided at all cost. Use 'reload' instead."
            )

    @test()
    def raw_systemctl_start(self):
        if self.containsregex(r"systemctl start \"?[^. ]+(\.service)?\"?\s"):
            yield Warning(
                "Please do not use 'systemctl start' to start services. Instead, you should use 'ynh_systemd_action' which will display the service log in case it fails to start. You can also use '--line_match' to wait until some specific word appear in the log, signaling the service indeed fully started."
            )

    @test()
    def bad_line_match(self):

        if self.containsregex(r"--line_match=Started$") or self.containsregex(
            r"--line_match=Stopped$"
        ):
            yield Warning(
                'Using --line_match="Started" or "Stopped" in ynh_systemd_action is counter productive because it will match the systemd message and not the actual app message ... Please check the log of the service to find an actual, relevant message to match, or remove the --line_match option entirely'
            )

    @test()
    def quiet_systemctl_enable(self):

        systemctl_enable = [
            line
            for line in [" ".join(line) for line in self.lines]
            if re.search(r"systemctl.*(enable|disable)", line)
        ]

        if any("-q" not in cmd for cmd in systemctl_enable):
            message = "Please add --quiet to systemctl enable/disable commands to avoid unnecessary warnings when the script runs"
            yield Warning(message)

    @test()
    def quiet_wget(self):

        wget_cmds = [
            line
            for line in [" ".join(line) for line in self.lines]
            if re.search(r"^wget ", line)
        ]

        if any(
            " -q " not in cmd and "--quiet" not in cmd and "2>" not in cmd
            for cmd in wget_cmds
        ):
            message = "Please redirect wget's stderr to stdout with 2>&1 to avoid unecessary warnings when the script runs (yes, wget is annoying and displays a warning even when things are going okay >_> ...)"
            yield Warning(message)

    @test(only=["install"])
    def argument_fetching(self):

        if self.containsregex(r"^\w+\=\$\{?[0-9]"):
            yield Critical(
                "Do not fetch arguments from manifest using 'variable=$N' (e.g."
                " domain=$1...) Instead, use 'name=$YNH_APP_ARG_NAME'"
            )

    @test(only=["install"])
    def sources_list_tweaking(self):
        if self.contains("/etc/apt/sources.list") or (
            os.path.exists(self.app_path + "/scripts/_common.sh")
            and "/etc/apt/sources.list"
            in open(self.app_path + "/scripts/_common.sh").read()
            and "ynh_add_repo" not in open(self.app_path + "/scripts/_common.sh").read()
        ):
            yield Error(
                "Manually messing with apt's sources.lists is strongly discouraged "
                "and should be avoided. Please use 'ynh_install_extra_app_dependencies' if you "
                "need to install dependencies from a custom apt repo."
            )

    @test()
    def firewall_consistency(self):
        if self.contains("yunohost firewall allow") and not self.contains(
            "--needs_exposed_ports"
        ):
            yield Info(
                "You used 'yunohost firewall allow' to expose a port on the outside but did not use 'yunohost service add' with '--needs_exposed_ports' ... If you are ABSOLUTELY SURE that the service needs to be exposed on THE OUTSIDE, then add '--needs_exposed_ports' to 'yunohost service add' with the relevant port number. Otherwise, opening the port leads to a significant security risk and you should keep the damn port closed !"
            )

        if self.contains("Configuring firewall") and not self.contains(
            "yunohost firewall allow"
        ):
            yield Warning(
                "Some message is talking about 'Configuring firewall' but there's no mention of 'yunohost firewall allow' ... If you're only finding an available port for *internal reverse proxy*, this has nothing to do with 'Configuring the firewall', so the message should be changed to avoid confusion... "
            )

    @test()
    def exit_ynhdie(self):

        if self.contains(r"\bexit\b"):
            yield Error(
                "'exit' command shouldn't be used. Please use 'ynh_die' instead."
            )

    @test()
    def old_regenconf(self):
        if self.contains("yunohost service regen-conf"):
            yield Error(
                "'yunohost service regen-conf' has been replaced by 'yunohost tools regen-conf'."
            )

    @test()
    def ssowatconf_or_nginx_reload(self):
        # Dirty hack to check only the 10 last lines for ssowatconf
        # (the "bad" practice being using this at the very end of the script, but some apps legitimately need this in the middle of the script)
        oldlines = list(self.lines)
        self.lines = self.lines[-10:]
        if self.contains("yunohost app ssowatconf"):
            yield Warning(
                "You probably don't need to run 'yunohost app ssowatconf' in the app self. It's supposed to be ran automatically after the script."
            )

        if app_packaging_format >= 2 and self.name not in ["change_url", "restore"]:
            if self.contains("ynh_systemd_action --service_name=nginx --action=reload"):
                yield Warning(
                    "You should not need to reload nginx at the end of the script ... it's already taken care of by ynh_add_nginx_config"
                )

        self.lines = oldlines

    @test()
    def sed(self):
        if self.containsregex(
            r"sed\s+(-i|--in-place)\s+(-r\s+)?s"
        ) or self.containsregex(r"sed\s+s\S*\s+(-i|--in-place)"):
            yield Info(
                "You should avoid using 'sed -i' for substitutions, please use 'ynh_replace_string' or 'ynh_add_config' instead"
            )

    @test()
    def sudo(self):
        if self.containsregex(
            r"sudo \w"
        ):  # \w is here to not match sudo -u, legit use because ynh_exec_as not official yet...
            yield Warning(
                "You should not need to use 'sudo', the script is being run as root. "
                "(If you need to run a command using a specific user, use 'ynh_exec_as' (or 'sudo -u'))"
            )

    @test()
    def chownroot(self):
        if self.containsregex(
            r"^\s*chown.* root:?[^$]* .*final_path"
        ) and not self.contains('chown root:root "$final_path"'):
            # (Mywebapp has a special case because of SFTP é_è)
            yield Warning(
                "Using 'chown root $final_path' is usually symptomatic of misconfigured and wide-open 'other' permissions ... Usually ynh_setup_source should now set sane default permissions on $final_path (if the app requires Yunohost >= 4.2) ... Otherwise, consider using 'chown $app', 'chown nobody' or 'chmod' to limit access to $final_path ..."
            )

    @test()
    def chmod777(self):
        if self.containsregex(r"chmod .*777") or self.containsregex(r"chmod .*o\+w"):
            yield Warning(
                "DO NOT use chmod 777 or chmod o+w that gives write permission to every users on the system!!! If you have permission issues, just make sure that the owner and/or group owner is right..."
            )

    @test()
    def random(self):
        if self.contains("dd if=/dev/urandom") or self.contains("openssl rand"):
            yield Error(
                "Instead of 'dd if=/dev/urandom' or 'openssl rand', you should use 'ynh_string_random'"
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
            yield Warning(
                "We recommend to *not* use 'ynh_script_progression' in backup "
                "scripts because no actual work happens when running the script "
                ": YunoHost only fetches the list of things to backup (apart "
                "from the DB dumps which effectively happens during the script...). "
                "Consider using a simple message like this instead: 'ynh_print_info \"Declaring files to be backed up...\"'"
            )

    @test()
    def progression_time(self):

        # Usage of ynh_script_progression with --time or --weight=1 all over the place...
        if self.containsregex(r"ynh_script_progression.*--time"):
            yield Info(
                "Using 'ynh_script_progression --time' should only be for calibrating the weight (c.f. '--weight'). It's not meant to be kept for production versions."
            )

    @test(ignore=["_common.sh", "backup"])
    def progression_meaningful_weights(self):
        def weight(line):
            match = re.search(
                r"ynh_script_progression.*--weight=([0-9]+)", " ".join(line)
            )
            if match:
                try:
                    return int(match.groups()[0])
                except Exception:
                    return -1
            else:
                return 1

        script_progress = [
            line for line in self.lines if "ynh_script_progression" in line
        ]
        weights = [weight(line) for line in script_progress]

        if not weights:
            return

        if len(weights) > 3 and statistics.stdev(weights) > 50:
            yield Warning(
                "To have a meaningful progress bar, try to keep the weights in the same range of values, for example [1,10], or [10,100]... otherwise, if you have super-huge weight differences, the progress bar rendering will be completely dominated by one or two steps... If these steps are really long, just try to indicated in the message that this will take a while."
            )

    @test(only=["install", "_common.sh"])
    def php_deps(self):
        if self.containsregex("dependencies.*php-"):
            # (Stupid hack because some apps like roundcube depend on php-pear or php-php-gettext and there's no phpx.y-pear phpx.y-php-gettext>_> ...
            if not self.contains("php-pear") or not self.contains("php-php-gettext"):
                yield Warning(
                    "You should avoid having dependencies like 'php-foobar'. Instead, specify the exact version you want like 'php7.0-foobar'. Otherwise, the *wrong* version of the dependency may be installed if sury is also installed. Note that for Stretch/Buster/Bullseye/... transition, YunoHost will automatically patch your file so there's no need to care about that."
                )

    @test(only=["backup"])
    def systemd_during_backup(self):
        if self.containsregex("^ynh_systemd_action"):
            yield Warning(
                "Unless you really have a good reason to do so, starting/stopping services during backup has no benefit and leads to unecessary service interruptions when creating backups... As a 'reminder': apart from possibly database dumps (which usually do not require the service to be stopped) or other super-specific action, running the backup script is only a *declaration* of what needs to be backed up. The real copy and archive creation happens *after* the backup script is ran."
            )

    @test(only=["backup"])
    def check_size_backup(self):
        if self.contains("CHECK_SIZE"):
            yield Error(
                "There's no need to 'CHECK_SIZE' during backup... This check is handled by the core automatically."
            )

    @test()
    def helpers_sourcing_after_official(self):
        helpers_after_official = subprocess.check_output(
            "head -n 30 '%s' | grep -A 10 '^ *source */usr/share/yunohost/helpers' | grep '^ *source ' | tail -n +2"
            % self.path,
            shell=True,
        ).decode("utf-8")
        helpers_after_official = (
            helpers_after_official.replace("source", "").replace(" ", "").strip()
        )
        if helpers_after_official:
            helpers_after_official = helpers_after_official.split("\n")
            yield Warning(
                "Please avoid sourcing additional helpers after the official helpers (in this case file %s)"
                % ", ".join(helpers_after_official)
            )

    @test(only=["backup", "restore"])
    def helpers_sourcing_backuprestore(self):
        if self.contains("source _common.sh") or self.contains("source ./_common.sh"):
            yield Error(
                'In the context of backup and restore scripts, you should load _common.sh with "source ../settings/scripts/_common.sh"'
            )

    @test(only=["_common.sh"])
    def no_progress_in_common(self):
        if self.contains("ynh_script_progression"):
            yield Warning(
                "You should not use `ynh_script_progression` in _common.sh because it will produce warnings when trying to install the application."
            )

    @test(only=["remove"])
    def no_log_remove(self):
        if self.containsregex("(ynh_secure_remove|ynh_safe_rm|rm).*(\/var\/log\/)"):
            yield Warning(
                "Do not delete logs on app removal, else they will be erased if the app upgrade fails. This is handled by the core."
            )


def main():
    if len(sys.argv) < 2:
        print("Give one app package path.")
        exit()

    app_path = sys.argv[1]

    global output
    output = "json" if "--json" in sys.argv else "plain"

    _print(
        """
    [{blue}{bold}YunoHost App Package Linter{end}]

 App packaging documentation - https://yunohost.org/en/contribute/packaging_apps
 App package example         - https://github.com/YunoHost/example_ynh
 Official helpers            - https://yunohost.org/en/contribute/packaging_apps/helpers
 Experimental helpers        - https://github.com/YunoHost-Apps/Experimental_helpers

 If you believe this linter returns false negative (warnings / errors which shouldn't happen),
 please report them on https://github.com/YunoHost/package_linter/issues
    """.format(
            blue=c.OKBLUE, bold=c.BOLD, end=c.END
        )
    )

    app = App(app_path)
    app.analyze()


if __name__ == "__main__":
    main()
