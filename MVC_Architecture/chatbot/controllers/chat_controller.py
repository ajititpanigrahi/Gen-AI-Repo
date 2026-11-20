"""Chat controller: takes input from the view, asks the models, tells the view what to show."""

from __future__ import annotations

from pathlib import Path

from ..models import Bot, Conversation
from ..views import ChatView


class ChatController:
    def __init__(self, bot: Bot, conversation: Conversation, view: ChatView, history_path: Path) -> None:
        self.bot = bot
        self.conversation = conversation
        self.view = view
        self.history_path = Path(history_path)
        self._commands = {
            "/help": self._cmd_help,
            "/teach": self._cmd_teach,
            "/forget": self._cmd_forget,
            "/learned": self._cmd_learned,
            "/history": self._cmd_history,
            "/save": self._cmd_save,
            "/clear": self._cmd_clear,
        }

    def run(self) -> None:
        """Interactive loop for views that can prompt (the console)."""
        self.view.show_welcome(self.bot.name)
        while True:
            line = self.view.prompt()
            if line is None or not self.handle(line):
                break
        self.view.show_goodbye(self.bot.name)

    def handle(self, line: str) -> bool:
        """Process one line of input. Returns False when the user wants to quit."""
        line = line.strip()
        if not line:
            return True

        if line.startswith("/"):
            command, _, argument = line.partition(" ")
            command = command.lower()
            if command in ("/quit", "/exit"):
                return False
            handler = self._commands.get(command)
            if handler is None:
                self.view.show_error(f"Unknown command {command}. Type /help.")
            else:
                handler(argument.strip())
            return True

        self.conversation.add("user", line)
        reply = self.bot.reply(line)
        self.conversation.add("bot", reply.text)
        self.view.show_reply(self.bot.name, reply.text)
        return True

    # --- command handlers -------------------------------------------------

    def _cmd_help(self, _: str) -> None:
        self.view.show_help()

    def _cmd_teach(self, argument: str) -> None:
        question, sep, answer = argument.partition("=")
        if not sep:
            self.view.show_error("Usage: /teach <question> = <answer>")
            return
        try:
            self.bot.knowledge.teach(question, answer)
        except ValueError as exc:
            self.view.show_error(str(exc))
            return
        self.view.show_info(f"Got it! When you say {question.strip()!r} I'll answer {answer.strip()!r}.")

    def _cmd_forget(self, argument: str) -> None:
        if self.bot.knowledge.forget(argument):
            self.view.show_info(f"Forgot {argument!r}.")
        else:
            self.view.show_error(f"I wasn't taught {argument!r}.")

    def _cmd_learned(self, _: str) -> None:
        self.view.show_learned(self.bot.knowledge.learned)

    def _cmd_history(self, _: str) -> None:
        self.view.show_history(self.conversation.messages, self.bot.name)

    def _cmd_save(self, _: str) -> None:
        self.conversation.save(self.history_path)
        self.view.show_info(f"Saved {len(self.conversation)} messages to {self.history_path}")

    def _cmd_clear(self, _: str) -> None:
        self.conversation.clear()
        self.view.show_info("Conversation cleared.")
