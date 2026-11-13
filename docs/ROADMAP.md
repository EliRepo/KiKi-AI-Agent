# Roadmap e critérios de entrega

Registro histórico da retomada em 13/11/2026: [validação inicial](VALIDACAO-LOCAL-2026-11-13.md). As cinco entregas subsequentes foram publicadas individualmente e integradas pelo [PR #2](https://github.com/EliRepo/KiKi-AI-Agent/pull/2), com CI aprovada. A distribuição Windows foi integrada pelo [PR #3](https://github.com/EliRepo/KiKi-AI-Agent/pull/3), com matriz de testes e verificação do EXE aprovadas.

Atualizado em 13/11/2026. Estados: **parcial**, **implementado no protótipo**, **planejado**. Implementado não significa validado no computador de destino.

M02 em avaliação local: Ollama 0.40.16 e qwen3:1.7b instalados; consultas reais no i5-1334U/16 GB, erro real de modelo ausente e falhas simuladas diferenciadas na interface. Ver [evidências e limites](VALIDACAO-OLLAMA-2026-11-13.md). Aceitação de qualidade, citações e teste sem internet seguem pendentes.

M03, M04 e recuperação M10 avançados localmente; veja [implementação e demonstração](VALIDACAO-MEMORIA-2026-11-13.md). M05–M07 agora possuem uma primeira implementação de pedidos explícitos com confirmação; veja [validação do agente](VALIDACAO-AGENTE-2026-11-13.md). A qualidade do modelo e o ensaio offline continuam pendentes e não são dispensados por esses avanços.

## Submódulos

| ID | Submódulo | Estado e evidência | Falta para concluir |
| --- | --- | --- | --- |
| M01 | Configuração e diagnóstico | Implementado: configuração persistente, diagnóstico real do serviço/modelo em 13/11 e detecção portátil | Avaliação do responsável durante o uso |
| M02 | Motor de IA local | Parcial: inferência real, tempos e memória registrados; falhas diferenciadas, incluindo 404 real | Qualidade/citações, uso diário, teste sem internet e timeout real |
| M03 | Memória persistente | Implementado localmente: edição, exclusão confirmada, esquema 2, backup pré-migração, rollback e conflitos testados | Avaliação visual e aceite no uso diário |
| M04 | Busca de contexto | Implementado localmente: palavras inteiras, 12 perguntas de aceitação, trechos enviados visíveis e aviso de IDs ausentes | Avaliar perguntas novas e qualidade das respostas do modelo; sinônimos não são tratados |
| M05 | Entendimento de pedidos | Implementado localmente para gramática explícita: guardar, lembrar e cenário combinado; campos ausentes geram pergunta | Ampliar vocabulário e avaliar pedidos novos; coleta em vários turnos não existe |
| M06 | Coordenador do agente | Implementado localmente: proposta imutável por ID, estados e resultado com IDs verificados na persistência | Aceite durante uso real e evolução de ferramentas |
| M07 | Ferramentas e confirmação | Implementado localmente: guardar/criar lembrete após confirmação, transação única e comprovante contra repetição | Edição/conclusão pelo chat futuras; política de retenção dos comprovantes |
| M08 | Agenda e lembretes | Implementado localmente: editar, adiar, cancelar com confirmação, revisão de conflitos e reaviso na nova data | Avaliação da entrega; permanece operação em primeiro plano, sem recorrência |
| M09 | Interface e histórico | M09.1 avaliado pelo responsável; M09.4 implementado localmente: paletas violeta e preferências de leitura | Avaliar M09.4; M09.2, M09.3, M09.5 e revisão completa M09.6 seguem pendentes |
| M10 | Proteção e recuperação | Parcial: backup, recuperação em novo arquivo e recusa de cópias inválidas/sobrescrita testados; exclusão de registros confirmada | Troca operacional do banco com aplicativo fechado, política de retenção e ensaio manual completo |
| M11 | Instalação e operação | Parcial: pacote portátil Windows x64 com Python/Tk, ZIP/hash e CI do EXE; instruções de atualização/transferência | Teste em equipamento adicional, assinatura/instalador opcionais e aceite de atualização real |
| M12 | Validação final | Parcial: 59 testes locais em 13/11; inferência real registrada; CI da primeira publicação aprovada em Windows/Linux e Python 3.11–3.13 | Nova CI, ensaio offline, uso diário e aceite final no computador de destino |

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
- [x] Avaliação de busca com dados fictícios (M04): 12 perguntas com IDs esperados, palavras inteiras e acentos; fontes enviadas visíveis na interface.
- [x] Restauração de backup testada (M10): cópia validada em arquivo novo, sem sobrescrever origem ou banco atual; integridade, arquivo ausente/corrompido e versão futura testados. Substituição operacional do banco permanece manual.

Saída: registros corrigíveis, recuperação comprovada e nenhuma perda de dados ao atualizar.

### Fase 3 — Agente com ações confirmadas

- [x] Intenções e campos ausentes (M05): gramática explícita determinística, sem delegar execução ao modelo.
- [x] Coordenador com estados (M06): propostas por ID e estados de confirmação, execução, cancelamento ou falha.
- [x] Ferramentas e proteção contra repetição (M07): tipos SaveNote/CreateReminder, comprovante persistente e hash do conteúdo aprovado.
- [x] Cenário combinado: atendimento mais lembrete, com conferência; execução única e rollback da primeira ação se a segunda falhar, testados com dados fictícios.

Saída: pedir “Atendi Ana, corrigi a permissão e quero conferir amanhã às dez”; revisar registro e data completa; confirmar uma vez; verificar ambos no banco. Cancelar não altera dados. Falha não anuncia sucesso.

### Fase 4 — Uso diário

- [x] Editar/adiar/cancelar lembretes (M08): implementação local com esquema 4 e testes; avaliação pendente, separada do pacote publicado v0.2.0.
- [x] M09.1: barra lateral e conversa central implementadas localmente; aguardam avaliação visual e aprovação para publicar.
- [ ] M09.2: interação de conversa e estados de operação.
- [ ] M09.3: janela de configurações por seções.
- [x] M09.4: temas violeta claro/escuro persistentes; aguardando avaliação visual. Antecipado porque depende apenas da configuração M01 e do layout M09.1, sem migrações de banco.
- [ ] M09.5: histórico local com migrações e política de retenção.
- [ ] M09.6: revisão de teclado, redimensionamento e fonte.
- [ ] Definir comportamento ao minimizar, fechar, suspender e reiniciar.
- [x] Distribuição portátil Windows sem instalar Python/Git (M11): build e verificação do EXE aprovados na CI do PR #3. Atualização mantém dados fora da pasta do programa; aceite em equipamento adicional pendente.

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
