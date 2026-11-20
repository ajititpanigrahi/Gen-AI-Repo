import tempfile
import unittest
from pathlib import Path

from chatbot.models import Conversation
from chatbot.views import WebView

try:
    from chatbot.web_app import create_app
except ImportError:  # Flask not installed
    create_app = None

INTENTS = Path(__file__).resolve().parent.parent / "chatbot" / "data" / "intents.json"


class WebViewTests(unittest.TestCase):
    def test_drain_returns_and_clears_events(self):
        view = WebView()
        view.show_reply("Bolt", "hi")
        view.show_error("oops")
        self.assertEqual(view.drain(), [
            {"kind": "bot", "sender": "Bolt", "text": "hi"},
            {"kind": "error", "text": "oops"},
        ])
        self.assertEqual(view.drain(), [])

    def test_history_as_list(self):
        conv = Conversation()
        conv.add("user", "hello")
        view = WebView()
        view.show_history(conv.messages, "Bolt")
        event = view.drain()[0]
        self.assertEqual(event["kind"], "list")
        self.assertTrue(event["items"][0].endswith("You: hello"))

    def test_help_mentions_session_reset(self):
        view = WebView()
        view.show_help()
        self.assertIn("End this chat session", view.drain()[0]["text"])


@unittest.skipIf(create_app is None, "Flask is not installed")
class WebAppTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.app = create_app(INTENTS, self.tmp)
        self.client = self.app.test_client()

    def tearDown(self):
        self._tmp.cleanup()

    def say(self, text, client=None):
        return (client or self.client).post("/api/message", json={"text": text})

    def test_index_page(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Bolt", res.data)

    def test_message_returns_bot_event(self):
        data = self.say("12 * (3 + 4)").get_json()
        self.assertEqual(data["events"], [{"kind": "bot", "sender": "Bolt", "text": "12 * (3 + 4) = 84"}])
        self.assertFalse(data["ended"])

    def test_history_is_per_session(self):
        self.say("hello")
        self.assertEqual(len(self.client.get("/api/history").get_json()["messages"]), 2)
        other = self.app.test_client()
        self.assertEqual(other.get("/api/history").get_json()["messages"], [])

    def test_taught_answers_are_shared(self):
        self.say("/teach ping = pong")
        other = self.app.test_client()
        self.assertEqual(self.say("ping", other).get_json()["events"][0]["text"], "pong")

    def test_quit_resets_session(self):
        self.say("hello")
        data = self.say("/quit").get_json()
        self.assertTrue(data["ended"])
        self.assertIn("Bye", data["events"][-1]["text"])
        self.assertEqual(self.client.get("/api/history").get_json()["messages"], [])

    def test_rejects_bad_input(self):
        self.assertEqual(self.client.post("/api/message", json={}).status_code, 400)
        self.assertEqual(self.say("   ").status_code, 400)
        self.assertEqual(self.say("x" * 1001).status_code, 400)
        self.assertEqual(self.client.post("/api/message", data="not json").status_code, 400)


if __name__ == "__main__":
    unittest.main()
