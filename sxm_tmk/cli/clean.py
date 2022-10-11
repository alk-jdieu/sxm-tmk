import pathlib

from sxm_tmk.core.conda.cache import CACHE_DIR, CondaCache
from sxm_tmk.core.out.terminal import Status, Terminal


def setup(subparser):
    clean_parser = subparser.add_parser(name="clean")
    clean_parser.add_argument(
        "--conda-cache",
        type=pathlib.Path,
        default=CACHE_DIR,
        help=f"Path to a conda cache. Default is to use {CACHE_DIR.as_posix()}",
    )
    clean_parser.set_defaults(func=main)


def main(options):
    Terminal("rich")
    Terminal().info("Validating cache path...")
    if not options.conda_cache.exists():
        Terminal().step_status("Invalid cache", False)
        return 1

    Terminal().step_status("Cache is healthy", True)
    cache = CondaCache(options.conda_cache)
    state = Status("Cleaning ...")
    with state:
        res = cache.clean()

    Terminal().info(f"Files deleted: {res['deleted']}")
    Terminal().info(f"Space claimed: {res['space-claimed'] / 1024:.2f} KB")
    return 0
