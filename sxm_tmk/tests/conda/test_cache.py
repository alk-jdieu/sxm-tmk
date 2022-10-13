import datetime
import subprocess
import sys
import tempfile

import mock.mock
import pytest
import ujson

from sxm_tmk.core.conda.cache import CondaCache


@mock.patch("sxm_tmk.core.conda.file_lock_wrapper.create_lock_file")
def test_ensure_condacache_do_not_lock_upon_init(create_lock_file_mock, tmp_path):
    create_lock_file_mock.return_value = mock.MagicMock()
    CondaCache(tmp_path)
    create_lock_file_mock.return_value.acquire.assert_not_called()
    create_lock_file_mock.return_value.release.assert_not_called()


@mock.patch("sxm_tmk.core.conda.file_lock_wrapper.create_lock_file")
def test_ensure_locked_call_for_method_contains(create_lock_file_mock, tmp_path):
    create_lock_file_mock.return_value = mock.MagicMock()
    a_cache: CondaCache = CondaCache(tmp_path)
    _ = "something" in a_cache
    create_lock_file_mock.return_value.acquire.assert_called_once()
    create_lock_file_mock.return_value.release.assert_called_once()

    create_lock_file_mock.return_value = mock.MagicMock()
    a_cache: CondaCache = CondaCache(tmp_path)
    _ = "something" not in a_cache
    create_lock_file_mock.return_value.acquire.assert_called_once()
    create_lock_file_mock.return_value.release.assert_called_once()


@mock.patch("sxm_tmk.core.conda.file_lock_wrapper.create_lock_file")
def test_ensure_locked_call_for_method_store(create_lock_file_mock, tmp_path):
    create_lock_file_mock.return_value = mock.MagicMock()
    CondaCache(tmp_path).store(
        "something",
        ujson.dumps(
            {
                "stuff": {
                    "pkg_name": "something",
                    "version": "1.0.0",
                },
            }
        ),
    )
    create_lock_file_mock.return_value.acquire.assert_called_once()
    create_lock_file_mock.return_value.release.assert_called_once()


@mock.patch("sxm_tmk.core.conda.file_lock_wrapper.create_lock_file")
def test_ensure_locked_call_for_method_clean(create_lock_file_mock, tmp_path):
    create_lock_file_mock.return_value = mock.MagicMock()
    CondaCache(tmp_path).clean()
    create_lock_file_mock.return_value.acquire.assert_called_once()
    create_lock_file_mock.return_value.release.assert_called_once()


@mock.patch("sxm_tmk.core.conda.file_lock_wrapper.create_lock_file")
def test_ensure_locked_call_for_method_get(create_lock_file_mock, tmp_path):
    create_lock_file_mock.return_value = mock.MagicMock()
    CondaCache(tmp_path).get("something")
    create_lock_file_mock.return_value.acquire.assert_called_once()
    create_lock_file_mock.return_value.release.assert_called_once()


def test_cache(tmp_path):
    a_cache: CondaCache = CondaCache(tmp_path)
    assert "something" not in a_cache
    a_cache.store(
        "something",
        ujson.dumps(
            {
                "stuff": {
                    "pkg_name": "something",
                    "version": "1.0.0",
                },
            }
        ),
    )
    assert "something" in a_cache
    value = a_cache.get("something")
    assert "sxm_tmk" in value
    assert "query_date" in value["sxm_tmk"]
    del value["sxm_tmk"]
    assert value == {
        "stuff": {
            "pkg_name": "something",
            "version": "1.0.0",
        }
    }


@mock.patch("sxm_tmk.core.conda.cache.compute_expiry_time", return_value=datetime.datetime.now().timestamp() + 100)
def test_cache_expiry(mock_expiry_time, tmp_path):
    a_cache: CondaCache = CondaCache(tmp_path)
    a_cache.store("something", ujson.dumps({"stuff": {"pkg_name": "something", "version": "1.0.0"}}))
    assert "something" in a_cache
    mock_expiry_time.assert_not_called()
    result = a_cache.clean()
    mock_expiry_time.assert_called_once_with(False)
    assert "something" not in a_cache
    assert result["deleted"] == 1
    assert 90 < result["space-claimed"] < 100


def test_cache_expiry_force_now(tmp_path):
    a_cache: CondaCache = CondaCache(tmp_path)
    a_cache.store("something", ujson.dumps({"stuff": {"pkg_name": "something", "version": "1.0.0"}}))
    assert "something" in a_cache
    result = a_cache.clean()
    assert result["deleted"] == 0
    assert result["space-claimed"] == 0
    assert "something" in a_cache
    result = a_cache.clean(now=True)
    assert "something" not in a_cache
    assert result["deleted"] == 1
    assert 90 < result["space-claimed"] < 100


def test_cache_lock(tmp_path):
    a_cache: CondaCache = CondaCache(tmp_path)
    a_temp_file = tempfile.mktemp()
    with open(a_temp_file, "w") as f:
        f.write(
            f"""
import pathlib
import sys
import ujson
from sxm_tmk.core.conda.cache import CondaCache

if __name__ == "__main__":
    cache = CondaCache(pathlib.Path("{tmp_path.as_posix()}"))
    cache.store("something", ujson.dumps(dict(stuff=dict(pkg_name="something", version="1.0.0"))))
    sys.exit(0)
"""
        )
    a_cache.acquire(-1)
    process = subprocess.Popen([sys.executable, a_temp_file])
    assert "something" not in a_cache
    with pytest.raises(subprocess.TimeoutExpired):
        process.communicate(timeout=1)
    now = datetime.datetime.now().timestamp()
    a_cache.release()
    process.communicate(timeout=1)
    assert process.returncode == 0
    assert "something" in a_cache
    assert now < a_cache.get("something")["sxm_tmk"]["query_date"]
