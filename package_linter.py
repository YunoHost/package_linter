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


# ############################################################################
#   Actual high-level checks
# ############################################################################

class App():

    def __init__(self, path):

        print_header("LOADING APP")
        self.path = path

        scripts = ["install", "remove", "upgrade", "backup", "restore"]
        self.scripts = {f: Script(self.path, f) for f in scripts}

    def analyze(self):

        self.misc_file_checks()
        self.check_helper_consistency()
        self.check_source_management()
        self.check_manifest()

        for script in self.scripts.values():
            if script.exists:
                script.analyze()

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
                print_error("File %s is mandatory" % filename)

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
        # Deprecated usage of 'add_header' in nginx conf
        #

        for filename in os.listdir(self.path + "/conf"):
            if not os.path.isfile(self.path + "/conf/" + filename):
                continue
            content = open(self.path + "/conf/" + filename).read()
            if "location" in content and "add_header" in content:
                print_warning(
                    "Do not use 'add_header' in the nginx conf. Use 'more_set_headers' instead. "
                    "(See https://www.peterbe.com/plog/be-very-careful-with-your-add_header-in-nginx "
                    "and https://github.com/openresty/headers-more-nginx-module#more_set_headers )"
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

    def check_source_management(self):
        print_header("SOURCES MANAGEMENT")
        DIR = os.path.join(self.path, "sources")
        # Check if there is more than six files on 'sources' folder
        if os.path.exists(os.path.join(self.path, "sources")) \
           and len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))]) > 5:
            print_warning(
                "[YEP-3.3] Upstream app sources shouldn't be stored in this 'sources' folder of this git repository as a copy/paste\n"
                "During installation, the package should download sources from upstream via 'ynh_setup_source'.\n"
                "See the helper documentation. "
                "Original discussion happened here : "
                "https://github.com/YunoHost/issues/issues/201#issuecomment-391549262"
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
                manifest = json.loads(data_file.read())
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
            if not re.match('^[a-z1-9]((_|-)?[a-z1-9])+$', manifest["id"]):
                print_error("[YEP-1.1] 'id' field '%s' should respect this regex '^[a-z1-9]((_|-)?[a-z1-9])+$'")

        if "name" in manifest:
            if len(manifest["name"]) > 22:
                print_warning(
                    "[YEP-1.1] The 'name' field shouldn't be too long to be able to be with one line in the app list. "
                    "The most current bigger name is actually compound of 22 characters."
                )

        # YEP 1.2 Put the app in a weel known repo
        if "id" in manifest:
            official_list_url = "https://raw.githubusercontent.com/YunoHost/apps/master/official.json"
            official_list = json.loads(urlopen(official_list_url)['content'])
            community_list_url = "https://raw.githubusercontent.com/YunoHost/apps/master/community.json"
            community_list = json.loads(urlopen(community_list_url)['content'])
            if manifest["id"] not in official_list and manifest["id"] not in community_list:
                print_warning("[YEP-1.2] This app is not registered in official or community applications")

        # YEP 1.3 License
        def license_mentionned_in_readme(path):
            readme_path = os.path.join(path, 'README.md')
            if os.path.isfile(readme_path):
                return "LICENSE" in open(readme_path).read()
            return False

        if "license" in manifest:
            for license in manifest['license'].replace('&', ',').split(','):
                code_license = '<code property="spdx:licenseId">' + license + '</code>'
                link = "https://spdx.org/licenses/"
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
                elif code_license not in urlopen(link)['content']:
                    print_warning(
                        "[YEP-1.3] The license '%s' is not registered in https://spdx.org/licenses/ . "
                        "It can be a typo error. If not, you should replace it by 'free' "
                        "or 'non-free' and give some explanations in the README.md." % (license)
                    )

        # YEP 1.4 Inform if we continue to maintain the app
        # YEP 1.5 Update regularly the app status
        # YEP 1.6 Check regularly the evolution of the upstream

        # YEP 1.7 - Add an app to the YunoHost-Apps organization
        if "id" in manifest:
            repo = "https://github.com/YunoHost-Apps/%s_ynh" % (manifest["id"])
            is_not_added_to_org =  urlopen(repo)['code'] == 404

            if is_not_added_to_org:
                print_warning("[YEP-1.7] You should add your app in the YunoHost-Apps organisation.")

        # YEP 1.8 Publish test request
        # YEP 1.9 Document app
        if "description" in manifest:
            descr = manifest["description"]
            if isinstance(descr, dict):
                descr = descr.get("en", None)

            if descr is None or descr == manifest.get("name", None):
                print_warning(
                    "[YEP-1.9] You should write a good description of the app, "
                    "at least in english (1 line is enough)."
                )

            elif "for yunohost" in descr.lower():
                print_warning(
                    "[YEP-1.9] The 'description' should explain what the app actually does. "
                    "No need to say that it is 'for YunoHost' - this is a YunoHost app "
                    "so of course we know it is for YunoHost ;-)."
                )

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

        if "url" in manifest and manifest["url"].endswith("_ynh"):
            print_warning(
                "'url' is not meant to be the url of the yunohost package, "
                "but rather the website or repo of the upstream app itself..."
            )


class Script():

    def __init__(self, app_path, name):
        self.name = name
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

        for line in lines:
            try:
                line = shlex.split(line, True)
                yield line
            except Exception as e:
                print_warning("%s : Could not parse this line (%s) : %s" % (self.path, e, line))

    def contains(self, command):
        """
        Iterate on lines to check if command is contained in line

        For instance, "app setting" is contained in "yunohost app setting $app ..."
        """
        return any(command in line
                   for line in [ ' '.join(line) for line in self.lines])

    def analyze(self):

        print_header(self.name.upper() + " SCRIPT")

        self.check_verifications_done_before_modifying_system()
        self.check_set_usage()
        self.check_helper_usage_dependencies()
        self.check_deprecated_practices()

    def check_verifications_done_before_modifying_system(self):
        """
        Check if verifications are done before modifying the system
        """

        if not self.contains("ynh_die") and not self.contains("exit"):
            return

        # FIXME : this really looks like a very small subset of command that
        # can be used ... also packagers are not supposed to use apt or service
        # anymore ...
        modifying_cmds = ("cp", "mkdir", "rm", "chown", "chmod", "apt-get", "apt",
                          "service", "find", "sed", "mysql", "swapon", "mount",
                          "dd", "mkswap", "useradd")
        cmds_before_exit = []
        for cmd in self.lines:
            cmd = " ".join(cmd)

            if "ynh_die" in cmd or "exit" in cmd:
                break
            cmds_before_exit.append(cmd)

        for modifying_cmd in modifying_cmds:
            if any(modifying_cmd in cmd for cmd in cmds_before_exit):
                print_error(
                    "[YEP-2.4] 'ynh_die' or 'exit' command is executed with system modification before (cmd '%s').\n"
                    "This system modification is an issue if a verification exit the script.\n"
                    "You should move this verification before any system modification." % modifying_cmd, False
                )
                return

    def check_set_usage(self):
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
            print_warning("'yunohost app setting' shouldn't be used directly. Please use 'ynh_app_setting_(set,get,delete)' instead.")
        if self.contains("yunohost app checkurl"):
            print_warning("'yunohost app checkurl' is deprecated. Please use 'ynh_webpath_register' instead.")
        if self.contains("yunohost app checkport"):
            print_warning("'yunohost app checkport' is deprecated. Please use 'ynh_find_port' instead.")
        if self.contains("yunohost app initdb"):
            print_warning("'yunohost app initdb' is deprecated. Please use 'ynh_mysql_setup_db' instead.")
        if self.contains("exit"):
            print_warning("'exit' command shouldn't be used. Please use 'ynh_die' instead.")

        if self.contains("rm -rf"):
            print_error("[YEP-2.12] You should avoid using 'rm -rf', please use 'ynh_secure_remove' instead")
        if self.contains("sed -i"):
            print_warning("[YEP-2.12] You should avoid using 'sed -i', please use 'ynh_replace_string' instead")
        if self.contains("sudo"):
            print_warning(
                "[YEP-2.12] You should not need to use 'sudo', the script is being run as root. "
                "(If you need to run a command using a specific user, use 'ynh_exec_as')"
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


def main():
    if len(sys.argv) != 2:
        print("Give one app package path.")
        exit()

    app_path = sys.argv[1]
    header(app_path)
    App(app_path).analyze()
    sys.exit(return_code)


if __name__ == '__main__':
    main()
