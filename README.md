# Dragon Slayer: Eiyuu Densetsu — PT-BR

Projeto de engenharia reversa e tradução para português brasileiro da versão japonesa de **Dragon Slayer: Eiyuu Densetsu (Mega Drive)**.

## Objetivo

Analisar a ROM, identificar fonte/charset, localizar e extrair textos, preservar códigos de controle, traduzir, realocar textos quando necessário, corrigir ponteiros, inserir a tradução e validar a ROM final.

A ROM japonesa original permanece local e **não é distribuída pelo repositório**.

## Estado atual

A investigação já estabeleceu uma base técnica sólida, mas o projeto **ainda não está na fase de inserção de tradução**.

### Confirmado

- ROM japonesa de 2 MiB.
- CRC32 `01BC1604`.
- SHA-1 `F67C9139BBC93F171E274A5CD3FBA66480CD8244`.
- Header Mega Drive válido.
- **Shift-JIS** nos trechos japoneses identificados.
- 47 regiões fortemente sustentadas como texto japonês.
- Controles binários misturados ao texto.
- `0x01` confirmado como separador/quebra na abertura.
- `0x06 xx yy` confirmado como comando de três bytes, ainda sem semântica completa.
- `0x0E` observado como controle.
- `0x00` observado como terminador em estruturas textuais.
- Tabela explícita de códigos em `0x1A551A`, observada até `0x1A62D2`.
- A tabela contém códigos latinos maiúsculos acentuados; os minúsculos acentuados portugueses observados não estão presentes.
- O decoder estrutural consegue atravessar a abertura preservando os controles.

### Ainda não confirmado

- rotina 68000 definitiva do engine de texto;
- gramática completa dos controles;
- limites exatos das entradas;
- mecanismo de seleção dos scripts;
- tabela/formato definitivo de ponteiros;
- relação completa entre códigos e glifos;
- formato da fonte;
- compressão, caso exista para algum recurso;
- allocator/realocação;
- encoder/importador definitivo;
- patch PT-BR.

A regra do projeto é não transformar uma hipótese em conhecimento específico do jogo sem evidência direta da ROM/código.

## Documentação

- **[docs/analysis-results.md](docs/analysis-results.md)** — evidências e resultados técnicos consolidados.
- **[docs/reverse-engineering.md](docs/reverse-engineering.md)** — estratégia e critérios da engenharia reversa.
- **[docs/project-roadmap.md](docs/project-roadmap.md)** — roadmap completo, gates e critérios para chegar ao primeiro teste PT-BR seguro.
- **[docs/third-party-tooling-and-validation-plan.md](docs/third-party-tooling-and-validation-plan.md)** — plano de validação, comparação de ferramentas externas, gates e evidências necessárias antes de escrever a ROM.
- `reports/` — resultados reproduzíveis das análises.
- `tests/` — testes automatizados.

## Próximo marco

A próxima etapa é a **localização do engine 68000**, não a escrita da ROM.

O objetivo é comprovar uma cadeia:

`seleção do script → referência → leitura do byte → teste de controle → processamento → acesso à fonte/renderização`.

O plano atual prioriza estabilizar o CI, reproduzir as contagens do CFG e comparar o decoder próprio com desassembladores externos antes de tentar rastrear a execução em emulador. Consulte o [plano de ferramentas e validação](docs/third-party-tooling-and-validation-plan.md).

Somente depois serão implementados encoder, ponteiros de escrita, realocação e patch.

## Primeiro teste de tradução

O primeiro teste PT-BR será um **vertical slice mínimo e reversível**, não uma tradução completa.

Antes dele, o projeto deverá provar:

1. formato do script;
2. terminador;
3. controles;
4. limites das entradas;
5. rotina de leitura;
6. seleção/referência do script;
7. encoder reversível;
8. realocação segura, se necessária;
9. validação de referências e sobreposição;
10. execução da ROM modificada no emulador sem quebrar o fluxo.

O marco será chamado **M1 — Primeiro Texto PT-BR Executável**.

## Instalação e análise

```bash
python -m pip install -e ".[dev]"
pytest
```

Exemplo de análise:

```powershell
python -m dragonslayer_ptbr analyze `
  --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" `
  --report reports/rom-analysis.json
```

Os candidatos encontrados pelos analisadores são heurísticos. Nenhum offset deve ser tratado como confirmado sem validação e documentação.

## Estrutura

```text
src/dragonslayer_ptbr/
├── analysis/       # análise da imagem e engenharia reversa
├── text/           # decoder, encoder, tabelas e extrator
├── pointers/       # leitura, escrita e realocação
├── profiles/       # conhecimento específico do jogo
└── cli.py
```

## Ponto de parada atual

A análise M68K avançou para um CFG conservador baseado no vetor de reset real da ROM.

- vetor de reset: 0x010620;
- os relatórios históricos contêm contagens divergentes de blocos e devem ser reproduzidos com a mesma configuração antes de comparação;
- chamadas JSR abs.l e destinos foram acompanhados em análises anteriores;
- várias rotinas com RTS foram identificadas;
- decoder ampliado incrementalmente conforme os opcodes reais foram confirmados.

Suporte/testes adicionados nesta etapa incluem BTST #imm,<EA>, MOVE.W SR,<EA>, NEGX.B/W/L <EA> e LEA abs.l para A0–A7.

Isso ainda não significa que o engine de texto foi localizado. A próxima investigação continua sendo corrigir/verificar o CI, estabilizar o CFG, comparar desassemblagem, e rastrear registradores, leituras de bytes, controles e chamadas até chegar à fonte/renderização.

O projeto permanece em análise somente leitura; a ROM japonesa original não é modificada nem distribuída.
