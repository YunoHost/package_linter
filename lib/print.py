#!/usr/bin/env python3

from typing import Any

output = "plain"


def _print(*args: Any, **kwargs: Any) -> None:
    if not is_json_output():
        print(*args, **kwargs)


def set_output_json() -> None:
    global output
    output = "json"


def is_json_output() -> bool:
    return output == "json"
