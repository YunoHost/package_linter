#!/usr/bin/env python3

import sys
import os
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
          "YUNOHOST APP PACKAGE LINTER\n" + c.END)
    print("App packaging documentation: https://yunohost.org/#/packaging_apps")
    print("App package example: https://github.com/YunoHost/example_ynh\n")
    print("Checking " + c.BOLD + app_path + c.END + " package\n")


def print_right(str):
    print(c.OKGREEN + "✔", str, c.END)


def print_wrong(str):
    print(c.FAIL + "✘", str, c.END)


def check_files_exist(app_path):
    """
    Check files exist
    """
    print (c.BOLD + c.HEADER + ">>>> MISSING FILES <<<<" + c.END)
    fname = ("manifest.json", "scripts/install", "scripts/remove",
             "scripts/upgrade", "scripts/backup", "scripts/restore", "LICENSE", "README.md")
    i = 0
    while (i < len(fname)):
        if (check_file_exist(app_path + "/" + fname[i])):
            print_right(fname[i])
        else:
            print_wrong(fname[i])
        i += 1


def check_file_exist(file_path):
    return 1 if os.path.isfile(file_path) and os.stat(file_path).st_size > 0 else 0


def read_file(file_path):
    with open(file_path) as f:
        file = f.read().splitlines()
    return file


def check_manifest(manifest):
    print (c.BOLD + c.HEADER + "\n>>>> MANIFEST <<<<" + c.END)
    """
	Check if there is no comma syntax issue
	"""
    try:
        with open(manifest, encoding='utf-8') as data_file:
            manifest = json.loads(data_file.read())
        print_right("Manifest syntax is good.")
    except:
        print_wrong(
            "Syntax (comma) or encoding issue with manifest.json. Can't check file.")
        return
    i, fields = 0, ("name", "id", "packaging_format", "description", "url",
                    "license", "maintainer", "requirements", "multi_instance", "services", "arguments")
    while (i < len(fields)):
        if fields[i] in manifest:
            print_right("\"" + fields[i] + "\" field is present")
        else:
            print_wrong("\"" + fields[i] + "\" field is missing")
        i += 1
    """
    Check values in keys
    """
    pf = 1
    if "packaging_format" not in manifest:
        print_wrong("\"packaging_format\" key is missing")
        pf = 0
    if pf == 1 and isinstance(manifest["packaging_format"], int) != 1:
        print_wrong("\"packaging_format\": value isn't an integer type")
        pf = 0
    if pf == 1 and manifest["packaging_format"] != 1:
        print_wrong("\"packaging_format\" field: current format value is '1'")
        pf = 0
    if pf == 1:
        print_right("\"packaging_format\" field is good")

    if "license" in manifest and manifest["license"] != "free" and manifest["license"] != "non-free":
        print_wrong(
            "You should specify 'free' or 'non-free' software package in the license field.")
    elif "license" in manifest:
        print_right("\"licence\" key value is good")
    if "multi_instance" in manifest and manifest["multi_instance"] != 1 and manifest["multi_instance"] != 0:
        print_wrong(
            "\"multi_instance\" field must be boolean type values 'true' or 'false' and not string type")
    elif "multi_instance" in manifest:
        print_right("\"multi_instance\" field is good")
    if "services" in manifest:
        services = ("nginx", "php5-fpm", "mysql", "uwsgi", "metronome",
                    "postfix", "dovecot")  # , "rspamd", "rmilter")
        i = 0
        while (i < len(manifest["services"])):
            if manifest["services"][i] not in services:
                print_wrong(manifest["services"][i] + " service doesn't exist")
            i += 1
    if "install" in manifest["arguments"]:
        types = ("domain", "path", "password", "user", "admin")
        i = 0
        while (i < len(types)):
            j = 0
            while (j < len(manifest["arguments"]["install"])):
                if types[i] == manifest["arguments"]["install"][j]["name"]:
                    if "type" not in manifest["arguments"]["install"][j]:
                        print("You should specify the type of the key with", end=" ")
                        print(types[i - 1]) if i == 4 else print(types[i])
                j += 1
            i += 1


