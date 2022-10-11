import sys
import threading
from typing import Any, Dict, Optional

from sxm_tmk.core.out.type import BackEndBase


class TTYBackEnd(BackEndBase):
    def __init__(self):
        super(TTYBackEnd, self).__init__()
        self._cache["progress"] = TTYProgress
        self._cache["status"] = TTYStatus
        self.__lock = threading.Lock()

    def write(self, message: str) -> None:
        try:
            self.__lock.acquire()
            sys.stdout.write(message + "\n")
        finally:
            self.__lock.release()

    def info(self, msg: str, indent: Optional[str] = None) -> None:
        try:
            self.__lock.acquire()
            sys.stdout.write(f'{indent or ""}{msg}\n')
        finally:
            self.__lock.release()

    def debug(self, msg: str, indent: Optional[str] = None) -> None:
        try:
            self.__lock.acquire()
            sys.stdout.write(f'{indent or ""}{msg}\n')
        finally:
            self.__lock.release()

    def error(self, msg: str, indent: Optional[str] = None) -> None:
        try:
            self.__lock.acquire()
            sys.stdout.write(f'error: {indent or ""}{msg}\n')
        finally:
            self.__lock.release()

    def warning(self, msg: str, indent: Optional[str] = None) -> None:
        try:
            self.__lock.acquire()
            sys.stdout.write(f'warning: {indent or ""}{msg}\n')
        finally:
            self.__lock.release()

    def build_status(self, message) -> Any:
        return self.build("status", self, message)

    def build_progress(self) -> Any:
        return self.build("progress", self)


class TTYProgress:
    class TTYTask:
        def __init__(self, name: str, total: float):
            self.name = name
            self.current = 0.0
            self.last_level = 0.0
            self.total = total

    def __init__(self, backend, task_group_name: Optional[str] = None):
        self.__be = backend
        self.__group_name = task_group_name
        self.__tasks: Dict[str, TTYProgress.TTYTask] = {}

    def add_task(self, name: str, total: float) -> TTYTask:
        self.__tasks[name] = TTYProgress.TTYTask(name, total)
        return self.__tasks[name]

    def update(self, task: TTYTask, advance):
        self.__tasks[task.name].current = min(self.__tasks[task.name].total, self.__tasks[task.name].current + advance)
        current_step_lvl = 100 * self.__tasks[task.name].current / self.__tasks[task.name].total
        if current_step_lvl - self.__tasks[task.name].last_level >= 10:
            self.__tasks[task.name].last_level = current_step_lvl
            self.__be.write(f"  {task.name} ({current_step_lvl:03.1f} %)")

    def start(self):
        if self.__group_name:
            self.__be.write(f"Starting {self.__group_name}")

    def stop(self):
        if self.__group_name:
            self.__be.write(f"Ending {self.__group_name}")

    def __enter__(self):
        self.start()

    def __exit__(self, exc, tb, value):
        self.stop()


class TTYStatus:
    def __init__(self, backend, message: str):
        self.__be = backend
        self.__msg = message

    def __enter__(self):
        self.__be.write(self.__msg)

    def __exit__(self, exc, tb, value):
        pass
