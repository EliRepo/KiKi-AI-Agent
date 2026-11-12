# ADR 0001 — Desktop local com Python, Tkinter, SQLite e Ollama

Status: adotada para o protótipo. Data: 12/11/2026.

## Contexto

Windows 11, SSD, Ryzen 5500U, 12 GB de RAM e nenhuma GPU dedicada. Necessidade de memória persistente e lembretes com possibilidade de conversar sem enviar dados a um serviço online.

## Decisão

Usar Python com biblioteca padrão, Tkinter na interface, SQLite nos dados e adaptador HTTP para Ollama com Qwen3 1.7B como candidato inicial. Começar por texto, contexto curto e ações manuais conferidas. Organizar em camadas sem adicionar servidor web, framework de agentes ou banco vetorial nesta fase.

## Consequências

Poucas dependências e funções básicas disponíveis sem IA. Exige Python/Tcl-Tk na primeira distribuição. Interface e lembretes encerram ao fechar. Busca textual tem limites. Desempenho e qualidade do modelo permanecem hipóteses até teste no hardware real. A evolução para agente exige propostas tipadas, confirmação e testes próprios; o modelo sozinho não fornece esses mecanismos.
