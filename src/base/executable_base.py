# -*- coding: utf-8 -*-

import abc
import uuid
from typing import Optional
from threading import Event

"""
Executable基础组件适用于含有阻塞exec函数的基础结构接口
"""

class ExecutableBase(object, metaclass=abc.ABCMeta):
    def __init__(self, name: Optional[str] = None):
        self.uuid = str(uuid.uuid4())
        self.name = name if name else f"Executable item <{self.uuid}>"
        self.running = Event()
        self._setup()

    def __del__(self):
        if self.is_running():
            self.stop()

    def get_name(self):
        return self.name

    def get_uuid(self):
        return self.uuid

    @abc.abstractmethod
    def _setup(self):
        raise NotImplementedError

    @abc.abstractmethod
    def _exec(self):
        raise NotImplementedError

    def exec(self):
        if self.is_running():
            raise RuntimeError("Cannot exec while executable is running.")
        try:
            self._set_running(True)
            self._exec()
        finally:
            self._set_running(False)

    def is_running(self):
        return self.running.is_set()

    def _set_running(self, running: bool):
        if running:
            self.running.set()
        else:
            self.running.clear()

    @abc.abstractmethod
    def _stop(self):
        raise NotImplementedError

    def stop(self):
        if not self.is_running():
            raise RuntimeError("Cannot stop while executable is not running.")
        self._stop()
