#!/usr/bin/env python3

import os
from pathlib import Path
import re
import shlex
import statistics
import subprocess
from typing import Generator

from lib.lib_package_linter import (
    Critical,
    Error,
    Info,
    TestResult,
    TestSuite,
    Warning,
    not_empty,
    report_warning_not_reliable,
    test,
)
from lib.print import _print


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
    def __init__(self, app: Path, name: str, app_id: str) -> None:
        self.name = name
        self.app = app
        self.app_id = app_id
        self.path = app / "scripts" / name
        self.exists = not_empty(self.path)
        if not self.exists:
            return
        self.lines = list(self.read_file())
        self.test_suite_name = "scripts/" + self.name

    def read_file(self) -> Generator[list[str], None, None]:
        lines = self.path.open().readlines()

        # Remove trailing spaces, empty lines and comment lines
        lines = [line.strip() for line in lines]
        lines = [line for line in lines if line and not line.startswith("#")]

        # Merge lines when ending with \
        lines = "\n".join(lines).replace("\\\n", "").split("\n")

        some_parsing_failed = False

        for line in lines:

            try:
                splitted_line = shlex.split(line, True)
                yield splitted_line
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

    def occurences(self, command: str) -> list[str]:
        return [
            line for line in [" ".join(line) for line in self.lines] if command in line
        ]

    def contains(self, command: str) -> bool:
        """
        Iterate on lines to check if command is contained in line

        For instance, "app setting" is contained in "yunohost app setting $app ..."
        """
        return any(command in line for line in [" ".join(line) for line in self.lines])

    def containsregex(self, regex: str) -> bool:
        """
        Iterate on lines to check if command is contained in line

        For instance, "app setting" is contained in "yunohost app setting $app ..."
        """
        return any(
            re.search(regex, line) for line in [" ".join(line) for line in self.lines]
        )

    @test()
    def error_handling(self) -> TestResult:

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
    def raw_apt_commands(self) -> TestResult:

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
    def obsolete_helpers(self) -> TestResult:
        if self.contains("yunohost app setting"):
            yield Critical(
                "Do not use 'yunohost app setting' directly. Please use 'ynh_app_setting_(set,get,delete)' instead."
            )
        if self.contains("ynh_detect_arch"):
            yield Warning(
                "(Requires yunohost 4.3) Using ynh_detect_arch is deprecated, since Yunohost 4.3, an $YNH_ARCH variable is directly available in the global context. Its value directly corresponds to `dpkg --print-architecture` which returns a value among : amd64, i386, armhf, arm64 and armel (though armel is probably not used at all?)"
            )

    @test(only=["install", "upgrade"])
    def deprecated_replace_string(self) -> TestResult:
        cmd1 = "grep -Ec 'ynh_replace_string' '%s' || true" % self.path
        cmd2 = "grep -Ec 'ynh_replace_string.*__\\w+__' '%s' || true" % self.path

        count1 = int(subprocess.check_output(cmd1, shell=True).decode("utf-8").strip())
        count2 = int(subprocess.check_output(cmd2, shell=True).decode("utf-8").strip())

        if count2 > 0 or count1 >= 5:
            yield Info(
                "Please consider using 'ynh_add_config' to handle config files instead of gazillions of manual cp + 'ynh_replace_string' + chmod"
            )

    @test()
    def bad_ynh_exec_syntax(self) -> TestResult:
        cmd = (
            'grep -q -IhEro "ynh_exec_(err|warn|warn_less|quiet|fully_quiet) (\\"|\').*(\\"|\')$" %s'
            % self.path
        )
        if os.system(cmd) == 0:
            yield Warning(
                "(Requires Yunohost 4.3) When using ynh_exec_*, please don't wrap your command between quotes (typically DONT write ynh_exec_warn_less 'foo --bar --baz')"
            )

    @test()
    def ynh_setup_source_keep_with_absolute_path(self) -> TestResult:
        cmd = 'grep -q -IhEro "ynh_setup_source.*keep.*install_dir" %s' % self.path
        if os.system(cmd) == 0:
            yield Info(
                "The --keep option of ynh_setup_source expects relative paths, not absolute path ... you do not need to prefix everything with '$install_dir' in the --keep arg ..."
            )

    @test()
    def ynh_npm_global(self) -> TestResult:
        if self.containsregex(r"ynh_npm.*install.*global"):
            yield Warning(
                "Please don't install stuff on global scope with npm install --global é_è"
            )

    @test()
    def ynh_add_fpm_config_deprecated_package_option(self) -> TestResult:
        if self.containsregex(r"ynh_add_fpm_config .*package=.*"):
            yield Error(
                "(Requires Yunohost 4.3) Option --package for ynh_add_fpm_config is deprecated : please use 'ynh_install_app_dependencies' with **all** your apt dependencies instead (no need to define a special 'extra_php_dependencies'). YunoHost will automatically install any phpX.Y-fpm / phpX.Y-common if needed."
            )

    @test()
    def set_is_public_setting(self) -> TestResult:
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
    def default_php_version_in_common(self) -> TestResult:
        if self.contains("YNH_DEFAULT_PHP_VERSION"):
            yield Warning(
                "Do not use YNH_DEFAULT_PHP_VERSION in _common.sh ... _common.sh is usually sourced *before* the helpers, which define the version of YNH_DEFAULT_PHP_VERSION (hence it gets replaced with empty string). Instead, please explicitly state the PHP version in the package, e.g. dependencies='php8.2-cli php8.2-imagemagick'"
            )

    @test(ignore=["install", "_common.sh"])
    def get_is_public_setting(self) -> TestResult:
        if self.contains("is_public=") or self.contains("$is_public"):
            yield Warning(
                "permission system: there should be no need to fetch or use $is_public ... is_public should only be used during installation to initialize the permission. The admin is likely to manually tweak the permission using YunoHost's interface later."
            )

    @test(only=["upgrade"])
    def temporarily_enable_visitors_during_upgrade(self) -> TestResult:
        if self.containsregex(
            "ynh_permission_update.*add.*visitors"
        ) and self.containsregex("ynh_permission_update.*remove.*visitors"):
            yield Warning(
                "permission system: since Yunohost 4.3, there should be no need to temporarily add 'visitors' to the main permission. ynh_local_curl will temporarily enable visitors access if needed"
            )

    @test()
    def set_legacy_permissions(self) -> TestResult:
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
    def normalize_url_path(self) -> TestResult:
        if self.contains("ynh_normalize_url_path"):
            yield Warning(
                "You probably don't need to call 'ynh_normalize_url_path'... this is only relevant for upgrades from super-old versions (like 3 years ago or so...)"
            )

    @test()
    def safe_rm(self) -> TestResult:
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
    def FIXMEs(self) -> TestResult:
        removeme = f"grep -q '#REMOVEME?' '{self.path}'"
        fixme = f"grep -q '# FIXMEhelpers2.1' '{self.path}'"

        if os.system(removeme) == 0:
            yield Warning("There are still some REMOVEME? flags to be taken care of")
        if os.system(fixme) == 0:
            yield Warning(
                "There are still some FIXMEhelpers2.1 flags to be taken care of"
            )

    @test()
    def nginx_restart(self) -> TestResult:
        if self.contains("systemctl restart nginx") or self.contains(
            "service nginx restart"
        ):
            yield Error(
                "Restarting NGINX is quite dangerous (especially for web installs) "
                "and should be avoided at all cost. Use 'reload' instead."
            )

    @test()
    def raw_systemctl_start(self) -> TestResult:
        if self.containsregex(r"systemctl start \"?[^. ]+(\.service)?\"?\s"):
            yield Warning(
                "Please do not use 'systemctl start' to start services. Instead, you should use 'ynh_systemd_action' which will display the service log in case it fails to start. You can also use '--line_match' to wait until some specific word appear in the log, signaling the service indeed fully started."
            )

    @test()
    def bad_line_match(self) -> TestResult:

        if self.containsregex(r"--line_match=Started$") or self.containsregex(
            r"--line_match=Stopped$"
        ):
            yield Warning(
                'Using --line_match="Started" or "Stopped" in ynh_systemd_action is counter productive because it will match the systemd message and not the actual app message ... Please check the log of the service to find an actual, relevant message to match, or remove the --line_match option entirely'
            )

    @test()
    def quiet_systemctl_enable(self) -> TestResult:

        systemctl_enable = [
            line
            for line in [" ".join(line) for line in self.lines]
            if re.search(r"^\s*systemctl.*(enable|disable)", line)
        ]

        if any("-q" not in cmd for cmd in systemctl_enable):
            message = "Please add --quiet to systemctl enable/disable commands to avoid unnecessary warnings when the script runs"
            yield Warning(message)

    @test()
    def quiet_wget(self) -> TestResult:

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
    def argument_fetching(self) -> TestResult:

        if self.containsregex(r"^\w+\=\$\{?[0-9]"):
            yield Critical(
                "Do not fetch arguments from manifest using 'variable=$N' (e.g."
                " domain=$1...) Instead, use 'name=$YNH_APP_ARG_NAME'"
            )

    @test(only=["install"])
    def sources_list_tweaking(self) -> TestResult:
        common_sh = self.app / "scripts" / "_common.sh"
        if self.contains("/etc/apt/sources.list") or (
            common_sh.exists()
            and "/etc/apt/sources.list" in common_sh.read_text()
            and "ynh_add_repo" not in common_sh.read_text()
        ):
            yield Error(
                "Manually messing with apt's sources.lists is strongly discouraged "
                "and should be avoided. Please use 'ynh_install_extra_app_dependencies' if you "
                "need to install dependencies from a custom apt repo."
            )

    @test()
    def firewall_consistency(self) -> TestResult:
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
    def exit_ynhdie(self) -> TestResult:

        if self.contains(r"\bexit\b"):
            yield Error(
                "'exit' command shouldn't be used. Please use 'ynh_die' instead."
            )

    @test()
    def old_regenconf(self) -> TestResult:
        if self.contains("yunohost service regen-conf"):
            yield Error(
                "'yunohost service regen-conf' has been replaced by 'yunohost tools regen-conf'."
            )

    @test()
    def ssowatconf_or_nginx_reload(self) -> TestResult:
        # Dirty hack to check only the 10 last lines for ssowatconf
        # (the "bad" practice being using this at the very end of the script, but some apps legitimately need this in the middle of the script)
        oldlines = list(self.lines)
        self.lines = self.lines[-10:]
        if self.contains("yunohost app ssowatconf"):
            yield Warning(
                "You probably don't need to run 'yunohost app ssowatconf' in the app self. It's supposed to be ran automatically after the script."
            )

        if self.name not in ["change_url", "restore"]:
            if self.contains("ynh_systemd_action --service_name=nginx --action=reload"):
                yield Warning(
                    "You should not need to reload nginx at the end of the script ... it's already taken care of by ynh_add_nginx_config"
                )

        self.lines = oldlines

    @test()
    def sed(self) -> TestResult:
        if self.containsregex(
            r"sed\s+(-i|--in-place)\s+(-r\s+)?s"
        ) or self.containsregex(r"sed\s+s\S*\s+(-i|--in-place)"):
            yield Info(
                "You should avoid using 'sed -i' for substitutions, please use 'ynh_replace_string' or 'ynh_add_config' instead"
            )

    @test()
    def sudo(self) -> TestResult:
        if self.containsregex(
            r"sudo \w"
        ):  # \w is here to not match sudo -u, legit use because ynh_exec_as not official yet...
            yield Warning(
                "You should not need to use 'sudo', the script is being run as root. "
                "(If you need to run a command using a specific user, use 'ynh_exec_as' (or 'sudo -u'))"
            )

    @test()
    def chownroot(self) -> TestResult:

        # Mywebapp has a legit use case for this >_>
        if self.app_id == "my_webapp":
            return

        if self.containsregex(
            r"^\s*chown.* root:?[^$]* .*install_dir"
        ) and not self.contains('chown root:root "$install_dir"'):
            # (Mywebapp has a special case because of SFTP é_è)
            yield Warning(
                "Using 'chown root $install_dir' is usually symptomatic of misconfigured and wide-open 'other' permissions ... Usually ynh_setup_source should now set sane default permissions on $install_dir (if the app requires Yunohost >= 4.2) ... Otherwise, consider using 'chown $app', 'chown nobody' or 'chmod' to limit access to $install_dir ..."
            )

    @test()
    def chmod777(self) -> TestResult:
        if self.containsregex(r"chmod .*777") or self.containsregex(r"chmod .*o\+w"):
            yield Warning(
                "DO NOT use chmod 777 or chmod o+w that gives write permission to every users on the system!!! If you have permission issues, just make sure that the owner and/or group owner is right..."
            )

    @test()
    def random(self) -> TestResult:
        if self.contains("dd if=/dev/urandom") or self.contains("openssl rand"):
            yield Error(
                "Instead of 'dd if=/dev/urandom' or 'openssl rand', you should use 'ynh_string_random'"
            )

    @test(only=["install"])
    def progression(self) -> TestResult:
        if not self.contains("ynh_script_progression"):
            yield Warning(
                "Please add a few messages for the user using 'ynh_script_progression' "
                "to explain what is going on (in friendly, not-too-technical terms) "
                "during the installation. (and ideally in scripts remove, upgrade and restore too)"
            )

    @test(only=["backup"])
    def progression_in_backup(self) -> TestResult:
        if self.contains("ynh_script_progression"):
            yield Warning(
                "We recommend to *not* use 'ynh_script_progression' in backup "
                "scripts because no actual work happens when running the script "
                ": YunoHost only fetches the list of things to backup (apart "
                "from the DB dumps which effectively happens during the script...). "
                "Consider using a simple message like this instead: 'ynh_print_info \"Declaring files to be backed up...\"'"
            )

    @test()
    def progression_time(self) -> TestResult:

        # Usage of ynh_script_progression with --time or --weight=1 all over the place...
        if self.containsregex(r"ynh_script_progression.*--time"):
            yield Info(
                "Using 'ynh_script_progression --time' should only be for calibrating the weight (c.f. '--weight'). It's not meant to be kept for production versions."
            )

    @test(ignore=["_common.sh", "backup"])
    def progression_meaningful_weights(self) -> TestResult:
        def weight(line: list[str]) -> int:
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
    def php_deps(self) -> TestResult:
        if self.containsregex("dependencies.*php-"):
            # (Stupid hack because some apps like roundcube depend on php-pear or php-php-gettext and there's no phpx.y-pear phpx.y-php-gettext>_> ...
            if not self.contains("php-pear") or not self.contains("php-php-gettext"):
                yield Warning(
                    "You should avoid having dependencies like 'php-foobar'. Instead, specify the exact version you want like 'php7.0-foobar'. Otherwise, the *wrong* version of the dependency may be installed if sury is also installed. Note that for Stretch/Buster/Bullseye/... transition, YunoHost will automatically patch your file so there's no need to care about that."
                )

    @test(only=["backup"])
    def systemd_during_backup(self) -> TestResult:
        if self.containsregex("^ynh_systemd_action"):
            yield Warning(
                "Unless you really have a good reason to do so, starting/stopping services during backup has no benefit and leads to unecessary service interruptions when creating backups... As a 'reminder': apart from possibly database dumps (which usually do not require the service to be stopped) or other super-specific action, running the backup script is only a *declaration* of what needs to be backed up. The real copy and archive creation happens *after* the backup script is ran."
            )

    @test()
    def helpers_sourcing_after_official(self) -> TestResult:
        helpers_after_official = subprocess.check_output(
            "head -n 30 '%s' | grep -A 10 '^ *source */usr/share/yunohost/helpers' | grep '^ *source ' | tail -n +2"
            % self.path,
            shell=True,
        ).decode("utf-8")
        helpers_after_official = (
            helpers_after_official.replace("source", "").replace(" ", "").strip()
        )
        if helpers_after_official:
            helpers_after_official_list = helpers_after_official.split("\n")
            yield Warning(
                "Please avoid sourcing additional helpers after the official helpers (in this case file %s)"
                % ", ".join(helpers_after_official_list)
            )

    @test(only=["backup", "restore"])
    def helpers_sourcing_backuprestore(self) -> TestResult:
        if self.contains("source _common.sh") or self.contains("source ./_common.sh"):
            yield Error(
                'In the context of backup and restore scripts, you should load _common.sh with "source ../settings/scripts/_common.sh"'
            )

    @test(only=["_common.sh"])
    def no_progress_in_common(self) -> TestResult:
        if self.contains("ynh_script_progression"):
            yield Warning(
                "You should not use `ynh_script_progression` in _common.sh because it will produce warnings when trying to install the application."
            )

    @test(only=["remove"])
    def no_log_remove(self) -> TestResult:
        if self.containsregex(r"(ynh_secure_remove|ynh_safe_rm|rm).*(\/var\/log\/)"):
            yield Warning(
                "Do not delete logs on app removal, else they will be erased if the app upgrade fails. This is handled by the core."
            )
