# -*- coding: utf-8 -*-

from threading import Thread
from typing import Optional

from src.base.executable_base import ExecutableBase


"""
HandleThread用于启动一个线程，用于处理某些组件需要使用线程运行，通过线程来运行同步阻塞任务。
"""

class HandleThread(object):
    def __init__(self, executable: ExecutableBase):
        self.executable = executable
        self.thread: Optional[Thread] = None
        self.daemon = True

    def _setup_thread(self):
        if not self.thread:
            self.thread = Thread(None, self._run, f"Thread <{self.executable.get_name()}>", daemon=self.daemon)

    def set_daemon(self, daemon: bool):
        self.daemon = daemon

    def get_daemon(self):
        return self.daemon

    def _run(self):
        if self.executable.is_running():
            raise RuntimeError(f"Executable item {self.executable.get_name()} is already running!")
        self.executable.exec()

    def start(self):
        if not self.thread:
            self._setup_thread()
        if not self.thread.is_alive():
            self.thread.start()

    def join(self, timeout: Optional[float] = None):
        self.executable.stop()
        self.thread.join(timeout=timeout)

    def get_executable(self):
        return self.executable
