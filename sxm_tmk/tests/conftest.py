import pathlib

import pytest

from sxm_tmk.core.env_manager.pipenv.lock import LockFile


@pytest.fixture()
def a_path_to_pipfile_lock():
    this_path = pathlib.Path(__file__).parent
    return this_path.parent / "tests" / "data" / "Pipfile.lock"


@pytest.fixture()
def a_pipfile_lock(a_path_to_pipfile_lock):
    return LockFile(a_path_to_pipfile_lock)
