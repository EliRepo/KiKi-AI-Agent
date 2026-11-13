# Retomada e validação local — 13/11/2026

Base analisada: main, commit bd43f64. Leitura do código Python, testes, documentação, launcher, configuração do projeto e workflow. M01–M12 são entregas funcionais do roadmap, não repositórios Git aninhados. Não há arquivo .gitmodules no checkout.

## Evidências neste computador

- Windows; processador Intel Core i5-1334U; 16.849.256.448 bytes de RAM física (aproximadamente 16 GB comerciais). O alvo Ryzen/12 GB descrito anteriormente não é esta máquina.
- Python 3.13.15 instalado pelo uv; ambiente local .venv criado. Nenhuma dependência externa de execução exigida.
- Suite original: 16 testes aprovados. Após a correção de layout: 17 testes aprovados, incluindo interface Tkinter, sem testes ignorados.
- KiKi aberta e conferida visualmente. O layout original escondia o compositor e a barra de estado nesta tela. A reserva de espaço foi corrigida; campo, envio e estado agora aparecem. Teste adicional cobre visibilidade do compositor em 960x680.
- Launcher passa a usar .venv quando disponível, preservando py -3 como alternativa.
- Diagnóstico executado fora do sandbox: Ollama não encontrado no PATH e serviço em 127.0.0.1:11434 sem resposta. Não houve inferência real, benchmark ou validação offline do modelo.
- Dados normais ficam em %LOCALAPPDATA%\KiKi. Testes usam bancos temporários/fictícios ou memória SQLite. Nenhum registro pessoal foi usado para inferência.
- Alterações desta retomada permanecem locais para avaliação.

## Situação dos módulos

- **M01 — Configuração e diagnóstico:** persistência, validação e diagnóstico implementados e testados; falta ensaio com serviço real.
- **M02 — Motor local:** contrato HTTP testado com simulação; faltam modelo instalado, erros reais, qualidade, latência e memória observada.
- **M03 — Memória:** inserir, buscar e reabrir funcionam nos testes; faltam editar/excluir, versão de esquema e migrações transacionais.
- **M04 — Contexto:** busca textual sem acentos, limitada a oito registros de 500 caracteres; faltam avaliação de relevância e apresentação explícita das fontes recuperadas.
- **M05 — Pedidos:** parser determinístico de datas; sem intenções gerais ou coleta de campos ausentes.
- **M06 — Coordenador:** ainda não implementado. A interface coordena os fluxos atuais.
- **M07 — Ferramentas:** ações manuais pelos botões; faltam propostas tipadas, confirmação por ID e proteção contra execução repetida.
- **M08 — Lembretes:** criação, aviso, reconhecimento e conclusão implementados; sem edição, adiamento, cancelamento ou execução em segundo plano.
- **M09 — Interface:** navegação e temas presentes; compositor corrigido nesta entrega. Cada resposta substitui a anterior, sem múltiplas conversas ou histórico; configurações ainda ocupam a área central. Campo de mensagem de linha única não atende a Shift+Enter.
- **M10 — Recuperação:** backup e reabertura da cópia testados automaticamente. Restauração operacional, retenção e exclusão controlada permanecem pendentes.
- **M11 — Operação:** execução local disponível e launcher ajustado; sem instalador ou atualização de distribuição validada.
- **M12 — Aceitação:** 17 testes locais aprovados; faltam cenários reais de IA, uso diário e aceite final.

## Pontos encontrados na revisão

1. A busca pontua substrings e lê todos os registros: pode retornar nomes parcialmente coincidentes e não tem evidência de desempenho com bases grandes. Validar um conjunto de perguntas antes de adotar embeddings.
2. A conversa envia apenas a pergunta atual e os registros recuperados; não preserva turnos anteriores. M09.2 e M09.5 precisam definir continuidade explicitamente.
3. Falhas HTTP são convertidas numa mensagem genérica na interface; diferenciar timeout, modelo ausente e resposta inválida ajudará M02. O estado final atual volta a “Pronta” mesmo após falha.
4. Métodos de persistência não validam texto vazio nem verificam linhas alteradas; a interface faz parte dessas verificações. Antes das ferramentas M07, centralizar contratos e resultados verificáveis na aplicação.
5. SQLite ainda não tem versão de esquema. Histórico e novas operações devem ser precedidos por migrações e testes com banco antigo.
6. A documentação contém estados antigos de entregas já publicadas e referência a branch anterior em SETUP. Reconciliar o estado atual com o histórico ao preparar a próxima publicação.
7. Cobertura atual é útil, porém não comprova notificações após suspensão, restauração manual, atualização instalada, cancelamento da IA ou desempenho do modelo.

## Sequência de continuidade

1. Concluir a fase 1: instalar/iniciar Ollama, baixar qwen3:1.7b, verificar serviço e modelo, executar três perguntas fictícias e medir duração e consumo; ensaiar indisponibilidade e operação offline após o download.
2. Fase 2: versão de esquema e migrações (M03), edição/exclusão de registros, aceitação da busca (M04) e recuperação (M10).
3. Fase 3: intenções e campos ausentes (M05), coordenador (M06), ferramentas confirmadas e idempotentes (M07).
4. Fase 4: completar lembretes (M08), conversa/configurações/histórico e revisão de uso (M09), operação e instalação (M11). Histórico depende das migrações e da decisão de retenção.
5. Fase 5: aceitação integrada, offline, recuperação e distribuição (M12).

Não há base para declarar percentuais de conclusão ou desempenho da IA. A aprovação para publicar esta entrega continua separada da autorização para trabalhar localmente, conforme AGENTS.md.
