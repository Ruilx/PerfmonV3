# -*- coding: utf-8 -*-


"""
Worker是一个处理工作的基本单元，对应一个Python的具体进程，由进程来处理各个job。

进程接收主进程发来的信号，并监听Pipe以获得相应的任务。
"""
import gc
import signal
import threading
from multiprocessing import ProcessError, Pipe, Queue

from src.base.executable_base import ExecutableBase
from src.core.logger import Logger, LogPathType
from src.util import util


class ProcessFinished(Warning):
    ...

class JobFinished(Warning):
    ...


class Worker(ExecutableBase):
    def __init__(self, name: str):
        self.logger = Logger().get_logger(__name__)
        self.job_list = []
        self.process_status = None

        self.stopped = threading.Event()
        self.running_job = False

        super().__init__(name)

    def _setup(self):
        def _signal_handler(signum, frame):
            if signum == signal.SIGINT:
                if not self.running_job:
                    self.logger.info(f"Process '{self.name}' received SIGINT, stopping process.")
                    self.stop()
                    raise ProcessFinished()

        signal.signal(signal.SIGINT, _signal_handler)

    def _exec(self):
        self.logger.info(f"Process '{self.name}' started.")
        while not self.stopped.is_set():
            try:
                ... # TODO: 待完善
            except JobFinished:
                continue
            except ProcessFinished:
                self.logger.info(f"Process '{self.name}' finished by tasks.")
                self.stop()
                break
            except ProcessError as e:
                self.logger.error(f"Process '{self.name}' encountered an error: {e!r}")
                util.print_with_traceback(e, self.logger.error)
                self.process_status = 'error'
                self.stop()
                break
            except AssertionError as e:
                self.logger.error(f"Process '{self.name}' assertion error: {e!r}")
                util.print_with_traceback(e, self.logger.error)
                continue
            except KeyboardInterrupt:
                self.logger.error("Processing has a keyboard interrupt.")
                self.stop()
                break
            except BaseException as e:
                self.logger.error(f"Process '{self.name}' unexpected error: {e!r}")
                util.print_with_traceback(e, self.logger.error)
                self.process_status = 'error'
                self.stop()
                break
            finally:
                self.running_job = False
                gc.collect()

        self.logger.info(f"Process '{self.name}' exiting.")
        return 1

    def _stop(self):
        self.stopped.set()
        self.logger.info(f"Process '{self.name}' stopping...")

    # agent是该运行实例的名称。
    @staticmethod
    def run(agent_name: str, tasks: dict, pipe_in: Pipe, queue_out: Queue, name: str, log_streams: tuple[LogPathType], log_level: str):
        util.setup_loggers(Logger(), log_streams, log_level)
        JobHub().register_tasks()
        jobs = Jobs()
        for task_name, task in tasks.items():
            jobs.add_job(task_name, )
