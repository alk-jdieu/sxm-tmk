from subprocess import CalledProcessError

import mock
import ujson

from sxm_tmk.core.conda.cache import CondaCache
from sxm_tmk.core.conda.repo import QueryPlan, SearchStatus, search_mamba_for
from sxm_tmk.core.dependency import Package


def test_search_mamba_package_issue(tmp_path):
    cache = CondaCache(tmp_path)
    with mock.patch("sxm_tmk.core.conda.repo.subprocess.check_output") as mocked_search:
        mocked_search.side_effect = CalledProcessError(3, cmd="mamba search something")
        result, pkg = search_mamba_for("something", cache)
        assert result == SearchStatus.NOT_FOUND
        assert pkg == "something"
    mocked_search.assert_called_once()


def test_search_mamba_package_not_found(tmp_path):
    cache = CondaCache(tmp_path)
    with mock.patch("sxm_tmk.core.conda.repo.subprocess.check_output") as mocked_search:
        mocked_search.return_value = ujson.dumps(
            {
                "caused_by": "None",
                "channel_urls": [
                    "https://conda.anaconda.org/conda-forge/osx-arm64",
                    "https://conda.anaconda.org/conda-forge/noarch",
                ],
                "channels_formatted": "  - https://conda.anaconda.org/conda-forge/osx-arm64",
                "error": "PackagesNotFoundError: This packages are not available from current channels: attrs2",
                "exception_name": "PackagesNotFoundError",
                "exception_type": "<class 'conda.exceptions.PackagesNotFoundError'>",
                "message": "The following packages are not available from current channels: attrs2",
                "packages": ["attrs2"],
                "packages_formatted": "  - attrs2",
            }
        )
        result, pkg = search_mamba_for("something", cache)
        assert result == SearchStatus.NOT_FOUND
        assert pkg == "something"
    mocked_search.assert_called_once()


def test_search_mamba_package_found_in_cache(tmp_path):
    cache = CondaCache(tmp_path)
    cache.store("something", ujson.dumps({"some": "value", "value": 42}))
    with mock.patch("sxm_tmk.core.conda.repo.subprocess.check_output") as mocked_search:
        result, pkg = search_mamba_for("something", cache)
        assert result == SearchStatus.FOUND_IN_CACHE
        assert pkg == "something"
    mocked_search.assert_not_called()


def test_search_mamba_package_found_in_forge(tmp_path):
    cache = CondaCache(tmp_path)
    with mock.patch("sxm_tmk.core.conda.repo.subprocess.check_output") as mocked_search:
        mocked_search.return_value = ujson.dumps({"some": "value", "value": 42}).encode("utf8")
        result, pkg = search_mamba_for("something", cache)
        assert result == SearchStatus.FOUND_IN_REPOSITORY
        assert pkg == "something"
    mocked_search.assert_called_once()


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

        all_pkgs_to_search = [
            Package("numpy", version="1.2.3", build_number=None, build=None),
            Package("pytest", version="4.5.6", build_number=None, build=None),
            Package("thingy", version="1.0.0", build_number=None, build=None),
        ]
        q.search_and_mark(all_pkgs_to_search)
    assert search_mock.call_count == 3

    assert q.stats == {"not_found": ["thingy"], "found": ["numpy", "pytest"]}
