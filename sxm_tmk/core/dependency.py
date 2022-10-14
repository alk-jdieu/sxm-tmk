from dataclasses import dataclass
from typing import Optional

import packaging.specifiers
from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version, parse

ALPHA = "abcdefghijklmnopqrstuvwxyz"
OPERATOR_BOUNDARY = [">=", "<=", "==", "~=", "!="]
OPERATOR_BOUNDARY_STRICT = ["<", ">", "="]


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


def clean_version(version: str) -> str:
    if any((version.startswith(this_op) for this_op in OPERATOR_BOUNDARY)):
        version = version[2:]
    elif any((version.startswith(this_op) for this_op in OPERATOR_BOUNDARY_STRICT)):
        version = version[1:]

    try:
        index = ALPHA.index(version[-1].lower())
    except ValueError:
        return version
    return f"{version[:-1]}.{str(index + 1)}"


def _canonicalize_specifier(specifier: str):
    if any((specifier.startswith(this_op) for this_op in OPERATOR_BOUNDARY)):
        op = specifier[0:2]
    elif any((specifier.startswith(this_op) for this_op in OPERATOR_BOUNDARY_STRICT)):
        op = specifier[0]
    else:
        op = "=="
    try:
        index = ALPHA.index(specifier[-1].lower())
    except ValueError:
        return specifier
    return f"{op}{specifier[len(op):-1]}.{str(index + 1)}"


def _canonicalize_specifier_set(specifiers: str):
    spec_set = specifiers.split(",")
    return ",".join((_canonicalize_specifier(spec) for spec in spec_set))


@dataclass(unsafe_hash=True)
class Package:
    """
    Basic representation of a requirement. Holds the requirement name.
    """

    name: str
    version: Optional[str]
    build_number: Optional[int]
    build: Optional[str]

    def parse_version(self) -> Version:  # type: ignore
        this_version = clean_version(self.version or "0.0.0")
        version = parse(this_version)
        if not isinstance(version, Version):
            raise InvalidVersion(self.version)
        return version

    def compare_key(self):
        if self.version is not None and self.build_number is not None:
            return self.parse_version(), self.build_number
        elif self.version is not None and self.build_number is None:
            return self.parse_version()
        elif self.version is None and self.build_number is not None:
            return self.build_number
        else:
            raise NotComparablePackage(self.name)

    def format_conda(self) -> str:
        if self.version is not None:
            return f"{self.name}={self.version}"
        return self.name

    def format_pip(self) -> str:
        if self.version is not None:
            return f"{self.name}=={self.version}"
        return self.name


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

    @classmethod
    def make(cls, name: str, version: str, specifier: str):
        return cls(name=name, version=version, build_number=None, build=None, specifier=Specifier(specifier))

    @classmethod
    def from_specifier(cls, name: str, version: Optional[str], specifier: str):
        specifier = _canonicalize_specifier(specifier)
        spec = Specifier(specifier)
        return cls(name=name, version=version, build_number=None, build=None, specifier=spec)

    def format_conda(self) -> str:
        return f"{self.name}{self.specifier}"


class Constraint:
    """
    A global constraint that can be used to ensure a Package is in the valid format or to solve a dependency given
    some conditions.
    """

    def __init__(self, pkg_name: str, constraint_description: str):
        self.__pkg_name: str = pkg_name
        try:
            self.__constraint_specifications = SpecifierSet(constraint_description.split(" ")[0])
        except packaging.specifiers.InvalidSpecifier:
            raise InvalidConstraintSpecification(constraint_description.split(" ")[0])

    def __repr__(self):
        return f"{self.__pkg_name} | {self.__constraint_specifications}"

    @property
    def pkg_name(self) -> str:
        return self.__pkg_name

    def ensure(self, pkg: Package) -> bool:
        if pkg.version:
            pkg_version = pkg.parse_version()
            return pkg_version in self.__constraint_specifications and self.__pkg_name == pkg.name
        else:
            return False

    @classmethod
    def from_conda_depends(cls, depends_on: str):
        depends_on_part = depends_on.split(" ")
        if len(depends_on_part) < 2:
            raise InvalidConstraintSpecification(depends_on)

        depends_on_part[1] = _canonicalize_specifier_set(depends_on_part[1])
        spec_set = depends_on_part[1].split(",")
        has_operators = [any(spec.startswith(op) for op in ("=", ">", "<")) for spec in spec_set]
        for i, has_operator in enumerate(has_operators):
            if not has_operator:
                spec_set[i] = f"=={spec_set[i]}"

        return cls(depends_on_part[0], ",".join(spec_set))
