#!/usr/bin/env python3

import datetime
import json
import os
import subprocess
import time
import tomllib
from collections.abc import Generator
from types import ModuleType

from lib.lib_package_linter import (
    APPS_CACHE,
    PACKAGE_LINTER_DIR,
    CatalogAppDescr,
    ReportCritical,
    ReportError,
    ReportInfo,
    ReportSuccess,
    ReportWarning,
    TestResult,
    TestSuite,
    get_app_list,
    test,
    urlopen,
)
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

        self.app_list = get_app_list()

        invalid_app = CatalogAppDescr(url="invalid", state="notworking")
        self.catalog_infos = self.app_list.get(app_id, invalid_app)

    def _fetch_app_repo(self) -> None:
        flagfile = PACKAGE_LINTER_DIR / ".apps_git_clone_cache"
        if (
            APPS_CACHE.exists()
            and flagfile.exists()
            and time.time() - flagfile.stat().st_mtime < 3600
        ):
            return

        if not APPS_CACHE.exists():
            subprocess.check_call(
                [
                    "git",
                    "clone",
                    "https://github.com/YunoHost/apps",
                    APPS_CACHE,
                    "--quiet",
                ]
            )
        else:
            subprocess.check_call(["git", "-C", APPS_CACHE, "fetch", "--quiet"])
            subprocess.check_call(
                ["git", "-C", APPS_CACHE, "reset", "origin/main", "--hard", "--quiet"]
            )

        flagfile.touch()

    @test()
    def is_in_catalog(self) -> TestResult:
        if self.catalog_infos["url"] == "invalid":
            yield ReportCritical("This app is not in YunoHost's application catalog")

    @test()
    def revision_is_HEAD(self) -> TestResult:  # noqa: N802
        if self.catalog_infos.get("revision", "HEAD") != "HEAD":
            yield ReportError(
                "You should make sure that the revision used in YunoHost's apps catalog is HEAD..."
            )

    @test()
    def state_is_working(self) -> TestResult:
        if self.catalog_infos.get("state", "working") != "working":
            yield ReportError(
                "The application is not flagged as working in YunoHost's apps catalog"
            )

    @test()
    def has_category(self) -> TestResult:
        if not self.catalog_infos.get("category"):
            yield ReportWarning(
                "The application has no associated category in YunoHost's apps catalog"
            )

    @test()
    def is_in_github_org(self) -> TestResult:
        repo_org = f"https://github.com/YunoHost-Apps/{self.app_id}_ynh"
        repo_brique = f"https://github.com/labriqueinternet/{self.app_id}_ynh"

        repo_url = self.catalog_infos["url"]
        if repo_url != "invalid":
            if repo_url.lower() not in [repo_org.lower(), repo_brique.lower()]:
                if repo_url.lower().startswith("https://github.com/YunoHost-Apps/"):
                    yield ReportWarning(f"The URL for this app in the catalog should be {repo_org}")
                else:
                    yield ReportInfo(
                        "Consider adding your app to the YunoHost-Apps organization to allow "
                        "the community to contribute more easily"
                    )

        else:

            def is_in_github_org() -> bool:
                return urlopen(repo_org)[0] != 404

            def is_in_brique_org() -> bool:
                return urlopen(repo_brique)[0] != 404

            if not is_in_github_org() and not is_in_brique_org():
                yield ReportInfo(
                    "Consider adding your app to the YunoHost-Apps organization to allow "
                    "the community to contribute more easily"
                )

    @test()
    def is_long_term_good_quality(self) -> TestResult:
        #
        # This analyzes the (git) history of apps.json in the past year and
        # compute a score according to the time when the app was
        # known + flagged working + level >= 5
        #

        def git(cmd: list[str]) -> str:
            return subprocess.check_output(["git", "-C", APPS_CACHE, *cmd]).decode("utf-8").strip()

        def _time_points_until_today() -> Generator[datetime.datetime, None, None]:

            # Prior to April 4th, 2019, we still had official.json and community.json
            # Nowadays we only have apps.json
            year = 2019
            month = 6
            day = 1
            today = datetime.datetime.now(tz=datetime.UTC)
            date = datetime.datetime(year, month, day, tzinfo=datetime.UTC)

            while date < today:
                yield date

                day += 14
                if day > 15:
                    day = 1
                    month += 1

                if month > 12:
                    month = 1
                    year += 1

                date = datetime.datetime(year, month, day, tzinfo=datetime.UTC)

        def get_history(
            count: int,
        ) -> Generator[tuple[datetime.datetime, CatalogAppDescr | None], None, None]:

            for timepoint in list(_time_points_until_today())[(-1 * count) :]:
                loader: ModuleType

                # Fetch apps.json content at this date
                time_str = timepoint.strftime("%b %d %Y")
                commit = git(
                    [
                        "rev-list",
                        "-1",
                        f"--before='{time_str}'",
                        "main",
                    ]
                )
                if (
                    os.system(f"git -C {APPS_CACHE}  cat-file -e {commit}:apps.json 2>/dev/null")
                    == 0
                ):
                    raw_catalog_at_this_date = git(["show", f"{commit}:apps.json"])
                    loader = json

                elif os.system(f"git -C {APPS_CACHE}  cat-file -e {commit}:apps.toml") == 0:
                    raw_catalog_at_this_date = git(["show", f"{commit}:apps.toml"])
                    loader = tomllib
                else:
                    msg = "No apps.json/toml at this point in history?"
                    raise RuntimeError(msg)

                try:
                    catalog_at_this_date: dict[str, CatalogAppDescr] = loader.loads(
                        raw_catalog_at_this_date
                    )
                # This can happen in stupid cases where there was a temporary syntax error
                # in the json..
                except json.decoder.JSONDecodeError:
                    _print(
                        "Failed to parse apps.json/toml history for at commit "
                        f"{commit} / {timepoint}... ignoring "
                    )
                    continue
                yield (timepoint, catalog_at_this_date.get(self.app_id))

        # We'll check the history for last 12 months (*2 points per month)
        count = 12 * 2
        history = list(get_history(count))

        # Must have been
        #   known
        # + flagged as working
        # + level > 5
        # for the past 6 months
        def good_quality(infos: CatalogAppDescr | None) -> bool:
            return (
                bool(infos)
                and isinstance(infos, dict)
                and infos.get("state") == "working"
                and infos.get("level", -1) >= 5
            )

        score = sum([good_quality(infos) for d, infos in history])
        rel_score = int(100 * score / count)
        if rel_score > 80:
            yield ReportSuccess("The app is long-term good quality in the catalog!")
