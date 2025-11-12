#-*- coding: utf-8 -*-
import asyncio
import unittest

from src.core.eventloop import Eventloop

class TestEventloop(unittest.TestCase):

    def test_new_eventloop(self):
        eventloop = Eventloop()
        print(f"current eventloop: {eventloop.get_eventloop()!r}")

        eventloop.set_graceful_stop(True)
        eventloop.emit(lambda x: print(f"Hello, world! {x}"), __name__)
        eventloop.emit(lambda: eventloop.stop())

        eventloop.exec()

        print("Eventloop is finished.")


    def test_main_eventloop(self):

        async def fn():
            exist_eventloop = asyncio.get_running_loop()
            eventloop = Eventloop(exist_eventloop)
            print(f"current eventloop: {eventloop.get_eventloop()!r}")

            eventloop.set_graceful_stop(True)
            eventloop.emit(lambda x: print(f"Hello, world! {x}"), __name__)
            eventloop.emit(lambda: eventloop.stop())

            print("Eventloop is finished.")

        asyncio.run(fn())

    def test_emit_after(self):
        eventloop = Eventloop()
        print(f"current eventloop: {eventloop.get_eventloop()!r}")
        eventloop.set_graceful_stop(True)

        eventloop.emit_after(1, lambda x: print(f"Hello, world! {x}"), __name__)
        eventloop.emit_after(2, lambda: eventloop.stop())

        eventloop.exec()

        print("Eventloop is finished.")
