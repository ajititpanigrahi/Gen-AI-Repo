"""Conversation model: keeps the message history and can save/load it."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Message:
    sender: str  # "user" or "bot"
    text: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


class Conversation:
    def __init__(self) -> None:
        self._messages: list[Message] = []

    def add(self, sender: str, text: str) -> Message:
        if sender not in ("user", "bot"):
            raise ValueError(f"Unknown sender: {sender!r}")
        message = Message(sender, text)
        self._messages.append(message)
        return message

    @property
    def messages(self) -> list[Message]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    def __len__(self) -> int:
        return len(self._messages)

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(m) for m in self._messages]
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Conversation":
        conversation = cls()
        path = Path(path)
        if path.exists():
            for item in json.loads(path.read_text(encoding="utf-8")):
                conversation._messages.append(Message(**item))
        return conversation
