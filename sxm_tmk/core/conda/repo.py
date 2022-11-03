import enum
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait
from typing import Dict, List, Optional

import ujson

from sxm_tmk.core.conda.cache import CondaCache
from sxm_tmk.core.conda.commands import MambaSearch
from sxm_tmk.core.custom_types import Packages
from sxm_tmk.core.out.terminal import Progress


class SearchStatus(enum.Enum):
    FOUND_IN_REPOSITORY = "found"
    FOUND_IN_CACHE = "found"
    NOT_FOUND = "not_found"


def search(method: MambaSearch, pkg: str, cache: CondaCache, progress_task: Progress.Task):
    if pkg not in cache:
        data = method.execute(pkg)
        progress_task.update(1)
        if data is None:
            return SearchStatus.NOT_FOUND, pkg

        json_data = ujson.loads(data)
        if "error" in json_data:
            return SearchStatus.NOT_FOUND, pkg
        else:
            cache.store(pkg, data)
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
        method = MambaSearch()
        method.use_index = False
        self._aggregate_results(*search(method, packages[0].name, self.__cache, progress_track))
        with ThreadPoolExecutor(max_workers=10) as tp:
            method.use_index = True
            for package in packages[1:]:
                futures.append(tp.submit(search, method, package.name, self.__cache, progress_track))
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
