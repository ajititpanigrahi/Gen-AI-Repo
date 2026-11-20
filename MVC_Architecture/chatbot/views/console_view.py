"""Console view: reads input and prints output. Contains no bot logic."""

from __future__ import annotations

import sys
from typing import Callable, TextIO

from ..models.conversation import Message

HELP_TEXT = """\
Commands:
  /help                       Show this help
  /teach <question> = <answer> Teach me a new answer
  /forget <question>          Forget a taught answer
  /learned                    List everything I've been taught
  /history                    Show this conversation
  /save                       Save the conversation to disk
  /clear                      Clear the conversation
  /quit                       Exit
You can also ask me things like "hello", "tell me a joke", "what time is it" or "12 * (3 + 4)"."""


class ConsoleView:
    def __init__(
        self,
        input_func: Callable[[str], str] = input,
        out: TextIO | None = None,
    ) -> None:
        self._input = input_func
        self._out = out or sys.stdout

    def _print(self, text: str = "") -> None:
        print(text, file=self._out)

    def prompt(self) -> str | None:
        """Return the user's line, or None on Ctrl+D / Ctrl+C."""
        try:
            return self._input("You: ")
        except (EOFError, KeyboardInterrupt):
            self._print()
            return None

    def show_welcome(self, bot_name: str) -> None:
        self._print(f"=== {bot_name} - MVC Chatbot ===")
        self._print("Type /help for commands, /quit to exit.\n")

    def show_reply(self, bot_name: str, text: str) -> None:
        self._print(f"{bot_name}: {text}")

    def show_info(self, text: str) -> None:
        self._print(f"[i] {text}")

    def show_error(self, text: str) -> None:
        self._print(f"[!] {text}")

    def show_help(self) -> None:
        self._print(HELP_TEXT)

    def show_history(self, messages: list[Message], bot_name: str) -> None:
        if not messages:
            self.show_info("No messages yet.")
            return
        for m in messages:
            who = "You" if m.sender == "user" else bot_name
            self._print(f"  [{m.timestamp}] {who}: {m.text}")

    def show_learned(self, learned: dict[str, str]) -> None:
        if not learned:
            self.show_info("I haven't been taught anything yet.")
            return
        for question, answer in learned.items():
            self._print(f"  {question!r} -> {answer}")

    def show_goodbye(self, bot_name: str) -> None:
        self._print(f"{bot_name}: Bye!")
