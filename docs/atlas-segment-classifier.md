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

Para limitar exemplos exibidos:

```powershell
python tools/inspect_atlas_segments.py reports/legacy-tooling-test/tools/text --limit 20
```

A saída é JSON no terminal e inclui contagens por tipo de linha e segmento,
exemplos de linhas japonesas e erros de decodificação. O script só abre os
arquivos em leitura.

## Categorias

- `DIRECTIVE`: linha iniciada por uma diretiva `#...`; não é segmentada.
- `FILE_REFERENCE`: linha que contém `[FILE]`; preservada como referência.
- `COMMENT`: comentários iniciados por `//` ou `;`, além de linhas `[TEXT]`.
- `TEXT`: linha com texto japonês e sem marcadores reconhecidos.
- `MIXED`: texto japonês misturado com marcadores inline.
- `OTHER`: linha sem texto japonês detectado, incluindo sequências de controle.

Os segmentos inline são classificados como `TEXT`, `DICTIONARY_MARKER`,
`LINE_MARKER`, `CONTROL_FLOW_MARKER`, `HEX_BYTE` ou `UNKNOWN_MARKER`.
Marcadores desconhecidos são preservados; a ferramenta não tenta adivinhar
sua semântica.

## Testes

```powershell
pytest tests/test_atlas_segmenter.py
ruff check src/dragonslayer_ptbr/text/atlas_segmenter.py tools/inspect_atlas_segments.py tests/test_atlas_segmenter.py
```

## Limitações e segurança

A classificação não prova que um segmento é seguro para tradução. O conteúdo
entre `<...>` pode representar códigos de texto, controles, marcadores específicos
do jogo ou outra sintaxe. A classificação de `<JMP.L>`, bytes hexadecimais e
marcadores especiais precisa ser confrontada com os scripts Atlas e a documentação
do projeto. Não use a saída como entrada para inserção na ROM.

O próximo passo após revisar o relatório é comparar a classificação com amostras
reais e ampliar os testes de reconstrução exata. A inserção continua bloqueada
até que a codificação, a tabela de caracteres e as regras do Atlas sejam validadas.
