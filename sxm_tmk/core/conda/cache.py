import datetime
import pathlib
from typing import Optional

import ujson
from filelock import FileLock

CACHE_DIR: pathlib.Path = pathlib.Path.home() / ".sxm_tmk" / "conda_query_cache"


def compute_expiry_time() -> float:
    now = datetime.datetime.now() - datetime.timedelta(days=1)
    return now.timestamp()


class CondaCache:
    def __init__(self, cache_dir: Optional[pathlib.Path] = None):
        self.__cache_dir = cache_dir or CACHE_DIR
        if not self.__cache_dir.exists():
            self.__cache_dir.mkdir(parents=True, exist_ok=True)
        lock_file = self.__cache_dir / "tmk.lock"
        lock_file.touch(exist_ok=True)
        self.__lock = FileLock(lock_file.as_posix())

    def __enter__(self):
        self.__lock.acquire(timeout=-1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__lock.release()

    def clean(self):
        xpire_time = compute_expiry_time()
        delete_file = None
        for pkg_file_query in self.__cache_dir.iterdir():
            if delete_file is not None:
                delete_file.unlink()
            if pkg_file_query.suffix == ".json":
                data = ujson.loads(pkg_file_query.read_text())
                try:
                    delete_file = pkg_file_query if data["sxm_tmk"]["query_date"] < xpire_time else None
                except KeyError:
                    delete_file = pkg_file_query
        if delete_file is not None:
            delete_file.unlink()

    def store(self, pkg: str, content: str):
        pkg_file = self.__cache_dir / f"{pkg}.json"
        if pkg_file.exists():
            pkg_file.unlink()
        json_data = ujson.loads(content)
        json_data["sxm_tmk"] = {"query_date": datetime.datetime.now().timestamp()}
        with pkg_file.open("w") as f:
            ujson.dump(json_data, f)

    def __contains__(self, item):
        return (self.__cache_dir / f"{item}.json").exists()

    def get(self, item):
        item_path: pathlib.Path = self.__cache_dir / f"{item}.json"
        if item_path.exists():
            return ujson.loads(item_path.read_text())
        return None
