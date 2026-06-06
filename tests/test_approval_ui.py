import unittest
import requests
import time
import subprocess
import os
import signal
import sys
from pathlib import Path

class TestApprovalUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start the UI server in a background process
        src_path = Path(__file__).resolve().parent.parent / "src"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(src_path) + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")

        cls.server_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "dgm_hub.ui.server:app", "--host", "127.0.0.1", "--port", "8765"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for server to start
        max_retries = 10
        for i in range(max_retries):
            try:
                resp = requests.get("http://127.0.0.1:8765/pending", timeout=1)
                if resp.status_code == 200:
                    break
            except requests.exceptions.ConnectionError:
                time.sleep(0.5)
        else:
            cls.server_proc.terminate()
            raise RuntimeError("Failed to start approval server for testing")

    @classmethod
    def tearDownClass(cls):
        cls.server_proc.terminate()
        cls.server_proc.wait()

    def test_ui_endpoints(self):
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
