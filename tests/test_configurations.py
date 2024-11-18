#!/usr/bin/env python3

import json
import os
import re
from pathlib import Path
import subprocess
import tomllib
from typing import Any, Generator

from lib.lib_package_linter import (Error, Info, TestReport, TestResult,
                                    TestSuite, Warning, not_empty, test,
                                    tests_v1_schema, validate_schema)
from lib.print import _print


class Configurations(TestSuite):
    def __init__(self, app) -> None:

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
    def tests_toml(self) -> TestResult:
        tests_toml_file = self.app.path / "tests.toml"
        if not not_empty(tests_toml_file):
            yield Error(
                "The 'check_process' file that interfaces with the app CI has now been replaced with 'tests.toml' format and is now mandatory for apps v2."
            )
        else:
            yield from validate_schema(
                "tests.toml",
                json.loads(tests_v1_schema()),
                tomllib.load(tests_toml_file.open("rb")),
            )

    @test()
    def encourage_extra_php_conf(self) -> TestResult:
        php_conf = self.app.path / "conf" / "php-fpm.conf"
        if not_empty(php_conf):
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
    def misc_source_management(self) -> TestResult:
        source_dir = self.app.path / "sources"

        if source_dir.exists() and len(list(elt for elt in source_dir.iterdir() if elt.is_file())) > 5:
            yield Error(
                "Upstream app sources shouldn't be stored in this 'sources' folder of this git repository as a copy/paste\n"
                "During installation, the package should download sources from upstream via 'ynh_setup_source'.\n"
                "See the helper documentation. "
                "Original discussion happened here: "
                "https://github.com/YunoHost/issues/issues/201#issuecomment-391549262"
            )

    @test()
    def systemd_config_specific_user(self) -> TestResult:
        conf_dir: Path = self.app.path / "conf"
        if not conf_dir.exists():
            return

        for file in conf_dir.iterdir():
            # Ignore subdirs or filename not containing nginx in the name
            if not file.name.endswith(".service"):
                continue

            # Some apps only provide an override conf file, which is different
            # from the full/base service config (c.f. ffsync)
            if "override" in file.name:
                continue

            try:
                content = file.read_text()
            except UnicodeDecodeError:
                yield Info("%s does not look like a text file." % file.name)
                continue
            except Exception as e:
                yield Warning("Can't open/read %s : %s" % (file.name, e))
                continue

            if "[Unit]" not in content:
                continue

            Level: type[TestReport]
            if re.findall(r"^ *Type=oneshot", content, flags=re.MULTILINE):
                Level = Info
            else:
                Level = Warning

            matches = re.findall(r"^ *(User)=(\S+)", content, flags=re.MULTILINE)
            if not any(match[0] == "User" for match in matches):
                yield Level(
                    "You should specify a 'User=' directive in the systemd config !"
                )
                continue

            if any(match[1] in ["root", "www-data"] for match in matches):
                yield Level(
                    "DO NOT run the app's systemd service as root or www-data! Use a dedicated system user for this app! If your app requires administrator priviledges, you should consider adding the user to the sudoers (and restrict the commands it can use!)"
                )

    @test()
    def systemd_config_harden_security(self) -> TestResult:
        conf_dir: Path = self.app.path / "conf"
        if not conf_dir.exists():
            return

        for file in conf_dir.iterdir():
            # Ignore subdirs or filename not containing nginx in the name
            if not file.name.endswith(".service"):
                continue

            if (
                os.system(f"grep -q '^ *CapabilityBoundingSet=' '{file}'") != 0
                or os.system(f"grep -q '^ *Protect.*=' '{file}'") != 0
                or os.system(f"grep -q '^ *SystemCallFilter=' '{file}'") != 0
                or os.system(f"grep -q '^ *PrivateTmp=' '{file}'") != 0
            ):
                yield Info(
                    f"You are encouraged to harden the security of the systemd configuration {file.name}. You can have a look at https://github.com/YunoHost/example_ynh/blob/master/conf/systemd.service#L14-L46 for a baseline."
                )

    @test()
    def php_config_specific_user(self) -> TestResult:
        conf_dir: Path = self.app.path / "conf"
        if not conf_dir.exists():
            return

        for file in conf_dir.iterdir():
            # Ignore subdirs or filename not containing nginx in the name
            if not file.name.startswith("php") or not file.name.endswith(".conf"):
                continue

            try:
                content = file.read_text()
            except UnicodeDecodeError:
                yield Info("%s does not look like a text file." % file.name)
                continue
            except Exception as e:
                yield Warning("Can't open/read %s : %s" % (file.name, e))
                continue

            matches = re.findall(
                r"^ *(user|group) = (\S+)", content, flags=re.MULTILINE
            )
            if not any(match[0] == "user" for match in matches):
                yield Error(
                    "You should at least specify a 'user =' directive in your PHP conf file"
                )
                continue

            if any(
                match[1] == "root" or match == ("user", "www-data") for match in matches
            ):
                yield Error(
                    "DO NOT run the app PHP worker as root or www-data! Use a dedicated system user for this app!"
                )

    @test()
    def nginx_http_host(self) -> TestResult:
        nginx_conf: Path = self.app.path / "conf" / "nginx.conf"
        if not nginx_conf.exists():
            return

        content = nginx_conf.read_text()
        if "$http_host" in content:
            yield Info(
                "In nginx.conf : please don't use $http_host but $host instead. C.f. https://github.com/yandex/gixy/blob/master/docs/en/plugins/hostspoofing.md"
            )

    @test()
    def nginx_https_redirect(self) -> TestResult:
        conf_dir: Path = self.app.path / "conf"
        if not conf_dir.exists():
            return

        for file in conf_dir.iterdir():
            # Ignore subdirs or filename not containing nginx in the name
            if not file.is_file() or "nginx" not in file.name:
                continue

            content = file.read_text()
            if "if ($scheme = http)" in content and "rewrite ^ https" in content:
                yield Error(
                    "Since Yunohost 4.3, the http->https redirect is handled by the core, "
                    "therefore having an if ($scheme = http) { rewrite ^ https://... } block "
                    "in the nginx config file is deprecated. (This helps with supporting Yunohost-behind-reverse-proxy use case)"
                )

    @test()
    def misc_nginx_add_header(self) -> TestResult:
        #
        # Analyze nginx conf
        # - Deprecated usage of 'add_header' in nginx conf
        # - Spot path traversal issue vulnerability
        #
        conf_dir: Path = self.app.path / "conf"
        if not conf_dir.exists():
            return

        for file in conf_dir.iterdir():
            # Ignore subdirs or filename not containing nginx in the name
            if not file.is_file() or "nginx" not in file.name:
                continue

            content = file.read_text()
            if "location" in content and "add_header" in content:
                yield Error(
                    "Do not use 'add_header' in the NGINX conf. Use 'more_set_headers' instead. "
                    "(See https://www.peterbe.com/plog/be-very-careful-with-your-add_header-in-nginx "
                    "and https://github.com/openresty/headers-more-nginx-module#more_set_headers )"
                )

    @test()
    def misc_nginx_more_set_headers(self) -> TestResult:
        conf_dir: Path = self.app.path / "conf"
        if not conf_dir.exists():
            return

        for file in conf_dir.iterdir():
            # Ignore subdirs or filename not containing nginx in the name
            if not file.is_file() or "nginx" not in file.name:
                continue

            content = file.read_text()

            if "location" in content and "more_set_headers" in content:
                lines = content.split("\n")
                more_set_headers_lines = [
                    zzz for zzz in lines if "more_set_headers" in zzz
                ]

                def right_syntax(line: str) -> re.Match[str] | None:
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
    def misc_nginx_check_regex_in_location(self) -> TestResult:
        conf_dir: Path = self.app.path / "conf"
        if not conf_dir.exists():
            return

        for file in conf_dir.iterdir():
            # Ignore subdirs or filename not containing nginx in the name
            if not file.is_file() or "nginx" not in file.name:
                continue

            cmd = 'grep -q -IhEro "location ~ __PATH__" %s' % file

            if os.system(cmd) == 0:
                yield Warning(
                    "When using regexp in the nginx location field (location ~ __PATH__), start the path with ^ (location ~ ^__PATH__)."
                )

    @test()
    def misc_nginx_path_traversal(self) -> TestResult:
        conf_dir: Path = self.app.path / "conf"
        if not conf_dir.exists():
            return

        for file in conf_dir.iterdir():
            # Ignore subdirs or filename not containing nginx in the name
            if not file.is_file() or "nginx" not in file.name:
                continue

            #
            # Path traversal issues
            #
            def find_location_with_alias(locationblock: Any) -> Generator[tuple[str, str], None, None]:

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

            def find_path_traversal_issue(nginxconf: list[Any]) -> Generator[str, None, None]:

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
                        # with / if __INSTALL_DIR__ ain't used...  that probably
                        # means that the app is not using the standard nginx
                        # helper, and therefore it is likely to be replaced by
                        # something ending with / ...
                        if not location.strip("'").endswith("/") and (
                            alias_path.endswith("/")
                            or "__INSTALL_DIR__" not in alias_path
                        ):
                            yield location

            do_path_traversal_check = False
            try:
                import pyparsing
                import six

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
                    nginxconf: list[Any] = nginxparser.load(file.open())
                except Exception as e:
                    _print(f"Could not parse NGINX conf...: {e}")
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
    def bind_public_ip(self) -> TestResult:
        conf_dir: Path = self.app.path / "conf"
        if not conf_dir.exists():
            return

        for file in conf_dir.rglob("*"):
            if not file.is_file():
                continue

            try:
                content = file.read_text()
            except UnicodeDecodeError:
                yield Info("%s does not look like a text file." % file.name)
                continue
            except Exception as e:
                yield Warning("Can't open/read %s: %s" % (file, e))
                continue

            for number, line in enumerate(content.split("\n"), 1):
                comment = ("#", "//", ";", "/*", "*")
                if (
                    "0.0.0.0" in line or "::" in line
                ) and not line.strip().startswith(comment):
                    for ip in re.split(r"[ \t,='\"(){}\[\]]", line):
                        if ip == "::" or ip.startswith("0.0.0.0"):
                            yield Info(
                                f"{file.relative_to(self.app.path)}:{number}: "
                                "Binding to '0.0.0.0' or '::' can result in a security issue "
                                "as the reverse proxy and the SSO can be bypassed by knowing "
                                "a public IP (typically an IPv6) and the app port. "
                                "Please be sure that this behavior is intentional. "
                                "Maybe use '127.0.0.1' or '::1' instead."
                            )
