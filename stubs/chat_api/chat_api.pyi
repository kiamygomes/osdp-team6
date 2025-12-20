from typing import Any

class Message:
    content: str
    channel_id: str
    user_id: str
    timestamp: str

    def __init__(
        self,
        content: str,
        channel_id: str,
        user_id: str,
        timestamp: str,
    ) -> None: ...

class ChatInterface:
    def __init__(self, **kwargs: Any) -> None: ...
    def send_message(self, channel_id: str, content: str) -> bool: ...
    def get_messages(
        self,
        channel_id: str,
        limit: int = 10,
    ) -> list[Message]: ...
