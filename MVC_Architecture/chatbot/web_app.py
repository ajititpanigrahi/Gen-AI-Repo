"""Flask front end. It only wires HTTP to the existing MVC pieces:

    browser --HTTP--> route --> ChatController.handle() --> Bot (model)
                                       |
                                       v
                                   WebView  --drain()--> JSON --> browser

Each browser gets its own Conversation + controller (keyed by a session cookie);
the knowledge base (taught answers) is shared by everyone.
"""

from __future__ import annotations

import os
import secrets
import threading
from dataclasses import asdict
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session

from .controllers import ChatController
from .models import Bot, Conversation, KnowledgeBase
from .views import WebView

MAX_MESSAGE_LENGTH = 1000


class SessionStore:
    """Keeps one controller (with its own conversation and view) per browser session."""

    def __init__(self, bot: Bot, storage_dir: Path) -> None:
        self.bot = bot
        self.storage_dir = Path(storage_dir)
        self._controllers: dict[str, ChatController] = {}
        self.lock = threading.Lock()

    def get(self, sid: str) -> ChatController:
        if sid not in self._controllers:
            self._controllers[sid] = ChatController(
                self.bot, Conversation(), WebView(), self.storage_dir / f"history-{sid}.json"
            )
        return self._controllers[sid]

    def reset(self, sid: str) -> None:
        self._controllers.pop(sid, None)


def create_app(intents_path: Path, storage_dir: Path, bot_name: str = "Bolt") -> Flask:
    app = Flask(__name__, template_folder="views/templates")
    app.secret_key = os.environ.get("CHATBOT_SECRET_KEY") or secrets.token_hex(32)

    knowledge = KnowledgeBase.from_file(intents_path, Path(storage_dir) / "learned.json")
    store = SessionStore(Bot(knowledge, name=bot_name), storage_dir)
    app.extensions["chat_store"] = store

    def session_id() -> str:
        if "sid" not in session:
            session["sid"] = secrets.token_hex(8)
        return session["sid"]

    @app.get("/")
    def index():
        session_id()
        return render_template("chat.html", bot_name=bot_name)

    @app.get("/api/history")
    def history():
        with store.lock:
            controller = store.get(session_id())
            messages = [asdict(m) for m in controller.conversation.messages]
        return jsonify(bot_name=bot_name, messages=messages)

    @app.post("/api/message")
    def message():
        payload = request.get_json(silent=True) or {}
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            return jsonify(error="Message text is required."), 400
        if len(text) > MAX_MESSAGE_LENGTH:
            return jsonify(error=f"Message is longer than {MAX_MESSAGE_LENGTH} characters."), 400

        sid = session_id()
        with store.lock:
            controller = store.get(sid)
            keep_going = controller.handle(text)
            if not keep_going:
                controller.view.show_goodbye(bot_name)
            events = controller.view.drain()
            if not keep_going:
                store.reset(sid)
        return jsonify(events=events, ended=not keep_going)

    return app
