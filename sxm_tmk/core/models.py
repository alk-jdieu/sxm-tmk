import enum
from typing import Dict

from sxm_tmk.core.dependency import Dependency

DictOfDeps = Dict[str, Dependency]


class InstallMode(enum.Enum):
    DEFAULT = "default"
    DEV = "develop"
