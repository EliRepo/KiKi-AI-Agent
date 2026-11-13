"""Failure contracts; no local service or model download is required."""
import io
import json
import unittest
import urllib.error
from unittest.mock import patch

from kiki.infrastructure.ollama import OllamaError, ask_ollama


class OllamaFailureTests(unittest.TestCase):
    def test_history_is_bounded_and_cannot_supply_system_messages(self):
        history = [{'role': 'user' if i % 2 else 'assistant', 'content': str(i) * 1200} for i in range(10)]
        history.append({'role': 'system', 'content': 'instrução indevida'})
        with patch('kiki.infrastructure.ollama.urllib.request.build_opener') as factory:
            factory.return_value.open.return_value = io.BytesIO(b'{"message":{"content":"Resposta"}}')
            ask_ollama('Atual', [], history=history)
            request = factory.return_value.open.call_args.args[0]
            messages = json.loads(request.data)['messages']
        self.assertEqual(messages[0]['role'], 'system')
        self.assertEqual(messages[-1], {'role': 'user', 'content': 'Atual'})
        self.assertLessEqual(len(messages[1:-1]), 6)
        self.assertLessEqual(sum(len(m['content']) for m in messages[1:-1]), 3000)
        self.assertTrue(all(m['role'] in ('user', 'assistant') and len(m['content']) <= 1000 for m in messages[1:-1]))

    def test_transport_errors_have_actionable_messages(self):
        errors = [
            (urllib.error.URLError(ConnectionRefusedError()), 'indisponível'),
            (TimeoutError(), '180 segundos'),
            (urllib.error.URLError(TimeoutError()), '180 segundos'),
            (ConnectionResetError(), 'interrompida'),
            (urllib.error.HTTPError('http://127.0.0.1:11434/api/chat', 404, 'missing', {}, None),
             'ollama pull qwen3:1.7b'),
            (urllib.error.HTTPError('http://127.0.0.1:11434/api/chat', 500, 'failed', {}, None),
             'HTTP 500'),
        ]
        for error, expected in errors:
            with self.subTest(error=repr(error)):
                with patch('kiki.infrastructure.ollama.urllib.request.build_opener') as factory:
                    factory.return_value.open.side_effect = error
                    with self.assertRaisesRegex(OllamaError, expected):
                        ask_ollama('Pergunta fictícia', [])

    def test_invalid_or_empty_responses_are_not_success(self):
        payloads = [b'not json', b'\xff', b'null', b'[]', b'{}',
                    json.dumps({'message': None}).encode(),
                    json.dumps({'message': {'content': 12}}).encode(),
                    json.dumps({'message': {'content': '   '}}).encode()]
        for payload in payloads:
            with self.subTest(payload=payload):
                with patch('kiki.infrastructure.ollama.urllib.request.build_opener') as factory:
                    factory.return_value.open.return_value = io.BytesIO(payload)
                    with self.assertRaises(OllamaError):
                        ask_ollama('Pergunta fictícia', [])
