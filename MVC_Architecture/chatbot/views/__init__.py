"""Views: everything the user sees. Swap one view for another without touching models or controllers."""

from .base import ChatView
from .console_view import ConsoleView
from .web_view import WebView

__all__ = ["ChatView", "ConsoleView", "WebView"]
