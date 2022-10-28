import pathlib

from sxm_tmk.core.bash import ExecutionDir


def test_with_force_dir_it_changes_the_cwd_and_then_restore_to_previous_path(tmpdir):
    root = pathlib.Path.cwd()
    subdir = pathlib.Path(tmpdir) / "subdir"

    xd = ExecutionDir(use_tempdir=False, force_dir=subdir)
    assert pathlib.Path.cwd() == root
    with xd:
        assert pathlib.Path.cwd() == subdir
    assert pathlib.Path.cwd() == root


def test_with_tempdir_it_changes_the_cwd_and_then_restore_to_previous_path():
    root = pathlib.Path.cwd()

    xd = ExecutionDir(use_tempdir=True)
    assert pathlib.Path.cwd() == root
    with xd:
        assert pathlib.Path.cwd() != root
    assert pathlib.Path.cwd() == root
