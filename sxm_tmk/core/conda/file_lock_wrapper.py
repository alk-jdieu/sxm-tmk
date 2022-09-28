import abc
import functools
import pathlib

from filelock import FileLock
from filelock import Timeout as CannotAcquireLock


class AbstractFileLock(abc.ABC):
    def __init__(self, path: pathlib.Path):
        self._file_path = path

    @abc.abstractmethod
    def acquire(self, timeout: int = -1):
        raise NotImplementedError

    @abc.abstractmethod
    def release(self):
        raise NotImplementedError

    @abc.abstractmethod
    def locked(self) -> bool:
        pass


class FSFileLock(AbstractFileLock):
    def __init__(self, path: pathlib.Path):
        super().__init__(path)
        self.__lock_impl = FileLock(path)

    def acquire(self, timeout: int = -1):
        try:
            self.__lock_impl.acquire(timeout=timeout)
        except TimeoutError:
            raise CannotAcquireLock(self._file_path.as_posix())

    def release(self) -> None:
        return self.__lock_impl.release()

    def locked(self) -> bool:
        return self.__lock_impl.is_locked


def create_lock_file(path: pathlib.Path) -> AbstractFileLock:
    return FSFileLock(path)


class LockMixin:
    def __init__(self, path):
        self.__lockfile = create_lock_file(path)

    def acquire(self, timeout=-1):
        self.__lockfile.acquire(timeout)

    def release(self):
        self.__lockfile.release()


def lock_call(func):
    @functools.wraps(func)
    def wrapper(lockable_instance, *args, **kw):
        lockable_instance.acquire()
        try:
            return func(lockable_instance, *args, **kw)
        finally:
            lockable_instance.release()

    return wrapper


def ensure_lock_on_public_interface_call():
    def decorator(cls):
        for name, obj in vars(cls).items():
            ensure_lock_acquired_before_call = False
            if callable(obj):
                ensure_lock_acquired_before_call = True
                if name.startswith("__"):
                    ensure_lock_acquired_before_call = name in ["__contains__", "__getitem__"]
            if ensure_lock_acquired_before_call:
                setattr(cls, name, lock_call(obj))
        return cls

    return decorator
