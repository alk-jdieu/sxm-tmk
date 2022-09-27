import pytest

from sxm_tmk.core.dependency import Dependency
from sxm_tmk.core.models import InstallMode


def test_collect_dependencies(a_pipfile_lock):
    assert len(a_pipfile_lock.collect_dependencies()) == 161
    a_pipfile_lock.mode = InstallMode.DEFAULT
    assert len(a_pipfile_lock.collect_dependencies()) == 120


def test_get_editable_packages(a_pipfile_lock):
    edit_pkgs = a_pipfile_lock.get_editable_packages()
    assert len(edit_pkgs) == 1
    assert "alk-service-test" in edit_pkgs
    assert edit_pkgs["alk-service-test"] == Dependency("alk-service-test", version="==0.0.0")


def test_pkg_version(a_pipfile_lock):
    assert a_pipfile_lock.get_version_of("pytest") == Dependency("pytest", "==7.1.2")


def test_pkg_not_found(a_pipfile_lock):
    with pytest.raises(KeyError, match="Unknown package"):
        a_pipfile_lock.get_version_of("donotexists")
