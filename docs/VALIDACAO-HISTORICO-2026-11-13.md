# M09 — conversas e histórico em avaliação local

Entrega local sobre a base publicada v0.2.1. Não integra esse pacote Windows.

## Implementação

- Conversas independentes, lista lateral, rascunho por conversa e transcrição com autores, rolagem e cópia da última resposta. Enter envia; Shift+Enter muda de linha.
- Consulta assíncrona mantém os turnos anteriores; contexto limitado a 6 mensagens e 3.000 caracteres, com até 1.000 por mensagem. Pedidos de ação e seus resultados não entram nesse contexto. Uma nova conversa começa vazia.
- Configuração em janela própria: Aparência, Modelo/diagnóstico, Dados/backup e Sobre. Ajustado o tamanho dos seletores e reservado espaço para Salvar e aplicar após revisão visual.
- Histórico **desativado por padrão**. Em Dados, a pessoa pode habilitar e escolher 7/30/90 dias desde a última atualização ou 0 para exclusão manual. A limpeza ocorre na abertura ou ao salvar a configuração. Não há limpeza periódica em segundo plano.
- Ativar não grava conversas anteriores. Desativar preserva o histórico existente, mas o próximo envio inicia uma conversa temporária. Conversas temporárias desaparecem ao fechar.
- Exclusão individual ou total pede confirmação. Não exclui notas, lembretes, comprovantes de ações ou backups. O histórico inclui texto e snapshots das fontes; não é criptografado.
- Esquema SQLite 5 com tabelas separadas conversations/chat_messages, migração transacional e backup prévio. Não abrir esse banco com a versão v0.2.1 (esquema 4); para voltar, preservar o banco novo e usar uma cópia anterior à migração.
- Reabrir um pedido antigo apenas mostra seu texto/resultado. Um turno pendente após interrupção exibe aviso para conferir Memória/Lembretes; nunca confirma nem reexecuta automaticamente.

## Evidências e limites

Resultado final: **85 testes locais aprovados** (`python -m unittest discover -s tests -q`). Smoke test a partir do código também aprovado: Tcl/Tk 8.6.12, Inter, três páginas principais, janela de configuração própria, esquema 5 e persistência confirmada de nota fictícia. O smoke test do pacote publicado v0.2.1 pertence à entrega anterior, esquema 4; não é validação de empacotamento do M09.

Testes abrangem persistência e preferências, migração v4→v5 com rollback e backup, retenção/exclusão sem atingir notas/lembretes, separação de conversas, bloqueio de navegação durante consulta/proposta, preservação das fontes, histórico limitado no adaptador e reabertura de ações sem repetição. Testes de interface incluem tamanho mínimo e botão Salvar visível. A suíte e o smoke test usam apenas dados fictícios.

Demonstração aberta neste computador com `python -m scripts.demo_workspace --chat-demo`: duas conversas fictícias, banco em memória e configurações temporárias. Respostas pré-preenchidas são explicitamente fictícias; não representam inferência real. Revisão visual feita no tema escuro e janela de configurações. Sem alteração do banco pessoal.

Pendentes: avaliação do responsável, revisão completa M09.6 em temas/tamanhos/foco, ensaio real de continuidade com Ollama e publicação após aceite. A recuperação operacional M10 e aceitação em outro computador M11 continuam separadas.