def check_script(path, script_name):
    script_path = path + "/scripts/" + script_name
    if check_file_exist(script_path) == 0:
        return
    print (c.BOLD + c.HEADER + "\n>>>>",
           script_name.upper(), "SCRIPT <<<<" + c.END)

    script = read_file(script_path)
    check_script_header_presence(script)
    check_sudo_prefix_commands(script)
    check_verifications_done_before_modifying_system(script)
    check_non_helpers_usage(script)


def check_script_header_presence(script):
    if "#!/bin/bash" in script[0]:
        print_right("Script starts with \"#!/bin/bash\"")
    else:
        print_wrong("Script must start with \"#!/bin/bash\"")


def check_sudo_prefix_commands(script):
    """
    Check if commands are prefix with "sudo"
    """
    cmd = ("rm", "chown", "chmod", "apt-get", "apt",
           "service", "yunohost", "find" "swapon", "mkswap", "useradd")  # , "dd") cp, mkdir
    i, ok = 0, 1
    while i < len(script):
        j = 0
        while j < len(cmd):
            if cmd[j] + " " in script[i] and "sudo " + cmd[j] + " " not in script[i] \
                    and "yunohost service" not in script[i] and "-exec " + cmd[j] not in script[i] \
                    and ".service" not in script[i] and script[i][0] != '#':
                print(c.FAIL + "✘ Line ", i + 1,
                      "you should add \"sudo\" before this command line:", c.END)
                print("  " + script[i].replace(cmd[j],
                                               c.BOLD + c.FAIL + cmd[j] + c.END))
                ok = 0
            j += 1
        i += 1
    if ok == 1:
        print_right("All commands are prefix with \"sudo\".")


def check_verifications_done_before_modifying_system(script):
    """
    Check if verifications are done before modifying the system
    """
    ex, i = 0, 0
    while i < len(script):
        if "ynh_die" in script[i] or "exit" in script[i]:
            ex = i
        i += 1
    cmd = ("cp", "mkdir", "rm", "chown", "chmod", "apt-get", "apt", "service",
           "find", "sed", "mysql", "swapon", "mount", "dd", "mkswap", "useradd")  # "yunohost"
    i, ok = 0, 1
    while i < len(script):
        if i >= ex:
            break
        j = 0
        while (j < len(cmd)):
            if cmd[j] in script[i] and script[i][0] != '#':
                ok = 0
            j += 1
        i += 1
    if ok == 0:
        print(c.FAIL + "✘ At line", ex + 1,
              "'ynh_die' or 'exit' command is executed with system modification before.")
        print("This system modification is an issue if a verification exit the script.")
        print("You should move this verification before any system modification." + c.END)
    else:
        print_right(
            "Verifications (with 'ynh_die' or 'exit' commands) are done before any system modification.")

def check_non_helpers_usage(script):
    """
    check if deprecated commands are used and propose helpers:
    - 'yunohost app setting' –> ynh_app_setting_(set,get,delete)
    - 'exit' –> 'ynh_die'
    """
    i, ok = 0, 1
    while i < len(script):
        if "yunohost app setting" in script[i]:
            print_wrong("Line {}: 'yunohost app setting' command is deprecated, please use helpers ynh_app_setting_(set,get,delete).".format(i + 1))
            ok = 0
        i += 1
    if ok == 1:
        print_right("Only helpers are used")
    else:
        print_wrong("Helpers documentation: https://yunohost.org/#/packaging_apps_helpers\ncode: https://github.com/YunoHost/yunohost/…helpers")

    i, ok = 0, 1
    while i < len(script):
        if "exit" in script[i]:
            print_wrong("Line {}: 'exit' command shouldn't be used. Use 'ynh_die' helper instead.".format(i + 1))
            ok = 0
        i += 1
    if ok == 1:
        print_right("no 'exit' command found: 'ynh_die' helper is possibly used")

if __name__ == '__main__':
    os.system("clear")
    if len(sys.argv) != 2:
        print("Give one app package path.")
        exit()
    app_path = sys.argv[1]
    header(app_path)
    check_files_exist(app_path)
    check_manifest(app_path + "/manifest.json")
    i, scripts = 0, ["install", "remove", "upgrade", "backup", "restore"]
    for (dirpath, dirnames, filenames) in os.walk(os.path.join(app_path, "scripts")):
        for filename in filenames:
            if filename not in scripts and filename[-4:] != ".swp":
                scripts.append(filename)
    while i < len(scripts):
        check_script(app_path, scripts[i])
        i += 1
