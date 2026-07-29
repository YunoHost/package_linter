#!/usr/bin/env python3

import sys
import time
import tomllib
import urllib.error
import urllib.request
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict, TypeVar

import jsonschema

from lib.print import _print

PACKAGE_LINTER_DIR = Path(__file__).resolve().parent.parent
APPS_CACHE = PACKAGE_LINTER_DIR / ".apps"

# ############################################################################
#   Utilities
# ############################################################################


class Color:
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


class ReportWarning(TestReport):
    style = Color.WARNING + " ! %s " + Color.END


class ReportError(TestReport):
    style = Color.FAIL + " ✘ %s" + Color.END


class ReportInfo(TestReport):
    style = " - %s" + Color.END


class ReportSuccess(TestReport):
    style = Color.OKGREEN + " ☺  %s ♥" + Color.END


class ReportCritical(TestReport):
    style = Color.FAIL + " ✘✘✘ %s" + Color.END


def report_warning_not_reliable(message: str) -> None:
    _print(Color.MAYBE_FAIL + "?", message, Color.END)


def print_happy(message: str) -> None:
    _print(Color.OKGREEN + " ☺ ", message, "♥")


def urlopen(url: str) -> tuple[int, str]:
    try:
        conn = urllib.request.urlopen(url)  # noqa: S310
    except urllib.error.HTTPError as e:
        return e.code, ""
    except urllib.error.URLError as e:
        _print(f"Could not fetch {url} : {e}")
        return 0, ""

    return 200, conn.read().decode("UTF8")


def not_empty(file: Path) -> bool:
    return file.is_file() and file.stat().st_size > 0


def cache_file(cachefile: Path, ttl_s: int) -> Callable[[Callable[..., str]], Callable[..., str]]:
    def cache_is_fresh() -> bool:
        return cachefile.exists() and time.time() - cachefile.stat().st_mtime < ttl_s

    def decorator(function: Callable[..., str]) -> Callable[..., str]:
        def wrapper() -> str:
            if not cache_is_fresh():
                cachefile.write_text(function())
            return cachefile.read_text()

        return wrapper

    return decorator


@cache_file(Path(".spdx_licenses"), 3600)
def spdx_licenses() -> str:
    return urlopen("https://spdx.org/licenses/")[1]


@cache_file(Path(".manifest.v2.schema.json"), 3600)
def manifest_v2_schema() -> str:
    url = "https://raw.githubusercontent.com/YunoHost/apps/main/schemas/manifest.v2.schema.json"
    return urlopen(url)[1]


@cache_file(Path(".tests.v1.schema.json"), 3600)
def tests_v1_schema() -> str:
    url = "https://raw.githubusercontent.com/YunoHost/apps/main/schemas/tests.v1.schema.json"
    return urlopen(url)[1]


class CatalogAppDescr(TypedDict):
    added_date: NotRequired[int]
    branch: NotRequired[str]
    category: NotRequired[str]
    subtags: NotRequired[list[str]]
    level: NotRequired[int]
    potential_alternative_to: NotRequired[list[str]]
    antifeatures: NotRequired[list[str]]
    revision: NotRequired[str]
    deprecated_date: NotRequired[int]
    state: Literal["working", "notworking", "inprogress"]
    url: str


def get_app_list() -> dict[str, CatalogAppDescr]:
    try:
        app_list = tomllib.load((APPS_CACHE / "apps.toml").open("rb"))
    except Exception:
        _print("Failed to read apps.toml :/")
        sys.exit(-1)
    return app_list


@cache_file(Path(".config_panel.v1.schema.json"), 3600)
def config_panel_v1_schema() -> str:
    url = "https://raw.githubusercontent.com/YunoHost/apps/main/schemas/config_panel.v1.schema.json"
    return urlopen(url)[1]


def validate_schema(
    name: str, schema: dict[str, Any], data: dict[str, Any]
) -> Generator[ReportInfo, None, None]:
    v = jsonschema.Draft7Validator(schema)

    for error in v.iter_errors(data):
        try:
            error_path = " > ".join([str(elt) for elt in error.path])
        except TypeError:
            error_path = str(error.path)

        msg = f"Error validating {name} using schema: in key {error_path}\n       {error.message}"
        yield ReportInfo(msg)


TestSuiteSelf = TypeVar("TestSuiteSelf", bound="TestSuite")
TestResult = Generator[TestReport, None, None]
TestFn = Callable[[TestSuiteSelf], TestResult]

tests: dict[str, list[tuple[TestFn, dict[str, list[str] | None]]]] = {}  # type: ignore[type-arg]
tests_reports: dict[str, list[tuple[str, TestReport]]] = {
    "success": [],
    "info": [],
    "warning": [],
    "error": [],
    "critical": [],
}


def test(
    only: list[str] | None = None,  # noqa: PT028
    ignore: list[str] | None = None,  # noqa: PT028
) -> Callable[[TestFn], TestFn]:  # type: ignore[type-arg]
    def decorator(f: TestFn) -> TestFn:  # type: ignore[type-arg]
        clsname = getattr(f, "__qualname__", "unnamed_callable").split(".")[0]
        if clsname not in tests:
            tests[clsname] = []
        tests[clsname].append((f, {"only": only, "ignore": ignore}))
        return f

    return decorator


class TestSuite:
    name: str = ""
    test_suite_name: str

    def run_tests(self) -> None:

        reports: list[TestReport] = []

        for testfn, options in tests[self.__class__.__name__]:
            if self.name and self.name not in (options["only"] or []):
                continue
            if self.name and self.name in (options["ignore"] or []):
                continue

            this_test_reports = list(testfn(self))
            for report in this_test_reports:
                report.test_name = str(getattr(testfn, "__qualname__", "unnamed_test"))

            reports += this_test_reports

        # Display part

        def report_type(report: TestReport) -> str:
            return report.__class__.__name__.lower().removeprefix("report")

        if any(report_type(r) in ["warning", "error", "critical"] for r in reports):
            prefix = Color.WARNING + "! "
        elif any(report_type(r) == "info" for r in reports):
            prefix = "ⓘ "
        else:
            prefix = Color.OKGREEN + "✔ "

        _print(f" {Color.BOLD}{prefix}{Color.OKBLUE}{self.test_suite_name}{Color.END}")

        if len(reports):
            _print("")

        for report in reports:
            report.display(prefix="   ")

        if len(reports):
            _print("")

        for report in reports:
            tests_reports[report_type(report)].append((report.test_name, report))

    def run_single_test(self, test: TestFn) -> None:  # type: ignore[type-arg]

        reports = list(test(self))

        def report_type(report: TestReport) -> str:
            return report.__class__.__name__.lower().removeprefix("report")

        for report in reports:
            report.display()
            test_name = getattr(test, "__qualname__", "unnamed_test")
            tests_reports[report_type(report)].append((test_name, report))
