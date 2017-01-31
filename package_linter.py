#!/usr/bin/env python3
# -*- coding: utf8 -*-

import sys
import os
import re
import json


class c:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
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


def print_wrong(str):
    print(c.FAIL + "✘", str, c.END)


def check_files_exist(app_path):
    """
    Check files exist
    """
    return_code = 0

    print (c.BOLD + c.HEADER + ">>>> MISSING FILES <<<<" + c.END)
    fnames = ("manifest.json", "scripts/install", "scripts/remove",
             "scripts/upgrade", "scripts/backup", "scripts/restore", "LICENSE", "README.md")

    for fname in fnames:
        if check_file_exist(app_path + "/" + fname):
            print_right(fname)
        else:
            print_wrong(fname)
            return_code = 1

    return return_code


def check_file_exist(file_path):
    return 1 if os.path.isfile(file_path) and os.stat(file_path).st_size > 0 else 0


def read_file(file_path):
    with open(file_path) as f:
        # remove every comments from the file content to avoid false positives
        file = re.sub("#.*[^\n]", "", f.read()).splitlines()
    return file


def check_manifest(manifest):
    print (c.BOLD + c.HEADER + "\n>>>> MANIFEST <<<<" + c.END)
    """
    Check if there is no comma syntax issue
    """

    return_code = 0

    try:
        with open(manifest, encoding='utf-8') as data_file:
            manifest = json.loads(data_file.read())
        print_right("Manifest syntax is good.")
    except:
        print_wrong(
            "Syntax (comma) or encoding issue with manifest.json. Can't check file.")
        return 1

    fields = ("name", "id", "packaging_format", "description", "url",
              "license", "maintainer", "requirements", "multi_instance", "services", "arguments")

    for field in fields:
        if field in manifest:
            print_right("\"" + field + "\" field is present")
        else:
            print_wrong("\"" + field + "\" field is missing")
            return_code = 1

    """
    Check values in keys
    """

    pf = 1

    if "packaging_format" not in manifest:
        print_wrong("\"packaging_format\" key is missing")
        return_code = 1
        pf = 0

    if pf == 1 and isinstance(manifest["packaging_format"], int) != 1:
        print_wrong("\"packaging_format\": value isn't an integer type")
        return_code = 1
        pf = 0

    if pf == 1 and manifest["packaging_format"] != 1:
        print_wrong("\"packaging_format\" field: current format value is '1'")
        return_code = 1
        pf = 0

    if pf == 1:
        print_right("\"packaging_format\" field is good")

    """
    if "license" in manifest and manifest["license"] != "free" and manifest["license"] != "non-free":
        print_wrong(
            "You should specify 'free' or 'non-free' software package in the license field.")
        return_code = 1
    elif "license" in manifest:
        print_right("\"licence\" key value is good")
    """

    if "multi_instance" in manifest and manifest["multi_instance"] != 1 and manifest["multi_instance"] != 0:
        print_wrong(
            "\"multi_instance\" field must be boolean type values 'true' or 'false' and not string type")
        return_code = 1
    elif "multi_instance" in manifest:
        print_right("\"multi_instance\" field is good")

    if "services" in manifest:
        services = ("nginx", "php5-fpm", "mysql", "uwsgi", "metronome",
                    "postfix", "dovecot")  # , "rspamd", "rmilter")

        for service in manifest["services"]:
            if service not in services:
                print_wrong(service + " service doesn't exist")
                return_code = 1

    if "install" in manifest["arguments"]:
        types = ("domain", "path", "password", "user", "admin")

        for nbr, typ in enumerate(types):
            for install_arg in manifest["arguments"]["install"]:
                if typ == install_arg["name"]:
                    if "type" not in install_arg:
                        print("You should specify the type of the key with", end=" ")
                        print(types[nbr - 1]) if nbr == 4 else print(typ)
                        return_code = 1

    return return_code


def check_script(path, script_name, script_nbr):
    return_code = 0

    script_path = path + "/scripts/" + script_name

    if check_file_exist(script_path) == 0:
        return

    print (c.BOLD + c.HEADER + "\n>>>>",
           script_name.upper(), "SCRIPT <<<<" + c.END)

    script = read_file(script_path)

    return_code = check_sudo_prefix_commands(script) or return_code
    return_code = check_non_helpers_usage(script) or return_code
    if script_nbr < 5:
        return_code = check_verifications_done_before_modifying_system(script) or return_code
        return_code = check_set_usage(script_name, script) or return_code

    return return_code


