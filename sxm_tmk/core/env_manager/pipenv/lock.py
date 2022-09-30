import collections
import enum
import pathlib
from typing import Callable, Dict

import ujson as json

from sxm_tmk.core.dependency import Dependency
from sxm_tmk.core.models import DictOfDeps, InstallMode, ListOfDeps


class LockFile:
    class PackageTypes(enum.IntEnum):
        EDITABLES_ONLY = 1
        EXCLUDE_EDITABLES = 2
        ALL = 4

    def __init__(self, fspath: pathlib.Path):
        self.__data = json.loads(fspath.read_text())
        self.__mode: InstallMode = InstallMode.DEV
        self.__filters: Dict[LockFile.PackageTypes, Callable[[collections.Mapping], bool]] = {
            LockFile.PackageTypes.EDITABLES_ONLY: lambda pkg: "editable" in pkg,
            LockFile.PackageTypes.EXCLUDE_EDITABLES: lambda pkg: "editable" not in pkg,
            LockFile.PackageTypes.ALL: lambda _: True,
        }
        self.__pkg_filter = self.__filters[LockFile.PackageTypes.ALL]

    @property
    def mode(self) -> InstallMode:
        return self.__mode

    @mode.setter
    def mode(self, mode: InstallMode):
        self.__mode = mode

    def collect_dependencies(self) -> ListOfDeps:
        self.__pkg_filter = self.__filters[LockFile.PackageTypes.EXCLUDE_EDITABLES]
        return list({Dependency(pkg=name, version=version) for name, version in self})

    def __iter__(self):
        modes = [InstallMode.DEFAULT] if self.__mode != InstallMode.DEV else [InstallMode.DEFAULT, InstallMode.DEV]

        for mode in modes:
            for element in self.__data[mode.value]:
                pkg_infos = self.__data[mode.value][element]
                if not self.__pkg_filter(pkg_infos):
                    continue
                try:
                    pkg_version = pkg_infos["version"]
                except KeyError:
                    pkg_version = ""
                yield element, pkg_version

    def get_editable_packages(self) -> DictOfDeps:
        self.__pkg_filter = self.__filters[LockFile.PackageTypes.EDITABLES_ONLY]
        edit_packages: DictOfDeps = {}
        for pkg, _ in self:
            edit_packages[pkg] = Dependency(pkg=pkg, version="==0.0.0")
        return edit_packages

    def get_version_of(self, pkg) -> Dependency:
        for mode in [InstallMode.DEFAULT, InstallMode.DEV]:
            try:
                pkg_info = self.__data[mode.value][pkg]
                if self.__filters[LockFile.PackageTypes.EXCLUDE_EDITABLES](pkg_info):
                    return Dependency(pkg, version=pkg_info["version"])
                return Dependency(pkg, version="==0.0.0")
            except KeyError:
                pass
        raise KeyError("Unknown package")
