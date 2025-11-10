# -*- coding: utf-8 -*-

"""
EventLoop是一个事件处理列表，能异步地将事件处理起来。
Broker是一个任务分配中间件，提交一个job信息，将其确定应用于哪个任务队列中，以及在输入队列满时，在任务中进行缓冲。
"""

import asyncio
from asyncio import BaseEventLoop
from concurrent.futures import Future
from typing import Optional, Callable, Any

from src.base.executable_base import ExecutableBase
from src.core import logger
from src.core.resettable_timer import TimerHandleProxy
from src.util import util


class Eventloop(ExecutableBase):
    def __init__(self, eventloop: Optional[BaseEventLoop] = None):
        if eventloop is None:
            self.eventloop = asyncio.new_event_loop()
            self.eventloop_owner = True
        else:
            self.eventloop = eventloop
            self.eventloop_owner = False

        self.graceful_stop: bool = True
        self.stop_timeout = 5

        super().__init__(self.__class__.__name__)

    def _setup(self):
        ...

    def get_eventloop(self) -> BaseEventLoop:
        return self.eventloop

    def is_running(self):
        return self.eventloop.is_running()

    def _set_running(self, running: bool):
        ...

    def is_closed(self):
        return self.eventloop.is_closed()

    def emit(self, cb: Callable[..., Any], /, *args: tuple[Any, ...], context: Any = None):
        if not self.is_running() or self.is_closed():
            raise RuntimeError("Cannot emit event while eventloop is not running or closed.")

        concurrent_future = Future()

        def _run_future(*_args):
            try:
                res = cb(*_args)
                concurrent_future.set_result(res)
            except Exception as e:
                concurrent_future.set_exception(e)

        self.eventloop.call_soon_threadsafe(_run_future, *args, context=context)
        return concurrent_future

    def emit_after(self, delay: float, cb: Callable[..., Any], /, *args, context: Any = None):
        if self.is_closed():
            raise RuntimeError("Eventloop is closed.")

        proxy = TimerHandleProxy(self.eventloop)

        def _create_timer():
            handle = self.eventloop.call_later(delay, _run_future, *args, context=context)
            proxy.set_handle(handle)

        def _run_future(*_args):
            try:
                cb(*_args)
            except BaseException as e:
                util.print_with_traceback(e, logger.Logger().global_logger().error)

        self.eventloop.call_soon_threadsafe(_create_timer)
        return proxy

    def run_coroutine(self, coro) -> Future:
        if self.is_closed():
            raise RuntimeError("Eventloop is closed.")
        return asyncio.run_coroutine_threadsafe(coro, self.eventloop)

    def set_graceful_stop(self, graceful: bool = True, timeout: float = 5.0):
        self.graceful_stop = graceful
        self.stop_timeout = timeout

    def get_graceful_stop(self):
        return self.graceful_stop

    def _stop(self):
        if self.is_closed() or not self.running.is_set():
            return
        if self.graceful_stop:
            async def _shutdown():
                tasks = [t for t in asyncio.all_tasks(self.eventloop) if not t.done()]
                for task in tasks:
                    task.cancel()
                if tasks:
                    try:
                        await asyncio.wait(tasks, timeout=self. timeout)
                    except asyncio.CancelledError:
                        pass
                    except BaseException as e:
                        util.print_with_traceback(e, logger.Logger().global_logger().error)
                self.eventloop.stop()
            asyncio.run_coroutine_threadsafe(_shutdown(), self.eventloop)
        else:
            self.eventloop.call_soon_threadsafe(self._stop)


    def close(self):
        self.stop()

    def _exec(self):
        try:
            if not self.eventloop.is_running():
                self.eventloop.run_forever()
        finally:
            if self.eventloop_owner and not self.eventloop.is_closed():
                self.eventloop.close()

    def _stop(self):
        if self.eventloop.is_running():
            self.eventloop.stop()
