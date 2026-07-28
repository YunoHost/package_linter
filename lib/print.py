#!/usr/bin/env python3

from functools import wraps

output = "plain"


@wraps(print)
def _print(*values: object, **kwargs) -> None:  # noqa: ANN003
    if not is_json_output():
        print(*values, **kwargs)


def set_output_json() -> None:
    global output  # noqa: PLW0603
    output = "json"


def is_json_output() -> bool:
    return output == "json"
