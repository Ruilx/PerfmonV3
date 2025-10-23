# -*- coding: utf-8 -*-

import abc
import uuid
from multiprocessing import Queue

from src import util
from src.logger import Logger


class SourceBase(object, metaclass=abc.ABCMeta):
    def __init__(self, name: str, config: dict):
        self.logger = Logger().getLogger(__name__)
        self.name = name
        self.config = config
        self.source_table = {}
        self._parse_config()

    def __del__(self):
        self.stop()

    def _parse_config(self):
        ...

    def register_source(self, name: str, config: dict):
        if name in self.source_table:
            raise ValueError(f"Source: '{name}' already registered.")

        params = []
        self._build_params(name, params)

        self.source_table[name] = {
            'name': name,
            'params': params
        }


    def _prepare_job(self, name: str, params: dict):
        cur_params = {}
        for key, value in params.items():
            cur_params[key] = value() if callable(value) else value
        return {
            'cmd': "task",
            'perfmon': name,
            'job_id': str(uuid.uuid4()),
            'source': self.name,
            'params': cur_params,
        }

    def _build_params(self):
        ...

    def _send_job(self, name, params: dict):
        sending_params = {}
        for key, value in params.items():
            sending_params[key] = value() if callable(value) else value

        mq_message = {
            'cmd': "task",
            'job': name,
            'job_id': str(uuid.uuid4()),
            'source': self.name,
            'params': sending_params,
        }
        self._mq_send_job(mq_message)

    def _mq_send_job(self, mq_message):
