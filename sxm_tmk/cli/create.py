import datetime
import pathlib
from typing import Callable, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

from sxm_tmk.core.bash import BashScript, ExecutionDir
from sxm_tmk.core.conda.commands import MambaEnv
from sxm_tmk.core.out.terminal import Section, Terminal


def setup(subparser):
    create_parser = subparser.add_parser(name="create")
    create_parser.add_argument("spec", type=pathlib.Path, help="Path to the project specification (conda format).")
    create_parser.add_argument(
        "--project-path",
        type=pathlib.Path,
        default=pathlib.Path.cwd(),
        help="Path to the project root (for installation only).",
    )
    create_parser.add_argument("--keep", "-k", action="store_true", help="Keep generated script files.")
    create_parser.add_argument("--debug", action="store_true", help="Print internal script statement when run.")
    create_parser.set_defaults(func=main)


class EnvironmentMaker:
    class StepInfo(BaseModel):
        exec_dir: pathlib.Path
        fail_msg: str
        run_msg: str
        step_msg: str
        step_name: str

    class Step(StepInfo):
        script: Optional[List[str]] = Field(min_length=1)
        call: Optional[Callable[[str], bool]] = None

    def __init__(
        self,
        project_path: pathlib.Path,
        specification_file: pathlib.Path,
        debug: bool = False,
        keep_files: Optional[bool] = False,
    ):
        self.__project_root_path = project_path
        self.__specification_path = specification_file
        self.__debug = debug
        self.__keep_files = keep_files
        self.__steps: Dict[str, EnvironmentMaker.Step] = {}
        self.__environment_name: str = ""

    @property
    def env_name(self) -> str:
        return self.__environment_name

    def _run_script(self, now: str, step: Step) -> bool:
        script: BashScript = BashScript(
            script=step.script,  # type: ignore
            name=f"{now}_{step.step_name}_{self.env_name}.sh",
            echo_statement=self.__debug,
        )
        rc = script.run() == 0
        if not self.__keep_files:
            script.unlink()
        if not rc:
            explain = Section()
            Terminal().error("\n" + step.fail_msg)
            self._dump_step(script, use_section=explain)
            Terminal().info(f"Environment creation failed with rc [{script.return_code}]")
        return rc  # noqa R504

    def _run_callable(self, step: Step) -> bool:
        rc = step.call(self.env_name)  # type: ignore
        if not rc:
            Terminal().error("\n" + step.fail_msg)
        return rc

    def _run(self, step_id: str) -> bool:
        now: str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        step_info: EnvironmentMaker.Step = self.__steps[step_id]

        status = Terminal().new_status(step_info.run_msg)
        execution_dir = ExecutionDir(use_tempdir=False, force_dir=step_info.exec_dir)
        with status, execution_dir:
            if step_info.script is not None:
                succeeded = self._run_script(now, step_info)
            else:
                succeeded = self._run_callable(step_info)
        Terminal().step(step_info.step_msg, succeeded)
        return succeeded

    def _read_environment_name(self) -> bool:
        try:
            with self.__specification_path.open("r") as f:
                y = yaml.load(f, yaml.SafeLoader)
            self.__environment_name = y["name"]
        except (FileNotFoundError, KeyError):
            Terminal().error(f"Cannot read environment name. Please check your {self.__specification_path.name} file")
            return False
        return True

    def _prepare_steps(self):
        check_step = EnvironmentMaker.Step(
            exec_dir=self.__specification_path.parent,
            fail_msg=f"This environment ({self.env_name}) already exists. "
            f"You must remove it prior to launch this command.",
            run_msg="Checking if an environment already exists",
            step_msg="Environment available",
            step_name="check",
            call=lambda env_name: MambaEnv().exists(env_name),
        )
        create_step = EnvironmentMaker.Step(
            exec_dir=self.__specification_path.parent,
            fail_msg="Cannot create environment. Try with --debug to get more info",
            run_msg=f"Installing your project into environment [{self.env_name}]",
            script=[f"mamba env create -f {self.__specification_path.as_posix()}"],
            step_msg=f"Environment created ({self.env_name})",
            step_name="create",
        )
        install_step = EnvironmentMaker.Step(
            exec_dir=self.__project_root_path,
            fail_msg=f"Cannot install {self.__project_root_path.name} in environment {self.env_name}."
            f" Try with --debug for more info",
            run_msg=f"Installing project {self.__project_root_path.name} into environment [{self.env_name}]",
            script=[
                'conda_root=$(conda config --show root_prefix | sed "s|.*: ||")',
                "init_script=${conda_root##*( )}/etc/profile.d/conda.sh",
                "source ${init_script}",
                f"conda activate {self.env_name}",
                "python -m pip install -e .",
            ],
            step_msg="Installed in environment",
            step_name="install",
        )
        self.__steps[check_step.step_name] = check_step
        self.__steps[create_step.step_name] = create_step
        self.__steps[install_step.step_name] = install_step

    def create(self) -> int:
        if not self._read_environment_name():
            return 1
        self._prepare_steps()
        for rc_fail, (step, method) in enumerate(
            [
                ("check", self._check_environment),
                ("create", self._create_environment),
                ("install", self._install_in_env),
            ]
        ):
            method()
            success = self._run(step)
            if not success:
                return rc_fail + 2
        return 0

    def _check_environment(self):
        Terminal().info(f"Checking that {self.env_name} can be created")

    def _create_environment(self):
        Terminal().info(f'Using specification "{self.__specification_path.as_posix()}"')

    def _install_in_env(self):
        Terminal().info(f"Proceeding to installation in {self.env_name}.")

    def _dump_step(self, script: BashScript, use_section: Optional[Section] = None) -> None:
        if self.__debug:
            out = len(list(filter(lambda line: line, script.stdout)))
            if out:
                Terminal().info("----------- Output log -----------")
                if use_section:
                    with use_section:
                        Terminal().info("\n".join(script.stdout))
            err = len(list(filter(lambda line: line, script.stderr)))
            if err:
                Terminal().info("----------- Error log -----------")
                if use_section:
                    with use_section:
                        Terminal().info("\n".join(script.stderr))
            if not err and not out:
                Terminal().error("~~~~~~~~~~~ No log can be found ~~~~~~~~~~~")


def main(options):
    Terminal("rich")
    env = EnvironmentMaker(
        project_path=options.project_path,
        specification_file=options.spec,
        debug=options.debug,
        keep_files=False,
    )
    result = env.create()
    if result == 0:
        explain = Section()
        with explain:
            Terminal().info("")
            Terminal().info("# To activate this environment, type")
            Terminal().info(f"  `conda activate {env.env_name}`")
            Terminal().info("")
            Terminal().info("# To deactivate it, type")
            Terminal().info("   `conda deactivate`")
            Terminal().info("")
    return result
