#!/usr/bin/env python3

import copy
import json
from pathlib import Path
import re
import sys
import tomllib
from typing import Any, Callable

from lib.lib_package_linter import (
    Critical,
    Error,
    Info,
    TestResult,
    TestSuite,
    Warning,
    c,
    manifest_v2_schema,
    spdx_licenses,
    test,
    validate_schema,
)

# Only packaging v2 is supported on the linter now ... But someday™ according The Prophecy™, packaging v3 will be a thing
app_packaging_format = 2


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
    def __init__(self, path: Path) -> None:

        self.path = path
        self.test_suite_name = "manifest"

        manifest_path = path / "manifest.toml"

        # Taken from https://stackoverflow.com/a/49518779
        def check_for_duplicate_keys(
            ordered_pairs: list[tuple[str, Any]],
        ) -> dict[str, Any]:
            dict_out = {}
            for key, val in ordered_pairs:
                if key in dict_out:
                    raise Exception("Duplicated key '%s' in %s" % (key, ordered_pairs))
                else:
                    dict_out[key] = val
            return dict_out

        self.raw_manifest = manifest_path.read_text()
        try:
            self.manifest = tomllib.loads(self.raw_manifest)
        except Exception as e:
            print(
                f"{c.FAIL}✘ Looks like there's a syntax issue in your manifest?\n ---> {e}"
            )
            sys.exit(1)

    @test()
    def mandatory_fields(self) -> TestResult:

        fields = [
            "packaging_format",
            "id",
            "name",
            "description",
            "version",
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

        if "license" not in self.manifest.get("upstream", ""):
            yield Error("The license key in the upstream section is missing")

    @test()
    def maintainer_sensible_values(self) -> TestResult:
        if "maintainers" in self.manifest.keys():
            for value in self.manifest["maintainers"]:
                if not value.strip():
                    yield Error("Please don't put empty string as a maintainer x_x")
                elif "," in value:
                    yield Error(
                        "Please don't use comma in maintainers value, this is supposed to be a list such as ['foo', bar'], not ['foo, bar'] x_x"
                    )

    @test()
    def upstream_fields(self) -> TestResult:
        if "upstream" not in self.manifest.keys():
            yield Warning(
                """READMEs are to be automatically generated using https://github.com/YunoHost/apps_tools/tree/main/readme_generator.
        - You are encouraged to add an 'upstream' section in the manifest, filled with the website, demo, repo, license of the upstream app, as shown here: https://github.com/YunoHost/example_ynh/blob/7b72b7334964b504e8c901637c73ce908204d38b/manifest.json#L11-L18 . (Not all infos are mandatory, you can remove irrelevant entries)"""
            )

    @test()
    def upstream_placeholders(self) -> TestResult:
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
            code = self.manifest["upstream"].get("code")
            if code and (
                code == self.manifest["upstream"].get("userdoc")
                or code == self.manifest["upstream"].get("admindoc")
            ):
                yield Warning(
                    "userdoc or admindoc: A code repository is not a documentation x_x"
                )

    @test()
    def FIXMEs(self) -> TestResult:
        if "FIXME" in self.raw_manifest:
            yield Warning("There are still some FIXMEs remaining in the manifest")

    @test()
    def yunohost_version_requirement_superold(app) -> TestResult:

        yunohost_version_req = (
            app.manifest.get("integration", {}).get("yunohost", "").strip(">= ")
        )
        if yunohost_version_req.startswith("4."):
            yield Critical(
                "Your app only requires yunohost >= 4.x, which tends to indicate that it may not be up to date with recommended packaging practices and helpers."
            )
        elif yunohost_version_req.startswith("11.0"):
            yield Error(
                "Your app only requires yunohost >= 11.0, which tends to indicate that it may not be up to date with recommended packaging practices and helpers."
            )

    @test()
    def basic_fields_format(self) -> TestResult:

        if self.manifest.get("packaging_format") != app_packaging_format:
            yield Error(f"packaging_format should be {app_packaging_format}")
        if not re.match("^[a-z0-9]((_|-)?[a-z0-9])+$", self.manifest.get("id", "")):
            yield Error("The app id is not a valid app id")
        elif self.manifest.get("id", "").endswith("_ynh"):
            yield Warning("The app id is not supposed to end with _ynh :| ...")
        if len(self.manifest["name"]) > 22:
            yield Error("The app name is too long")

        keys: dict[str, tuple[Callable[..., bool | re.Match[str] | None], str]] = {
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
    def license(self) -> TestResult:

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
    def description(self) -> TestResult:

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
    def version_format(self) -> TestResult:
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
    def custom_install_dir(self) -> TestResult:
        custom_install_dir = (
            self.manifest.get("resources", {}).get("install_dir", {}).get("dir")
        )
        if not custom_install_dir:
            return

        if custom_install_dir.startswith("/opt/yunohost"):
            yield Warning(
                "Installing apps in /opt/yunohost is deprecated ... YunoHost is about standardization, and the standard is to install in /var/www/__APP__ (yes, even if not a webapp, because whatever). Please stick to the default value. the resource system should automatically move the install dir if needed so you don't really need to think about backward compatibility."
            )

    @test()
    def install_args(self) -> TestResult:

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
            "alert",
            "markdown",
            "file",
            "app",
        )

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
    def obsolete_or_missing_ask_strings(self) -> TestResult:

        ask_string_managed_by_the_core = [
            ("domain", "domain"),
            ("path", "path"),
            ("admin", "user"),
            ("is_public", "boolean"),
            ("password", "password"),
            ("init_main_permission", "group"),
        ]

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
    def old_php_version(self) -> TestResult:

        resources = self.manifest["resources"]

        if "apt" in list(resources.keys()):
            packages = resources["apt"].get("packages", "")
            packages = str(packages) if isinstance(packages, list) else packages
            assert isinstance(packages, str)
            if "php7.4-" in packages:
                yield Error(
                    "The app currently runs on php7.4 which is pretty old (unsupported by the PHP group since January 2023). Ideally, upgrade it to at least php8.2."
                )
            elif "php8.0-" in packages:
                yield Warning(
                    "The app currently runs on php8.0 which is pretty old (unsupported by the PHP group since January 2024). Ideally, upgrade it to at least php8.2."
                )
            elif "php8.1-" in packages:
                yield Warning(
                    "The app currently runs on php8.1 which is deprecated since January 2024. Ideally, upgrade it to at least php8.2."
                )
    
    @test()
    def require_php_fpm(self) -> TestResult:

        resources = self.manifest["resources"]

        found_php = False
        found_fpm = False
        php_version = ""
        rgx = re.compile(r"php(?P<version>[0-9]+\.[0-9]+)")

        if "apt" in list(resources.keys()):
            packages = resources["apt"].get("packages", "")
            packages = packages.split(",") if isinstance(packages, str) else packages
            assert isinstance(packages, list)
            for package in packages:
                match = rgx.match(package.strip())
                if match:
                    found_php = True
                    php_version = match.group(1)
                if rgx.match(package.strip()) and package.strip().endswith("fpm"):
                    found_fpm = True
                    break
                
        if found_php and not found_fpm:
            yield Warning(
                f"The app requires PHP but doesn't seem to install php{php_version}-fpm. It's recommended to use php{php_version}-fpm for safer package resolution."
            )

    @test()
    def resource_consistency(self) -> TestResult:

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
        def manifest_schema(self: "Manifest") -> TestResult:
            yield from validate_schema(
                "manifest", json.loads(manifest_v2_schema()), self.manifest
            )