def check_sudo_prefix_commands(script):
    """
    Check if commands are prefix with "sudo"
    """
    cmds = ("rm", "chown", "chmod", "apt-get", "apt",
           "service", "yunohost", "find" "swapon", "mkswap", "useradd")  # , "dd") cp, mkdir
    ok = True

    for line_nbr, line in enumerate(script):
        for cmd in cmds:
            if cmd + " " in line and "sudo " + cmd + " " not in line \
                    and "yunohost service" not in line and "-exec " + cmd not in line \
                    and ".service" not in line and line[0] != '#':
                print(c.FAIL + "✘ Line ", line_nbr + 1,
                      "you should add \"sudo\" before this command line:", c.END)
                print("  " + line.replace(cmd,
                                       c.BOLD + c.FAIL + cmd + c.END))
                ok = False
    if ok:
        print_right("All commands are prefix with \"sudo\".")
        return 0

    return 1


def check_verifications_done_before_modifying_system(script):
    """
    Check if verifications are done before modifying the system
    """
    ex = 0
    for line_number, line in enumerate(script):
        if "ynh_die" in line or "exit" in line:
            ex = line_number

    cmds = ("cp", "mkdir", "rm", "chown", "chmod", "apt-get", "apt", "service",
           "find", "sed", "mysql", "swapon", "mount", "dd", "mkswap", "useradd")  # "yunohost"

    ok = True

    for line_nbr, line in enumerate(script):
        if line_nbr >= ex:
            break

        for cmd in cmds:
            if cmd in line and line[0] != '#':
                ok = False

    if not ok:
        print(c.FAIL + "✘ At line", ex + 1,
              "'ynh_die' or 'exit' command is executed with system modification before.\n",
        "This system modification is an issue if a verification exit the script.\n",
        "You should move this verification before any system modification." + c.END)
        return 1
    else:
        print_right(
            "Verifications (with 'ynh_die' or 'exit' commands) are done before any system modification.")
        return 0

def check_non_helpers_usage(script):
    """
    check if deprecated commands are used and propose helpers:
    - 'yunohost app setting' –> ynh_app_setting_(set,get,delete)
    - 'exit' –> 'ynh_die'
    """
    return_code = 0

    ok = True

    for line_nbr, line in enumerate(script):
        if "yunohost app setting" in line:
            print_wrong("Line {}: 'yunohost app setting' command is deprecated, please use helpers ynh_app_setting_(set,get,delete).".format(line_nbr + 1))
            ok = False

    if ok:
        print_right("Only helpers are used")
    else:
        print_wrong("Helpers documentation: https://yunohost.org/#/packaging_apps_helpers\ncode: https://github.com/YunoHost/yunohost/…helpers")
        return_code = 1

    ok = True

    for line_nbr, line in enumerate(script):
        if "exit" in line:
            print_wrong("Line {}: 'exit' command shouldn't be used. Use 'ynh_die' helper instead.".format(line_nbr + 1))
            ok = False

    if ok:
        print_right("no 'exit' command found: 'ynh_die' helper is possibly used")
    else:
        return_code = 1

    return return_code


def check_set_usage(script_name, script):
    return_code = 0
    present = False
    set_val = "set -u" if script_name == "remove" else "set -eu"

    for line_nbr, line in enumerate(script):
        if set_val in line:
            present = True
            break
        if line_nbr > 5:
            break
    if present:
        print_right(set_val + " is present at beginning of file")
    else:
        print_wrong(set_val + " is missing at beginning of file. For details, look at https://dev.yunohost.org/issues/419")
        return_code = 1

    return return_code

if __name__ == '__main__':
    os.system("clear")

    return_code = 0

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
    return_code = check_files_exist(app_path) or return_code
    return_code = check_manifest(app_path + "/manifest.json") or return_code

    scripts = ["install", "remove", "upgrade", "backup", "restore"]
    for (dirpath, dirnames, filenames) in os.walk(os.path.join(app_path, "scripts")):
        for filename in filenames:
            if filename not in scripts and filename[-4:] != ".swp":
                scripts.append(filename)

    for script_nbr, script in enumerate(scripts):
        return_code = check_script(app_path, script, script_nbr) or return_code

    sys.exit(return_code)
