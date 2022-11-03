import collections
import enum
import pathlib
from typing import Callable, Dict, List

import ujson as json

from sxm_tmk.core.custom_types import (
    DictOfPackages,
    InstallMode,
    PinnedPackages,
    TMKLockFileNotFound,
)
from sxm_tmk.core.dependency import Package, PinnedPackage, clean_version


class LockFile:
    class PackageTypes(enum.IntEnum):
        EDITABLES_PACKAGES_ONLY = 1
        EXCLUDE_EDITABLES_PACKAGES = 2
        ALL_PACKAGES = 4

    def __init__(self, fspath: pathlib.Path):
        lock_file_path = fspath
        if lock_file_path.name != "Pipfile.lock":
            lock_file_path = lock_file_path / "Pipfile.lock"
        if not lock_file_path.exists():
            raise TMKLockFileNotFound(f"Cannot find pipfile in '{lock_file_path.as_posix()}'.")

        self.__data = json.loads(lock_file_path.read_text())
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
        return list(
            {PinnedPackage.from_specifier(name=name, version=version[2:], specifier=version) for name, version in self}
        )

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
            edit_packages[pkg] = Package(name=pkg, version=None, build_number=None, build=None)
        return edit_packages

    def get_sources(self) -> List[str]:
        known_sources = self.__data.get("_meta", {}).get("sources", [])
        sources = []
        for source in known_sources:
            url = source.get("url", "")
            if url != "https://pypi.org:8443/simple":
                # We need to exclude public pypi as it cause PIP to hang out with --extra-index-url option
                sources.append(source.get("url", ""))
        return list(filter(lambda u: u, sources))

    def get_python_version(self) -> PinnedPackage:
        version = None
        try:
            version = self.__data["_meta"]["requires"]["python_version"]
        except KeyError:
            for key in ("python_full_version", "python_version"):
                try:
                    if version:
                        continue
                    version = self.__data["_meta"]["host-environment-markers"][key]
                except KeyError:
                    pass

        py_pkg = Package("python", version, None, None)
        py_pkg_version = py_pkg.parse_version()
        pinned_version = f"~={py_pkg_version.major}.{py_pkg_version.minor}.{py_pkg_version.micro}"
        return PinnedPackage.from_specifier("python", version, pinned_version)

    def get_package(self, pkg: str) -> Package:
        for mode in [InstallMode.DEFAULT, InstallMode.DEV]:
            try:
                pkg_info = self.__data[mode.value][pkg]
                if self.__filters[LockFile.PackageTypes.EXCLUDE_EDITABLES_PACKAGES](pkg_info):
                    pinned_package = PinnedPackage.from_specifier(
                        pkg, version=clean_version(pkg_info["version"]), specifier=pkg_info["version"]
                    )
                    return Package(pinned_package.name, version=pinned_package.version, build_number=None, build=None)
                return Package(pkg, version=None, build_number=None, build=None)
            except KeyError:
                pass
        raise KeyError(f'Unknown package "{pkg}"')
