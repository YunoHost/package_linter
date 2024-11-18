#!/usr/bin/env python3

import os
import time
import urllib.request
from typing import Any, Callable, Generator, TypeVar

import jsonschema

from lib.print import _print

# ############################################################################
#   Utilities
# ############################################################################


class c:
    HEADER = "\033[94m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    MAYBE_FAIL = "\033[96m"
    FAIL = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class TestReport:
    style: str
    test_name: str

    def __init__(self, message: str) -> None:
        self.message = message

    def display(self, prefix: str = "") -> None:
        _print(prefix + self.style % self.message)


class Warning(TestReport):
    style = c.WARNING + " ! %s " + c.END


class Error(TestReport):
    style = c.FAIL + " ✘ %s" + c.END


class Info(TestReport):
    style = " - %s" + c.END


class Success(TestReport):
    style = c.OKGREEN + " ☺  %s ♥" + c.END


class Critical(TestReport):
    style = c.FAIL + " ✘✘✘ %s" + c.END


def report_warning_not_reliable(message: str) -> None:
    _print(c.MAYBE_FAIL + "?", message, c.END)


def print_happy(message: str) -> None:
    _print(c.OKGREEN + " ☺ ", message, "♥")


def urlopen(url: str) -> tuple[int, str]:
    try:
        conn = urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        return e.code, ""
    except urllib.error.URLError as e:
        _print("Could not fetch %s : %s" % (url, e))
        return 0, ""
    return 200, conn.read().decode("UTF8")


def file_exists(file_path: str) -> bool:
    return os.path.isfile(file_path) and os.stat(file_path).st_size > 0


def cache_file(cachefile: str, ttl_s: int) -> Callable[[Callable[..., str]], Callable[..., str]]:
    def cache_is_fresh() -> bool:
        return (
            os.path.exists(cachefile)
            and time.time() - os.path.getmtime(cachefile) < ttl_s
        )

    def decorator(function: Callable[..., str]) -> Callable[..., str]:
        def wrapper(*args: Any, **kwargs: Any) -> str:
            if not cache_is_fresh():
                with open(cachefile, "w+") as outfile:
                    outfile.write(function(*args, **kwargs))
            return open(cachefile).read()

        return wrapper

    return decorator


@cache_file(".spdx_licenses", 3600)
def spdx_licenses() -> str:
    return urlopen("https://spdx.org/licenses/")[1]


@cache_file(".manifest.v2.schema.json", 3600)
def manifest_v2_schema() -> str:
    url = "https://raw.githubusercontent.com/YunoHost/apps/master/schemas/manifest.v2.schema.json"
    return urlopen(url)[1]


@cache_file(".tests.v1.schema.json", 3600)
def tests_v1_schema() -> str:
    url = "https://raw.githubusercontent.com/YunoHost/apps/master/schemas/tests.v1.schema.json"
    return urlopen(url)[1]


@cache_file(".config_panel.v1.schema.json", 3600)
def config_panel_v1_schema() -> str:
    url = "https://raw.githubusercontent.com/YunoHost/apps/master/schemas/config_panel.v1.schema.json"
    return urlopen(url)[1]


def validate_schema(name: str, schema: dict[str, Any], data: dict[str, Any]) -> Generator[Info, None, None]:
    v = jsonschema.Draft7Validator(schema)

    for error in v.iter_errors(data):
        try:
            error_path = " > ".join(error.path)
        except TypeError:
            error_path = str(error.path)

        yield Info(
            f"Error validating {name} using schema: in key {error_path}\n       {error.message}"
        )


TestResult = Generator[TestReport, None, None]
TestFn = Callable[[Any], TestResult]

tests: dict[str, list[tuple[TestFn, Any]]] = {}
tests_reports: dict[str, list[Any]] = {
    "success": [],
    "info": [],
    "warning": [],
    "error": [],
    "critical": [],
}



def test(**kwargs: Any) -> Callable[[TestFn], TestFn]:
    def decorator(f: TestFn) -> TestFn:
        clsname = f.__qualname__.split(".")[0]
        if clsname not in tests:
            tests[clsname] = []
        tests[clsname].append((f, kwargs))
        return f

    return decorator


class TestSuite():
    name: str
    test_suite_name: str

    def run_tests(self) -> None:

        reports = []

        for test, options in tests[self.__class__.__name__]:
            if "only" in options and self.name not in options["only"]:
                continue
            if "ignore" in options and self.name in options["ignore"]:
                continue

            this_test_reports = list(test(self))
            for report in this_test_reports:
                report.test_name = test.__qualname__

            reports += this_test_reports

        # Display part

        def report_type(report: TestReport) -> str:
            return report.__class__.__name__.lower()

        if any(report_type(r) in ["warning", "error", "critical"] for r in reports):
            prefix = c.WARNING + "! "
        elif any(report_type(r) in ["info"] for r in reports):
            prefix = "ⓘ "
        else:
            prefix = c.OKGREEN + "✔ "

        _print(" " + c.BOLD + prefix + c.OKBLUE + self.test_suite_name + c.END)

        if len(reports):
            _print("")

        for report in reports:
            report.display(prefix="   ")

        if len(reports):
            _print("")

        for report in reports:
            tests_reports[report_type(report)].append((report.test_name, report))

    def run_single_test(self, test: TestFn) -> None:

        reports = list(test(self))

        def report_type(report: TestReport) -> str:
            return report.__class__.__name__.lower()

        for report in reports:
            report.display()
            test_name = test.__qualname__
            tests_reports[report_type(report)].append((test_name, report))
