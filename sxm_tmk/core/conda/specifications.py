import pathlib
from typing import List

from pydantic import BaseModel, Field

from sxm_tmk.core.types import Packages


class Conda(BaseModel):
    channels: List[str] = Field(default=[])
    packages: Packages = Field(default=[])

    def __init__(self, **data):
        super(Conda, self).__init__(**data)
        conda_forge = "https://conda.anaconda.org/conda-forge"
        if conda_forge not in self.channels:
            self.channels.insert(0, "https://conda.anaconda.org/conda-forge")


class Pip(BaseModel):
    packages: Packages = Field(default=[])
    extra_indexes: List[str] = Field(default=[])


class Environment(BaseModel):
    name: str
    conda: Conda = Field(default=Conda())
    pip: Pip = Field(default=Pip())

    def write_as_yaml(self, path: pathlib.Path) -> None:
        with path.open("w") as f:
            f.write(f"name: {self.name}\n")
            f.write("channels:\n")
            for c in self.conda.channels:
                f.write(f" - {c}\n")

            f.write("dependencies:\n")
            for p in sorted([pkg.format_conda() for pkg in self.conda.packages]):
                f.write(f" - {p}\n")

            if self.pip.packages:
                if not any((pkg.name == "pip" for pkg in self.conda.packages)):
                    f.write(" - pip\n")
                f.write(" - pip:\n")
                for url in self.pip.extra_indexes:
                    f.write(f"   - --extra-index-url {url}\n")
                for p in sorted([pkg.format_pip() for pkg in self.pip.packages]):
                    f.write(f"   - {p}\n")
