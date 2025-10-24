# -*- coding: utf-8 -*-

"""
EventLoop是一个事件处理列表，能异步地将事件处理起来。
Broker是一个任务分配中间件，提交一个job信息，将其确定应用于哪个任务队列中，以及在输入队列满时，在任务中进行缓冲。
"""

import asyncio
from asyncio import BaseEventLoop
from typing import Optional, Callable, Any

from src.base.executable_base import ExecutableBase


class EventLoop(ExecutableBase):
    def __init__(self, eventloop: Optional[BaseEventLoop] = None):
        self.eventloop = eventloop if isinstance(eventloop, BaseEventLoop) else asyncio.new_event_loop()
        super().__init__(self.__class__.__name__)

    def _setup(self):
        self.running = self.is_running()

    def is_running(self):
        self.running = self.eventloop.is_running()
        return self.running

    def emit(self, cb: Callable, *args, context: Any = None):
        if not self.is_running():
            raise RuntimeError("Cannot emit event while eventloop is not running.")
        self.eventloop.call_soon_threadsafe(cb, *args, context=context)

    def exec(self):
        if self.is_running():
            raise RuntimeError("Cannot run while eventloop is running.")
        try:
            self.eventloop.run_forever()
        finally:
            if not self.eventloop.is_closed():
                self.eventloop.close()

    def stop(self):
        if self.eventloop.is_running():
            self.eventloop.stop()
