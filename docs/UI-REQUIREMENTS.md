# M09 — Interface de uma assistente de conversação

Estado: M09.1 avaliado pelo responsável; M09.2–M09.5 implementados no protótipo local, aguardando avaliação. Revisão completa M09.6 pendente. Ver [evidências do histórico](VALIDACAO-HISTORICO-2026-11-13.md).

## Objetivo

Evoluir a interface atual para um ambiente de conversação inspirado na organização do chat/IDE usado nesta avaliação: navegação lateral, conversa central e configurações em janela própria. Preservar a execução local e o uso de memória e lembretes sem IA.

## Entregas do submódulo

| Etapa | Entrega | Critério de aceite |
| --- | --- | --- |
| M09.1 | Estrutura da janela | Barra lateral à esquerda; seção ativa identificada; conversa ocupa a área central; navegação não perde o conteúdo digitado |
| M09.2 | Conversa | Nova conversa, lista de conversas e mensagens com identificação de autor; rolagem, cópia de texto e indicação de processamento/erro; Enter envia e Shift+Enter quebra linha |
| M09.3 | Configurações | Janela própria, com Aparência, Modelo e diagnóstico, Dados e backup, Sobre; configurações M01 continuam acessíveis |
| M09.4 | Temas | Temas claro e escuro; escolha persistida e aplicada ao reabrir; cores legíveis em campos, listas, mensagens, diálogos e estados de foco |
| M09.5 | Histórico e continuidade | Conversas persistidas localmente, separadas de registros de memória; lista reabre a conversa correta; nova conversa começa sem herdar mensagens de outra |
| M09.6 | Revisão de uso | Redimensionamento, teclado, foco visível e escala de fonte; ensaio no computador de destino sem esconder controles essenciais |

## Navegação proposta

```text
┌──────────────────┬───────────────────────────────────────────┐
│ KiKi             │ Conversa atual       Modelo / estado local│
│ + Nova conversa  ├───────────────────────────────────────────┤
│                  │                                           │
│ Conversas        │ Mensagens da pessoa e da KiKi              │
│ Memória          │                                           │
│ Lembretes        │                                           │
│                  ├───────────────────────────────────────────┤
│ Histórico        │ Escreva sua mensagem…            [Enviar] │
│                  │                                           │
│ Configurações    │                                           │
└──────────────────┴───────────────────────────────────────────┘
```

Configurações abre uma janela dentro do aplicativo, com seções organizadas. Memória e lembretes usam a mesma área de trabalho central, mantendo a barra lateral. A primeira apresentação deve mostrar o tema escuro e o claro, sem exigir instalação do Ollama.

## Dependências e decisões

- M01 fornece seleção persistente de modelo e diagnóstico; migrar esses controles sem perder preferências.
- M03 precisará de migrações para novas tabelas de histórico; banco atual deve ser preservado.
- M02 fornece respostas e erros; o estado “respondendo” precisa refletir o processamento real.
- M10 define retenção, backup e exclusão do histórico; não habilitar gravação de conversas silenciosamente. Explicar a persistência na interface antes de seu primeiro uso.
- Usar Tkinter inicialmente. Avaliar outra tecnologia apenas se um protótipo demonstrar limitações relevantes; registrar decisão antes da migração.
- Temas são uma preferência local; não exigem serviço online. Seguir o tema do sistema e múltiplos painéis de editor podem ser avaliados depois.

## Fluxo de avaliação por implementação

1. Implementar uma entrega delimitada e testar localmente.
2. Abrir a KiKi no computador do responsável e demonstrar o resultado real.
3. Informar o que mudou, os testes e pendências.
4. Receber aprovação explícita dessa entrega; ajustes voltam para avaliação.
5. Publicar no GitHub somente a versão aprovada e perguntar se pode seguir para a próxima entrega.

Este documento registra a direção visual; ainda não representa uma interface pronta. Não incluir nesta etapa terminal integrado, execução de código, plugins de terceiros ou ferramentas autônomas de agente.

## Avaliação M09.1

Implementado: navegação lateral com indicação da seção selecionada, conversa como página inicial, acesso a Memória/Lembretes/Configuração e rolagem da resposta. Backup fica em Configuração. Os campos digitados são preservados ao navegar.

Avaliar: digitar sem enviar, trocar entre as quatro seções e voltar; conferir rascunhos; verificar os botões de memória, lembretes, configuração e backup. O visual usa duas faixas laterais (ícones e navegação), seleção arredondada e área central de conversa. A referência fornecida é a IDE do Codex/ChatGPT. Janela de configurações própria, múltiplas conversas e histórico continuam pendentes.

## Avaliação M09.4 — cores e leitura

Configuração oferece exatamente duas opções de tema: **Claro** e **Escuro**, usando respectivamente as paletas violeta clara e escura. Há escolha de fonte disponível e tamanho de leitura entre 11 e 18. Clique em Salvar e aplicar: a aparência muda sem reconstruir páginas e as preferências persistem em settings.json. Arquivos antigos que só contêm o modelo continuam compatíveis.

A opção automática prefere Inter, Segoe UI Variable Text/Variable e, na ausência delas, Arial, Segoe UI ou a fonte disponível do sistema. Inter Regular e Bold agora acompanham a KiKi e são carregadas privadamente no Windows. A família efetivamente renderizada foi verificada como Inter. Segoe UI comum já está instalada; Variable não foi instalada. Ver THIRD_PARTY_NOTICES.md para procedência e limites. Não há download de fontes durante a execução da KiKi.

Pesquisas consultadas: [Inter — documentação do autor](https://rsms.me/inter/), projetada para telas e interfaces; [Tipografia no Windows — Microsoft](https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/typography), com orientação de Segoe UI Variable, hierarquia e legibilidade. O conforto depende também do tamanho, espaçamento, contraste e preferência da pessoa.

Verificações: contraste de pelo menos 4,5:1 nos pares principais de leitura e botões; troca repetida claro/escuro sem perda dos rascunhos; persistência das preferências; carregamento de configuração antiga. Avaliar manualmente as quatro seções, os estados de seleção e tamanhos maiores. Diálogos nativos do Windows seguem a aparência do sistema.

## Refinamento — controles arredondados

Referência adicional do responsável: navegação em cápsulas e campo de mensagem arredondado do Codex. Implementação em `ui/rounded.py`: botões com foco de teclado e estado desabilitado, campos envoltos em superfícies arredondadas, seletores com contorno arredondado e compositor em cápsula com envio circular. Enter envia; enquanto uma resposta está em andamento, envios duplicados são bloqueados. Os menus de opções e diálogos do sistema continuam nativos.

Mudança visual não altera as tabelas SQLite nem o contrato da IA. Temas continuam usando chaves internas light/dark, compatíveis com configurações já salvas.
