# -*- coding: utf-8 -*-

"""
Broker是一个能够接收到被分配的task，并且能够得到所有处理的分配通道，并选择一个合适的任务节点执行。
"""
from typing import Optional

from src.core.eventloop import Eventloop


class Broker(object):
    def __init__(self, eventloop: Optional[Eventloop] = None):
        if isinstance(eventloop, Eventloop):
            self.eventloop = eventloop
        else:
            self.eventloop = Eventloop()
        self.processes: dict = {}


    def register_process(self, name: str, process: ProcessHandle):
        if name in self.processes:
            raise RuntimeError(f"Process with name '{name}' is already registered.")
        self.processes[name] = process



    def unregister_process(self, name: str):
        ...

    def send_job(self, job: Job):
        ...
