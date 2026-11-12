# Orientações de desenvolvimento

- Leia README.md, docs/ARCHITECTURE.md e docs/ROADMAP.md antes de ampliar o escopo.
- A KiKi é local: não adicionar IA online, telemetria ou sincronização sem uma decisão explícita do responsável.
- Nunca versionar bancos, dados pessoais, backups ou credenciais. Use dados fictícios nos testes.
- Domínio não depende de Tkinter, HTTP ou SQLite. Regras reutilizáveis ficam em domain/application.
- Teste alterações de comportamento: `python -m unittest discover -s tests -v`.
- Demonstre cada implementação local ao responsável e publique somente após aprovação explícita dessa entrega. Depois de publicar, pergunte se pode avançar para a próxima.
- Não declarar validação real do Ollama com base em mocks. Atualize o roadmap com evidências.
- Respostas livres do modelo não executam código, comandos ou SQL. Ferramentas futuras exigem argumentos tipados e confirmação da pessoa.
