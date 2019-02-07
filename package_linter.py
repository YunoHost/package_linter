#!/usr/bin/env python3
# -*- coding: utf8 -*-

import sys
import os
import re
import json
import shlex
import urllib.request
import codecs

reader = codecs.getreader("utf-8")
return_code = 0


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


def header(app):
    print("""
    [{header}{bold}YunoHost App Package Linter{end}]

 App packaging documentation - https://yunohost.org/#/packaging_apps
 App package example         - https://github.com/YunoHost/example_ynh
 Official helpers            - https://yunohost.org/#/packaging_apps_helpers_en
 Experimental helpers        - https://github.com/YunoHost-Apps/Experimental_helpers

    Analyzing package {header}{app}{end}"""
    .format(header=c.HEADER, bold=c.BOLD, end=c.END, app=app))


def print_header(str):
    print("\n [" + c.BOLD + c.HEADER + str.title() + c.END + "]\n")


def print_right(str):
    print(c.OKGREEN + "✔", str, c.END)


def print_warning(str):
    print(c.WARNING + "!", str, c.END)


def print_error(str, reliable=True):
    if reliable:
        global return_code
        return_code = 1
        print(c.FAIL + "✘", str, c.END)
    else:
        print(c.MAYBE_FAIL + "?", str, c.END)


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


def read_file_shlex(file_path):
    f = open(file_path)
    return shlex.shlex(f, False)


def read_file_raw(file_path):
    # remove every comments and empty lines from the file content to avoid
    # false positives
    f = open(file_path)
    file = "\n".join(filter(None, re.sub("#.*[^\n]", "", f.read()).splitlines()))
    return file


# ############################################################################
#   Actual high-level checks
# ############################################################################


def check_files_exist(app_path):
    """
    Check files exist
    'backup' and 'restore' scripts are not mandatory
    """

    print_header("MISSING FILES")
    filenames = ("manifest.json",
                 "scripts/install", "scripts/remove",
                 "scripts/upgrade",
                 "scripts/backup", "scripts/restore",
                 "LICENSE", "README.md")
    non_mandatory = ("script/backup", "script/restore")

    for filename in filenames:
        if file_exists(app_path + "/" + filename):
            continue
        elif filename in non_mandatory:
            print_warning(filename)
        else:
            print_error(filename)

    # Deprecated php-fpm.ini thing
    if file_exists(app_path + "/conf/php-fpm.ini"):
        print_warning("Using a separate php-fpm.ini file is deprecated. Please merge your php-fpm directives directly in the pool file. (c.f. https://github.com/YunoHost-Apps/nextcloud_ynh/issues/138 )")


def check_source_management(app_path):
    print_header("SOURCES MANAGEMENT")
    DIR = os.path.join(app_path, "sources")
    # Check if there is more than six files on 'sources' folder
    if os.path.exists(os.path.join(app_path, "sources")) \
       and len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))]) > 5:
        print_warning("[YEP-3.3] Upstream app sources shouldn't be stored on this "
                      "'sources' folder of this git repository as a copy/paste."
                      "\nAt installation, the package should download sources "
                      "from upstream via 'ynh_setup_source'.\nSee the helper"
                      "documentation. Original discussion happened here : "
                      "https://github.com/YunoHost/issues/issues/201#issuecomment-391549262")


def license_mentionned_in_readme(path):
    readme_path = os.path.join(path, 'README.md')
    if os.path.isfile(readme_path):
        return "LICENSE" in open(readme_path).read()
    return False


