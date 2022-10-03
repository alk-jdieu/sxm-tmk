import collections
import enum
import pathlib
from typing import Callable, Dict

import ujson as json

from sxm_tmk.core.dependency import Package, PinnedPackage
from sxm_tmk.core.types import DictOfPackages, InstallMode, PinnedPackages


class LockFile:
    class PackageTypes(enum.IntEnum):
        EDITABLES_PACKAGES_ONLY = 1
        EXCLUDE_EDITABLES_PACKAGES = 2
        ALL_PACKAGES = 4

    def __init__(self, fspath: pathlib.Path):
        self.__data = json.loads(fspath.read_text())
        self.__mode: InstallMode = InstallMode.DEV
        self.__filters: Dict[LockFile.PackageTypes, Callable[[collections.Mapping], bool]] = {
            LockFile.PackageTypes.EDITABLES_PACKAGES_ONLY: lambda pkg: "editable" in pkg,
            LockFile.PackageTypes.EXCLUDE_EDITABLES_PACKAGES: lambda pkg: "editable" not in pkg,
            LockFile.PackageTypes.ALL_PACKAGES: lambda _: True,
        }
        self.__pkg_filter = self.__filters[LockFile.PackageTypes.ALL_PACKAGES]

    @property
    def mode(self) -> InstallMode:
        return self.__mode

    @mode.setter
    def mode(self, mode: InstallMode):
        self.__mode = mode

    def list_dependencies(self) -> PinnedPackages:
        self.__pkg_filter = self.__filters[LockFile.PackageTypes.EXCLUDE_EDITABLES_PACKAGES]
        return list({PinnedPackage.make_from_specifier(name=name, specifier=version) for name, version in self})

    def __iter__(self):
        modes = [InstallMode.DEFAULT] if self.mode != InstallMode.DEV else [InstallMode.DEFAULT, InstallMode.DEV]

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

    def get_editable_packages(self) -> DictOfPackages:
        self.__pkg_filter = self.__filters[LockFile.PackageTypes.EDITABLES_PACKAGES_ONLY]
        edit_packages: DictOfPackages = {}
        for pkg, _ in self:
            edit_packages[pkg] = Package(name=pkg, version=None)
        return edit_packages

    def get_package(self, pkg: str) -> Package:
        for mode in [InstallMode.DEFAULT, InstallMode.DEV]:
            try:
                pkg_info = self.__data[mode.value][pkg]
                if self.__filters[LockFile.PackageTypes.EXCLUDE_EDITABLES_PACKAGES](pkg_info):
                    pinned_package = PinnedPackage.make_from_specifier(pkg, specifier=pkg_info["version"])
                    return Package(pinned_package.name, version=pinned_package.version)
                return Package(pkg, version=None)
            except KeyError:
                pass
        raise KeyError(f'Unknown package "{pkg}"')
