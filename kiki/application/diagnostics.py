"""Non-destructive checks; never send personal records to the model."""
import json
import platform
import shutil
import urllib.request


def diagnose(settings, folder):
    lines = [f'Python: {platform.python_version()}', f'Dados: {folder}',
             f'Modelo configurado: {settings.model}', 'Servidor: http://127.0.0.1:11434']
    lines.append('Comando Ollama: encontrado.' if shutil.which('ollama') else
                 'Comando Ollama: não encontrado no PATH. Se o serviço não responder, instale em ollama.com/download/windows.')
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open('http://127.0.0.1:11434/api/tags', timeout=5) as response:
            payload = json.load(response)
        models = payload['models']
        if not isinstance(models, list) or any(not isinstance(item, dict) or not isinstance(item.get('name'), str) for item in models):
            raise ValueError('Formato inválido')
        names = {item['name'] for item in models}
        expected = settings.model if ':' in settings.model else settings.model + ':latest'
        lines.append('Ollama: serviço local acessível.')
        if expected in names:
            lines.append('Modelo: instalado. Pronto para testar uma conversa; desempenho ainda não medido.')
        else:
            lines.append(f'Modelo: não encontrado. Execute no PowerShell: ollama pull {settings.model}')
    except (ValueError, KeyError, TypeError):
        lines.append('Ollama: resposta inválida. Atualize ou reinicie o Ollama e tente novamente.')
    except OSError:
        lines.append('Ollama: sem resposta local. Abra o Ollama, aguarde iniciar e clique em Verificar novamente.')
    return '\n\n'.join(lines)
