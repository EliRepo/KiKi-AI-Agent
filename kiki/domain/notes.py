"""Memory records and validation, independent of storage and interface."""
from dataclasses import dataclass


class NoteNotFoundError(LookupError):
    pass


class NoteConflictError(ValueError):
    pass


@dataclass(frozen=True)
class Note:
    id: int
    text: str
    created: str
    updated: str | None
    revision: int


def validate_note_text(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Escreva um texto para o registro.')
    return text.strip()
