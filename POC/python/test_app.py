import unittest

from app import health_check


class HealthCheckTests(unittest.TestCase):
    def test_health_check(self):
        self.assertEqual(
            health_check(),
            {"service": "python-poc", "status": "ok"},
        )


if __name__ == "__main__":
    unittest.main()
