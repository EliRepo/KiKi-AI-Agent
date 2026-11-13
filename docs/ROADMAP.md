# Roadmap e critérios de entrega

Validação de retomada em 13/11/2026: 17 testes locais aprovados com Python 3.13.15, interface aberta neste computador e compositor corrigido para permanecer visível. Ollama sem resposta local; inferência real permanece pendente. Detalhes e sequência: [registro local](VALIDACAO-LOCAL-2026-11-13.md). Correções desta retomada ainda não publicadas.

Atualizado em 13/11/2026. Estados: **parcial**, **implementado no protótipo**, **planejado**. Implementado não significa validado no computador de destino.

M02 em avaliação local: Ollama 0.40.16 e qwen3:1.7b instalados; consultas reais no i5-1334U/16 GB, erro real de modelo ausente e falhas simuladas diferenciadas na interface. Ver [evidências e limites](VALIDACAO-OLLAMA-2026-11-13.md). Aceitação de qualidade, citações e teste sem internet seguem pendentes.

## Submódulos

| ID | Submódulo | Estado e evidência | Falta para concluir |
| --- | --- | --- | --- |
| M01 | Configuração e diagnóstico | Implementado: configuração persistente, diagnóstico real do serviço/modelo em 13/11 e detecção portátil | Avaliação do responsável durante o uso |
| M02 | Motor de IA local | Parcial: inferência real, tempos e memória registrados; falhas diferenciadas, incluindo 404 real | Qualidade/citações, uso diário, teste sem internet e timeout real |
| M03 | Memória persistente | Implementado localmente: edição, exclusão confirmada, esquema 2, backup pré-migração, rollback e conflitos testados | Avaliação visual e aceite no uso diário |
| M04 | Busca de contexto | Parcial: busca sem acentos e contexto limitado | Conjunto de perguntas de aceitação, fontes visíveis e avaliação de relevância |
| M05 | Entendimento de pedidos | Parcial: datas explícitas com validação | Intenções, campos obrigatórios e perguntas sobre dados ausentes |
| M06 | Coordenador do agente | Planejado | Estados do pedido, ferramentas permitidas e resultados verificáveis |
| M07 | Ferramentas e confirmação | Parcial: ações pelos botões | Propostas tipadas, confirmação por ID e execução sem duplicidade |
| M08 | Agenda e lembretes | Parcial: criação, aviso e conclusão | Editar, adiar, cancelar e decidir operação em segundo plano |
| M09 | Interface e histórico | M09.1 avaliado pelo responsável; M09.4 implementado localmente: paletas violeta e preferências de leitura | Avaliar M09.4; M09.2, M09.3, M09.5 e revisão completa M09.6 seguem pendentes |
| M10 | Proteção e recuperação | Parcial: backup testado, banco ignorado no Git | Ensaio de restauração, exclusão controlada e política de retenção |
| M11 | Instalação e operação | Parcial: launcher e instruções | Instalador validado e atualização sem perda de dados |
| M12 | Validação final | Parcial: 16 testes locais; CI aprovada em Windows/Linux e Python 3.11–3.13 | Ensaio offline, Ollama real e aceite final no computador de destino |

## Marcos em ordem

### Fase 1 — Base modular e validação local (atual)

- [x] Separar domínio, aplicação, infraestrutura e interface.
- [x] Preservar o formato do banco do protótipo.
- [x] Testar persistência, datas, backup e contrato da API com simulação.
- [x] Definir CI para Windows/Linux e Python 3.11–3.13.
- [x] CI executada e aprovada em Windows/Linux e Python 3.11–3.13: [execução validada](https://github.com/EliRepo/KiKi-AI-Agent/actions/runs/43322972528).
- [x] Instalar/abrir Ollama no computador de destino e baixar o modelo: Ollama 0.40.16 e qwen3:1.7b em 13/11/2026; evidências no ensaio M02.
- [ ] Medir tempo de resposta, memória e impacto nos programas habituais.
- [ ] Validar sem internet após o download.

Saída: decidir se Qwen3 1.7B atende à qualidade e ao desempenho necessários. Registrar hardware, versões, três perguntas, tempo de cada resposta e memória observada. A aprovação de desempenho depende da experiência da usuária, sem prometer velocidade antecipadamente.

### Fase 2 — Memória e operação confiáveis

- [x] Configuração persistente e diagnóstico (M01); serviço/modelo reais verificados em 13/11/2026.
- [x] Edição/exclusão e migrações (M03): 33 testes locais aprovados nesta etapa, incluindo bancos v0/v1, rollback, backup, conflitos e interface.
- [ ] Avaliação de busca com dados fictícios (M04).
- [ ] Restauração de backup testada (M10).

Saída: registros corrigíveis, recuperação comprovada e nenhuma perda de dados ao atualizar.

### Fase 3 — Agente com ações confirmadas

- [ ] Intenções e campos ausentes (M05).
- [ ] Coordenador com estados (M06).
- [ ] Ferramentas e proteção contra repetição (M07).
- [ ] Cenário combinado: atendimento mais lembrete, com conferência.

Saída: pedir “Atendi Ana, corrigi a permissão e quero conferir amanhã às dez”; revisar registro e data completa; confirmar uma vez; verificar ambos no banco. Cancelar não altera dados. Falha não anuncia sucesso.

### Fase 4 — Uso diário

- [ ] Editar/adiar/cancelar lembretes (M08).
- [x] M09.1: barra lateral e conversa central implementadas localmente; aguardam avaliação visual e aprovação para publicar.
- [ ] M09.2: interação de conversa e estados de operação.
- [ ] M09.3: janela de configurações por seções.
- [x] M09.4: temas violeta claro/escuro persistentes; aguardando avaliação visual. Antecipado porque depende apenas da configuração M01 e do layout M09.1, sem migrações de banco.
- [ ] M09.5: histórico local com migrações e política de retenção.
- [ ] M09.6: revisão de teclado, redimensionamento e fonte.
- [ ] Definir comportamento ao minimizar, fechar, suspender e reiniciar.
- [ ] Instalação e atualização simples (M11).

Saída: operação previsível durante uma jornada de trabalho e limites claros na interface.

### Fase 5 — Primeira versão estável

- [ ] Testes ponta a ponta no equipamento real (M12).
- [ ] Testes offline, recuperação, falha de IA e retomada de avisos.
- [ ] Revisar privacidade, instruções e pendências.
- [ ] Criar versão de distribuição e notas de lançamento.

## Regra para atualizar o progresso

Cada conclusão precisa indicar teste, execução real ou evidência de revisão. Não converter “API simulada passou” em “modelo validado”. Funcionalidades futuras permanecem identificadas como planejadas. Sem prazo estimado antes do ensaio real da fase 1.

Cada implementação deve ser mostrada ao responsável antes de publicar no GitHub. Depois da avaliação e aprovação explícita, publicar a entrega e perguntar se pode avançar. Requisitos detalhados da interface: [M09](UI-REQUIREMENTS.md).

## Publicação da base

Base e refinamentos visuais publicados na main pelo [PR #1](https://github.com/EliRepo/KiKi-AI-Agent/pull/1), com autorização explícita do responsável. Próxima entrega depende de nova avaliação. Testes reais do modelo permanecem pendentes.
