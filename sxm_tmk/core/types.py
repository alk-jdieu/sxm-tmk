import enum
from typing import Dict, List

from sxm_tmk.core.dependency import Constraint, Package, PinnedPackage

Constraints = List[Constraint]
DictOfPackages = Dict[str, Package]
Packages = List[Package]
DictOfPinnedPackages = Dict[str, PinnedPackage]
PinnedPackages = List[PinnedPackage]


class InstallMode(enum.Enum):
    DEFAULT = "default"
    DEV = "develop"


#
#
# from packaging.version import Version, parse
# from packaging.specifiers import Specifier, SpecifierSet
#
#
# from dataclasses import dataclass
# from typing import Optional
#
#
# class InvalidVersion(Exception):
#     def __init__(self, version):
#         super().__init__(f'Version "{version}" is invalid.')
#
#
# class Package:
#     def __init__(self, pkg_name: str, pkg_version: str, clear_specifiers: Optional[bool] = True):
#         self.__name: str = pkg_name
#         has_specifier: bool = any((pkg_version.startswith(specifier) for specifier in ('=', '<', '>', '!', '^')))
#         if not clear_specifiers and has_specifier:
#             raise InvalidVersion(pkg_version)
#         version_to_parse = pkg_version if not has_specifier else Specifier(pkg_version).version
#         self.__version: Version = parse(version_to_parse)
#
#     @property
#     def name(self) -> str:
#         return self.__name
#
#     @property
#     def version_str(self) -> str:
#         return str(self.__version)
#
#     @property
#     def version(self) -> Version:
#         return self.__version
#
#
# class Constraint:
#     def __init__(self, pkg_name: str, constraint_description: str):
#         self.__pkg_name: str = pkg_name
#         self.__constraint_specifications = SpecifierSet(constraint_description)
#
#     @property
#     def pkg_name(self) -> str:
#         return self.__pkg_name
#
#     def ensure(self, pkg: Package) -> bool:
#         return pkg.version in self.__constraint_specifications and self.__pkg_name == pkg.name
#
#
# def
#
# def get_python_as_constraint() -> Constraint:
#     return Constraint('python', '3.8.10')
#
#
# # 1. Collect dependencies from Pipfile.lock
# #   -> sxm_tmk.core.env_manager.pipenv.lock.LockFile
# # 2. Search them through conda/mamba
# #   -> sxm_tmk.core.conda.repo.QueryPlan
# # 3. Isolate constraints (a minima Python)
# #   -> get_python_as_constraint
# # 4. Iterate through all conda found requirements and check if env constraints are fulfilled
# #   -> EnvResolver(QueryPlan, CondaCache, Constraint)
# # 5. Print env
# #   -> sxm_tmk.core.conda.specifications.Environment
#
#
# env_constraints = [Constraint('python', ">=3.8.1,<3.9"),
#                    Constraint('numpy', '~=1.15,!=1.15.3')]
#
# # checker = CondaConstraintProcessor()
# # checker.add_environment_constraint(py38_constraint)
# # cache = CondaCache()
#
# # if checker(cache.get('pytest'), pytest):
# #     conda_env.dependencies.append(pytest)
# # else:
# #     conda_env.pip.packages.append(pytest)
# #
# #
# # pytest.pin_for_conda()  # pytest = 7.1.2
# # pytest.pin_for_pip()  # pytest == 7.1.2
