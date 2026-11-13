"""A deliberately bounded Portuguese command grammar, independent of the LLM."""
import re
from kiki.domain.actions import SaveNote, CreateReminder, Clarification
from kiki.domain.reminders import schedule_parts
from kiki.domain.text import normalize

SAVE = re.compile(r'^(?:guarde|guardar|salve|salvar|registre|registrar|anote|anotar)\b\s*:?\s*', re.I)
REMIND = re.compile(r'^(?:lembre-me de|me lembre de|crie um lembrete para|lembrete\s*:|agende)\s*', re.I)
COMBINED = re.compile(r'^(?P<note>atendi\s+.+?)\s+e\s+quero\s+(?P<reminder>conferir\b.*)$', re.I)
SPLIT = re.compile(r'(?:;|\s+e\s+)\s*(?=(?:lembre-me de|me lembre de|crie um lembrete para|agende)\b)', re.I)


def _reminder(text, now, note=None):
    due, description = schedule_parts(text, now)
    if not description or (description in {'em', 'para', 'no', 'na', 'dia', 'no dia', 'conferir'} and not note):
        raise ValueError('O que você quer lembrar? Inclua uma descrição no pedido.')
    # Keep the user's original text; do not infer a name or remove accented characters.
    if note:
        text = f'{text} — Referência: {note}'
    return CreateReminder(text, due)


def interpret_request(request, now):
    """Return typed actions, a question, or None for ordinary conversation."""
    text = request.strip()
    text = re.sub(r'^(?:por favor[, ]+|kiki[, ]+)\s*', '', text, flags=re.I)
    save, remind, combined = SAVE.match(text), REMIND.match(text), COMBINED.match(text)
    try:
        if combined:
            note = combined['note'].strip(' ,;')
            return (SaveNote(note), _reminder(combined['reminder'], now, note))
        if save:
            body = text[save.end():]
            parts = SPLIT.split(body, maxsplit=1)
            if not parts[0].strip():
                return Clarification('O que você quer guardar? Reenvie como “Guarde: texto do registro”.')
            actions = (SaveNote(parts[0]),)
            if len(parts) == 2:
                reminder = REMIND.match(parts[1])
                actions += (_reminder(parts[1][reminder.end():], now, parts[0]),)
            return actions
        if remind:
            return (_reminder(text[remind.end():], now),)
    except ValueError as error:
        return Clarification(str(error) + ' Reenvie o pedido completo; nada foi gravado.')
    if re.match(r'^(?:exclua|apague|delete|edite|altere|conclua|cancele)\b', normalize(text)):
        return Clarification('Essa ação ainda deve ser feita pelos botões Memória ou Lembretes. Nada foi alterado.')
    return None
