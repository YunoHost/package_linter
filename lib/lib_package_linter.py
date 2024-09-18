#!/usr/bin/env python3

import os
import time
import urllib
import jsonschema

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
    def __init__(self, message):
        self.message = message

    def display(self, prefix=""):
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


output = "plain"


def _print(*args, **kwargs):
    if output == "plain":
        print(*args, **kwargs)


def set_output_json():
    global output
    output = "json"


def report_warning_not_reliable(str):
    _print(c.MAYBE_FAIL + "?", str, c.END)


def print_happy(str):
    _print(c.OKGREEN + " ☺ ", str, "♥")


def urlopen(url):
    try:
        conn = urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        return {"content": "", "code": e.code}
    except urllib.error.URLError as e:
        _print("Could not fetch %s : %s" % (url, e))
        return {"content": "", "code": 0}
    return {"content": conn.read().decode("UTF8"), "code": 200}


def file_exists(file_path):
    return os.path.isfile(file_path) and os.stat(file_path).st_size > 0


def cache_file(cachefile: str, ttl_s: int):
    def cache_is_fresh():
        return (
            os.path.exists(cachefile)
            and time.time() - os.path.getmtime(cachefile) < ttl_s
        )

    def decorator(function):
        def wrapper(*args, **kwargs):
            if not cache_is_fresh():
                with open(cachefile, "w+") as outfile:
                    outfile.write(function(*args, **kwargs))
            return open(cachefile).read()

        return wrapper

    return decorator


@cache_file(".spdx_licenses", 3600)
def spdx_licenses():
    return urlopen("https://spdx.org/licenses/")["content"]


@cache_file(".manifest.v2.schema.json", 3600)
def manifest_v2_schema():
    return urlopen(
        "https://raw.githubusercontent.com/YunoHost/apps/master/schemas/manifest.v2.schema.json"
    )["content"]


@cache_file(".tests.v1.schema.json", 3600)
def tests_v1_schema():
    return urlopen(
        "https://raw.githubusercontent.com/YunoHost/apps/master/schemas/tests.v1.schema.json"
    )["content"]


@cache_file(".config_panel.v1.schema.json", 3600)
def config_panel_v1_schema():
    return urlopen(
        "https://raw.githubusercontent.com/YunoHost/apps/master/schemas/config_panel.v1.schema.json"
    )["content"]


def validate_schema(name: str, schema, data):
    v = jsonschema.Draft7Validator(schema)

    for error in v.iter_errors(data):
        try:
            error_path = " > ".join(error.path)
        except:
            error_path = str(error.path)

        yield Info(
            f"Error validating {name} using schema: in key {error_path}\n       {error.message}"
        )


tests = {}
tests_reports = {
    "success": [],
    "info": [],
    "warning": [],
    "error": [],
    "critical": [],
}


def test(**kwargs):
    def decorator(f):
        clsname = f.__qualname__.split(".")[0]
        if clsname not in tests:
            tests[clsname] = []
        tests[clsname].append((f, kwargs))
        return f

    return decorator


class TestSuite:
    def run_tests(self):

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

        def report_type(report):
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

    def run_single_test(self, test):

        reports = list(test(self))

        def report_type(report):
            return report.__class__.__name__.lower()

        for report in reports:
            report.display()
            test_name = test.__qualname__
            tests_reports[report_type(report)].append((test_name, report))
