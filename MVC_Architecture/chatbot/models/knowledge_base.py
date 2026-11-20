"""Knowledge base model: intents the bot understands, plus facts it has been taught."""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

_WORD_RE = re.compile(r"[a-z0-9']+")


def tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def normalize(text: str) -> str:
    return " ".join(_WORD_RE.findall(text.lower()))


@dataclass
class Intent:
    name: str
    patterns: list[str]
    responses: list[str]
    _pattern_tokens: list[set[str]] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self._pattern_tokens = [tokenize(p) for p in self.patterns]

    def score(self, text: str) -> float:
        """Best overlap between the text and any pattern (0.0 – 1.0)."""
        words = tokenize(text)
        if not words:
            return 0.0
        best = 0.0
        for pattern in self._pattern_tokens:
            if not pattern:
                continue
            overlap = len(words & pattern) / len(pattern)
            best = max(best, overlap)
        return best

    def respond(self, rng: random.Random) -> str:
        return rng.choice(self.responses)


class KnowledgeBase:
    def __init__(self, intents: list[Intent], learned_path: Path | None = None) -> None:
        self.intents = intents
        self.learned_path = Path(learned_path) if learned_path else None
        self.learned: dict[str, str] = {}
        if self.learned_path and self.learned_path.exists():
            self.learned = json.loads(self.learned_path.read_text(encoding="utf-8"))

    @classmethod
    def from_file(cls, intents_path: Path, learned_path: Path | None = None) -> "KnowledgeBase":
        raw = json.loads(Path(intents_path).read_text(encoding="utf-8"))
        intents = [Intent(i["name"], i["patterns"], i["responses"]) for i in raw["intents"]]
        return cls(intents, learned_path)

    def best_intent(self, text: str, threshold: float = 0.5) -> Intent | None:
        scored = [(intent.score(text), intent) for intent in self.intents]
        score, intent = max(scored, key=lambda pair: pair[0], default=(0.0, None))
        return intent if score >= threshold else None

    def teach(self, question: str, answer: str) -> None:
        key = normalize(question)
        if not key or not answer.strip():
            raise ValueError("Both a question and an answer are required.")
        self.learned[key] = answer.strip()
        self._save_learned()

    def forget(self, question: str) -> bool:
        removed = self.learned.pop(normalize(question), None) is not None
        if removed:
            self._save_learned()
        return removed

    def lookup_learned(self, question: str) -> str | None:
        return self.learned.get(normalize(question))

    def _save_learned(self) -> None:
        if self.learned_path:
            self.learned_path.parent.mkdir(parents=True, exist_ok=True)
            self.learned_path.write_text(json.dumps(self.learned, indent=2), encoding="utf-8")
