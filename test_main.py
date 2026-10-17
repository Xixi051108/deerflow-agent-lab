import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from urllib.error import HTTPError

import main


class ConfigurationSafetyTests(unittest.TestCase):
    def test_missing_key_does_not_send_request(self):
        with patch("main.load_dotenv"), patch.dict("os.environ", {}, clear=True):
            with patch("main.urlopen") as send, redirect_stdout(io.StringIO()):
                self.assertEqual(main.main(), 1)
                send.assert_not_called()

    def test_http_failure_does_not_print_credentials_or_response_body(self):
        error = HTTPError("https://api.deepseek.com/chat/completions", 401,
                          "test-secret", {}, io.BytesIO(b"test-secret"))
        output = io.StringIO()
        with patch("main.load_dotenv"), patch.dict(
            "os.environ", {"DEEPSEEK_API_KEY": "test-secret"}, clear=True
        ):
            with patch("main.urlopen", side_effect=error), redirect_stdout(output):
                self.assertEqual(main.main(), 1)
        self.assertIn("401", output.getvalue())
        self.assertNotIn("test-secret", output.getvalue())


if __name__ == "__main__":
    unittest.main()
