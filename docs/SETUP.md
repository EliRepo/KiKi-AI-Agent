# Instalação e operação no Windows 11

## Pré-requisitos

Python 3.11+ com launcher `py` e Tcl/Tk: https://www.python.org/downloads/windows/ . Ollama é opcional para memória/agenda e necessário para conversar: https://ollama.com/download/windows . Reserve espaço para o modelo e faça primeiro o teste com dados fictícios.

```powershell
git clone https://github.com/EliRepo/KiKi-AI-Agent.git
cd KiKi-AI-Agent
py -3 -m kiki
```

Se recebeu um ZIP, extraia e abra `scripts/start.cmd`. O iniciador prefere `.venv\Scripts\python.exe`, quando esse ambiente já existir; caso contrário usa `py -3`. Criar o ambiente é opcional: `py -3 -m venv .venv`. A base publicada está na main; a próxima entrega M02 está em avaliação local.

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

### Instalação portátil usada neste computador

O pacote oficial Ollama 0.40.16 foi extraído em `%LOCALAPPDATA%\Programs\Ollama`, com SHA-256 verificado. Essa instalação não adicionou atalho, entrada no PATH nem inicialização automática. Para iniciar o serviço manualmente, abra `scripts/start-ollama.cmd`: ele usa essa pasta, desativa nuvem e fixa o servidor em `127.0.0.1:11434`. Mantenha o serviço aberto enquanto conversa. Se outro Ollama já estiver atendendo nessa porta, não inicie uma segunda instância. A KiKi continua sendo aberta por `scripts/start.cmd`.

Se o comando não estiver no PATH, use no PowerShell:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" list
```

O diagnóstico reconhece tanto o comando no PATH quanto o executável nessa pasta. Modelos ficam em `%USERPROFILE%\.ollama\models`, fora do repositório. O modelo qwen3:1.7b já foi baixado neste computador. Referência oficial para o pacote portátil: https://docs.ollama.com/windows .

### Ensaio real, opcional

Na raiz do checkout, com Ollama aberto e modelo instalado:

```powershell
.\.venv\Scripts\python.exe -m scripts.benchmark_ollama --output resultado-local.json
```

Esse comando envia três perguntas com registros fictícios em SQLite na memória, sem abrir o banco pessoal. Não instala nem baixa modelos. O arquivo contém perguntas, respostas e duração; receber uma resposta não significa que seu conteúdo passou na avaliação. Confira fatos e citações manualmente. Os testes unitários continuam sem rede ou downloads.

A conversa agora diferencia indisponibilidade, timeout de 180 segundos, modelo ausente e resposta inválida. Uma falha fica identificada como falha, preserva a pergunta e libera o botão para tentar novamente. Não há repetição automática de consultas.

## Dados e recuperação

### Edição e exclusão de registros

Em Memória, selecione uma linha para ler o texto completo abaixo. **Editar selecionado** (ou duplo clique/Enter na linha) abre uma janela separada; **Salvar alterações** grava a correção. O rascunho de um novo registro permanece no campo principal. Cancelar ou fechar o editor pede confirmação se houver mudanças ainda não salvas.

**Excluir selecionado…** mostra ID e prévia antes da confirmação. Cancelar não muda o banco. A exclusão não tem desfazer e não apaga cópias de segurança já existentes. Se o registro mudar enquanto a confirmação/editor estiver aberto, a KiKi recusa a versão antiga e pede nova conferência.

### Atualização automática do banco

O esquema atual é a versão 2. Ao abrir um banco do protótipo anterior, a KiKi cria uma cópia consistente na mesma pasta, com nome `kiki.pre-migration-v0-<identificador>.sqlite3` (ou v1), antes de atualizar. A cópia contém os dados anteriores e deve receber o mesmo cuidado de privacidade do banco. Falha no backup impede a migração. Falha na migração reverte as alterações; não apague o banco para resolver um erro. Bancos de versões futuras são recusados para evitar perda de dados.

IDs, textos e datas de criação são preservados. Lembretes não mudam. As cópias automáticas não têm exclusão nem retenção automática nesta etapa.

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

O [ensaio de 13/11/2026](VALIDACAO-OLLAMA-2026-11-13.md) registra inferência real, tempos, memória observada e falhas de qualidade. O teste com a conexão de internet desligada e a avaliação durante uma jornada de trabalho continuam pendentes.
