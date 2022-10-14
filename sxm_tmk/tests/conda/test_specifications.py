import pathlib

import yaml

from sxm_tmk.core.conda.specifications import Conda, Environment
from sxm_tmk.core.dependency import Package


def test_conda():
    conda = Conda()
    conda.packages.append(Package(name="pydantic", version="1.23.1", build_number=None, build=None))
    conda.packages.append(Package(name="cryptography", version="2.9.2", build_number=None, build=None))

    assert conda.channels == ["https://conda.anaconda.org/conda-forge"]

    conda.channels.append("defaults")
    assert conda.channels == ["https://conda.anaconda.org/conda-forge", "defaults"]


def test_environment_without_pip(tmp_path):
    result_file = tmp_path / "no_pip.yml"
    env_no_pip = Environment(name="test-env")

    env_no_pip.conda.channels.append("defaults")
    env_no_pip.conda.packages.append(Package(name="pydantic", version="1.23.1", build_number=None, build=None))
    env_no_pip.conda.packages.append(Package(name="cryptography", version="2.9.2", build_number=None, build=None))

    env_no_pip.write_as_yaml(result_file)
    assert result_file.exists()

    with result_file.open("r") as f:
        result = yaml.load(f, yaml.SafeLoader)

    assert result == {
        "name": "test-env",
        "channels": ["https://conda.anaconda.org/conda-forge", "defaults"],
        "dependencies": ["cryptography=2.9.2", "pydantic=1.23.1"],
    }


def test_environment_including_pip_packages(tmp_path):
    result_file: pathlib.Path = pathlib.Path(tmp_path) / "with_pip.yml"
    env_with_pip = Environment(name="test-env-pip")

    env_with_pip.conda.channels.append("defaults")
    env_with_pip.conda.packages.append(Package(name="pydantic", version="1.23.1", build_number=None, build=None))
    env_with_pip.conda.packages.append(Package(name="cryptography", version="2.9.2", build_number=None, build=None))

    env_with_pip.pip.extra_indexes.append("https://some_user:some_password@pypi.someorga.com:8443/simple")
    env_with_pip.pip.packages.append(Package(name="alk_web", version="2.8.1", build_number=None, build=None))
    env_with_pip.pip.packages.append(Package(name="alk_core", version="15.3.8", build_number=None, build=None))

    env_with_pip.write_as_yaml(result_file)
    assert result_file.exists()

    with result_file.open("r") as f:
        result = yaml.load(f, yaml.SafeLoader)

    assert result == {
        "name": "test-env-pip",
        "channels": ["https://conda.anaconda.org/conda-forge", "defaults"],
        "dependencies": [
            "cryptography=2.9.2",
            "pydantic=1.23.1",
            "pip",
            {
                "pip": [
                    "--extra-index-url https://some_user:some_password@pypi.someorga.com:8443/simple",
                    "alk_core==15.3.8",
                    "alk_web==2.8.1",
                ]
            },
        ],
    }
