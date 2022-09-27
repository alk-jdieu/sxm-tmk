import operator
from dataclasses import dataclass, field
from typing import Iterable, List, Protocol, Tuple, Union

VersionType = Tuple[Union[int, str], ...]


class ConstraintValidator(Protocol):
    def __call__(self, left: VersionType, right: VersionType) -> bool:
        pass


def constraint_eq(left: VersionType, right: VersionType) -> bool:
    return operator.eq(left, right)


def constraint_gt(left: VersionType, right: VersionType) -> bool:
    return operator.gt(left, right)


def constraint_ge(left: VersionType, right: VersionType) -> bool:
    return operator.ge(left, right)


def constraint_le(left: VersionType, right: VersionType) -> bool:
    return operator.le(left, right)


def constraint_lt(left: VersionType, right: VersionType) -> bool:
    return operator.lt(left, right)


@dataclass
class Dependency:
    pkg: str
    version: str

    def __post_init__(self):
        if any((self.version.startswith("=="), self.version.startswith(">="), self.version.startswith("<="))):
            self.version = self.version[2:]
        elif self.version.startswith(">") or self.version.startswith("<"):
            self.version = self.version[1:]

    @property
    def version_tuple(self) -> VersionType:
        return tuple(self.version.split("."))

    def __str__(self):
        return f"{self.pkg}-{self.version}"

    def __eq__(self, other):
        if isinstance(other, Dependency):
            return str(self) == str(other)
        raise NotImplementedError()


@dataclass
class Constraint:
    version: str
    validator: ConstraintValidator = field(default=constraint_eq)

    def __post_init__(self):
        if self.version.startswith("=="):
            self.version = self.version[2:]
        if self.version.startswith(">="):
            self.version = self.version[2:]
            self.validator = constraint_ge
        if self.version.startswith("<="):
            self.version = self.version[2:]
            self.validator = constraint_le
        if self.version.startswith(">"):
            self.version = self.version[1:]
            self.validator = constraint_gt
        if self.version.startswith("<"):
            self.version = self.version[1:]
            self.validator = constraint_lt

    def match(self, dependency: Dependency) -> bool:
        return self.validator(dependency.version_tuple, self.version_tuple)

    @property
    def version_tuple(self):
        return tuple(self.version.split("."))


@dataclass
class DependencyChecker:
    reference_pkg: str
    checker: Constraint

    def match(self, proposal: Dependency) -> bool:
        return self.reference_pkg == proposal.pkg and self.checker.match(proposal)

    def filter_matching_propositions(self, proposals: List[Dependency]) -> Iterable[Dependency]:
        return filter(lambda dep: self.reference_pkg == dep.pkg and self.checker.match(dep), proposals)
