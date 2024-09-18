#!/usr/bin/env python3
# -*- coding: utf8 -*-

import argparse
from pathlib import Path

from lib.lib_package_linter import _print, c, set_output_json

from tests.test_app import App


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("app_path", type=Path, help="The path to the app to lint")
    parser.add_argument(
        "--json", action="store_true", help="Output json instead of plain text"
    )
    args = parser.parse_args()

    if args.json:
        set_output_json()

    _print(
        """
    [{blue}{bold}YunoHost App Package Linter{end}]

 App packaging documentation - https://yunohost.org/en/contribute/packaging_apps
 App package example         - https://github.com/YunoHost/example_ynh
 Official helpers            - https://yunohost.org/en/contribute/packaging_apps/helpers
 Experimental helpers        - https://github.com/YunoHost-Apps/Experimental_helpers

 If you believe this linter returns false negative (warnings / errors which shouldn't happen),
 please report them on https://github.com/YunoHost/package_linter/issues
    """.format(
            blue=c.OKBLUE, bold=c.BOLD, end=c.END
        )
    )

    app = App(str(args.app_path))
    app.analyze()


if __name__ == "__main__":
    main()
