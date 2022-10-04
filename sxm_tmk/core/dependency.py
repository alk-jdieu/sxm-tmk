from dataclasses import dataclass
from typing import Optional

from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import parse


class InvalidVersion(Exception):
    def __init__(self, version):
        super().__init__(f'Version "{version}" is invalid.')


class InvalidConstraintSpecification(Exception):
    def __init__(self, specifier):
        super().__init__(f'Specifier "{specifier}" is invalid.')


class BrokenVersionSpecifier(Exception):
    def __init__(self, version, specifier):
        super().__init__(f'Broken specifier: version "{version}" does not fulfil specifier "{specifier}" contract.')


class NotComparablePackage(Exception):
    def __init__(self, package: str):
        super().__init__(f'Package "{package}" cannot be compared to another package: no version information found.')


@dataclass(unsafe_hash=True)
class Package:
    """
    Basic representation of a requirement. Holds the requirement name.
    """

    name: str
    version: Optional[str]
    build_number: Optional[int]
    build: Optional[str]

    def __repr__(self):
        return f"{self.name}-{self.version or 'none'}-{self.build or 'none'}-{self.build_number or 'none'}"

    def compare_key(self):
        if self.version is not None and self.build_number is not None:
            return self.version, self.build_number
        elif self.version is not None and self.build_number is None:
            return self.version
        elif self.version is None and self.build_number is not None:
            return self.build_number
        else:
            raise NotComparablePackage(self.name)


@dataclass(unsafe_hash=True)
class PinnedPackage(Package):
    """
    A requirement specification, including also the version specifier.
    """

    specifier: Specifier

    def __post_init__(self):
        if self.version:
            version = parse(self.version)
            if version not in self.specifier:
                raise BrokenVersionSpecifier(self.version, str(self.specifier))

    def __repr__(self):
        return f"{super().__str__()} {self.specifier}"

    @classmethod
    def make(cls, name: str, version: str, specifier: str):
        return cls(name=name, version=version, build_number=None, build=None, specifier=Specifier(specifier))

    @classmethod
    def from_specifier(cls, name: str, specifier: str):
        spec = Specifier(specifier)
        return cls(name=name, version=spec.version, build_number=None, build=None, specifier=spec)


class Constraint:
    """
    A global constraint that can be used to ensure a Package is in the valid format or to solve a dependency given
    some conditions.
    """

    def __init__(self, pkg_name: str, constraint_description: str):
        self.__pkg_name: str = pkg_name
        self.__constraint_specifications = SpecifierSet(constraint_description.split(" ")[0])

    def __repr__(self):
        return f"{self.__pkg_name} | {self.__constraint_specifications}"

    @property
    def pkg_name(self) -> str:
        return self.__pkg_name

    def ensure(self, pkg: Package) -> bool:
        if pkg.version:
            return pkg.version in self.__constraint_specifications and self.__pkg_name == pkg.name
        else:
            return False

    @classmethod
    def from_conda_depends(cls, depends_on: str):
        depends_on_part = depends_on.split(" ")
        if len(depends_on_part) < 2:
            raise InvalidConstraintSpecification(depends_on)

        has_operator = any((depends_on_part[1].startswith(op) for op in ("=", ">", "<")))
        if not has_operator:
            return cls(depends_on_part[0], f"=={depends_on_part[1]}")
        return cls(depends_on_part[0], depends_on_part[1])
