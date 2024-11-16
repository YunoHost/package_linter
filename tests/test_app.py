#!/usr/bin/env python3

import copy
import json
import os
import subprocess
import sys

import tomllib
from lib.lib_package_linter import (
    Error,
    Info,
    Success,
    TestSuite,
    Warning,
    config_panel_v1_schema,
    file_exists,
    test,
    tests_reports,
    validate_schema,
)
from lib.print import _print, is_json_output

from tests.test_catalog import AppCatalog
from tests.test_configurations import Configurations
from tests.test_manifest import Manifest
from tests.test_scripts import Script

scriptnames = ["_common.sh", "install", "remove", "upgrade", "backup", "restore"]


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


class App(TestSuite):
    def __init__(self, path):

        _print("  Analyzing app %s ..." % path)
        self.path = path
        self.manifest_ = Manifest(self.path)
        self.manifest = self.manifest_.manifest
        self.scripts = {
            f: Script(self.path, f, self.manifest.get("id")) for f in scriptnames
        }
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

        if is_json_output():
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
            if screenshots_size > 1024 * 1000:
                yield Warning(
                    "Please keep the content of doc/screenshots under ~512Kb. Having screenshots bigger than 512kb is probably a waste of resource and will take unecessarily long time to load on the webadmin UI and app catalog."
                )
            elif screenshots_size > 512 * 1000:
                yield Info(
                    "Please keep the content of doc/screenshots under ~512Kb. Having screenshots bigger than 512kb is probably a waste of resource and will take unecessarily long time to load on the webadmin UI and app catalog."
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
                """DISCLAIMER.md has been replaced with several files in packaging v2 to improve the UX and provide the user with key information at the appropriate step of the app install / upgrade cycles.

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
    def admin_has_to_finish_install(app):

        # Mywebapp has a legit use case for this
        if app.manifest.get("id") == "my_webapp":
            return

        cmd = f"grep -q -IhEr '__DB_PWD__' '{app.path}/doc/'"
        if os.path.exists(app.path + "/doc") and os.system(cmd) == 0:
            yield Warning(
                "(doc folder) It looks like this app requires the admin to finish the install by entering DB credentials. Unless it's absolutely not easily automatizable, this should be handled automatically by the app install script using curl calls, or (CLI tools provided by the upstream maybe ?)."
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
    def custom_python_version(app):

        cmd = f"grep -q -IhEr '^[^#]*install_python' '{app.path}/scripts/'"
        if os.system(cmd) == 0:
            yield Warning(
                "It looks like this app installs a custom version of Python which is heavily discouraged, both because it takes a shitload amount of time to compile Python locally, and because it is likely to create complication later once the system gets upgraded to newer Debian versions..."
            )

    @test()
    def change_url_script(app):

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

        if file_exists(app.path + "/config_panel.toml.example"):
            yield Warning(
                "Please do not commit config_panel.toml.example ... This is just a 'documentation' for the config panel syntax meant to be kept in example_ynh"
            )

        if not file_exists(app.path + "/config_panel.toml") and file_exists(
            app.path + "/scripts/config"
        ):
            yield Warning(
                "The script 'config' exists but there is no config_panel.toml ... Please remove the 'config' script if this is just the example from example_ynh, or add a proper config_panel.toml if the point is really to have a config panel"
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
                tomllib.load(open(app.path + "/config_panel.toml", "rb")),
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

    @test()
    def remaining_replacebyyourapp(self):
        if os.system("grep -I -qr 'REPLACEBYYOURAPP' %s 2>/dev/null" % self.path) == 0:
            yield Error("You should replace all occurences of REPLACEBYYOURAPP.")

    @test()
    def supervisor_usage(self):
        if (
            os.system(r"grep -I -qr '^\s*supervisorctl' %s 2>/dev/null" % self.path)
            == 0
        ):
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
        cmd = (
            f"grep -I 'git clone' '{app.path}'/scripts/install '{app.path}'/scripts/_common.sh 2>/dev/null"
            r" | grep -qv 'xxenv\|rbenv\|oracledb'"
        )
        if os.system(cmd) == 0:
            yield Warning(
                "Using 'git clone' is not recommended ... most forge do provide the ability to download a proper archive of the code for a specific commit. Please use the 'sources' resource in the manifest.toml in combination with ynh_setup_source."
            )

    @test()
    def helpers_version_requirement(app):

        cmd = "grep -IhEro 'ynh_\\w+ *\\( *\\)' '%s/scripts' | tr -d '() '" % app.path
        custom_helpers = (
            subprocess.check_output(cmd, shell=True).decode("utf-8").strip().split("\n")
        )
        custom_helpers = [c.split("__")[0] for c in custom_helpers]

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
