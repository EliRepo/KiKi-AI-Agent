# Roadmap e critérios de entrega

Atualizado em 12/11/2026. Estados: **parcial**, **implementado no protótipo**, **planejado**. Implementado não significa validado no computador de destino.

## Submódulos

| ID | Submódulo | Estado e evidência | Falta para concluir |
| --- | --- | --- | --- |
| M01 | Configuração e diagnóstico | Implementado: aba Configuração, modelo persistido e diagnóstico com cinco testes adicionais | Ensaio manual com Ollama no computador de destino |
| M02 | Motor de IA local | Parcial: adaptador HTTP e teste simulado | Teste real, timeout, modelo ausente e medição no equipamento |
| M03 | Memória persistente | Parcial: guardar, buscar e reabrir testados | Editar, excluir, migrações e testes de atualização |
| M04 | Busca de contexto | Parcial: busca sem acentos e contexto limitado | Conjunto de perguntas de aceitação, fontes visíveis e avaliação de relevância |
| M05 | Entendimento de pedidos | Parcial: datas explícitas com validação | Intenções, campos obrigatórios e perguntas sobre dados ausentes |
| M06 | Coordenador do agente | Planejado | Estados do pedido, ferramentas permitidas e resultados verificáveis |
| M07 | Ferramentas e confirmação | Parcial: ações pelos botões | Propostas tipadas, confirmação por ID e execução sem duplicidade |
| M08 | Agenda e lembretes | Parcial: criação, aviso e conclusão | Editar, adiar, cancelar e decidir operação em segundo plano |
| M09 | Interface e histórico | M09.1 avaliado pelo responsável; M09.4 implementado localmente: paletas violeta e preferências de leitura | Avaliar M09.4; M09.2, M09.3, M09.5 e revisão completa M09.6 seguem pendentes |
| M10 | Proteção e recuperação | Parcial: backup testado, banco ignorado no Git | Ensaio de restauração, exclusão controlada e política de retenção |
| M11 | Instalação e operação | Parcial: launcher e instruções | Instalador validado e atualização sem perda de dados |
| M12 | Validação final | Parcial: testes locais e CI definida | CI executada, ensaio offline e aceite no computador real |

## Marcos em ordem

### Fase 1 — Base modular e validação local (atual)

- [x] Separar domínio, aplicação, infraestrutura e interface.
- [x] Preservar o formato do banco do protótipo.
- [x] Testar persistência, datas, backup e contrato da API com simulação.
- [x] Definir CI para Windows/Linux e Python 3.11–3.13.
- [ ] Executar CI no GitHub e conferir os resultados.
- [ ] Instalar/abrir Ollama no computador de destino e baixar o modelo.
- [ ] Medir tempo de resposta, memória e impacto nos programas habituais.
- [ ] Validar sem internet após o download.

Saída: decidir se Qwen3 1.7B atende à qualidade e ao desempenho necessários. Registrar hardware, versões, três perguntas, tempo de cada resposta e memória observada. A aprovação de desempenho depende da experiência da usuária, sem prometer velocidade antecipadamente.

### Fase 2 — Memória e operação confiáveis

- [x] Configuração persistente e diagnóstico (M01); teste com serviço real ainda pendente.
- [ ] Edição/exclusão e migrações (M03).
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
