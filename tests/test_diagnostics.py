import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import uuid

from kiki.application.diagnostics import diagnose
from kiki.infrastructure.settings import Settings


class SettingsTests(unittest.TestCase):
    def test_configuration_round_trip_and_invalid_file(self):
        folder = Path.cwd() / ('settings-test-' + uuid.uuid4().hex)
        folder.mkdir()
        try:
            self.assertEqual(Settings.load(folder), Settings())
            Settings('qwen3:0.6b').save(folder)
            self.assertEqual(Settings.load(folder).model, 'qwen3:0.6b')
            Settings('qwen3:0.6b', 'light', 'Arial', 15).save(folder)
            self.assertEqual(Settings.load(folder), Settings('qwen3:0.6b', 'light', 'Arial', 15))
            (folder / 'settings.json').write_text('{"model":"qwen3:1.7b"}', encoding='utf-8')
            self.assertEqual(Settings.load(folder), Settings())
            (folder / 'settings.json').write_text('{broken', encoding='utf-8')
            with self.assertRaises(ValueError):
                Settings.load(folder)
        finally:
            (folder / 'settings.json').unlink(missing_ok=True)
            folder.rmdir()

    def test_remote_or_malformed_model_rejected(self):
        for model in ['https://example.com/model', '../model', 'model:cloud', '', 'a;command', None]:
            with self.assertRaises(ValueError):
                Settings(model)


class DiagnosticsTests(unittest.TestCase):
    def test_portable_installation_is_detected_without_path_entry(self):
        with patch('kiki.application.diagnostics.shutil.which', return_value=None), \
             patch.dict('os.environ', {'LOCALAPPDATA': 'example-local-data'}), \
             patch('kiki.application.diagnostics.Path.is_file', return_value=True), \
             patch('kiki.application.diagnostics.urllib.request.build_opener') as factory:
            factory.return_value.open.side_effect = OSError('offline')
            result = diagnose(Settings(), Path('example-data'))
        self.assertIn('Comando Ollama: encontrado em', result)
        self.assertIn('ollama.exe', result)

    def check(self, payload):
        with patch('kiki.application.diagnostics.urllib.request.build_opener') as factory:
            factory.return_value.open.return_value = io.BytesIO(json.dumps(payload).encode())
            result = diagnose(Settings(), Path('example-data'))
            args, kwargs = factory.return_value.open.call_args
            self.assertEqual(args[0], 'http://127.0.0.1:11434/api/tags')
            self.assertEqual(kwargs['timeout'], 5)
            return result

    def test_available_and_missing_model(self):
        self.assertIn('Modelo: instalado', self.check({'models': [{'name': 'qwen3:1.7b'}]}))
        self.assertIn('ollama pull qwen3:1.7b', self.check({'models': []}))

    def test_malformed_response(self):
        self.assertIn('resposta inválida', self.check({'models': 'wrong'}))

    def test_service_unavailable(self):
        with patch('kiki.application.diagnostics.urllib.request.build_opener') as factory:
            factory.return_value.open.side_effect = OSError('offline')
            self.assertIn('Abra o Ollama', diagnose(Settings(), Path('example-data')))
