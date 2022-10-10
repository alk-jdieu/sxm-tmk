import pytest

from sxm_tmk.core.dependency import Package, PinnedPackage
from sxm_tmk.core.env_manager.pipenv.lock import LockFile
from sxm_tmk.core.types import InstallMode


def test_lockfile_from_dir_can_resolve_pipfile_lock(a_path_containing_a_pipfile_lock):
    a_lock = LockFile(a_path_containing_a_pipfile_lock)
    assert a_lock.mode == InstallMode.DEV


def test_lockfile_from_path_resolve_pipfile_lock(a_path_to_pipfile_lock):
    a_lock = LockFile(a_path_to_pipfile_lock)
    assert a_lock.mode == InstallMode.DEV


def test_lockfile_with_invalid_path(tmp_path):
    with pytest.raises(FileNotFoundError, match=f"Cannot find pipfile in '{tmp_path.as_posix()}/Pipfile.lock'."):
        LockFile(tmp_path)


def test_collect_dependencies(a_pipfile_lock):
    assert len(a_pipfile_lock.list_dependencies()) == 161
    a_pipfile_lock.mode = InstallMode.DEFAULT
    assert len(a_pipfile_lock.list_dependencies()) == 120


def test_get_editable_packages(a_pipfile_lock):
    edit_pkgs = a_pipfile_lock.get_editable_packages()
    assert len(edit_pkgs) == 1
    assert "alk-service-test" in edit_pkgs
    assert edit_pkgs["alk-service-test"] == Package("alk-service-test", version=None, build_number=None, build=None)


def test_get_not_editable_pkg(a_pipfile_lock):
    assert a_pipfile_lock.get_package("pytest") == Package("pytest", version="7.1.2", build_number=None, build=None)


def test_get_editable_pkg(a_pipfile_lock):
    assert a_pipfile_lock.get_package("alk-service-test") == Package(
        "alk-service-test", version=None, build_number=None, build=None
    )


def test_get_pkg_not_found(a_pipfile_lock):
    with pytest.raises(KeyError, match='Unknown package "donotexists"'):
        a_pipfile_lock.get_package("donotexists")


def test_get_sources(a_pipfile_lock):
    expected = [
        "https://${ALK_PYPI_USERNAME}:${ALK_PYPI_PASSWORD}@pypi.alkemics.com:8443/simple",
        "https://pypi.org:8443/simple",
    ]
    assert expected == a_pipfile_lock.get_sources()


def test_get_python_version(a_pipfile_lock):
    got = a_pipfile_lock.get_python_version()
    py = PinnedPackage.from_specifier("python", "3.8", "~=3.8.0")
    assert py == got
