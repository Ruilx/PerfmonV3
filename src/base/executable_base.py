# -*- coding: utf-8 -*-

import abc
import uuid
from typing import Optional

"""
Executable基础组件适用于含有阻塞exec函数的基础结构接口
"""

class ExecutableBase(object, metaclass=abc.ABCMeta):
    def __init__(self, name: Optional[str] = None):
        self.name = name if name else f"Executable item {uuid.uuid4()}"
        self.running = False
        self._setup()

    def __del__(self):
        if self.is_running():
            self.stop()

    def get_name(self):
        return self.name

    @abc.abstractmethod
    def _setup(self):
        raise NotImplementedError

    @abc.abstractmethod
    def exec(self):
        if self.running:
            raise RuntimeError("Cannot exec while executable is running.")

    def is_running(self):
        return self.running

    @abc.abstractmethod
    def stop(self):
        raise NotImplementedError