def check_manifest(path):
    manifest = os.path.join(path, 'manifest.json')
    if not os.path.exists(manifest):
        return
    print_header("MANIFEST")
    """
    Check if there is no comma syntax issue
    """

    try:
        with open(manifest, encoding='utf-8') as data_file:
            manifest = json.loads(data_file.read())
    except:
        print_error("[YEP-2.1] Syntax (comma) or encoding issue with manifest.json. "
                    "Can't check file.")

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
        if not re.match('^[a-z1-9]((_|-)?[a-z1-9])+$', manifest["id"]):
            print_error("[YEP-1.1] 'id' field '%s' should respect this regex "
                        "'^[a-z1-9]((_|-)?[a-z1-9])+$'")

    if "name" in manifest:
        if len(manifest["name"]) > 22:
            print_warning("[YEP-1.1] The 'name' field shouldn't be too long to be"
                          " able to be with one line in the app list. The most "
                          "current bigger name is actually compound of 22 characters.")

    # YEP 1.2 Put the app in a weel known repo
    if "id" in manifest:
        official_list_url = "https://raw.githubusercontent.com/YunoHost/apps/master/official.json"
        official_list = json.loads(urlopen(official_list_url)['content'])
        community_list_url = "https://raw.githubusercontent.com/YunoHost/apps/master/community.json"
        community_list = json.loads(urlopen(community_list_url)['content'])
        if manifest["id"] not in official_list and manifest["id"] not in community_list:
            print_warning("[YEP-1.2] This app is not registered in official or community applications")

    # YEP 1.3 License
    if "license" in manifest:
        for license in manifest['license'].replace('&', ',').split(','):
            code_license = '<code property="spdx:licenseId">' + license + '</code>'
            link = "https://spdx.org/licenses/"
            if license == "nonfree":
                print_warning("[YEP-1.3] The correct value for non free license in license"
                              " field is 'non-free' and not 'nonfree'")
                license = "non-free"
            if license in ["free", "non-free", "dep-non-free"]:
                if not license_mentionned_in_readme(path):
                    print_warning("[YEP-1.3] The use of '%s' in license field implies to "
                                  "write something about the license in your "
                                  "README.md" % (license))
                if license in ["non-free", "dep-non-free"]:
                    print_warning("[YEP-1.3] 'non-free' apps can't be officialized."
                                  "Their integration is still being discussed,"
                                  "especially for apps with non-free dependencies")
            elif code_license not in urlopen(link)['content']:
                print_warning("[YEP-1.3] The license '%s' is not registered in "
                            "https://spdx.org/licenses/ . It can be a typo error. "
                            "If not, you should replace it by 'free' or 'non-free'"
                            "and give some explanations in the README.md." % (license))

    # YEP 1.4 Inform if we continue to maintain the app
    # YEP 1.5 Update regularly the app status
    # YEP 1.6 Check regularly the evolution of the upstream

    # YEP 1.7 - Add an app to the YunoHost-Apps organization
    if "id" in manifest:
        repo = "https://github.com/YunoHost-Apps/%s_ynh" % (manifest["id"])
        is_not_added_to_org =  urlopen(repo)['code'] == 404

        if is_not_added_to_org:
            print_warning("[YEP-1.7] You should add your app in the "
                          "YunoHost-Apps organisation.")

    # YEP 1.8 Publish test request
    # YEP 1.9 Document app
    if "description" in manifest:
        descr = manifest["description"]
        if isinstance(descr, dict):
            descr = descr.get("en", None)

        if descr is None or descr == manifest.get("name", None):
            print_warning("[YEP-1.9] You should write a good description of the app, at least in english (1 line is enough).")

        elif "for yunohost" in descr.lower():
            print_warning("[YEP-1.9] The 'description' should explain what the app actually does. No need to say that it is 'for YunoHost' - this is a YunoHost app so of course we know it is for YunoHost ;-).")

    # TODO test a specific template in README.md

    # YEP 1.10 Garder un historique de version propre

    # YEP 1.11 Cancelled

    # YEP 2.1
    if "multi_instance" in manifest and manifest["multi_instance"] != 1 and manifest["multi_instance"] != 0:
        print_error(
            "[YEP-2.1] \"multi_instance\" field must be boolean type values 'true' or 'false' and not string type")

    if "services" in manifest:
        services = ("nginx", "mysql", "uwsgi", "metronome",
                    "php5-fpm", "php7.0-fpm", "php-fpm", 
                    "postfix", "dovecot", "rspamd")

        for service in manifest["services"]:
            if service not in services:
                # FIXME : wtf is it supposed to mean ...
                print_warning("[YEP-2.1] " + service + " service may not exist")

    if "install" in manifest["arguments"]:

        recognized_types = ("domain", "path", "boolean", "app", "password", "user", "string")

        for argument in manifest["arguments"]["install"]:
            if not "type" in argument.keys():
                print_error("[YEP-2.1] You should specify the type of the argument '%s'. You can use : %s." % (argument["name"], ', '.join(recognized_types)))
            elif argument["type"] not in recognized_types:
                print_warning("[YEP-2.1] The type '%s' for argument '%s' is not recognized... it probably doesn't behave as you expect ? Choose among those instead : %s" % (argument["type"], argument["name"], ', '.join(recognized_types)))

            if "choices" in argument.keys():
                choices = [ c.lower() for c in argument["choices"] ]
                if len(choices) == 2:
                    if ("true" in choices and "false" in choices) or ("yes" in choices and "no" in choices):
                        print_warning("Argument %s : you might want to simply use a boolean-type argument. No need to specify the choices list yourself." % argument["name"])


    if "url" in manifest and manifest["url"].endswith("_ynh"):
        print_warning("'url' is not meant to be the url of the yunohost package, but rather the website or repo of the upstream app itself...")


