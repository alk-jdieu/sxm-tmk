import enum
import subprocess
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait
from typing import Dict, List, Optional

import ujson

from sxm_tmk.core.conda.cache import CondaCache
from sxm_tmk.core.custom_types import Packages
from sxm_tmk.core.out.terminal import Progress


class SearchStatus(enum.Enum):
    FOUND_IN_REPOSITORY = "found"
    FOUND_IN_CACHE = "found"
    NOT_FOUND = "not_found"


def search_mamba_for(pkg: str, cache: CondaCache, progress_task: Progress.Task):
    if pkg not in cache:
        try:
            data = subprocess.check_output(f"mamba search --json {pkg}".split())
        except subprocess.CalledProcessError:
            return SearchStatus.NOT_FOUND, pkg
        finally:
            progress_task.update(1)

        json_data = ujson.loads(data)
        if "error" in json_data:
            return SearchStatus.NOT_FOUND, pkg
        else:
            cache.store(pkg, data.decode("utf8"))
        return SearchStatus.FOUND_IN_REPOSITORY, pkg
    else:
        progress_task.update(1)
        return SearchStatus.FOUND_IN_CACHE, pkg


class QueryPlan:
    def __init__(self, jobs: int = 5, cache: Optional[CondaCache] = None):
        self.__cache = cache or CondaCache()
        self.__jobs = jobs
        self.__stats: Dict[str, List[str]] = {"found": [], "not_found": []}

    def _aggregate_results(self, search_result: SearchStatus, pkg: str):
        self.__stats[str(search_result.value)].append(pkg)

    def search_and_mark(self, packages: Packages, progress_track: Progress.Task):
        futures = []
        with ThreadPoolExecutor(max_workers=10) as tp:
            for package in packages:
                futures.append(tp.submit(search_mamba_for, package.name, self.__cache, progress_track))
            wait(futures, return_when=ALL_COMPLETED)
        for result in futures:
            k, v = result.result()
            self._aggregate_results(k, v)

    @property
    def stats(self):
        return self.__stats

    @property
    def found_pkgs(self):
        return self.__stats["found"]

    @property
    def not_found_pkgs(self):
        return self.__stats["not_found"]
