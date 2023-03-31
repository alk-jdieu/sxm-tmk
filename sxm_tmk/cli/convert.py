import pathlib

from sxm_tmk.converters.pipenv import FromPipenv
from sxm_tmk.core.custom_types import TMKLockFileNotFound
from sxm_tmk.core.out.terminal import Terminal


def setup(subparser):
    convert_parser = subparser.add_parser(name="convert")
    convert_parser.add_argument(
        "path",
        type=pathlib.Path,
        help="Path to the project you wish to convert.",
    )
    convert_parser.add_argument(
        "--jobs",
        action="store",
        default=5,
        type=int,
        help="Number of jobs to use when querying conda indexes. You should not go beyond 10 jobs.",
    )
    convert_parser.add_argument(
        "--no-dev",
        action="store_true",
        help="Do not consider development dependencies during migration."
        "Default behaviour is to take them into account.",
    )
    convert_parser.set_defaults(func=main)


def main(options):
    Terminal("rich")
    try:
        processor = FromPipenv(options.path.resolve(), options.jobs, not options.no_dev)
        return processor.convert()
    except TMKLockFileNotFound as e:
        Terminal().error(str(e))
        return 1
