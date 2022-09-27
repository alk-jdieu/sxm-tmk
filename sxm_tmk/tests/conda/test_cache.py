import datetime
import subprocess
import tempfile

import mock.mock
import pytest
import ujson

from sxm_tmk.core.conda.cache import CondaCache


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
    a_cache.clean()
    mock_expiry_time.assert_called()
    assert "something" not in a_cache


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
    with cache:
        cache.store("something", ujson.dumps(dict(stuff=dict(pkg_name="something", version="1.0.0"))))
    sys.exit(0)
        """
        )
    with a_cache:
        process = subprocess.Popen(["python", a_temp_file])
        assert "something" not in a_cache
        with pytest.raises(subprocess.TimeoutExpired):
            process.communicate(timeout=1)
        now = datetime.datetime.now().timestamp()
    process.communicate(timeout=1)
    assert process.returncode == 0
    assert "something" in a_cache
    assert now < a_cache.get("something")["sxm_tmk"]["query_date"]
