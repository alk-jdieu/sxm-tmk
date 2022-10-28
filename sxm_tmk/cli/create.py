import datetime
import pathlib
from typing import Optional

import yaml

from sxm_tmk.core.bash import BashScript, ExecutionDir
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
    create_parser.add_argument("--debug", action="store_true", help="Print internal script statement when run.")
    create_parser.set_defaults(func=main)


def _run_step(step_msg: str, running_msg: str, script: BashScript, execution_dir: ExecutionDir) -> bool:
    status = Terminal().new_status(running_msg)
    with status, execution_dir:
        succeeded = script.run() == 0
    Terminal().step(step_msg, succeeded)
    return succeeded


def _dump_step(script: BashScript, use_section: Optional[Section] = None) -> None:
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


def _create_env(spec_path: pathlib.Path, env_name: str, echo_statements: bool = True) -> int:
    create_env: BashScript = BashScript(
        [f"mamba env create -f {spec_path.as_posix()}"],
        name=f'{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}_create_{env_name}.sh',
        echo_statement=echo_statements,
    )
    Terminal().info(f'Using specification "{spec_path.as_posix()}"')
    exec_dir = ExecutionDir(use_tempdir=False, force_dir=spec_path.parent)
    if not _run_step(
        f"Environment created ({env_name})",
        f"Installing your project into environment [{env_name}]",
        create_env,
        exec_dir,
    ):
        explain = Section()
        Terminal().info(f"Environment creation failed with rc [{create_env.return_code}]")
        _dump_step(create_env, use_section=explain)
    return create_env.return_code


def _install_in_env(project_root: pathlib.Path, env_name: str, echo_statements: bool = True) -> int:
    install_in_env: BashScript = BashScript(
        [
            'conda_root=$(conda config --show root_prefix | sed "s|.*: ||")',
            "init_script=${conda_root##*( )}/etc/profile.d/conda.sh",
            "source ${init_script}",
            f"conda activate {env_name}",
            "python -m pip install -e .",
        ],
        name=f'{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}_install_{env_name}.sh',
        echo_statement=echo_statements,
    )
    exec_dir = ExecutionDir(use_tempdir=False, force_dir=project_root)
    if not _run_step(
        "Installed in environment",
        f"Installing project {project_root.name} into environment [{env_name}]",
        install_in_env,
        exec_dir,
    ):
        rc: int = install_in_env.return_code
        explain: Section = Section()
        Terminal().info(f"Installing {project_root.name} in environment {env_name} failed with rc [{rc}]")
        _dump_step(install_in_env, use_section=explain)
    return install_in_env.return_code


def main(options):
    Terminal("rich")
    try:
        with options.spec.open("r") as f:
            y = yaml.load(f, yaml.SafeLoader)
        env_name = y["name"]
    except (FileNotFoundError, KeyError):
        Terminal().error("Cannot read environment name")
        return 1

    if 0 != _create_env(options.spec.absolute(), env_name, echo_statements=options.debug):
        return 2

    if 0 != _install_in_env(options.project_path.absolute(), env_name, echo_statements=options.debug):
        return 3
    explain = Section()
    with explain:
        Terminal().info("")
        Terminal().info("# To activate this environment, type")
        Terminal().info(f"  `conda activate {env_name}`")
        Terminal().info("")
        Terminal().info("# To deactivate it, type")
        Terminal().info("   `conda deactivate`")
        Terminal().info("")

    return 0
