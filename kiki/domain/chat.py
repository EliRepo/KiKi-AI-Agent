"""Conversation data is separate from notes and executable proposals."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChatMessage:
    key: str
    role: str
    text: str
    status: str
    created: str
    sources: tuple = ()
    stored_id: int | None = None


@dataclass
class ChatSession:
    key: str
    title: str = 'Nova conversa'
    stored_id: int | None = None
    messages: list[ChatMessage] = field(default_factory=list)
    draft: str = ''
