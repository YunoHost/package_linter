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


class c:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    MAYBE_FAIL = '\033[96m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def header(app_path):
    print(c.UNDERLINE + c.HEADER + c.BOLD +
          "YUNOHOST APP PACKAGE LINTER\n", c.END,
    "App packaging documentation: https://yunohost.org/#/packaging_apps\n",
    "App package example: https://github.com/YunoHost/example_ynh\n",
    "Checking " + c.BOLD + app_path + c.END + " package\n")


def print_right(str):
    print(c.OKGREEN + "✔", str, c.END)


def print_warning(str):
    print(c.WARNING + "!", str, c.END)


def print_wrong(str, reliable=True):
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


def check_files_exist(app_path):
    """
    Check files exist
    'backup' and 'restore' scripts are mandatory
    """

    print(c.BOLD + c.HEADER + ">>>> MISSING FILES <<<<" + c.END)
    fnames = ("manifest.json", "scripts/install", "scripts/remove",
              "scripts/upgrade", "scripts/backup", "scripts/restore", "LICENSE",
              "README.md")

    for nbr, fname in enumerate(fnames):
        if not check_file_exist(app_path + "/" + fname):
            if nbr != 4 and nbr != 5:
                print_wrong(fname)
            else:
                print_warning(fname)


def check_file_exist(file_path):
    return 1 if os.path.isfile(file_path) and os.stat(file_path).st_size > 0 else 0


def read_file(file_path):
    f = open(file_path)
    # remove every comments and empty lines from the file content to avoid
    # false positives
    file = shlex.shlex(f, False)
    #file = filter(None, re.sub("#.*[^\n]", "", f.read()).splitlines())
    return file


def check_source_management(app_path):
    print(c.BOLD + c.HEADER + "\n>>>> SOURCES MANAGEMENT <<<<" + c.END)
    DIR = os.path.join(app_path, "sources")
    # Check if there is more than six files on 'sources' folder
    if os.path.exists(os.path.join(app_path, "sources")) and \
     len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))]) > 5:
        print_warning("[YEP-3.3] Upstream app sources shouldn't be stored on this "
                      "'sources' folder of this git repository as a copy/paste."
                      "\nAt installation, the package should download sources "
                      "from upstream via 'ynh_setup_source'.\nSee "
                      "https://dev.yunohost.org/issues/201#Conclusion-chart")

def is_license_mention_in_readme(path):
    readme_path = os.path.join(path, 'README.md')
    if os.path.isfile(readme_path):
        return "LICENSE" in open(readme_path).read()
    return False

