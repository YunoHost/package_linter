#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import time
import tomllib
from datetime import datetime
from types import ModuleType
from typing import Any, Generator

from lib.lib_package_linter import (Critical, Error, Info, Success, TestResult,
                                    TestSuite, Warning, test, urlopen)
from lib.print import _print

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
    def __init__(self, app_id: str) -> None:

        self.app_id = app_id
        self.test_suite_name = "Catalog infos"

        self._fetch_app_repo()

        try:
            self.app_list = tomllib.load(open("./.apps/apps.toml", "rb"))
        except Exception:
            _print("Failed to read apps.toml :/")
            sys.exit(-1)

        self.catalog_infos = self.app_list.get(app_id, {})

    def _fetch_app_repo(self) -> None:

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
    def is_in_catalog(self) -> TestResult:

        if not self.catalog_infos:
            yield Critical("This app is not in YunoHost's application catalog")

    @test()
    def revision_is_HEAD(self) -> TestResult:

        if self.catalog_infos and self.catalog_infos.get("revision", "HEAD") != "HEAD":
            yield Error(
                "You should make sure that the revision used in YunoHost's apps catalog is HEAD..."
            )

    @test()
    def state_is_working(self) -> TestResult:

        if (
            self.catalog_infos
            and self.catalog_infos.get("state", "working") != "working"
        ):
            yield Error(
                "The application is not flagged as working in YunoHost's apps catalog"
            )

    @test()
    def has_category(self) -> TestResult:
        if self.catalog_infos and not self.catalog_infos.get("category"):
            yield Warning(
                "The application has no associated category in YunoHost's apps catalog"
            )

    @test()
    def is_in_github_org(self) -> TestResult:

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

            def is_in_github_org() -> bool:
                return urlopen(repo_org)[0] != 404

            def is_in_brique_org() -> bool:
                return urlopen(repo_brique)[0] != 404

            if not is_in_github_org() and not is_in_brique_org():
                yield Info(
                    "Consider adding your app to the YunoHost-Apps organization to allow the community to contribute more easily"
                )

    @test()
    def is_long_term_good_quality(self) -> TestResult:

        #
        # This analyzes the (git) history of apps.json in the past year and
        # compute a score according to the time when the app was
        # known + flagged working + level >= 5
        #

        def git(cmd: list[str]) -> str:
            return (
                subprocess.check_output(["git", "-C", "./.apps"] + cmd)
                .decode("utf-8")
                .strip()
            )

        def _time_points_until_today() -> Generator[datetime, None, None]:

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

        def get_history(N: int) -> Generator[tuple[datetime, dict[str, Any]], None, None]:

            for t in list(_time_points_until_today())[(-1 * N) :]:
                loader: ModuleType

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
                    loader = tomllib
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
        def good_quality(infos: dict[str, Any]) -> bool:
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
