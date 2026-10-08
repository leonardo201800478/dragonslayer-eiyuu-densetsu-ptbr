# Estratégia de engenharia reversa do texto

## Objetivo

Identificar o sistema real de texto de **Dragon Slayer: Eiyuu Densetsu (Mega Drive)** sem assumir charset, ponteiros ou códigos de controle antes de obter evidência da ROM.

A ROM original permanece local e não é modificada durante a análise.

## Evidência externa usada como referência

O trabalho de engenharia reversa da tradução de **Lord Monarch: Tokoton Sentou Densetsu (Mega Drive)** descreve um engine em que:

- diálogos são conduzidos por uma máquina de estados;
- caracteres podem ocupar 1 ou 2 bytes;
- existem códigos de controle para eventos como quebra de linha, atraso e retratos;
- alguns códigos executam ASM, chamam subrotinas ou redirecionam o fluxo;
- scripts são referenciados por ponteiros de diferentes formatos;
- existem tabelas de ponteiros;
- os scripts podem estar fragmentados pela ROM;
- a análise das referências foi feita com Ghidra antes da criação do extrator/importador.

Essa informação é uma **referência metodológica**, não uma afirmação de que Dragon Slayer: Eiyuu Densetsu utiliza exatamente o mesmo formato.

## Estado atual

A análise estatística inicial da ROM japonesa encontrou muitos candidatos a ponteiros e regiões textuais, mas eles não são suficientes para confirmar o formato.

Portanto, os módulos:

- `analysis/rom.py`
- `analysis/pointers.py`
- `analysis/text_regions.py`

continuam sendo ferramentas exploratórias.

Nenhum offset retornado por eles deve entrar no profile do jogo como conhecimento confirmado sem validação adicional.

## Próxima etapa

A investigação deve migrar de heurística de dados para análise do código 68000:

1. identificar regiões de código executável plausíveis;
2. localizar instruções que referenciem dados da ROM;
3. acompanhar referências que possam chegar a rotinas de impressão;
4. identificar a rotina que consome os bytes do texto;
5. determinar o formato dos caracteres;
6. determinar terminadores e códigos de controle;
7. determinar como os scripts são referenciados;
8. somente depois implementar o decoder específico.

## Por que não ampliar o scanner textual

Uma sequência estatisticamente parecida com texto não prova que seja texto.

Da mesma forma, um valor de 16, 24 ou 32 bits que aponta para dentro da ROM não prova que seja um ponteiro de script.

O scanner deve permanecer conservador para não transformar ruído em conhecimento específico do jogo.

## Objetivo do primeiro decoder

O primeiro decoder não deve traduzir nem modificar a ROM.

Ele deverá somente produzir uma representação auditável, por exemplo:

```text
script @ 0xXXXXXX
  [controle 0x??]
  [char 0x??]
  [char 0x??]
  [controle 0x??]
  ...
```

Depois que o formato estiver confirmado, essa representação poderá evoluir para:

- dump de script;
- tabela de caracteres;
- preservação de códigos de controle;
- encoder;
- cálculo de tamanho;
- realocação;
- correção de ponteiros;
- geração de patch.

## Referências

- Nebulous Translations — Lord Monarch: Tokoton Sentou Densetsu, seção "Hacking notes".
- O projeto atual: `README.md`.

## Regra de validação

Toda informação específica do jogo deve ser classificada como:

- **CONFIRMADO** — demonstrado diretamente pela ROM/código;
- **REFERÊNCIA** — observado em outro projeto e usado somente como hipótese metodológica;
- **HIPÓTESE** — ainda precisa de validação;
- **DESCARTADO** — testado e considerado incompatível.

Nenhum item classificado como REFERÊNCIA ou HIPÓTESE deve ser usado como offset definitivo do jogo.


## Primeira confirmação direta da ROM

Com a ROM japonesa local de 2 MiB, identificada por CRC32 **01BC1604** e SHA-1 **F67C9139BBC93F171E274A5CD3FBA66480CD8244**, foi possível confirmar diretamente o charset em regiões de texto:

- **CONFIRMADO — Shift-JIS:** nomes e frases japonesas presentes na ROM decodificam corretamente com o codec shift_jis.
- Exemplos de evidência binária: **セリオス** em **0x016529** e **アクダム** em **0x016583**.
- A abertura narrativa forma uma região textual contínua aproximadamente entre **0x01626B** e **0x01667F**.
- Há outras regiões textuais confirmáveis, entre elas aproximadamente **0x02DF10–0x02E14D**, **0x02EE63–0x02F036** e **0x032325–0x03267A**.

Também foi confirmado o uso de bytes de controle misturados ao Shift-JIS:

- **0x01** aparece como separador de linha na abertura;
- **0x06 xx yy** aparece repetidamente como controle de três bytes;
- **0x00** aparece como terminador em diversas estruturas;
- outros bytes abaixo de **0x20** (**0x05**, **0x07**, **0x0A**, **0x0D**, **0x0F**, **0x1E** e **0x1F**) também aparecem no script e ainda não tiveram sua semântica determinada.

Isso permite afirmar que o problema não é mais "descobrir se existe texto": **o texto japonês foi localizado e o charset foi confirmado**. O próximo problema é reconstruir o formato lógico das entradas, seus ponteiros e a semântica dos controles.

## Ferramenta inicial de leitura

Foi adicionado o módulo text/script_codec.py, que:

- decodifica caracteres Shift-JIS;
- preserva controles simples;
- preserva 0x06 mais dois bytes como controle estendido;
- preserva bytes desconhecidos como RAW;
- pode parar no terminador 0x00;
- não modifica a ROM;
- não atribui significado aos controles ainda.

A CLI agora possui o comando decode-text. Exemplo:

    python -m dragonslayer_ptbr decode-text --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --offset 0x1626B --size 0x420 --output reports/opening-script.txt

Esse comando é deliberadamente de leitura. A etapa de encoder/inserção permanece bloqueada até que o formato das referências e o significado dos controles sejam confirmados.


## Segunda confirmação: tabela de caracteres

Há uma segunda evidência direta relevante em **0x1A551A**:

- o conteúdo começa com códigos Shift-JIS como **0x8140** e segue em sequência por pontuação, hiragana e katakana;
- depois aparecem centenas de códigos de kanji em ordem;
- a estrutura é compatível com uma tabela de repertório/códigos de caracteres usada pelo sistema de fonte.

**CONFIRMADO:** a ROM contém uma tabela explícita de códigos Shift-JIS em **0x1A551A**.

**HIPÓTESE ainda não resolvida:** essa tabela pode participar diretamente da localização dos glifos ou de uma etapa de compressão/renderização da fonte. O significado exato e a rotina que a consulta ainda precisam ser encontrados no código 68000.

Isso é particularmente importante para a tradução porque reduz o risco de criar uma tabela de caracteres artificial: o próprio jogo já fornece uma tabela de repertório que podemos usar como referência para o encoder futuro.
