#-*- coding: utf-8 -*-
import unittest

from src.core.eventloop import Eventloop

class TestEventloop(unittest.TestCase):

    def test_new_eventloop(self):
        eventloop = Eventloop()
        print(f"current eventloop: {eventloop.get_eventloop()!r}")

        eventloop.set_graceful_stop(False)
        eventloop.emit(lambda x: print(f"Hello, world! {x}"), __name__)
        eventloop.emit(lambda: eventloop.stop())

        eventloop.exec()

        print("Eventloop is finished.")
