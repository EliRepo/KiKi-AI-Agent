# KiKi AI Agent

Assistente pessoal para Windows, com memória local, lembretes e conversa opcional via Ollama. Projetada inicialmente para Ryzen 5 5500U, 12 GB de RAM e SSD. O desempenho nesse equipamento ainda precisa ser medido.

**Estado: protótipo modular v0.2.0.** Pedidos explícitos no chat podem propor um registro e/ou lembrete, executados somente após conferência e confirmação na interface. Perguntas comuns usam o Ollama; suas respostas não executam ferramentas.

## Começar

No Windows 10/11 x64, baixe o [pacote portátil v0.2.0](https://github.com/EliRepo/KiKi-AI-Agent/releases/tag/v0.2.0), extraia todo o ZIP e abra `KiKi/KiKi.exe`. Python e Tcl/Tk acompanham o pacote; não é necessário instalar Python ou Git. Veja [uso em outros computadores](docs/USO-WINDOWS.md). Ollama/modelo são opcionais e instalados separadamente para respostas de IA.

Para executar a partir do código-fonte:

Instale Python 3.11 ou superior com Tcl/Tk. Na raiz do repositório:

```powershell
py -3 -m kiki
```

Ou abra `scripts/start.cmd`. Memória e lembretes não exigem bibliotecas Python externas nem Ollama. Para ativar a IA, siga [a instalação](docs/SETUP.md).

## Funcionalidades atuais

- Registros persistentes em SQLite, edição, exclusão confirmada e busca textual que ignora acentos.
- Atualização transacional de bancos antigos, com cópia automática antes da migração e proteção contra sobrescrita de uma edição desatualizada.
- Busca por palavras inteiras, fontes enviadas à IA visíveis e alerta para citações de IDs ausentes.
- Recuperação de backup verificada em arquivo novo, sem substituir o banco atual.
- Lembretes com data explícita e preenchimento por frases como “amanhã às 10h”.
- Pedidos “Guarde: texto” e “Lembre-me de conferir Ana amanhã às dez”, com coleta de dados ausentes, proposta tipada e confirmação por ID.
- Registro e lembrete juntos em uma transação; confirmação repetida do mesmo pedido não duplica gravações.
- Avisos com o aplicativo aberto e computador acordado.
- Backup manual consistente do banco.
- Adaptador Ollama local com contexto limitado e resposta em português.
- Aba Configuração com escolha persistente do modelo e diagnóstico do serviço local.
- M09.1: navegação lateral e conversa central, com campos preservados entre as seções; Configuração agora fica no menu lateral.
- Temas Claro/Escuro em violeta, controles arredondados, Inter incluída no Windows e preferências de leitura persistentes.

## Acompanhar o projeto

| Documento | Finalidade |
| --- | --- |
| [Arquitetura](docs/ARCHITECTURE.md) | Módulos, dependências e fluxo atual/futuro |
| [Roadmap](docs/ROADMAP.md) | Situação dos 12 submódulos e critérios de conclusão |
| [Interface e temas](docs/UI-REQUIREMENTS.md) | Requisitos do M09 para navegação lateral, conversa e configurações |
| [Instalação](docs/SETUP.md) | Instalar, executar, testar e recuperar dados |
| [Decisão técnica](docs/adr/0001-local-desktop.md) | Por que Python, Tkinter, SQLite e Ollama |
| [Contribuição](CONTRIBUTING.md) | Fluxo de desenvolvimento e validação |
| [Privacidade](SECURITY.md) | Armazenamento e limites |
| [Fontes e licenças](THIRD_PARTY_NOTICES.md) | Inter incluída e limites das fontes Microsoft |

## Testes

```powershell
py -3 -m unittest discover -s tests -v
```

Os testes não baixam modelos nem enviam dados à rede. O adaptador Ollama usa resposta simulada nos testes. A entrega M02 em avaliação local tem um [ensaio real com Ollama](docs/VALIDACAO-OLLAMA-2026-11-13.md) no Intel i5-1334U/16 GB. Qualidade, citações e aceitação offline ainda têm pendências. A [CI da primeira publicação](https://github.com/EliRepo/KiKi-AI-Agent/actions/runs/43322972528) passou em Windows/Linux e Python 3.11–3.13. Testes de interface são ignorados quando o ambiente não tem display; foram executados localmente no Windows.

## Estrutura

```text
kiki/
  __main__.py        # inicialização e composição
  domain/            # texto e interpretação limitada de datas
  application/       # contexto, coordenador e ferramentas confirmadas
  infrastructure/    # SQLite e adaptador Ollama
  ui/                # interface Tkinter
tests/               # persistência, backup, datas, contrato HTTP
docs/                # arquitetura, roadmap e operação
scripts/             # inicialização Windows
.github/workflows/   # testes automatizados
```
