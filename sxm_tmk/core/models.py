import enum
from typing import Dict, List

from sxm_tmk.core.dependency import Dependency

DictOfDeps = Dict[str, Dependency]
ListOfDeps = List[Dependency]


class InstallMode(enum.Enum):
    DEFAULT = "default"
    DEV = "develop"
