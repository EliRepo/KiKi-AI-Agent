"""Local settings, separate from personal records."""
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path
import re


def data_directory():
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home() / '.local' / 'share'))) / 'KiKi'


@dataclass(frozen=True)
class Settings:
    model: str = 'qwen3:1.7b'
    theme: str = 'dark'
    font_family: str = 'Automática'
    font_size: int = 13
    history_enabled: bool = False
    history_days: int = 30

    def __post_init__(self):
        if not isinstance(self.model, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+(?::[A-Za-z0-9_.-]+)?', self.model) or 'cloud' in self.model.lower():
            raise ValueError('Use o nome de um modelo local, como qwen3:1.7b. Modelos de nuvem não são permitidos.')
        if self.theme not in ('light', 'dark'):
            raise ValueError('Escolha o tema claro ou escuro.')
        if not isinstance(self.font_family, str) or not self.font_family.strip() or len(self.font_family) > 100:
            raise ValueError('Escolha uma família de fonte válida.')
        if type(self.font_size) is not int or not 11 <= self.font_size <= 18:
            raise ValueError('O tamanho de leitura deve estar entre 11 e 18.')
        if type(self.history_enabled) is not bool or type(self.history_days) is not int or self.history_days not in (0, 7, 30, 90):
            raise ValueError('Escolha uma preferência válida de histórico e retenção.')

    @classmethod
    def load(cls, folder):
        path = folder / 'settings.json'
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                raise ValueError('Formato inválido')
            return cls(model=data['model'], theme=data.get('theme', 'dark'),
                       font_family=data.get('font_family', 'Automática'), font_size=data.get('font_size', 13),
                       history_enabled=data.get('history_enabled', False), history_days=data.get('history_days', 30))
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise ValueError('Não foi possível ler settings.json. Corrija o arquivo ou renomeie-o para usar o padrão.') from error

    def save(self, folder):
        folder.mkdir(parents=True, exist_ok=True)
        temporary = folder / 'settings.json.tmp'
        temporary.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(folder / 'settings.json')
