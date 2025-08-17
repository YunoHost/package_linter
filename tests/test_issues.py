#!/usr/bin/env python3
import json

from lib.lib_package_linter import (
    Critical,
    Info,
    TestReport,
    TestResult,
    TestSuite,
    Warning,
    not_empty,
    test,
    urlopen,
    get_app_list,
    PACKAGE_LINTER_DIR,
    APPS_CACHE,
    report_warning_not_reliable
)


class Issues(TestSuite):
    def __init__(self, app) -> None:
        self.app = app
        self.test_suite_name = "Issues"

        self.app_list = get_app_list()
        repo_url = self.app_list[app]["url"]
        if "github.com" not in repo_url:
            report_warning_not_reliable("Can't check if there are any blocking issues pending, can only do this for apps hosted on github for now.")
            return
        repo = repo_url.replace("https://github.com/", "")
        issues_uri = f"https://api.github.com/repos/{repo}/issues?state=open"

        code, issues_result = urlopen(issues_uri)
        if 200 <= code < 300:
            self.issues:list[dict] = json.loads(issues_result)


    @test()
    def broken_issue(self) -> TestResult:
        issues = [f"#{issue['number']} : {issue['title']}"
            for issue in self.issues
            if "broken" in [label["name"] for label in issue.get('labels', [])]
        ]

        if issues:
            yield Critical("There are critical pending issues on the git repo to be solved :\n      - "+"\n      - ".join(issues)+"\n      The app will be considered BROKEN (level 0) as long as it's not solved.")

    @test()
    def low_quality_issue(self) -> TestResult:
        issues = [f"#{issue['number']} : {issue['title']}"
            for issue in self.issues
            if "low quality" in [label["name"] for label in issue.get('labels', [])]
        ]

        if issues:
            yield Warning("There are important pending issues on the git repo to be solved :\n      - "+"\n      - ".join(issues)+"\n      The app will be considered low quality as long as it's not solved.")

    @test()
    def small_bug(self) -> TestResult:
        ignored_labels = {"wontfix", "invalid", "broken", "low quality"}
        nb_bugs = 0
        for issue in self.issues:
            labels = [label["name"] for label in issue.get('labels', [])]
            if "bug" in labels and ignored_labels.isdisjoint(set(labels)):
                nb_bugs += 1

        if nb_bugs:
            yield Info(f"{nb_bugs} small bugs are known in this package, it could be useful to try to fix them or close it if not relevant anymore.")

