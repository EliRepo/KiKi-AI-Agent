# M03, M04 e recuperação M10 — Validação local

Entrega de 13/11/2026, posterior ao ensaio M02. Sem dependências adicionais e sem publicação remota.

Resultado final: **42 testes aprovados**, sem ignorados, com `python -m unittest discover -s tests -q`; `git diff --check` sem problemas de espaços (considerando CRLF do Windows).

## Memória e atualização

- M03: registros selecionáveis, prévia completa, editor separado e exclusão confirmada. Cancelar não muda o banco; editar não apaga o rascunho do campo de novo registro.
- Banco versão 2 com revisão e data de alteração; IDs excluídos não são reutilizados. Conflitos e registros removidos geram erro em vez de sobrescrever ou anunciar sucesso.
- Bancos originais v0 e v1 são atualizados em transação após backup consistente na mesma pasta. IDs, datas de criação, textos e todos os campos dos lembretes são preservados.
- Testes provocam falha depois de uma alteração de esquema e verificam rollback de esquema e versão. Falha na cópia impede a migração; banco futuro é recusado sem modificar o arquivo.

## Busca e fontes

- M04: tokens inteiros sem acentos, com empate por registro recente. O conjunto de aceitação contém 12 perguntas com IDs esperados, incluindo Ana/Mariana, João/Joao, falta de informação e palavras funcionais.
- A janela de fontes mostra o contexto exato enviado, limitado a oito trechos de 500 caracteres. Teste altera um registro após o envio e comprova que a conferência continua mostrando a versão enviada.
- IDs nos formatos [ID] e #ID ausentes do contexto geram aviso. Isso não prova que uma afirmação é verdadeira, não garante relevância e não interpreta todos os formatos de citação. Sinônimos/flexões e qualidade geral do modelo continuam fora dessa garantia.

## Recuperação

- M10: abertura da origem somente para leitura, verificação de integridade e estrutura, criação exclusiva de destino novo e verificação do resultado.
- Testes cobrem cópia íntegra, arquivo ausente/corrompido, versão futura, falha de gravação, destino existente e recuperação de banco antigo seguida de migração. A origem permanece inalterada.
- A interface não substitui o banco em uso. Adoção do arquivo restaurado exige fechar a KiKi e seguir SETUP.md. Não há política automática de retenção ou exclusão de backups.

## Demonstração neste computador

A interface real foi aberta com `python -m scripts.demo_workspace`, banco em memória e registros fictícios. Foram inspecionados lista/prévia, editor de registro e cancelamento sem mudanças. Na conversa, “Como resolvi o problema da Ana?” consultou o Ollama real e recebeu “O problema da Ana foi resolvido ajustando as permissões. [1]”. A janela de fontes mostrou somente o registro [1] enviado, sem Mariana.

Nenhum registro pessoal foi usado para essa demonstração. Nenhuma exclusão real foi acionada pela automação da interface. Edição, exclusão confirmada, cancelamento, conflitos e recuperação foram exercitados com dados fictícios nos testes.

O ensaio adicional no tamanho mínimo da janela identificou prévia de memória comprimida; o campo de novo registro foi reduzido de cinco para três linhas para manter a leitura acessível. O conteúdo continua multilinha e rolável.

M05–M07 continuam planejados para a próxima fase: identificar intenções, reunir campos ausentes, coordenar propostas e executar ferramentas somente após confirmação. A conversa atual continua sem gravar registros ou agendar ações por conta própria.
