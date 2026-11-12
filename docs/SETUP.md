# Instalação e operação no Windows 11

## Pré-requisitos

Python 3.11+ com launcher `py` e Tcl/Tk: https://www.python.org/downloads/windows/ . Ollama é opcional para memória/agenda e necessário para conversar: https://ollama.com/download/windows . Reserve espaço para o modelo e faça primeiro o teste com dados fictícios.

```powershell
git clone https://github.com/EliRepo/KiKi-AI-Agent.git
cd KiKi-AI-Agent
py -3 -m kiki
```

Se recebeu um ZIP, extraia e abra `scripts/start.cmd`. A branch `feat/kiki-modular-foundation` contém a entrega para revisão enquanto o pull request não for integrado à main.

## Ollama local

No PowerShell:

```powershell
[Environment]::SetEnvironmentVariable('OLLAMA_NO_CLOUD', '1', 'User')
```

Encerre o Ollama pelo ícone próximo ao relógio e abra novamente para receber essa configuração. Depois:

```powershell
ollama pull qwen3:1.7b
ollama list
```

O download requer internet. O endpoint usado é `http://127.0.0.1:11434/api/chat`; a KiKi ignora proxies nessa chamada. Não configure `OLLAMA_HOST` para expor o serviço à rede. Documentação da API: https://docs.ollama.com/api/chat e configuração: https://docs.ollama.com/faq . Não há provedor online alternativo na KiKi.

## Dados e recuperação

### Cores e tipografia

Abra Configuração e escolha Claro ou Escuro. Ambos usam as respectivas paletas violeta. Selecione uma fonte disponível ou Automática e ajuste o tamanho entre 11 e 18. Salvar e aplicar atualiza a janela sem perder rascunhos e preserva a escolha para a próxima abertura. Inter acompanha o aplicativo e é carregada privadamente no Windows; não é preciso instalá-la no sistema. A fonte efetivamente aplicada aparece na tela. Segoe UI Variable só aparece se já estiver instalada. Consulte THIRD_PARTY_NOTICES.md.

Na aba **Configuração**, informe um modelo local e clique em **Salvar configuração**. A escolha fica em `%LOCALAPPDATA%\KiKi\settings.json` e é usada nas próximas perguntas e ao reabrir. O botão **Verificar ambiente** informa a versão do Python, pasta dos dados, presença do comando Ollama, disponibilidade do serviço e do modelo. Não inicia instalações nem downloads. Mensagens indicam como corrigir o problema. Esse diagnóstico não mede a qualidade nem o desempenho da IA.

Se o arquivo de configuração estiver inválido, a KiKi avisa e usa o modelo padrão apenas na sessão; salvar uma nova configuração substitui o arquivo inválido. O backup SQLite não inclui `settings.json`; preserve-o separadamente se quiser manter essa preferência.

Banco: `%LOCALAPPDATA%\KiKi\kiki.sqlite3`. Compatível com o protótipo anterior. Sem criptografia própria. O botão de backup cria uma cópia consistente mesmo com o aplicativo aberto; o arquivo contém todos os registros e tarefas.

Para restaurar, feche a KiKi. Preserve uma cópia do banco atual, copie o backup para essa pasta com o nome `kiki.sqlite3` e reabra. Não substitua o banco com a aplicação aberta. Não guarde dados reais no repositório.

## Limites operacionais

- Use uma instância por vez.
- Fechar encerra os avisos. Não existe serviço em segundo plano ou ícone na bandeja.
- O computador deve estar ligado e acordado; ao reabrir, lembretes vencidos ainda não avisados aparecem.
- Avisos são janelas do aplicativo, não notificações nativas do Windows.
- Datas usam o horário do computador. Não há conversão de fuso, recorrência ou interpretação de “semana que vem”.
- A conversa não é persistida e não salva nem agenda ações.
- Busca é textual, sem sinônimos; contexto pode omitir partes longas de registros.

## Aceitação manual

1. Guarde “Atendi Ana e corrigi o acesso ajustando a permissão”. Feche e reabra; busque Ana.
2. Preencha uma frase com amanhã e horário; confira a data antes de salvar. Frase sem horário deve pedir correção.
3. Crie aviso para dois minutos à frente, aguarde e conclua a pendência.
4. Com o modelo pronto, pergunte “Como resolvi o problema da Ana?”. Confira conteúdo e ID.
5. Desconecte a internet e repita. Feche Ollama e confirme que memória/agenda continuam disponíveis.
6. Faça backup; teste recuperação com dados fictícios e confira registros e pendências.

Não há benchmark real registrado ainda. Informe tempos, memória observada e erros no ensaio para atualizar o roadmap.
