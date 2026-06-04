import unittest
import requests
import time
import subprocess
import os

class TestApprovalUI(unittest.TestCase):
    def test_ui_endpoints(self):
        # UI should already be running from the previous plan step
        base_url = "http://127.0.0.1:8765"

        # Test GET /pending
        resp = requests.get(f"{base_url}/pending")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

        # Test POST /submit
        action_payload = {
            "action_id": "test-id-123",
            "action_type": "shell",
            "description": "test command",
            "payload": {"cmd": "ls"}
        }
        resp = requests.post(f"{base_url}/submit", json=action_payload)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])

        # Verify it's in pending
        resp = requests.get(f"{base_url}/pending")
        pending = resp.json()
        self.assertTrue(any(x["action_id"] == "test-id-123" for x in pending))

        # Test POST /approve
        resp = requests.post(f"{base_url}/approve/test-id-123")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["approved"])
        self.assertEqual(resp.json()["action"]["action_id"], "test-id-123")

        # Verify it's gone
        resp = requests.get(f"{base_url}/pending")
        self.assertFalse(any(x["action_id"] == "test-id-123" for x in resp.json()))

if __name__ == "__main__":
    unittest.main()
