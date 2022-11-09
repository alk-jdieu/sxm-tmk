import pathlib

from sxm_tmk.core.bash import BashScript


def test_bash_script_runs_correctly(bash_script_cleaner):
    sh = BashScript(['echo "Hello World"'], name=bash_script_cleaner)
    assert sh.run() == 0
    assert sh.return_code == 0
    assert sh.stdout == ["Hello World", ""]
    assert sh.stderr == [""]
    assert sh.has_completed


def test_bash_script_ends_nicely_on_timeout(bash_script_cleaner):
    sh = BashScript(["sleep 5", 'echo "Shall not be seen"'], name=bash_script_cleaner)
    assert sh.run(timeout=1) == 100
    assert sh.stdout == [""]
    assert sh.stderr == ["Timed out", ""]
    assert not sh.has_completed


def test_bash_script_exit_on_first_error(bash_script_cleaner):
    sh = BashScript(['echo "Falsy" && false', 'echo "Shall not be seen"'], name=bash_script_cleaner, exit_on_error=True)
    assert sh.run() == 1
    assert sh.stdout == ["Falsy", ""]
    assert sh.stderr == [""]
    assert sh.has_completed


def test_bash_script_echoes_command(bash_script_cleaner):
    sh = BashScript(
        ['echo "Truthy"', 'echo "Shall be seen"'], name=bash_script_cleaner, exit_on_error=False, echo_statement=True
    )
    assert sh.run() == 0
    assert sh.stdout == ["Truthy", "Shall be seen", ""]
    assert sh.stderr == ["+ echo Truthy", "+ echo 'Shall be seen'", ""]
    assert sh.has_completed


def test_bash_script_exit_on_first_error_and_echoes(bash_script_cleaner):
    sh = BashScript(
        ['echo "Falsy" && false', 'echo "Shall not be seen"'],
        name=bash_script_cleaner,
        exit_on_error=True,
        echo_statement=True,
    )
    assert sh.run() == 1
    assert sh.stdout == ["Falsy", ""]
    assert sh.stderr == ["+ echo Falsy", "+ false", ""]
    assert sh.has_completed


def test_reset_only_reset_state(bash_script_cleaner):
    sh = BashScript(
        ['echo "Falsy" && false', 'echo "Shall not be seen"'],
        name=bash_script_cleaner,
        exit_on_error=True,
        echo_statement=True,
    )
    assert sh.run() == 1
    assert sh.stdout == ["Falsy", ""]
    assert sh.stderr == ["+ echo Falsy", "+ false", ""]
    assert sh.has_completed

    sh.reset()
    assert not sh.stderr
    assert not sh.stdout
    assert not sh.return_code
    assert not sh.has_completed
    assert sh.run() == 1
    assert sh.stdout == ["Falsy", ""]
    assert sh.stderr == ["+ set -xe", "+ echo Falsy", "+ false", ""]
    assert sh.has_completed


def test_script_unlinks_correctly(tmp_path):
    sh = BashScript(
        ['echo "Hello"'],
        name="test.sh",
        exit_on_error=True,
        echo_statement=True,
    )
    assert sh.run() == 0
    sh.unlink()
    path = pathlib.Path(tmp_path) / "test.sh"
    assert not path.exists()
