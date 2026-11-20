import tempfile
import unittest
from pathlib import Path

from chatbot.models import Bot, Conversation, KnowledgeBase
from chatbot.models.bot import safe_eval

INTENTS = Path(__file__).resolve().parent.parent / "chatbot" / "data" / "intents.json"


class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class BotTests(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.kb = KnowledgeBase.from_file(INTENTS, self.tmp / "learned.json")
        self.bot = Bot(self.kb, name="Bolt", seed=1)

    def test_greeting_intent(self):
        self.assertEqual(self.bot.reply("Hello!").source, "intent:greeting")

    def test_name_intent_uses_bot_name(self):
        reply = self.bot.reply("What is your name?")
        self.assertEqual(reply.source, "intent:name")
        self.assertIn("Bolt", reply.text)

    def test_time_intent(self):
        self.assertEqual(self.bot.reply("what time is it").source, "time")

    def test_math(self):
        self.assertEqual(self.bot.reply("12 * (3 + 4)").text, "12 * (3 + 4) = 84")
        self.assertEqual(self.bot.reply("what is 10 / 4?").text, "10 / 4 = 2.5")

    def test_divide_by_zero(self):
        self.assertIn("divide by zero", self.bot.reply("5 / 0").text)

    def test_plain_number_is_not_math(self):
        self.assertNotEqual(self.bot.reply("42").source, "math")

    def test_fallback(self):
        self.assertEqual(self.bot.reply("purple elephants dancing").source, "fallback")

    def test_teach_persists_and_overrides(self):
        self.kb.teach("What is the capital of France?", "Paris")
        self.assertEqual(self.bot.reply("what is the capital of france").text, "Paris")
        reloaded = KnowledgeBase.from_file(INTENTS, self.tmp / "learned.json")
        self.assertEqual(reloaded.lookup_learned("What is the capital of France"), "Paris")

    def test_forget(self):
        self.kb.teach("ping", "pong")
        self.assertTrue(self.kb.forget("PING"))
        self.assertFalse(self.kb.forget("ping"))

    def test_teach_rejects_empty(self):
        with self.assertRaises(ValueError):
            self.kb.teach("  ", "x")


class SafeEvalTests(unittest.TestCase):
    def test_rejects_names(self):
        with self.assertRaises(ValueError):
            safe_eval("__import__('os')")


class ConversationTests(TempDirTestCase):
    def test_save_and_load_roundtrip(self):
        conv = Conversation()
        conv.add("user", "hi")
        conv.add("bot", "hello")
        conv.save(self.tmp / "h.json")
        loaded = Conversation.load(self.tmp / "h.json")
        self.assertEqual([(m.sender, m.text) for m in loaded.messages], [("user", "hi"), ("bot", "hello")])

    def test_rejects_unknown_sender(self):
        with self.assertRaises(ValueError):
            Conversation().add("alien", "x")


if __name__ == "__main__":
    unittest.main()
