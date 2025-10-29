# -*- coding: utf-8 -*-

import os
import time
import datetime
import traceback

from typing import Callable


def print_with_traceback(e: BaseException, printer: Callable = print):
    printer(f"{e.__class__.__name__}: {e!r}")
    for line in traceback.format_tb(e.__traceback__):
        printer(line.rstrip())

def timestamp():
    return int(time.time())

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def machine_cpu_count():
    return os.cpu_count() or 1
