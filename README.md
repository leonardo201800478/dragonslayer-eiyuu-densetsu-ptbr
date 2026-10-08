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
