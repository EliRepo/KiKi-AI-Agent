# KiKi para Windows — versão de avaliação

## Abrir em outro computador

1. Baixe o ZIP `KiKi-0.2.1-windows-x64.zip` da página Releases do repositório EliRepo/KiKi-AI-Agent no GitHub.
2. Extraia todo o ZIP para uma pasta da sua conta Windows. Não execute o EXE dentro do ZIP.
3. Abra a pasta KiKi e execute KiKi.exe. Preserve a pasta `_internal` junto dele.

O pacote é para Windows 10/11 de 64 bits (x64) e inclui Python, Tcl/Tk e fontes. Não é necessário instalar Python, Git ou bibliotecas. Não inclui dados pessoais, configuração deste computador, Ollama nem modelo de IA. O executável não possui assinatura digital própria.

## O que funciona imediatamente

Memória, busca, edição/exclusão confirmada, lembretes, backup/recuperação e pedidos explícitos confirmados funcionam sem Ollama. Exemplos:

- Guarde: Atendi Ana e corrigi a permissão.
- Lembre-me de conferir Ana amanhã às 10h.
- Atendi Ana, corrigi a permissão e quero conferir amanhã às dez.

Confira a janela com textos e data completa antes de confirmar. Cancelar não grava. Essas frases fazem parte de uma gramática limitada, não de uma interpretação geral da IA.

## Ativar as respostas de IA (opcional)

Instale Ollama pelo site oficial https://ollama.com/download/windows . Configure o modo local sem nuvem conforme https://docs.ollama.com/faq e abra o serviço. No PowerShell, baixe o modelo:

    ollama pull qwen3:1.7b

O download exige internet e espaço adicional. Em Configuração, use Verificar ambiente. A KiKi usa somente 127.0.0.1:11434. Não configure o Ollama para expor o serviço à rede. O modelo pode errar; confira registros e citações. Desempenho depende do computador.

## Dados e atualizações

Cada conta Windows tem seu banco em `%LOCALAPPDATA%\KiKi\kiki.sqlite3` e preferências em settings.json na mesma pasta. Nada é sincronizado automaticamente entre computadores. Backups contêm seus dados e não são criptografados pela KiKi.

Para atualizar, feche a KiKi, faça backup e extraia a nova versão em outra pasta. Os dados ficam fora da pasta do programa. Não copie seu banco para o repositório. A atualização de esquema cria uma cópia prévia e preserva os registros existentes; voltar a um programa mais antigo pode exigir restaurar um backup compatível.

Para transferir dados, faça backup no computador de origem. No destino, com a KiKi fechada, preserve o banco atual e adote a cópia como kiki.sqlite3 na pasta acima. O botão Restaurar cópia em novo arquivo verifica uma cópia sem substituir o banco em uso. Preferências e modelos devem ser configurados separadamente no destino.

## Lembretes

A versão 0.2.1 inclui Editar, Adiar e Cancelar lembrete com confirmação. Selecione a pendência antes de usar esses controles. Editar/adiar exige nova data futura; adiar mantém o texto e exige horário posterior ao anterior. Cancelar retira dos avisos, mas preserva o registro no banco e em backups. A atualização para esquema 4 faz backup prévio; a versão 0.2.0 antiga não abre banco v4.

Os avisos exigem a KiKi aberta e o computador acordado. Fechar encerra os avisos. Não há serviço de lembretes em segundo plano. Datas seguem o relógio local, sem recorrência nem conversão de fuso.

Código e documentação: https://github.com/EliRepo/KiKi-AI-Agent . Esta versão continua sendo um protótipo; a validação em computadores adicionais e o ensaio com a rede desligada não substituem a avaliação de quem utiliza o aplicativo.
