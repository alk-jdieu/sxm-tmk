import pathlib

from sxm_tmk.converters.pipenv import FromPipenv
from sxm_tmk.core.out.terminal import Terminal


def setup(subparser):
    convert_parser = subparser.add_parser(name="convert")
    convert_parser.add_argument("path", type=pathlib.Path, help="Path to the project to convert.")
    convert_parser.add_argument(
        "--jobs",
        action="store",
        default=5,
        type=int,
        help="Number of jobs to use when querying conda. You should not go beyond 10 jobs.",
    )
    convert_parser.add_argument(
        "--dev",
        action="store_true",
        help="Consider also development dependencies for migration."
        "Otherwise, only production ones will be considered.",
    )
    convert_parser.set_defaults(func=main)


def main(options):
    Terminal("rich")
    processor = FromPipenv(options.path, options.jobs, options.dev)
    return processor.convert()
