"""Bot model: decides what to say. Pure logic — no printing, no input()."""

from __future__ import annotations

import ast
import operator
import random
import re
from dataclasses import dataclass
from datetime import datetime

from .knowledge_base import KnowledgeBase

FALLBACKS = [
    "I'm not sure I understand. Try /help, or teach me with /teach question = answer.",
    "Hmm, I don't know that one yet. You can teach me with /teach question = answer.",
]

_MATH_RE = re.compile(r"^\s*(?:what is|calculate|calc|compute)?\s*([-+*/().%\d\s]+?)\s*\??\s*$", re.I)
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


@dataclass
class BotReply:
    text: str
    source: str  # "learned", "intent:<name>", "math", "time", "fallback"


def safe_eval(expression: str) -> float:
    """Evaluate + - * / % and parentheses without using eval()."""

    def walk(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](walk(node.operand))
        raise ValueError("Unsupported expression")

    return walk(ast.parse(expression, mode="eval"))


class Bot:
    def __init__(self, knowledge: KnowledgeBase, name: str = "Bolt", seed: int | None = None) -> None:
        self.knowledge = knowledge
        self.name = name
        self._rng = random.Random(seed)

    def reply(self, text: str) -> BotReply:
        text = text.strip()

        learned = self.knowledge.lookup_learned(text)
        if learned:
            return BotReply(learned, "learned")

        math_reply = self._try_math(text)
        if math_reply:
            return math_reply

        intent = self.knowledge.best_intent(text)
        if intent:
            if intent.name == "time":
                return BotReply(f"It's {datetime.now():%H:%M} on {datetime.now():%A, %d %B %Y}.", "time")
            response = intent.respond(self._rng).replace("{name}", self.name)
            return BotReply(response, f"intent:{intent.name}")

        return BotReply(self._rng.choice(FALLBACKS), "fallback")

    def _try_math(self, text: str) -> BotReply | None:
        match = _MATH_RE.match(text)
        if not match or not re.search(r"\d\s*[-+*/%]\s*[\d(]", match.group(1)):
            return None
        try:
            result = safe_eval(match.group(1))
        except ZeroDivisionError:
            return BotReply("You can't divide by zero!", "math")
        except (ValueError, SyntaxError):
            return None
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return BotReply(f"{match.group(1).strip()} = {result}", "math")
