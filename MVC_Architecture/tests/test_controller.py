import io
import tempfile
import unittest
from pathlib import Path

from chatbot.controllers import ChatController
from chatbot.models import Bot, Conversation, KnowledgeBase
from chatbot.views import ConsoleView

INTENTS = Path(__file__).resolve().parent.parent / "chatbot" / "data" / "intents.json"


class ControllerTests(unittest.TestCase):
    def run_session(self, lines):
        """Drive the full MVC loop with scripted input; return printed output."""
        feed = iter(lines)

        def fake_input(_prompt):
            try:
                return next(feed)
            except StopIteration:
                raise EOFError

        out = io.StringIO()
        kb = KnowledgeBase.from_file(INTENTS, self.tmp / "learned.json")
        self.conversation = Conversation()
        controller = ChatController(
            Bot(kb, seed=1), self.conversation, ConsoleView(fake_input, out), self.tmp / "history.json"
        )
        controller.run()
        return out.getvalue()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_chat_and_quit(self):
        output = self.run_session(["hello", "2 + 2", "/quit", "never reached"])
        self.assertIn("2 + 2 = 4", output)
        self.assertIn("Bye!", output)
        self.assertEqual(len(self.conversation), 4)

    def test_teach_command(self):
        output = self.run_session(["/teach favourite color = blue", "favourite color"])
        self.assertIn("Bolt: blue", output)

    def test_bad_teach_usage(self):
        self.assertIn("Usage: /teach", self.run_session(["/teach nothing here"]))

    def test_unknown_command(self):
        self.assertIn("Unknown command /dance", self.run_session(["/dance"]))

    def test_save_and_clear(self):
        self.run_session(["hi", "/save", "/clear", "/history"])
        self.assertTrue((self.tmp / "history.json").exists())
        self.assertEqual(len(self.conversation), 0)

    def test_eof_exits_cleanly(self):
        self.assertIn("Bye!", self.run_session([]))


if __name__ == "__main__":
    unittest.main()
