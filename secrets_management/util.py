from typing import Union


def bool_converter(value: Union[str, int, bool]) -> bool:
    """Helper function to convert some common "yes"/"no" command line inputs into a boolean.
    This originally extended the (now deprecated) distutils's strtobool function.
    """
    if value in (True, 1) or str(value).lower() in ("y", "yes", "t", "true", "1", "on"):
        return True

    if value in (False, 0) or str(value).lower() in ("n", "no", "f", "false", "0", "off"):
        return False

    raise ValueError(f"Don't know how to convert: {value}")
