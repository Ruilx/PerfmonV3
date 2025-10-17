# -*- coding: utf-8 -*-

import logging
import os
import sys
from typing import Literal, Union

from src.base.singleton import singleton

LogLevel = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
}

LogLevelType = Literal["DEBUG", "INFO", "WARNING", "ERROR"]
LogPathType = Union[os.PathLike, Literal["_stderr"], Literal["_stdout"]]
