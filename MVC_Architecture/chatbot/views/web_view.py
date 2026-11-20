"""Web view: same interface as ConsoleView, but collects output as JSON-ready events.

The controller calls show_*() exactly as it does for the console; the Flask route
then calls drain() and sends the events to the browser.
"""

from __future__ import annotations

from ..models.conversation import Message
from .console_view import HELP_TEXT


class WebView:
    def __init__(self) -> None:
        self._events: list[dict] = []

    def _emit(self, kind: str, **data) -> None:
        self._events.append({"kind": kind, **data})

    def drain(self) -> list[dict]:
        events, self._events = self._events, []
        return events

    def show_welcome(self, bot_name: str) -> None:
        self._emit("info", text=f"Hi, I'm {bot_name}. Type /help for commands.")

    def show_reply(self, bot_name: str, text: str) -> None:
        self._emit("bot", sender=bot_name, text=text)

    def show_info(self, text: str) -> None:
        self._emit("info", text=text)

    def show_error(self, text: str) -> None:
        self._emit("error", text=text)

    def show_help(self) -> None:
        self._emit("help", text=HELP_TEXT.replace("/quit                       Exit", "/quit                       End this chat session"))

    def show_history(self, messages: list[Message], bot_name: str) -> None:
        if not messages:
            self.show_info("No messages yet.")
            return
        lines = [f"[{m.timestamp}] {'You' if m.sender == 'user' else bot_name}: {m.text}" for m in messages]
        self._emit("list", title="Conversation history", items=lines)

    def show_learned(self, learned: dict[str, str]) -> None:
        if not learned:
            self.show_info("I haven't been taught anything yet.")
            return
        self._emit("list", title="Things I've been taught", items=[f"{q} -> {a}" for q, a in learned.items()])

    def show_goodbye(self, bot_name: str) -> None:
        self._emit("info", text=f"{bot_name}: Bye! The chat has been reset.")
