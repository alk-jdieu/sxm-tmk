import sys
from argparse import ArgumentParser

from sxm_tmk import __version__ as version
from sxm_tmk.cli.clean import setup as setup_clean
from sxm_tmk.cli.convert import setup as setup_convert
from sxm_tmk.cli.create import setup as setup_create


def main(args=None):
    parser = ArgumentParser("sxm-tmk", description="Tool for managing environment using conda")
    parser.add_argument("--version", action="version", version=f"%(prog)s, version {version}")
    parsers = parser.add_subparsers()
    setup_convert(parsers)
    setup_clean(parsers)
    setup_create(parsers)

    options = parser.parse_args(args)
    if hasattr(options, "func"):
        rc = options.func(options)
        sys.exit(rc)
    sys.exit(0)
