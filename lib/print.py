output = "plain"


def _print(*args, **kwargs):
    if not is_json_output():
        print(*args, **kwargs)


def set_output_json():
    global output
    print("setting")
    output = "json"


def is_json_output() -> bool:
    return output == "json"
