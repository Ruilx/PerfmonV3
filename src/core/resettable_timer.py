# -*- coding: utf-8 -*-
import asyncio
import threading
from asyncio import AbstractEventLoop
from typing import Callable, Optional, Any

from src.core.eventloop import Eventloop


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

class ResettableTimer(object):
    def __init__(self, eventloop: Eventloop, cb: Callable[..., Any]):
        self.eventloop = eventloop
        self.cb = cb
        self.proxy: Optional[TimerHandleProxy] = None
        self.cancelled = False
        self.active = False
        self.lock = threading.Lock()

    def start(self, delay: float):
        if self.cancelled:
            raise RuntimeError("Timer cancelled and cannot be restarted.")
        with self.lock:
            if self.proxy is not None:
                self.proxy.cancel()
                self.proxy = None
            self.proxy = self.eventloop.emit_after(delay, self.cb)
            self.active = True

    def stop(self):
        with self.lock:
            if self.proxy is not None:
                self.proxy.cancel()
                self.proxy = None
            self.active = False

    def cancel(self):
        with self.lock:
            self.stop()
            self.cancelled = True

    def is_active(self) -> bool:
        return self.active and not self.cancelled
