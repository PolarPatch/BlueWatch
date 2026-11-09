"""Self-hosted ntfy (server and token) and the BLUEWATCH_PORT default."""

import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bluewatch import config, db, notifications


class NtfyTests(unittest.IsolatedAsyncioTestCase):
    def test_url_uses_saved_server_then_env_default(self):
        settings = db.Settings(ntfy_topic="alerts")
        with patch.object(notifications, "NTFY_SERVER", "https://ntfy.example.org/"):
            self.assertEqual(notifications.ntfy_url(settings), "https://ntfy.example.org/alerts")
            settings.ntfy_server = "http://10.0.0.5:8090/"
            self.assertEqual(notifications.ntfy_url(settings), "http://10.0.0.5:8090/alerts")

    async def test_bearer_token_sent(self):
        sent = {}

        class Response:
            status = 200
            async def __aenter__(self):
                return self
            async def __aexit__(self, *a):
                return False
            async def text(self):
                return ""

        class Session:
            def post(self, url, data=None, headers=None, timeout=None):
                sent.update(url=url, headers=headers)
                return Response()

        manager = notifications.NotificationManager()
        manager._settings = db.Settings(ntfy_topic="t", ntfy_enabled=True,
                                        ntfy_server="https://push.example.org", ntfy_token="tk_abc")
        manager._session = Session()
        self.assertTrue(await manager._send_notification("Title", "Body"))
        self.assertEqual(sent["url"], "https://push.example.org/t")
        self.assertEqual(sent["headers"]["Authorization"], "Bearer tk_abc")

    async def test_settings_round_trip(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(db, "DB_PATH", Path(directory) / "n.db"):
            await db.init_db()
            settings = await db.get_settings()
            settings.ntfy_server = "https://push.example.org"
            settings.ntfy_token = "tk_abc"
            await db.update_settings(settings)
            loaded = await db.get_settings()
            self.assertEqual((loaded.ntfy_server, loaded.ntfy_token), ("https://push.example.org", "tk_abc"))


class PortTests(unittest.TestCase):
    def test_port_env(self):
        with patch.dict(os.environ, {"BLUEWATCH_PORT": "8181"}):
            self.assertEqual(importlib.reload(config).WEB_PORT, 8181)
        self.assertEqual(importlib.reload(config).WEB_PORT, int(os.environ.get("BLUEWATCH_PORT", "8080")))


if __name__ == "__main__":
    unittest.main()
