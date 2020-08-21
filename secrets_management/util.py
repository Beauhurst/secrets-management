from distutils.util import strtobool


def bool_converter(val):
    """
    Convert string representations of True/False to real booleans

    See `distutils.util.strtobool` for full list of supported inputs
    """
    return bool(strtobool(str(val)))
