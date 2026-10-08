# Dragon Slayer: Eiyuu Densetsu — PT-BR

Projeto de engenharia reversa e tradução para português brasileiro da versão japonesa de **Dragon Slayer: Eiyuu Densetsu (Mega Drive)**.

## Objetivo

Analisar a ROM, identificar fonte/charset, localizar e extrair textos, preservar códigos de controle, traduzir, realocar textos quando necessário, corrigir ponteiros, inserir a tradução e validar a ROM final.

## Primeiro marco

O primeiro componente é o analisador `analyze`, que não modifica a ROM.

```bash
python -m pip install -e ".[dev]"
dslayer-ptbr analyze --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --report reports/rom-analysis.json
pytest
```

Os candidatos encontrados pelo analisador são heurísticos. Nenhum offset será considerado confirmado antes da validação e documentação no profile do jogo.

## Estrutura

```text
src/dragonslayer_ptbr/
├── analysis/       # análise da imagem e regiões candidatas
├── text/           # decoder, encoder, tabelas e extrator
├── pointers/       # leitura, escrita e realocação
├── profiles/       # conhecimento específico do jogo
└── cli.py
```

A ROM original deve permanecer local e não deve ser distribuída pelo projeto.


## Documentação de engenharia reversa

O estado detalhado da investigação está consolidado em:

- `docs/analysis-results.md` — relatório técnico completo das análises da ROM, evidências, offsets confirmados, controles, tabela de caracteres, ponteiros e estado de cada componente.
- `docs/reverse-engineering.md` — estratégia, critérios de validação e próximos passos da engenharia reversa.

### Estado técnico atual

Já foram confirmados diretamente na ROM:

- ROM japonesa de 2 MiB;
- charset **Shift-JIS**;
- diversas regiões de texto;
- controles binários misturados ao texto;
- estrutura `0x06 xx yy`;
- terminador `0x00` em estruturas observadas;
- tabela explícita de códigos Shift-JIS em `0x1A551A`.

Ainda não foram confirmados:

- rotina 68000 responsável pela leitura/impressão;
- tabela definitiva de ponteiros de script;
- semântica completa dos controles;
- formato final das entradas;
- mecanismo de realocação.

A regra do projeto é não transformar uma hipótese em conhecimento específico do jogo sem evidência direta da ROM/código.
