from dataclasses import dataclass
from typing import Optional

from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import parse


class InvalidVersion(Exception):
    def __init__(self, version):
        super().__init__(f'Version "{version}" is invalid.')


class BrokenVersionSpecifier(Exception):
    def __init__(self, version, specifier):
        super().__init__(f'Broken specifier: version "{version}" does not fulfil specifier "{specifier}" contract.')


@dataclass(unsafe_hash=True)
class Package:
    """
    Basic representation of a requirement. Holds the requirement name.
    """

    name: str
    version: Optional[str]

    def __str__(self):
        if self.version:
            return f"{self.name}-{self.version} {self.specifier}"
        return f"{self.name} {self.specifier}"


@dataclass(unsafe_hash=True)
class PinnedPackage(Package):
    """
    A requirement specification, including also the version specifiers.
    """

    specifier: Specifier

    def __post_init__(self):
        if self.version:
            version = parse(self.version)
            if version not in self.specifier:
                raise BrokenVersionSpecifier(self.version, str(self.specifier))

    def __str__(self):
        if self.version:
            return f"{self.name}-{self.version} {self.specifier}"
        return f"{self.name} {self.specifier}"

    @classmethod
    def make(cls, name: str, version: str, specifier: str):
        return cls(name=name, version=version, specifier=Specifier(specifier))

    @classmethod
    def make_from_specifier(cls, name: str, specifier: str):
        spec = Specifier(specifier)
        return cls(name=name, version=spec.version, specifier=spec)


class Constraint:
    """
    A global constraint that can be used to ensure a Package is in the valid format or to solve a dependency given
    some conditions.
    """

    def __init__(self, pkg_name: str, constraint_description: str):
        self.__pkg_name: str = pkg_name
        self.__constraint_specifications = SpecifierSet(constraint_description.split(" ")[0])

    @property
    def pkg_name(self) -> str:
        return self.__pkg_name

    def ensure(self, pkg: Package) -> bool:
        if pkg.version:
            return pkg.version in self.__constraint_specifications and self.__pkg_name == pkg.name
        else:
            return False
