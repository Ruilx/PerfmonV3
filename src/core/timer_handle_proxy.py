# -*- coding: utf-8 -*-
import asyncio
import threading
from asyncio import AbstractEventLoop
from typing import Optional


class TimerHandleProxy(object):
    def __init__(self, loop: AbstractEventLoop):
        self.loop = loop
        self.handle: Optional[asyncio.TimerHandle] = None
        self.cancelled = False
        self.lock = threading.Lock()

    def set_handle(self, handle: asyncio.TimerHandle):
        with self.lock:
            self.handle = handle
            if self.cancelled and self.handle is not None:
                self.handle.cancel()

    def cancel(self):
        with self.lock:
            self.cancelled = True
            if self.handle is not None:
                self.loop.call_soon_threadsafe(self.handle.cancel)
