import datetime
import functools
import pathlib
from typing import Callable, Optional

import ujson

from sxm_tmk.core.conda.file_lock_wrapper import (
    LockMixin,
    ensure_lock_on_public_interface_call,
)
from sxm_tmk.core.dependency import Constraint, Package, PinnedPackage
from sxm_tmk.core.types import Constraints, Packages

CACHE_DIR: pathlib.Path = pathlib.Path.home() / ".sxm_tmk" / "conda_query_cache"


def compute_expiry_time(force_now: bool = False) -> float:
    if force_now:
        return datetime.datetime.now().timestamp()
    now = datetime.datetime.now() - datetime.timedelta(days=1)
    return now.timestamp()


@ensure_lock_on_public_interface_call()
class CondaCache(LockMixin):
    def __init__(self, cache_dir: Optional[pathlib.Path] = None):
        self.__cache_dir: pathlib.Path = cache_dir or CACHE_DIR
        if not self.__cache_dir.exists():
            self.__cache_dir.mkdir(parents=True, exist_ok=True)
        lock_file_path: pathlib.Path = self.__cache_dir / "tmk.lock"
        lock_file_path.touch(exist_ok=True)
        super().__init__(lock_file_path)

    def clean(self, now: bool = False):
        expiry_time = compute_expiry_time(now)
        delete_file = None

        res = {"deleted": 0, "space-claimed": 0}

        for pkg_file_query in self.__cache_dir.iterdir():
            if delete_file is not None:
                res["deleted"] = res["deleted"] + 1
                res["space-claimed"] = res["space-claimed"] + delete_file.stat().st_size
                delete_file.unlink()
                delete_file = None
            if pkg_file_query.suffix == ".json":
                data = ujson.loads(pkg_file_query.read_text())
                try:
                    delete_file = pkg_file_query if data["sxm_tmk"]["query_date"] < expiry_time else None
                except KeyError:
                    delete_file = pkg_file_query
        if delete_file is not None:
            res["deleted"] = res["deleted"] + 1
            res["space-claimed"] = res["space-claimed"] + delete_file.stat().st_size
            delete_file.unlink()
        return res

    def store(self, pkg: str, content: str):
        pkg_file = self.__cache_dir / f"{pkg}.json"
        if pkg_file.exists():
            pkg_file.unlink()
        json_data = ujson.loads(content)
        json_data["sxm_tmk"] = {"query_date": datetime.datetime.now().timestamp()}
        with pkg_file.open("w") as f:
            ujson.dump(json_data, f)

    def __contains__(self, item):
        return (self.__cache_dir / f"{item}.json").exists()

    def __getitem__(self, item):
        return self.get(item)

    def get(self, item):
        item_path: pathlib.Path = self.__cache_dir / f"{item}.json"
        if item_path.exists():
            return ujson.loads(item_path.read_text())
        return None


def _no_restrict(version):  # noqa
    return True


def _restrict_with(spec, version):
    return version in spec


class PackageCacheExtractor:
    """Extracts package from a cache key.
    The extraction results in an ordered list using:
     * version as primary key
     * build_number as second key
    """

    def __init__(self, cache: CondaCache):
        self.__cache = cache

    @staticmethod
    def _check_conditions_on_pkg_requirements(pkg_requires: Constraints, conditions: Packages):
        def join_constraint_on_condition(a_condition: Package, a_constraint: Constraint):
            return a_constraint.pkg_name == a_condition.name

        conditions_are_matched = [False] * len(conditions)
        for i, condition in enumerate(conditions):
            # Join constraints given our conditions
            fix_condition_joiner = functools.partial(join_constraint_on_condition, condition)
            joined_constraints = list(filter(fix_condition_joiner, pkg_requires))
            if joined_constraints:
                conditions_are_matched[i] = any((constraint.ensure(condition) for constraint in joined_constraints))
            else:
                # If the current condition has no constraint on current package, consider condition as being ok.
                conditions_are_matched[i] = True
        return all(conditions_are_matched)

    def _extract_matching_packages(
        self, pkg_name: str, conditions: Packages, version_restrict: Callable[[str], bool]
    ) -> Packages:
        pkg_info = self.__cache[pkg_name]
        if not pkg_info or pkg_name not in pkg_info:
            return []

        all_matching_packages = []
        for package_desc in pkg_info[pkg_name]:
            _depends = list(filter(lambda pkg_constraint: " " in pkg_constraint, package_desc["depends"]))
            depends: Constraints = [Constraint.from_conda_depends(specification) for specification in _depends]

            this_package_version = package_desc["version"]
            if (conditions and self._check_conditions_on_pkg_requirements(depends, conditions)) or not conditions:
                this_package = Package(
                    name=pkg_name,
                    version=this_package_version,
                    build_number=package_desc["build_number"],
                    build=package_desc["build"],
                )
                if version_restrict(this_package.parse_version().base_version):
                    all_matching_packages.append(this_package)

        return sorted(all_matching_packages, reverse=True, key=lambda p: p.compare_key())

    def extract_packages(self, pkg: Package, conditions: Packages) -> Packages:
        restriction = _no_restrict
        if pkg.version is not None:
            use_spec = PinnedPackage.from_specifier(pkg.name, pkg.version, f"=={pkg.version}").specifier
            restriction = functools.partial(_restrict_with, use_spec)
        return self._extract_matching_packages(pkg.name, conditions, restriction)

    def extract_pinned_packages(self, pin_pkg: PinnedPackage, conditions: Packages) -> Packages:
        restriction = functools.partial(_restrict_with, pin_pkg.specifier)
        return self._extract_matching_packages(pin_pkg.name, conditions, restriction)
