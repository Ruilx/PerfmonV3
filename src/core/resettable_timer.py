# -*- coding: utf-8 -*-
import asyncio
import threading

from typing import Callable, Optional, Any

from src.core.eventloop import Eventloop

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
