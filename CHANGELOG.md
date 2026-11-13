# Atualizações

## M03 — Memória corrigível e atualização de bancos

- Lista de registros selecionável, leitura completa, editor separado e exclusão confirmada; cancelar não altera o banco e não perde o rascunho de novo registro.
- Esquema 2, com revisão e data de alteração; IDs excluídos não são reutilizados. Edições/exclusões desatualizadas são recusadas.
- Migração transacional dos bancos v0/v1, com cópia automática consistente antes da atualização, rollback e recusa de versões futuras/estrutura desconhecida.
- 33 testes locais aprovados nesta etapa; nenhuma dependência nova ou alteração no contrato de lembretes.

## M02 — Inferência real e tratamento de falhas (avaliação local)

- Ollama 0.40.16 portátil e qwen3:1.7b preparados no i5-1334U/16 GB; primeiro ensaio real documentado em docs/VALIDACAO-OLLAMA-2026-11-13.md, com respostas e tempos preservados.
- Registros enviados ao modelo com campos identificados e orientação de contexto ajustada após falhas reais de qualidade. Citações ainda precisam de avaliação.
- Mensagens específicas para serviço indisponível, conexão interrompida, timeout, modelo ausente, HTTP e resposta inválida/vazia. Interface distingue falha e permite nova tentativa.
- Diagnóstico reconhece executável portátil; adicionados iniciador local do Ollama e benchmark opcional com dados fictícios em memória.
- 22 testes locais aprovados. Consulta pela janela real demonstrada. Internet desligada e aceite de desempenho/qualidade continuam pendentes; sem publicação remota desta entrega.

## Primeira publicação no GitHub

- Base modular e refinamentos integrados à main pelo PR #1, com remoção do código C anterior.
- CI aprovada em Windows/Linux com Python 3.11, 3.12 e 3.13; 16 testes locais aprovados, incluindo interface.
- Autorização do conector limitada ao repositório KiKi-AI-Agent.
- Ollama real e benchmark continuam pendentes; esta publicação não significa que a IA foi validada no equipamento de destino.

## Refinamento M09.4 — controles arredondados e fonte Inter

- Temas renomeados para exatamente Claro e Escuro, preservando as paletas violeta e configurações existentes.
- Botões, campos, seletores e compositor arredondados; botão circular de envio, com teclado e bloqueio de envios duplicados.
- Inter 4.1 Regular/Bold incluídas com a licença oficial e carregadas privadamente no Windows. Fonte efetivamente renderizada verificada como Inter.
- Segoe UI existente mantida; Segoe UI Variable não instalada por falta de distribuição avulsa oficial identificada.
- Documentação, procedência das fontes e limites atualizados.
- Dezesseis testes locais aprovados; publicação autorizada pelo responsável nesta solicitação.

## M09.4 — Duas paletas violeta e preferências de leitura

- Temas Violeta claro e Violeta escuro com aplicação imediata em todas as seções.
- Escolha de fonte instalada, identificação da fonte aplicada e tamanho de leitura ajustável de 11 a 18.
- Mais espaçamento entre linhas e parágrafos para leitura; fontes ausentes usam alternativa local.
- Preferências persistem em settings.json com compatibilidade para o arquivo antigo do M01.
- Quinze testes locais aprovados: contraste dos pares principais, persistência, configuração antiga, troca repetida de tema e preservação de rascunhos.
- Nesta máquina, Automática usa Arial. Referências de tipografia documentadas em UI-REQUIREMENTS.md.
- Aguardando avaliação; sem publicação remota.

## Refinamento visual do M09.1 — referência Codex/ChatGPT

- Visual escuro neutro, barra estreita de ícones, navegação com seleção arredondada e conversa central com menos elementos visuais.
- Campo de mensagem redesenhado; cores consistentes em memória, lembretes, configuração, listas e campos.
- Ícones vetoriais desenhados localmente, sem dependências ou recursos de rede.
- Ponto de retorno: commit 3f5c44f e tag local checkpoint/pre-modern-ui.
- Tema escuro fixo nesta revisão. Alternância de temas e histórico permanecem planejados.
- Aguardando avaliação do responsável antes da publicação.

## M09.1 — Navegação lateral e conversa central

- Ponto de retorno anterior: commit 41abf0c e tag local checkpoint/pre-m09-1.
- Abas substituídas por navegação lateral com Conversa, Memória, Lembretes e Configuração.
- Conversa é a página inicial, com área central de resposta, rolagem e campo de envio na parte inferior.
- Rascunhos preservados ao trocar de seção; backup movido para Configuração.
- Nenhuma alteração no banco, modelo ou ferramentas da IA.
- Doze testes locais aprovados, incluindo dois de integração da interface. Avaliação visual e publicação ainda pendentes.
- Próximas entregas visuais dependem da aprovação do responsável.

## Planejamento M09 — Interface de conversação

- Registrados requisitos de barra lateral esquerda, conversa central, janela de configurações e temas claro/escuro persistentes.
- M09 dividido em seis entregas com critérios de aceite, dependências e fluxo de avaliação antes da publicação.
- Interface nova ainda não implementada; esta atualização registra os requisitos. A base M01 foi avaliada pelo responsável; publicação remota pendente de permissão do GitHub.

## M01 — Configuração e diagnóstico

- Adicionada aba Configuração para salvar o nome do modelo local e verificar o ambiente.
- Preferência persistida em settings.json fora do repositório, junto à pasta local da KiKi.
- Diagnóstico informa Python, pasta dos dados, comando Ollama, serviço e modelo disponível.
- A consulta de diagnóstico usa somente metadados de modelos; não envia registros pessoais.
- Configuração inválida produz aviso e padrão temporário; nomes remotos e de nuvem são rejeitados.
- Dez testes automatizados aprovados, incluindo cinco novos testes de configuração/diagnóstico. Inicialização da interface verificada separadamente.
- Pendente: teste com Ollama real e avaliação no hardware de destino (M02).

## Base modular

- Domínio, aplicação, infraestrutura, interface e testes separados.
- Roadmap de doze submódulos e documentação de operação.
- Conteúdo antigo em C removido da versão atual; histórico Git preservado.
