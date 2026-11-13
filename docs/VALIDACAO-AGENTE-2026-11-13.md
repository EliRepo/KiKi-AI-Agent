# M05–M07 — Pedidos e ferramentas confirmadas

Entrega local de 13/11/2026. Primeira implementação do cenário de ações do roadmap, sem depender de interpretação do Ollama.

## Comportamento entregue

- M05: gramática limitada de guardar registro, criar lembrete e pedido combinado. Campos ausentes ou data/horário inválidos geram pergunta, sem gravar. A correção exige reenvio do pedido completo; não há preenchimento livre em vários turnos.
- M06: coordenador com propostas imutáveis por ID e estados proposta, confirmada, executada, cancelada ou falhou. IDs de outra sessão e propostas canceladas/falhas são recusados. “Sim” no chat não confirma.
- M07: ferramentas tipadas SaveNote e CreateReminder. Apenas o botão de confirmação da proposta abre a execução. O mesmo ID/conteúdo não grava duas vezes; conteúdo diferente com ID já usado é recusado.
- Pedido combinado grava registro, lembrete e comprovante numa transação. Se o lembrete falhar ou o horário vencer durante a conferência, não sobra registro parcial nem comprovante de sucesso.
- Esquema 3 adiciona action_receipts com ID, hash do conteúdo aprovado, IDs gerados e horário. Migração de v0/v1/v2 continua com backup prévio e transação. Comprovantes entram nos backups; não são histórico completo da conversa.

## Verificações automatizadas

Resultado final: **59 testes aprovados**, sem ignorados, com `python -m unittest discover -s tests -v`. Verificação de espaços do diff aprovada considerando CRLF do Windows. Nenhuma nova execução de CI remota foi atribuída a esses resultados locais.

A suíte desta entrega inclui interpretação de pedidos, horas por extenso, campos ausentes, ambiguidades, rejeição de ferramenta desconhecida, recusa de execução sem confirmação, cancelamento, ID desconhecido, proposta imutável, rollback provocado na segunda ação, horário vencido e repetição após reabrir o banco. Também verifica atualização de banco v2 preservando registros/lembretes.

Os testes Tkinter percorrem a janela real de proposta: prévia somente para leitura, cancelamento, bloqueio de envio repetido, confirmação do pedido combinado, atualização das listagens e falha sem mensagem de sucesso. O Ollama é mockado para comprovar que não é chamado nesses pedidos; isso não constitui validação nova do modelo.

## Demonstração no computador

Foi aberta a interface real por `python -m scripts.demo_workspace --agent-demo`, usando banco exclusivamente em memória e dados fictícios. A janela mostrou o pedido “Atendi Ana, corrigi a permissão e quero conferir amanhã às dez”, dividido em registro e lembrete para **14/11/2026 às 10:00**, com ID e textos completos antes de executar.

A conferência visual da proposta foi realizada. A execução/cancelamento e a inspeção dos dados resultantes foram verificadas nos testes da interface com dados fictícios; não se afirma uma confirmação manual concluída nesta demonstração. O banco pessoal não foi aberto para o ensaio.

## Limites preservados

- Não existe executor de shell, Python ou SQL livre. Respostas do modelo não viram propostas ou chamadas de ferramentas.
- Editar/excluir registros e concluir lembretes continuam pelos controles existentes. Outras ferramentas e linguagem natural mais ampla permanecem futuras.
- Reenviar o mesmo texto cria outro ID e pode gerar registros iguais se houver nova confirmação. A proteção é por ID/conteúdo, sem deduplicação semântica.
- Propostas pendentes/canceladas são da sessão e desaparecem ao fechar. Comprovantes de execução permanecem no banco; retenção automática ainda não foi definida.
- Horários são locais e explícitos, sem recorrência ou inferência de manhã/noite. Avisos precisam da KiKi aberta e do computador acordado.
- Qualidade/citações do Ollama, ensaio com rede desligada e aceitação durante uma jornada de trabalho continuam pendentes.
