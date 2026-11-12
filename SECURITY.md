# Privacidade e limites

A aplicação chama apenas o Ollama em loopback e grava dados localmente. Não possui telemetria, sincronização ou IA online. A configuração do processo Ollama continua sendo responsabilidade do ambiente; siga docs/SETUP.md.

O banco e os backups não são criptografados pela KiKi. Uma pessoa ou processo com acesso à conta Windows pode lê-los. Não há autenticação interna nem isolamento de múltiplos usuários. A pasta local reduz a chance de sincronização acidental, mas backups escolhidos em pastas sincronizadas podem sair do computador.

O modelo pode responder incorretamente. O contexto recuperado é tratado como dado no prompt, mas isso não constitui garantia contra injeção de instruções. O adaptador não oferece ferramentas de execução ao modelo. SQL usa parâmetros.

Use dados fictícios na validação. Não publique dados pessoais, bancos, prompts privados ou credenciais em issues. Para relatar falha, use exemplos mínimos anonimizados; se o repositório oferecer relato privado de vulnerabilidades, prefira esse canal para detalhes sensíveis.
