# Atualizações

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
