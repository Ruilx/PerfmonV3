# -*- coding: utf-8 -*-

"""
EventLoop是一个事件处理列表，能异步地将事件处理起来。
Broker是一个任务分配中间件，提交一个job信息，将其确定应用于哪个任务队列中，以及在输入队列满时，在任务中进行缓冲。
"""

import asyncio
from asyncio import BaseEventLoop
from threading import Thread
from typing import Optional, Callable, Any


class EventLoop(object):
    def __init__(self, loop: Optional[BaseEventLoop] = None):
        self.event_loop = loop if isinstance(loop, BaseEventLoop) else asyncio.new_event_loop()
        self.running = True

    def __del__(self):
        print("Broker deleted.")
        if self.event_loop.is_running():
            self.stop()
        if not self.event_loop.is_closed():
            self.event_loop.close()

    def emit(self, cb: Callable, *args, context: Any = None):
        if not self.running:
            raise RuntimeError("Cannot emit while eventloop is stopped.")
        self.event_loop.call_soon_threadsafe(cb, *args, context=context)

    def exec(self):
        self.event_loop.run_forever()

    def is_running(self):
        return self.event_loop.is_running()

    def stop(self):
        self.running = False
        self.event_loop.stop()


class EventLoopThread(object):
    def __init__(self, eventloop: EventLoop):
        self.eventloop = eventloop
        self.thread = Thread(None, self.daemon, "BrokerThread", (self.eventloop,), daemon=True)

    def daemon(self, broker: EventLoop):
        if broker.is_running():
            print("EventLoop is running...")
            return
        print("Broker starting...")
        self.eventloop.exec()

    def run(self):
        if not self.thread.is_alive():
            print(f"{self.thread.name} running...")
            self.thread.start()

    def join(self):
        self.eventloop.stop()
        self.thread.join()

    def get_broker(self):
        return self.eventloop


if __name__ == "__main__":
    import time
    broker = EventLoop()
    brokerThread = EventLoopThread(broker)
    brokerThread.run()

    time.sleep(2)
    broker.emit(print, "Hello, world!")
    broker.emit(print, "Hello, world! For twice")
    broker.emit(print, "Hello, world! For 3")
    broker.emit(print, "Hello, world! For 4")
    broker.emit(print, "Hello, world! For 5")
    broker.emit(print, "Hello, world! For 6")
    broker.emit(print, "Hello, world! For 7")
    broker.emit(print, "Hello, world! For 8")
    broker.emit(print, "Hello, world! For 9")

    brokerThread.join()
