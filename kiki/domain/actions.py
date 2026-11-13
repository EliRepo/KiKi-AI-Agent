"""Typed, immutable action contracts. No storage, UI or model dependency."""
from dataclasses import dataclass
import datetime as dt
from enum import Enum
from kiki.domain.notes import validate_note_text


@dataclass(frozen=True)
class SaveNote:
    text: str

    def __post_init__(self):
        object.__setattr__(self, 'text', validate_note_text(self.text))


@dataclass(frozen=True)
class CreateReminder:
    text: str
    due: dt.datetime

    def __post_init__(self):
        object.__setattr__(self, 'text', validate_note_text(self.text))
        if not isinstance(self.due, dt.datetime) or self.due.tzinfo is not None:
            raise ValueError('Informe data e horário locais válidos para o lembrete.')
        if self.due.second or self.due.microsecond:
            raise ValueError('Use um horário com precisão de minutos.')


Action = SaveNote | CreateReminder


def validate_actions(actions):
    if not isinstance(actions, tuple) or not 1 <= len(actions) <= 2:
        raise ValueError('A proposta precisa conter uma ou duas ações permitidas.')
    kinds = [type(action) for action in actions]
    if any(kind not in (SaveNote, CreateReminder) for kind in kinds) or len(set(kinds)) != len(kinds):
        raise ValueError('Esta combinação de ferramentas não é permitida.')


class ProposalState(str, Enum):
    PROPOSED = 'proposta'
    CONFIRMED = 'confirmada'
    EXECUTED = 'executada'
    CANCELLED = 'cancelada'
    FAILED = 'falhou'


@dataclass(frozen=True)
class ActionResult:
    note_id: int | None = None
    task_id: int | None = None
    replayed: bool = False


@dataclass(frozen=True)
class ActionProposal:
    id: str
    request: str
    actions: tuple[Action, ...]
    state: ProposalState = ProposalState.PROPOSED
    result: ActionResult | None = None
    error: str | None = None

    def __post_init__(self):
        validate_actions(self.actions)


@dataclass(frozen=True)
class Clarification:
    message: str
