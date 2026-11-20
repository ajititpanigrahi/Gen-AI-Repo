"""Entry point: build the models, a view and the controller, then start chatting.

Console:  python main.py
Web:      python main.py --web            (then open http://127.0.0.1:5000)
"""

import argparse
from pathlib import Path

from chatbot.controllers import ChatController
from chatbot.models import Bot, Conversation, KnowledgeBase
from chatbot.views import ConsoleView

BASE_DIR = Path(__file__).resolve().parent
INTENTS_PATH = BASE_DIR / "chatbot" / "data" / "intents.json"
STORAGE_DIR = BASE_DIR / "storage"
BOT_NAME = "Bolt"


def run_console() -> None:
    knowledge = KnowledgeBase.from_file(INTENTS_PATH, STORAGE_DIR / "learned.json")
    bot = Bot(knowledge, name=BOT_NAME)
    controller = ChatController(bot, Conversation(), ConsoleView(), STORAGE_DIR / "history.json")
    controller.run()


def run_web(host: str, port: int, debug: bool) -> None:
    try:
        from chatbot.web_app import create_app
    except ImportError:
        raise SystemExit("The web view needs Flask. Install it with:  pip install -r requirements.txt")
    app = create_app(INTENTS_PATH, STORAGE_DIR, bot_name=BOT_NAME)
    app.run(host=host, port=port, debug=debug)


def main() -> None:
    parser = argparse.ArgumentParser(description="MVC chatbot")
    parser.add_argument("--web", action="store_true", help="run the web view instead of the console")
    parser.add_argument("--host", default="127.0.0.1", help="web host (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="web port (default 5000)")
    parser.add_argument("--debug", action="store_true", help="Flask debug mode (auto-reload)")
    args = parser.parse_args()

    if args.web:
        run_web(args.host, args.port, args.debug)
    else:
        run_console()


if __name__ == "__main__":
    main()