def check_manifest(path):
    manifest = os.path.join(path, 'manifest.json')
    if not os.path.exists(manifest):
        return
    print(c.BOLD + c.HEADER + "\n>>>> MANIFEST <<<<" + c.END)
    """
    Check if there is no comma syntax issue
    """

    try:
        with open(manifest, encoding='utf-8') as data_file:
            manifest = json.loads(data_file.read())
    except:
        print_wrong("[YEP-2.1] Syntax (comma) or encoding issue with manifest.json. "
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
        print_wrong("[YEP-2.1] \"packaging_format\" key is missing")
    elif not isinstance(manifest["packaging_format"], int):
        print_wrong("[YEP-2.1] \"packaging_format\": value isn't an integer type")
    elif manifest["packaging_format"] != 1:
        print_wrong("[YEP-2.1] \"packaging_format\" field: current format value is '1'")

    # YEP 1.1 Name is app
    if "id" in manifest:
        if not re.match('^[a-z1-9]((_|-)?[a-z1-9])+$', manifest["id"]):
            print_wrong("[YEP-1.1] 'id' field '%s' should respect this regex "
                        "'^[a-z1-9]((_|-)?[a-z1-9])+$'")

    if "name" in manifest:
        if len(manifest["name"]) > 22 :
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
                if not is_license_mention_in_readme(path):
                    print_warning("[YEP-1.3] The use of '%s' in license field implies to "
                                  "write something about the license in your "
                                  "README.md" % (license))
                if license in ["non-free", "dep-non-free"]:
                    print_warning("[YEP-1.3] 'non-free' apps can't be officialized."
                                  "Their integration is still being discussed,"
                                  "especially for apps with non-free dependencies")
            elif code_license not in urlopen(link)['content']:
                print_warning("[YEP-1.3] The license '%s' is not registered in "
                            "https://spdx.org/licenses/ . It can be a typo error."
                            "If no, you should write free or non-free in place and"
                            " gice more explanation in README.md" % (license))

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
    if "description" in manifest and "name" in manifest:
        if manifest["description"] == manifest["name"]:
            print_warning("[YEP-1.9] You should write a good description of the"
                          "app (1 line is enough).")
    #TODO test a specific template in README.md

    # YEP 1.10 Garder un historique de version propre

    # YEP 1.11 Cancelled

    # YEP 2.1
    if "multi_instance" in manifest and manifest["multi_instance"] != 1 and manifest["multi_instance"] != 0:
        print_wrong(
            "[YEP-2.1] \"multi_instance\" field must be boolean type values 'true' or 'false' and not string type")

    if "services" in manifest:
        services = ("nginx", "php5-fpm", "mysql", "uwsgi", "metronome",
                    "postfix", "dovecot")  # , "rspamd", "rmilter")

        for service in manifest["services"]:
            if service not in services:
                print_warning("[YEP-2.1]" + service + " service may not exist")

    if "install" in manifest["arguments"]:
        types = ("domain", "path", "password", "user", "admin")

        for nbr, typ in enumerate(types):
            for install_arg in manifest["arguments"]["install"]:
                if typ == install_arg["name"]:
                    if "type" not in install_arg:
                        print_wrong("[YEP-2.1] You should specify the type of the key with %s" % (typ))



def check_script(path, script_name, script_nbr):

    script_path = path + "/scripts/" + script_name

    if check_file_exist(script_path) == 0:
        return

    print(c.BOLD + c.HEADER + "\n>>>>",
           script_name.upper(), "SCRIPT <<<<" + c.END)

    check_non_helpers_usage(read_file(script_path))
    if script_nbr < 5:
        check_verifications_done_before_modifying_system(read_file(script_path))
        check_set_usage(script_name, read_file(script_path))
        #check_arg_retrieval(script.copy())


def check_verifications_done_before_modifying_system(script):
    """
    Check if verifications are done before modifying the system
    """
    ok = True
    modify_cmd = ''
    cmds = ("cp", "mkdir", "rm", "chown", "chmod", "apt-get", "apt", "service",
           "find", "sed", "mysql", "swapon", "mount", "dd", "mkswap", "useradd")
    cmds_before_exit = []
    is_exit = False
    for cmd in script:
        if "ynh_die" == cmd or "exit " == cmd:
            is_exit = True
            break
        cmds_before_exit.append(cmd)

    if not is_exit:
        return

    for cmd in cmds_before_exit:
        if "ynh_die" == cmd or "exit " == cmd:
            break
        if not ok or cmd in cmds:
            modify_cmd = cmd
            ok = False
            break

    if not ok:
        print_wrong("[YEP-2.4] 'ynh_die' or 'exit' command is executed with system modification before (cmd '%s').\n"
        "This system modification is an issue if a verification exit the script.\n"
        "You should move this verification before any system modification." % (modify_cmd) , False)


def check_non_helpers_usage(script):
    """
    check if deprecated commands are used and propose helpers:
    - 'yunohost app setting' –> ynh_app_setting_(set,get,delete)
    - 'exit' –> 'ynh_die'
    """

    ok = True
    #TODO
    #for line_nbr, cmd in script:
    #    if "yunohost app setting" in cmd:
    #        print_wrong("[YEP-2.11] Line {}: 'yunohost app setting' command is deprecated,"
    #                    " please use helpers ynh_app_setting_(set,get,delete)."
    #                    .format(line_nbr + 1))
    #        ok = False

    if not ok:
        print("Helpers documentation: "
                    "https://yunohost.org/#/packaging_apps_helpers\n"
                    "code: https://github.com/YunoHost/yunohost/…helpers")

    if "exit" in script:
        print_wrong("[YEP-2.4] 'exit' command shouldn't be used."
                    "Use 'ynh_die' helper instead.")


def check_set_usage(script_name, script):
    present = False

    if script_name in ["backup", "remove"]:
        present = "ynh_abort_if_errors" in script or "set -eu" in script
    else:
        present = "ynh_abort_if_errors" in script

    if script_name == "remove":
        # Remove script shouldn't use set -eu or ynh_abort_if_errors
        if present:
            print_wrong("[YEP-2.4] set -eu or ynh_abort_if_errors is present. "
                        "If there is a crash it could put yunohost system in "
                        "invalidated states. For details, look at "
                        "https://dev.yunohost.org/issues/419")
    else:
        if not present:
            print_wrong("[YEP-2.4] ynh_abort_if_errors is missing. For details,"
                        "look at https://dev.yunohost.org/issues/419")



def check_arg_retrieval(script):
    """
    Check arguments retrival from manifest is done with env var $YNH_APP_ARG_* and not with arg $1
    env var was found till line ~30 on scripts. Stop file checking at L30: This could avoid wrong positives
    Check only from '$1' to '$10' as 10 arg retrieval is already a lot.
    """
    present = False

    for cmd in script:
        if cmd =='$' and script.get_token() in [str(x) for x in range(1, 10)]:
            present = True
            break

    if present:
        print_wrong("Argument retrieval from manifest with $1 is deprecated. You may use $YNH_APP_ARG_*")
        print_wrong("For more details see: https://yunohost.org/#/packaging_apps_arguments_management_en")


if __name__ == '__main__':
    os.system("clear")


    if len(sys.argv) != 2:
        print("Give one app package path.")
        exit()

    # "or" trick to always be 1 if 1 is present:
    # 1 or 0 = 1
    # 1 or 1 = 1
    # 0 or 1 = 1
    # 0 or 0 = 0

    app_path = sys.argv[1]
    header(app_path)
    check_files_exist(app_path)
    check_source_management(app_path)
    check_manifest(app_path) # + "/manifest.json")

    scripts = ["install", "remove", "upgrade", "backup", "restore"]
    for (dirpath, dirnames, filenames) in os.walk(os.path.join(app_path, "scripts")):
        for filename in filenames:
            if filename not in scripts and filename[-4:] != ".swp":
                scripts.append(filename)

    for script_nbr, script in enumerate(scripts):
        check_script(app_path, script, script_nbr)

    sys.exit(return_code)
