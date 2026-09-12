import os
from django.core.asgi import get_asgi_application
from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.generic.websocket import AsyncWebsocketConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

class FallbackWebSocketConsumer(AsyncWebsocketConsumer):
    """Gracefully close unmatched WebSocket connections to prevent unhandled ValueError tracebacks."""
    async def connect(self):
        await self.close()

# ProtocolTypeRouter routes HTTP requests to standard Django views,
# and WebSocket requests to Channels URLRouter.
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            # App-specific WebSocket routes will be linked here
            re_path(r"^.*$", FallbackWebSocketConsumer.as_asgi()),
        ])
    ),
})

