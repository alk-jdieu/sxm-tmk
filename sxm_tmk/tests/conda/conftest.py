import pathlib

import pytest

from sxm_tmk.core.dependency import Package


@pytest.fixture()
def cache_with_numpy(tmp_path) -> pathlib.Path:
    numpy_json = (pathlib.Path(__file__).parent.parent / "data" / "cached_result_of_numpy.json").read_text()
    path_to_cache = tmp_path / "cache"
    path_to_cache.mkdir(exist_ok=True)
    numpy_in_cache: pathlib.Path = path_to_cache / "numpy.json"
    numpy_in_cache.touch(exist_ok=False)
    numpy_in_cache.write_text(numpy_json)
    return path_to_cache


@pytest.fixture()
def numpy_package() -> Package:
    return Package(name="numpy", version=None, build_number=None, build=None)
