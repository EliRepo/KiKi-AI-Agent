"""Failure contracts; no local service or model download is required."""
import io
import json
import unittest
import urllib.error
from unittest.mock import patch

from kiki.infrastructure.ollama import OllamaError, ask_ollama


class OllamaFailureTests(unittest.TestCase):
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