def check_verifications_done_before_modifying_system(script):
    """
    Check if verifications are done before modifying the system
    """
    ok = True
    modify_cmd = ''
    cmds = ("cp", "mkdir", "rm", "chown", "chmod", "apt-get", "apt", "service",
           "find", "sed", "mysql", "swapon", "mount", "dd", "mkswap", "useradd")
    cmds_before_exit = []
    has_exit = False
    for cmd in script["shlex"]:
        if cmd in ["ynh_die", "exit"]:
            has_exit = True
            break
        cmds_before_exit.append(cmd)

    if not has_exit:
        return

    for cmd in cmds_before_exit:
        if cmd in ["ynh_die", "exit"]:
            break
        if not ok or cmd in cmds:
            modify_cmd = cmd
            ok = False
            break

    if not ok:
        print_error("[YEP-2.4] 'ynh_die' or 'exit' command is executed with system modification before (cmd '%s').\n"
        "This system modification is an issue if a verification exit the script.\n"
        "You should move this verification before any system modification." % (modify_cmd), False)


def check_set_usage(script):
    present = False

    if script["name"] in ["backup", "remove"]:
        present = "ynh_abort_if_errors" in script["shlex"] or "set -eu" in script["raw"]
    else:
        present = "ynh_abort_if_errors" in script["shlex"]

    if script["name"] == "remove":
        # Remove script shouldn't use set -eu or ynh_abort_if_errors
        if present:
            print_error("[YEP-2.4] set -eu or ynh_abort_if_errors is present. "
                        "If there is a crash, it could put yunohost system in "
                        "a broken state. For details, look at "
                        "https://github.com/YunoHost/issues/issues/419")
    else:
        if not present:
            print_error("[YEP-2.4] ynh_abort_if_errors is missing. For details, "
                        "look at https://github.com/YunoHost/issues/issues/419")


def check_arg_retrieval(script):
    """
    Check arguments retrival from manifest is done with env var $YNH_APP_ARG_* and not with arg $1
    env var was found till line ~30 on scripts. Stop file checking at L30: This could avoid wrong positives
    Check only from '$1' to '$10' as 10 arg retrieval is already a lot.
    """
    present = False

    for cmd in script:
        if cmd == '$' and script.get_token() in [str(x) for x in range(1, 10)]:
            present = True
            break

    if present:
        print_error("Argument retrieval from manifest with $1 is deprecated. You may use $YNH_APP_ARG_*")
        print_error("For more details see: https://yunohost.org/#/packaging_apps_arguments_management_en")


def check_helper_usage_dependencies(script):
    """
    Detect usage of ynh_package_* & apt-get *
    and suggest herlpers ynh_install_app_dependencies and ynh_remove_app_dependencies
    """

    if "ynh_package_install" in script["shlex"] or "apt-get install" in script["raw"]:
        print_warning("You should not use `ynh_package_install` or `apt-get install`, use `ynh_install_app_dependencies` instead")

    if "ynh_package_remove" in script["shlex"] or "apt-get remove" in script["raw"]:
        print_warning("You should not use `ynh_package_remove` or `apt-get removeè, use `ynh_remove_app_dependencies` instead")


