Atualização da prévia Windows x64 com M08 publicado pelo PR #4.

- Editar descrição/data de lembretes e adiar para horário posterior.
- Cancelar lembrete após confirmação, retirando-o das pendências e avisos.
- Revisão protege alterações simultâneas; editar/adiar reinicia o aviso para a nova data.
- Esquema 4 com backup prévio, preservação dos campos antigos e rollback de falha de migração.

69 testes locais aprovados; CI do PR #4 também aprovada, incluindo pacote e verificação do EXE. A publicação desta tag só ocorre após nova passagem da matriz Windows/Linux e da verificação do pacote.

Baixe KiKi-0.2.1-windows-x64.zip, extraia tudo e abra KiKi/KiKi.exe. Python e Tcl/Tk já estão incluídos. Ollama/modelo são opcionais e separados. Não há dados pessoais no ZIP. Executável sem assinatura digital própria.

Antes de atualizar, feche a KiKi e faça backup. Dados permanecem em %LOCALAPPDATA%\KiKi. Depois da migração, não reabra o banco v4 na versão v0.2.0 antiga: preserve o backup compatível para retorno. Avisos ainda precisam do aplicativo aberto e computador acordado; sem recorrência ou serviço em segundo plano.

O histórico M09 segue em desenvolvimento separado e não integra esta versão.
