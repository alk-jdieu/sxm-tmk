import pathlib
from typing import Optional

from sxm_tmk.converters.base import Base
from sxm_tmk.core.conda.cache import CondaCache, PackageCacheExtractor
from sxm_tmk.core.conda.repo import QueryPlan
from sxm_tmk.core.conda.specifications import Environment
from sxm_tmk.core.custom_types import InstallMode, Packages, PinnedPackages
from sxm_tmk.core.dependency import PinnedPackage
from sxm_tmk.core.env_manager.pipenv.lock import LockFile
from sxm_tmk.core.out.terminal import Progress, Section, Status, Terminal


class FromPipenv(Base):
    def __init__(self, path_to_project: pathlib.Path, jobs: Optional[int] = None, dev_mode: bool = False):
        super().__init__()
        self.__pipfile_lock = LockFile(path_to_project)
        self.__pipfile_lock.mode = InstallMode.DEV if dev_mode else InstallMode.DEFAULT
        self.__path = path_to_project
        self.__max_jobs = jobs or 5
        self.__env_constrained_pkg: PinnedPackages = []
        self.__solved_constraints: Packages = []
        self.__conda_packages: Packages = []
        self.__pip_packages: Packages = []
        self.__cache = CondaCache()

    def _read_env_constraints(self):
        step = Status("Building profile ...")

        with step:
            ssl_pkg = self.get_openssl_profile()
            py_pkg = self.__pipfile_lock.get_python_version()
            pip_pkg = PinnedPackage.from_specifier(name="pip", version=None, specifier=">1.0.0")
            self.__env_constrained_pkg = [ssl_pkg, py_pkg, pip_pkg]
        Terminal().step("Profile built", True)

    def _solve_env_constraints(self):
        progress = Progress("")
        this_task = progress.add_task("Fetching package info", len(self.__env_constrained_pkg))
        with progress:
            q = QueryPlan(jobs=self.__max_jobs, cache=self.__cache)
            xtractor = PackageCacheExtractor(self.__cache)
            q.search_and_mark(self.__env_constrained_pkg, this_task)
            for constrained_package in self.__env_constrained_pkg:
                valid_pkg = xtractor.extract_pinned_packages(constrained_package, self.__solved_constraints)
                if valid_pkg:
                    self.__solved_constraints.append(valid_pkg[0])
        step_success = len(self.__solved_constraints) == len(self.__env_constrained_pkg)
        Terminal().step("Profile solved", step_success)
        Terminal().info("Profile contains:")
        with Section():
            for pkg in self.__solved_constraints:
                Terminal().info(f"{pkg.name} -> {pkg.version}")

    def _solve_dependencies(self):
        progress = Progress("")
        project_dependencies = self.__pipfile_lock.list_dependencies()
        this_task = progress.add_task("Fetching package info", len(project_dependencies))
        q = QueryPlan(jobs=self.__max_jobs, cache=self.__cache)
        with progress:
            q.search_and_mark(project_dependencies, this_task)
        this_status = Terminal().new_status("Solving")
        with this_status:
            xtractor = PackageCacheExtractor(self.__cache)
            for package in q.found_pkgs:
                this_pkg = self.__pipfile_lock.get_package(package)
                valid_pkg = xtractor.extract_packages(this_pkg, self.__solved_constraints)
                if valid_pkg:
                    self.__conda_packages.append(valid_pkg[0])
                else:
                    self.__pip_packages.append(self.__pipfile_lock.get_package(package))

            for not_found_package in q.not_found_pkgs:
                self.__pip_packages.append(self.__pipfile_lock.get_package(not_found_package))

    def convert(self):
        self._read_env_constraints()
        self._solve_env_constraints()
        self._solve_dependencies()
        self.dump_environment()

    def dump_environment(self):
        this_status = Terminal().new_status("Writing conda specification for your environment ...")
        with this_status:
            path = self.__path if self.__path.is_dir() else self.__path.parent
            dir_name = self.__path.name
            path = path / f"{dir_name}.conda.yaml"
            env = Environment(name=dir_name)

            env.conda.packages.extend(self.__solved_constraints)
            env.conda.packages.extend(self.__conda_packages)
            env.pip.extra_indexes.extend(self.__pipfile_lock.get_sources())
            env.pip.packages.extend(self.__pip_packages)

            env.write_as_yaml(path)

        Terminal().step(f"Environment at {path.as_posix()}", path.exists())
