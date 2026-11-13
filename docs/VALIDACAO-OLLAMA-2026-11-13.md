# M02 — Primeiro ensaio real do Ollama

Data: 13/11/2026. Entrega local na branch feat/m02-local-validation, posterior ao commit aprovado 8cd659b. Este registro comprova integração real; não encerra a aceitação do modelo.

## Ambiente e instalação

- Windows 11 build 26200, Intel Core i5-1334U, aproximadamente 16 GB de RAM, Python 3.13.15.
- Ollama 0.40.16 portátil em `%LOCALAPPDATA%\Programs\Ollama`. Pacote oficial x86-64 com SHA-256 `50fcf5ad54277f2fa5d173ebfc93bcb017adbc0c9ef2314daabc96ca9e6aa64e` conferido antes da extração.
- Serviço iniciado com `OLLAMA_NO_CLOUD=1` e `OLLAMA_HOST=127.0.0.1:11434`. Sem conta, serviço do Windows, alteração de PATH ou inicialização automática.
- Modelo `qwen3:1.7b`, download de 1.359.293.444 bytes, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`, quantização Q4_K_M. A API reporta parâmetro nominal 2.0B para essa tag.
- Inferência em CPU; `/api/ps` retornou `size_vram=0`, contexto de 4096 e memória estimada do modelo de 1.886.629.395 bytes. Não foi habilitada a GPU integrada.
- Fontes oficiais: [Windows e pacote portátil](https://docs.ollama.com/windows), [modo local e configurações](https://docs.ollama.com/faq), [modelo](https://ollama.com/library/qwen3:1.7b).

## Consultas com dados fictícios

O comando `python -m scripts.benchmark_ollama --output resultado.json` usa a mesma busca de contexto e o mesmo adaptador da interface, com SQLite exclusivamente na memória. Não acessa o banco pessoal. Foram usados dois registros fictícios: Ana/acesso/permissão e Bruno/impressora/página de teste.

Na execução final, iniciada às 15:32:36, horário de São Paulo:

1. **Como resolvi o problema da Ana?** — 8,868 s. Resposta correta sobre permissões, com citação [1].
2. **O que fiz para Bruno?** — 12,167 s. Resposta correta sobre impressora e página de teste; omitiu a citação [2] e acrescentou orientação desnecessária sobre botões.
3. **Qual é o telefone da Carla?** — 8,816 s. Reconheceu ausência de informação e não inventou telefone; acrescentou orientação desnecessária sobre botões.

Respostas integrais: [execução final](OLLAMA-BENCHMARK-2026-11-13.json). Transporte funcionou nas três consultas; a segunda não cumpriu todos os critérios de conteúdo/citação. Os tempos são amostras individuais, não média, p95 ou promessa de desempenho.

No segundo ensaio, o pico observado da soma dos working sets de `ollama.exe` e `llama-server.exe` foi **1.964.843.008 bytes (1,83 GiB)**, com 28 amostras a intervalos nominais de 500 ms. Isso mede memória residente dos processos, pode contar páginas compartilhadas mais de uma vez e não é consumo total do sistema. Evidência: [medição](OLLAMA-MEMORY-2026-11-13.json). Essa medição corresponde ao segundo ensaio, não à execução final. A primeira tentativa de medir apenas ollama.exe foi descartada por excluir o processo de inferência.

As execuções anteriores também ficam disponíveis: [prompt original](OLLAMA-BASELINE-2026-11-13.json) e [primeiro ajuste](OLLAMA-PROMPT-1-2026-11-13.json). Ambas falharam ao responder sobre Bruno. A versão final passou a identificar os campos dos registros e a explicar a referência a atividades em primeira pessoa. Essa pequena amostra não comprova robustez geral.

## Interface e falhas

Suite final: **22 testes aprovados**, sem ignorados, com `python -m unittest discover -s tests -v`. Esses testes são independentes do serviço real e não usam a rede. As consultas reais foram executadas separadamente.

- KiKi atualizada foi reaberta e consultou o modelo pela janela real. Para “Quanto é 2 + 2?”, respondeu “2 + 2 é 4. [1]”. A conta está correta, mas a citação em uma resposta de aritmética é desnecessária e reforça que citações geradas não devem ser tratadas como prova automática de origem.
- O diagnóstico real encontrou executável, serviço e modelo instalado.
- Consulta real ao modelo fictício inexistente `kiki-validation-missing:local` produziu HTTP 404 e a mensagem específica de modelo ausente. Nenhum outro modelo foi baixado por essa consulta.
- Timeout, conexão recusada/interrompida, HTTP 500 e respostas malformadas/vazias foram verificados por simulação automatizada, não por falhas reais do modelo instalado.
- A interface agora identifica erro como “Falha na consulta”, preserva a pergunta e permite nova tentativa. Não anuncia sucesso após erro. Estados de sucesso, erro e bloqueio de envio repetido são testados.
- O diagnóstico reconhece a instalação portátil mesmo sem entrada no PATH.

## Pendências de aceitação

- Citações ainda não são confiáveis; melhorar avaliação e apresentação de fontes em M04.
- Reduzir orientações sobre botões em respostas factuais e avaliar perguntas novas, sem ajustar apenas aos exemplos.
- Teste com a internet efetivamente desligada não foi executado. Modo local sem nuvem não equivale a ensaio com a rede desligada.
- Não foi avaliado o impacto durante uma jornada de trabalho nem obtido aceite do responsável quanto à velocidade/qualidade.
- Histórico de conversa e execução de ações pelo chat continuam fora desta entrega.

Memória e lembretes continuam locais. Nenhuma migração de banco foi feita. O Ollama foi deixado disponível nesta sessão; após reiniciar o computador, inicie-o manualmente pelo script documentado em SETUP.md.
