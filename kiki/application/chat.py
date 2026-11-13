"""Session navigation and opt-in history. Loading history never executes requests."""
from dataclasses import replace
import datetime as dt
import uuid
from kiki.domain.chat import ChatMessage, ChatSession


class ChatManager:
    def __init__(self, memory, history_enabled=False, retention_days=30, clock=None):
        self.memory, self.clock = memory, clock or dt.datetime.now
        self.sessions, self.pending = {}, {}
        self.current_key = None
        self.history_enabled, self.retention_days = False, 30
        self.new_chat()
        self.configure(history_enabled, retention_days)

    @property
    def current(self):
        return self.sessions[self.current_key]

    def _idle(self):
        if self.pending:
            raise ValueError('Aguarde o resultado ou cancele a proposta antes de trocar de conversa/configuração.')

    def new_chat(self):
        self._idle()
        session = ChatSession(uuid.uuid4().hex)
        self.sessions[session.key] = session
        self.current_key = session.key
        return session

    def configure(self, enabled, days):
        self._idle()
        if type(enabled) is not bool or type(days) is not int or days not in (0, 7, 30, 90):
            raise ValueError('Escolha uma retenção de 7, 30, 90 dias ou até excluir manualmente.')
        if enabled and days:
            cutoff = (self.clock() - dt.timedelta(days=days)).isoformat(timespec='seconds')
            self.memory.prune_conversations(cutoff)
            existing = {row[0] for row in self.memory.conversation_list()}
            self.sessions = {key: session for key, session in self.sessions.items()
                             if session.stored_id is None or session.stored_id in existing}
            if self.current_key not in self.sessions:
                self.new_chat()
        self.history_enabled, self.retention_days = enabled, days

    def summaries(self):
        stored = self.memory.conversation_list()
        loaded = {session.stored_id: key for key, session in self.sessions.items() if session.stored_id is not None}
        summaries = [(loaded.get(identifier, f'saved-{identifier}'), title, True) for identifier, title, _, _ in stored]
        return [(session.key, session.title, False) for session in self.sessions.values() if session.stored_id is None] + summaries

    def open_chat(self, key):
        self._idle()
        if key not in self.sessions:
            available = {f'saved-{row[0]}': row for row in self.memory.conversation_list()}
            if key not in available:
                raise ValueError('Conversa não encontrada.')
            identifier, title, _, _ = available[key]
            session = ChatSession(key, title, identifier)
            for message_id, role, text, status, sources, created in self.memory.conversation_messages(identifier):
                if status == 'pending':
                    text = 'A sessão terminou antes de registrar o resultado nesta conversa. Confira Memória e Lembretes antes de repetir.'
                    status = 'interrupted'
                session.messages.append(ChatMessage(uuid.uuid4().hex, role, text, status, created, sources, message_id))
            self.sessions[key] = session
        self.current_key = key
        return self.current

    def begin(self, text, kind='ok'):
        self._idle()
        text = text.strip()
        if not text:
            raise ValueError('Escreva uma mensagem.')
        session = self.current
        if (not self.history_enabled and session.stored_id is not None) or (
            self.history_enabled and session.stored_id is None and session.messages
        ):
            session = self.new_chat()
        title = session.title if session.messages else text.replace('\n', ' ')[:60]
        created = self.clock().isoformat(timespec='seconds')
        user = ChatMessage(uuid.uuid4().hex, 'user', text, kind, created)
        reply = ChatMessage(uuid.uuid4().hex, 'assistant', 'Aguardando resultado…', 'pending', created)
        if self.history_enabled:
            identifier, user_id, reply_id = self.memory.begin_chat_exchange(session.stored_id, title, text, kind, created)
            session.stored_id = identifier
            user, reply = replace(user, stored_id=user_id), replace(reply, stored_id=reply_id)
        session.title = title
        session.messages.extend([user, reply])
        session.draft = ''
        self.pending[reply.key] = session.key
        return session.key, reply.key

    def complete(self, session_key, reply_key, text, status='ok', sources=()):
        if self.pending.get(reply_key) != session_key:
            raise ValueError('Esse resultado não pertence à consulta em andamento.')
        session = self.sessions[session_key]
        index = next(index for index, message in enumerate(session.messages) if message.key == reply_key)
        message = replace(session.messages[index], text=text, status=status, sources=tuple(sources))
        session.messages[index] = message
        del self.pending[reply_key]
        if message.stored_id is not None:
            self.memory.complete_chat_message(session.stored_id, message.stored_id, text, status, sources,
                                               self.clock().isoformat(timespec='seconds'))
        return message

    def context(self):
        messages, remaining = [], 3000
        for message in reversed(self.current.messages):
            if message.status != 'ok':
                continue
            text = message.text[:min(1000, remaining)]
            if text:
                messages.append({'role': message.role, 'content': text})
                remaining -= len(text)
            if remaining <= 0 or len(messages) == 6:
                break
        return list(reversed(messages))

    def delete_chat(self, key):
        self._idle()
        session = self.open_chat(key)
        if session.stored_id is not None:
            self.memory.delete_conversation(session.stored_id)
        del self.sessions[key]
        self.new_chat()

    def clear_history(self):
        self._idle()
        self.memory.clear_conversations()
        self.sessions.clear()
        self.new_chat()