def check_helper_consistency(script):
    """
    check if ynh_install_app_dependencies is present in install/upgrade/restore
    so dependencies are up to date after restoration or upgrade
    """

    if script["name"] == "install" and "ynh_install_app_dependencies" in script["shlex"]:
        for name in ["upgrade", "restore"]:
            try:
                script2 = read_file_raw(os.path.dirname(script["path"] + "/" + name))
                if "ynh_install_app_dependencies" not in script2:
                    print_warning("ynh_install_app_dependencies should also be in %s script" % name)
            except FileNotFoundError:
                pass

    if script["name"] == "install" and "yunohost service add" in script["raw"]:
        try:
            script2 = read_file_raw(os.path.dirname(script["path"]) + "/remove")
            if "yunohost service remove" not in script2:
                print_error("You used 'yunohost service add' in the install script, but not 'yunohost service remove' in the remove script.")
        except FileNotFoundError:
            pass


def check_deprecated_practices(script):

    if "yunohost app setting" in script["raw"]:
        print_warning("'yunohost app setting' shouldn't be used directly. Please use 'ynh_app_setting_(set,get,delete)' instead.")
    if "yunohost app checkurl" in script["raw"]:
        print_warning("'yunohost app checkurl' is deprecated. Please use 'ynh_webpath_register' instead.")
    if "yunohost app checkport" in script["raw"]:
        print_warning("'yunohost app checkport' is deprecated. Please use 'ynh_find_port' instead.")
    if "yunohost app initdb" in script["raw"]:
        print_warning("'yunohost app initdb' is deprecated. Please use 'ynh_mysql_setup_db' instead.")
    if "exit" in script["shlex"]:
        print_warning("'exit' command shouldn't be used. Please use 'ynh_die' instead.")

    if "rm -rf" in script["raw"] or "rm -Rf" in script["raw"]:
        print_error("[YEP-2.12] You should avoid using 'rm -rf', please use 'ynh_secure_remove' instead")
    if "sed -i" in script["raw"]:
        print_warning("[YEP-2.12] You should avoid using 'sed -i', please use 'ynh_replace_string' instead")
    if "sudo " in script["raw"]:
        print_warning("[YEP-2.12] You should not need to use 'sudo', the script is being run as root. (If you need to run a command using a specific user, use 'ynh_exec_as')")

    if "dd if=/dev/urandom" in script["raw"] or "openssl rand" in script["raw"]:
        print_warning("Instead of 'dd if=/dev/urandom' or 'openssl rand', you might want to use ynh_string_random")

    if "systemctl restart nginx" in script["raw"] or "service nginx restart" in script["raw"]:
        print_error("Restarting nginx is quite dangerous (especially for web installs) and should be avoided at all cost. Use 'reload' instead.")

def main():
    if len(sys.argv) != 2:
        print("Give one app package path.")
        exit()

    app_path = sys.argv[1]
    header(app_path)

    # Global checks
    check_files_exist(app_path)
    check_source_management(app_path)
    check_manifest(app_path)

    # Scripts checks
    scripts = ["install", "remove", "upgrade", "backup", "restore"]
    for script_name in scripts:

        script = {"name": script_name,
                  "path": app_path + "/scripts/" + script_name}

        if not file_exists(script["path"]):
            continue

        print_header(script["name"].upper() + " SCRIPT")

        script["raw"] = read_file_raw(script["path"])
        # We transform the shlex thing into a list because the original
        # object has completely fucked-up behaviors :|.
        script["shlex"] = [ l for l in read_file_shlex(script["path"]) ]

        check_verifications_done_before_modifying_system(script)
        check_set_usage(script)
        check_helper_usage_dependencies(script)
        check_helper_consistency(script)
        check_deprecated_practices(script)
        # check_arg_retrieval(script)

    sys.exit(return_code)


if __name__ == '__main__':
    main()
