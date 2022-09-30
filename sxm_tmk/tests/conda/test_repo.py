import mock
import ujson

from sxm_tmk.core.conda.cache import CondaCache
from sxm_tmk.core.conda.repo import QueryPlan, SearchStatus
from sxm_tmk.core.dependency import Dependency


def search_mamba_for_replacement(dep: str, cache: CondaCache):
    return_value = {
        "numpy": (SearchStatus.FOUND_IN_REPOSITORY, {"numpy": [{"version": "1.2.3"}]}),
        "pytest": (SearchStatus.FOUND_IN_CACHE, {"pytest": [{"version": "4.5.6"}]}),
        "thingy": (SearchStatus.NOT_FOUND, {"error": "error"}),
    }
    status, value = return_value[dep]

    if status == SearchStatus.FOUND_IN_REPOSITORY:
        cache.store(dep, ujson.dumps(value))
    return status, dep


def test_query_plan_search_result(tmp_path):
    # This test checks the results collected through the pool of query to ensure the final aggregation is correct
    a_cache: CondaCache = CondaCache(tmp_path)

    # We want one value from the pool
    a_cache.store("pytest", ujson.dumps({"pytest": [{"version": "4.5.6"}]}))

    q = QueryPlan(jobs=1, cache=a_cache)
    with mock.patch(
        "sxm_tmk.core.conda.repo.search_mamba_for", side_effect=search_mamba_for_replacement
    ) as search_mock:

        all_deps_to_search = [
            Dependency("numpy", "==1.2.3"),
            Dependency("pytest", "==4.5.6"),
            Dependency("thingy", "==1.0.0"),
        ]
        q.search_and_mark(all_deps_to_search)
    assert search_mock.call_count == 3

    assert q.stats == {"not_found": ["thingy"], "found": ["numpy", "pytest"]}
