# Contribuir

1. Leia AGENTS.md e a arquitetura. Escolha um item do roadmap com critério de conclusão.
2. Use uma branch por alteração. Preserve a compatibilidade dos dados existentes da KiKi.
3. Execute `python -m unittest discover -s tests -v` na raiz.
4. Para mudanças visuais, abra `python -m kiki` com dados fictícios e verifique as três abas. Os testes de CI não abrem janelas.
5. Descreva problema, comportamento final, testes e limites no pull request. Atualize o roadmap apenas com evidências.

Dependências de execução atuais: biblioteca padrão com Tkinter. `pip install -e .` é opcional para desenvolvimento e exige ferramentas de build disponíveis. Não é necessário para executar a partir do checkout.
