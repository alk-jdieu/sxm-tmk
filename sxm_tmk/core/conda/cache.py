import datetime
import pathlib
from typing import Optional

import ujson

from sxm_tmk.core.conda.file_lock_wrapper import (
    LockMixin,
    ensure_lock_on_public_interface_call,
)

CACHE_DIR: pathlib.Path = pathlib.Path.home() / ".sxm_tmk" / "conda_query_cache"


def compute_expiry_time() -> float:
    now = datetime.datetime.now() - datetime.timedelta(days=1)
    return now.timestamp()


@ensure_lock_on_public_interface_call()
class CondaCache(LockMixin):
    def __init__(self, cache_dir: Optional[pathlib.Path] = None):
        self.__cache_dir: pathlib.Path = cache_dir or CACHE_DIR
        if not self.__cache_dir.exists():
            self.__cache_dir.mkdir(parents=True, exist_ok=True)
        lock_file_path: pathlib.Path = self.__cache_dir / "tmk.lock"
        lock_file_path.touch(exist_ok=True)
        super().__init__(lock_file_path)

    def clean(self):
        xpire_time = compute_expiry_time()
        delete_file = None
        for pkg_file_query in self.__cache_dir.iterdir():
            if delete_file is not None:
                delete_file.unlink()
                delete_file = None
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

    def __getitem__(self, item):
        return self.get(item)

    def get(self, item):
        item_path: pathlib.Path = self.__cache_dir / f"{item}.json"
        if item_path.exists():
            return ujson.loads(item_path.read_text())
        return None
