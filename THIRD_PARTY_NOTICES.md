# Recursos de terceiros

## Inter 4.1

Autor: Rasmus Andersson e colaboradores. Distribuição oficial: https://github.com/rsms/inter/releases/tag/v4.1 .

Incluídos Inter-Regular.ttf e Inter-Bold.ttf, sem modificações, extraídos da distribuição oficial. A licença SIL Open Font License 1.1 está em `kiki/assets/fonts/LICENSE.txt` e acompanha o aplicativo.

No Windows, a KiKi registra essas fontes apenas no próprio processo por AddFontResourceExW com FR_PRIVATE. Não exige administrador, não altera a fonte padrão do Windows e não cria entradas no Registro. Em outras plataformas usa uma fonte disponível; instalação de fontes fora do Windows não foi implementada nesta etapa.

## Segoe UI e Segoe UI Variable

São fontes fornecidas pela Microsoft. A KiKi pode utilizar uma versão já instalada, mas não inclui nem redistribui arquivos dessas fontes. Segoe UI comum está disponível no computador de avaliação. Segoe UI Variable não foi encontrada; não foi instalada por ausência de distribuição avulsa oficial identificada neste trabalho. Documentação: https://learn.microsoft.com/en-us/typography/font-list/segoe-ui e https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/typography .
