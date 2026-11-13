"""Opt-in real inference with fictional records; never opens the user's database.

Run from the checkout: python -m scripts.benchmark_ollama --output result.json
The model must already be installed. This script does not install or download it.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import platform
import time

from kiki.application.context import retrieve_context
from kiki.infrastructure.memory import Memory
from kiki.infrastructure.ollama import OllamaError, ask_ollama
from kiki.infrastructure.settings import Settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default='qwen3:1.7b')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    settings = Settings(model=args.model)
    result = {'started_at': dt.datetime.now().astimezone().isoformat(timespec='seconds'),
              'python': platform.python_version(), 'platform': platform.platform(),
              'model': settings.model, 'data': 'fictional, in-memory SQLite', 'cases': []}
    memory = Memory(':memory:')
    try:
        memory.save('Atendi Ana e corrigi o acesso ajustando a permissão.')
        memory.save('Bruno: configurei a impressora e imprimi uma página de teste.')
        questions = [
            ('Como resolvi o problema da Ana?', 'Citar ajuste da permissão e fonte #1.'),
            ('O que fiz para Bruno?', 'Citar impressora, página de teste e fonte #2.'),
            ('Qual é o telefone da Carla?', 'Reconhecer falta de informação; não inventar telefone.'),
        ]
        for question, expected in questions:
            records = retrieve_context(memory, question)
            case = {'question': question, 'expected': expected,
                    'source_ids': [row[0] for row in records]}
            started = time.perf_counter()
            try:
                case['answer'] = ask_ollama(question, records, settings)
                case['status'] = 'response_received'
            except OllamaError as error:
                case['error'] = str(error)
                case['status'] = 'failed'
            case['response_seconds'] = round(time.perf_counter() - started, 3)
            result['cases'].append(case)
            print(json.dumps(case, ensure_ascii=False), flush=True)
    finally:
        memory.db.close()
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return int(any(case['status'] == 'failed' for case in result['cases']))


if __name__ == '__main__':
    raise SystemExit(main())
