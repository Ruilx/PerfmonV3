# -*- coding: utf-8 -*-


"""
Process是一个处理任务的基本单元，对应一个Python的具体进程，由进程来处理各个job。

进程接收主进程发来的信号，并监听Pipe以获得相应的任务。
"""
import signal
import threading
from multiprocessing import ProcessError

from src.core.logger import Logger

class ProcessFinished(Warning):
    ...

class JobFinished(Warning):
    ...


class Process(object):
    def __init__(self, name: str):
        self.logger = Logger().getLogger(__name__)
        self.name = name
        self.job_list = []
        self.process_status = None

        self.stopped = threading.Event()
        self.running_job = False

        self._setup()

    def _setup(self):
        def _signal_handler(signum, frame):
            if signum == signal.SIGINT:
                if not self.running_job:
                    self.logger.info(f"Process '{self.name}' received SIGINT, stopping process.")
                    self.stopped.set()
                    raise ProcessFinished()

        signal.signal(signal.SIGINT, _signal_handler)

    def exec(self):
        self.logger.info(f"Process '{self.name}' started.")
        while not self.stopped.is_set():
            try:

            except JobFinished:
                continue
            except ProcessFinished:
                self.logger.info(f"Process '{self.name}' finished.")
                self.stopped.set()
                break
            except ProcessError as e:
                self.logger.error(f"Process '{self.name}' encountered an error: {e!r}")
                self.process_status = 'error'
                self.stopped.set()
                break
