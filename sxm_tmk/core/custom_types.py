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


class TMKException(Exception):
    def __init__(self, *args):
        super(TMKException, self).__init__(*args)


class TMKLockFileNotFound(TMKException):
    def __init__(self, msg):
        super(TMKLockFileNotFound, self).__init__(msg)
