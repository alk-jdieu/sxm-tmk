import pathlib
import time

import pytest

from sxm_tmk.core.env_manager.pipenv.lock import LockFile


@pytest.fixture()
def bash_script_cleaner():
    basename = f"{int(time.time())}.sh"
    yield basename
    path = pathlib.Path.cwd() / basename
    if path.exists():
        path.unlink()


@pytest.fixture()
def a_path_to_pipfile_lock():
    this_path = pathlib.Path(__file__).parent
    return this_path.parent / "tests" / "data" / "Pipfile.lock"


@pytest.fixture()
def a_path_containing_a_pipfile_lock():
    this_path = pathlib.Path(__file__).parent
    return this_path.parent / "tests" / "data"


@pytest.fixture()
def a_pipfile_lock(a_path_to_pipfile_lock):
    return LockFile(a_path_to_pipfile_lock)
