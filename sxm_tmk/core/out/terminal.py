from typing import Optional

from sxm_tmk.core.out.classic import TTYBackEnd
from sxm_tmk.core.out.devnull import NullBackEnd
from sxm_tmk.core.out.rich_term import RichBackEnd
from sxm_tmk.core.out.type import Singleton


def build_backend(backend):
    return {"rich": RichBackEnd, "tty": TTYBackEnd, "null": NullBackEnd}[backend]()


class Terminal(metaclass=Singleton):
    def __init__(self, backend="null"):
        self.__backend = build_backend(backend)
        self.__tab = 0

    def write(self, message: str):
        self.__backend.write(message)

    def info(self, msg):
        self.__backend.info(msg, self.tab * "  ")

    def debug(self, msg):
        self.__backend.debug(msg, self.tab * "  ")

    def error(self, msg):
        self.__backend.error(msg, self.tab * "  ")

    def warning(self, msg):
        self.__backend.warning(msg, self.tab * "  ")

    def new_progress(self):
        return self.__backend.build_progress()

    def new_status(self, message: str):
        return self.__backend.build_status(message)

    @property
    def tab(self):
        return self.__tab

    @tab.setter
    def tab(self, value):
        self.__tab = value

    def step(self, message: str, status: bool):
        self.__backend.step(message, status, self.tab * "  ")


class Section:
    def __enter__(self):
        Terminal().tab = Terminal().tab + 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        Terminal().tab = Terminal().tab - 1


class Progress:
    class Task:
        def __init__(self, name, tid, pb):
            self.name = name
            self.tid = tid
            self.pb = pb

        def update(self, count: Optional[float] = 1):
            self.pb.update(self, count)

    def __init__(self, task_group_name: str):
        self.__progress_bar = Terminal().new_progress()
        self.__group_name = task_group_name

    def add_task(self, name: str, total: float) -> Task:
        tid = self.__progress_bar.add_task(name, total=total)
        return Progress.Task(name, tid, self)

    def update(self, task: Task, count):
        self.__progress_bar.update(task.tid, advance=count)

    def __enter__(self):
        if self.__group_name:
            Terminal().info(f"Starting '{self.__group_name}'")
        self.__progress_bar.start()

    def __exit__(self, exc, tb, value):
        self.__progress_bar.stop()
        if self.__group_name:
            Terminal().info(f"Ending '{self.__group_name}'")


class Status:
    def __init__(self, message: str):
        self.__msg = message
        self.__s = Terminal().new_status(message)

    def __enter__(self):
        self.__s.start()

    def __exit__(self, exc, tb, value):
        self.__s.stop()
        Terminal().info(self.__msg)


#
# if __name__ == "__main__":
#     from sys import argv
#     from time import sleep
#
#     try:
#         Terminal(argv[1])
#     except IndexError:
#         Terminal("rich")
#
#     def show_progress():
#         p = Progress("A set of 1 task")
#         with p:
#             task = p.add_task("my task", 150)
#             for _ in range(150):
#                 task.update(1)
#                 sleep(0.01)
#
#     def show_m_progress():
#         p = Progress("A set of 3 tasks")
#         with p:
#             task1 = p.add_task("task1", 200)
#             task2 = p.add_task("task2", 50)
#             task3 = p.add_task("task3", 100)
#             for _ in range(200):
#                 task1.update(1)
#                 task2.update(2.5)
#                 task3.update(0.8)
#                 sleep(0.01)
#
#     s = Terminal().new_status("Collecting data")
#     with s:
#         sleep(1.5)
#     #    show_progress(TTYTerminal())
#     show_progress()
#     #    show_m_progress(TTYTerminal())
#     show_m_progress()
#
#     Terminal().debug("This is a DEBUG")
#     Terminal().info("This is an INFO")
#     Terminal().warning("This is a WARNING")
#     Terminal().error("This is an ERROR")
#
#     with Section():
#         Terminal().info("Section level 1")
#         with Section():
#             Terminal().info("Section level 2")
#             with Section():
#                 Terminal().info("Section level 3")
#                 with Section():
#                     Terminal().info("Section level 4")
#                     with Section():
#                         Terminal().info("Section level 5")
#     Terminal().info("Section level 0")
#
#     Terminal().step_status("Test KO", False)
#     Terminal().step_status("Test OK", True)
