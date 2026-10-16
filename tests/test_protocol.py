import unittest

from src.core.protocol import JobRequest, ProtocolError


class TestJobRequest(unittest.TestCase):
    def test_round_trip(self):
        request = JobRequest.create(
            "demo",
            "test-source",
            {"message": "hello"},
            priority=4,
            metadata={"env": "test"},
        )

        restored = JobRequest.from_message(request.to_message())

        self.assertEqual(restored, request)

    def test_rejects_wrong_message_type(self):
        with self.assertRaises(ProtocolError):
            JobRequest.from_message({"type": "job_result"})
