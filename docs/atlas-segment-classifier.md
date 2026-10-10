# Classificação conservadora de scripts Atlas

## Objetivo

O módulo `src/dragonslayer_ptbr/text/atlas_segmenter.py` classifica linhas e
separa marcadores inline dos trechos intermediários sem reescrever o texto.
O inspetor é lexical e experimental: não executa diretivas Atlas, não calcula
ponteiros e não cria arquivos para inserção na ROM.

## Executar relatório

Na raiz do repositório, com o ambiente virtual ativo:

```powershell
python tools/inspect_atlas_segments.py reports/legacy-tooling-test/tools/text
```

Para limitar exemplos de linhas textuais exibidos:

```powershell
python tools/inspect_atlas_segments.py reports/legacy-tooling-test/tools/text --limit 20
```

A saída JSON inclui contagens por tipo de linha e segmento, exemplos de linhas
japonesas, erros de decodificação e marcadores `UNKNOWN_MARKER` ordenados por
frequência. Cada marcador desconhecido inclui até três exemplos com arquivo,
número da linha, classificação da linha e conteúdo bruto. Comentários e
diretivas não são segmentados e não entram nessa contagem.

## Categorias de linha

- `DIRECTIVE`: linha iniciada por uma diretiva `#...`; não é segmentada.
- `FILE_REFERENCE`: linha que contém `[FILE]`; preservada como referência.
- `COMMENT`: comentários iniciados por `//` ou `;`, além de linhas `[TEXT]`.
- `TEXT`: linha com texto japonês e sem marcadores inline.
- `MIXED`: texto japonês misturado com marcadores inline.
- `OTHER`: linha sem texto japonês detectado, incluindo sequências de controle.

## Categorias de segmento

- `TEXT`: trecho textual entre marcadores.
- `DICTIONARY_MARKER`: marcador `<DICT XX>`.
- `LINE_MARKER`: marcador `<LINE>`.
- `CONTROL_FLOW_MARKER`: marcadores de fluxo listados no código e forma
  parametrizada `<JMP XX>`.
- `WAIT_MARKER`: formas `<WAIT>` e `<WAIT CLEAR>`.
- `COLOR_MARKER`: formas `<COLOR OFF>` e `<COLOR XX>`.
- `HERO_MARKER`: forma parametrizada `<HERO N>`.
- `FLAG_MARKER`: forma parametrizada `<FLAG XX>`.
- `CODE_MARKER`: forma parametrizada `<CODE XX>`.
- `NAME_MARKER`: marcador `<NAME>`.
- `HEX_BYTE`: byte hexadecimal no formato `<$XX>`.
- `UNKNOWN_MARKER`: marcador que não corresponde às formas reconhecidas.

As categorias são sintáticas, não uma confirmação da semântica do jogo. Por
exemplo, reconhecer `<FLAG 14>` não significa conhecer o efeito dessa flag.
Marcadores desconhecidos permanecem preservados e não são corrigidos
automaticamente. A concatenação dos valores dos segmentos deve reproduzir a
linha original exatamente.

## Testes

```powershell
pytest tests/test_atlas_segmenter.py
ruff check src/dragonslayer_ptbr/text/atlas_segmenter.py tools/inspect_atlas_segments.py tests/test_atlas_segmenter.py
```

## Limitações e segurança

A classificação não prova que um segmento é seguro para tradução. O conteúdo
entre `<...>` pode representar códigos de texto, controles, marcadores
específicos do jogo ou outra sintaxe. O projeto documenta texto comprimido,
dados e código embutidos, ponteiros relativos e fluxo de execução não trivial.
Não use a saída como entrada para inserção na ROM.

O relatório serve para priorizar revisão manual. A inserção continua bloqueada
até que codificação, tabela de caracteres e regras Atlas sejam validadas.
