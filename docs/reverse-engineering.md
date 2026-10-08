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


## Mapa confirmado de controles da abertura

O scanner de controles foi executado sobre a região:

```
0x01626B–0x01668A
```

Resultado: **42 ocorrências**.

### Frequência

| Bytes | Ocorrências | Estado |
|---|---:|---|
| `01` | 33 | **CONFIRMADO — controle de apresentação; contexto indica separação/quebra de linha** |
| `06 FE 0E` | 5 | **CONFIRMADO — comando de 3 bytes; semântica ainda desconhecida** |
| `06 00 FE` | 1 | **CONFIRMADO — comando de 3 bytes; semântica ainda desconhecida** |
| `06 08 06` | 1 | **CONFIRMADO — comando de 3 bytes; semântica ainda desconhecida** |
| `0E` | 1 | **CONFIRMADO — controle individual; semântica ainda desconhecida** |
| `00` | 1 | **CONFIRMADO — terminador observado na estrutura analisada** |

### Ocorrências relevantes

Os comandos `06 FE 0E` aparecem em:

```
0x0162F1
0x016399
0x016459
0x016515
0x0165F7
```

A sequência especial próxima ao fim da abertura é:

```
0x016658  06 00 FE
0x01665B  0E
0x01665C  01
0x01665D  01
0x01665E  01
0x01665F  01
0x016660  01
0x016681  06 08 06
0x016686  00
0x016688  01
```

### Regularidade dos separadores

Os `0x01` aparecem em posições aproximadamente regulares. Há vários intervalos de **32 ou 33 bytes** entre separadores consecutivos, embora também existam intervalos menores e maiores.

Isso constitui uma **HIPÓTESE de estrutura de linhas/blocos com largura limitada**, e não uma confirmação de que o jogo utiliza exatamente 32 ou 33 bytes por linha.

A sequência de cinco `0x01` consecutivos após `06 00 FE` é especialmente relevante: ela reforça que `0x01` pertence ao protocolo de apresentação e não ao conjunto de caracteres Shift-JIS.

### Assinatura útil para a análise 68000

A abertura fornece agora uma assinatura de dados suficientemente específica para procurar a rotina de interpretação:

```
Shift-JIS
  +
0x01
  +
0x06 xx yy
  +
0x0E
  +
0x00
```

A repetição de `06 FE 0E` cinco vezes torna essa sequência uma boa assinatura para validar se uma rotina 68000 encontrada realmente processa esse protocolo.

### Limite da interpretação atual

Ainda não é permitido afirmar que:

- `06 FE 0E` significa mudança de página, atraso, retrato, som ou outro evento;
- `06 00 FE` ou `06 08 06` tenham funções específicas;
- `0x0E` tenha uma função específica;
- 32/33 bytes sejam a largura fixa da janela;
- a região inteira corresponda a uma única entrada de script.

Essas questões devem ser resolvidas pela análise estática do código 68000.

## Próxima etapa de engenharia reversa

A investigação deixa de priorizar heurísticas genéricas de ponteiros e passa a procurar a rotina 68000 que:

1. recebe ou calcula um endereço de dados próximo de `0x01626B`;
2. lê bytes sequencialmente;
3. diferencia caracteres Shift-JIS de controles;
4. trata `0x01`;
5. reconhece `0x06` e consome os dois bytes seguintes;
6. trata `0x0E`;
7. reconhece `0x00` quando aplicável;
8. possivelmente consulta a tabela de caracteres em `0x1A551A`.

O objetivo imediato é identificar o **engine real de processamento de texto**, antes de implementar encoder, realocação ou patching.


## 26. Ferramenta inicial de referências 68000

Foi adicionada a ferramenta:

src/dragonslayer_ptbr/analysis/m68k_references.py

e o comando:

    python -m dragonslayer_ptbr scan-refs --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --output reports/m68k-references.md

O scanner procura os alvos confirmados:

    0x01626B  abertura / região de script investigada
    0x1A551A  tabela de caracteres Shift-JIS

em representações:

- 24-bit big-endian;
- 32-bit big-endian.

Quando os quatro bytes imediatamente anteriores a uma referência formam um opcode 68000 reconhecido de forma inequívoca, o relatório também registra a classificação, incluindo:

    LEA abs.l
    PEA abs.l
    JSR abs.l
    JMP abs.l
    MOVEA.L #imm,An

### Limite metodológico

Esta ferramenta não é um desassembler.

Uma ocorrência literal de 01 62 6B ou 00 1A 55 1A pode estar em dados, gráficos, código ou estruturas não relacionadas. Mesmo uma instrução reconhecida não prova, isoladamente, que aquele caminho é executado como rotina de texto.

O objetivo é reduzir o espaço de busca e produzir evidência para a análise seguinte.

### Próximo passo após executar o scanner

Os resultados mais importantes serão:

1. referências ao 0x01626B classificadas como instrução 68000;
2. referências ao 0x1A551A classificadas como LEA, MOVEA, JSR ou JMP;
3. proximidade dessas referências entre si;
4. blocos de código que contenham testes/leituras próximos aos controles 0x01, 0x06 e 0x0E.

A partir daí será possível escolher pontos de entrada para uma análise 68000 mais profunda, em vez de procurar cegamente por toda a ROM.


## 27. Resultado: referências literais não encontradas

A primeira execução do comando scan-refs retornou:

    opening_script: 0
    character_table: 0

Isso é um resultado válido e importante.

**CONFIRMADO:** a ROM não contém, nas formas pesquisadas, referências literais diretas aos offsets 0x01626B e 0x1A551A.

Portanto, não devemos concluir que essas estruturas sejam inacessíveis ao programa. O código pode calcular os endereços, usar tabelas intermediárias, carregar offsets relativos ou acessar dados através de registradores e estruturas de contexto.

A estratégia de procurar somente o endereço final foi encerrada como método principal.

## 28. Segunda abordagem: procurar a interpretação dos controles

Foi adicionada:

    src/dragonslayer_ptbr/analysis/m68k_control_tests.py

Ela procura instruções 68000 inequívocas do formato:

    CMPI.B #imm,Dn

para os valores de controle já observados:

    0x01
    0x06
    0x0E
    0x00

Novo comando:

    python -m dragonslayer_ptbr scan-control-tests --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --output reports/m68k-control-tests.md

Essa abordagem procura o comportamento do parser em vez do endereço final do texto.

### Resultado exploratório na ROM local

Uma análise equivalente sobre a ROM validada encontrou:

- 28 ocorrências de CMPI.B para 0x01;
- 28 ocorrências para 0x06;
- 4 ocorrências para 0x0E.

Os bytes 0x00 produzem muitas ocorrências e, por isso, são pouco discriminantes isoladamente.

Foram observados três agrupamentos particularmente relevantes de comparações não-zero próximas:

    0x1DE6C – 0x1DF0A
    0x266C0 – 0x266E8
    0x30B16 – 0x30B70

Esses agrupamentos são **CANDIDATOS DE INVESTIGAÇÃO**, não engine confirmado.

O bloco em torno de 0x266C0 contém uma sequência de comparações de D0 com valores 0x00–0x07, aparentando ser uma tabela/dispatcher de estados. Isso torna o bloco útil para entender o mecanismo de despacho, mas não há evidência suficiente para classificá-lo como parser de texto.

O bloco em torno de 0x30B16 contém testes explícitos de 0x01 e 0x0E. Também é apenas candidato.

### Próxima análise

O próximo passo é correlacionar essas comparações com:

1. instruções que leem bytes de memória;
2. operações de pós-incremento em registradores de endereço, como MOVE.B (An)+,...;
3. saltos condicionais imediatamente posteriores;
4. chamadas JSR próximas;
5. acesso a estruturas que possam apontar para scripts.

A meta passa a ser reconstruir uma pequena cadeia de execução:

    leitura de byte
        ↓
    comparação/teste
        ↓
    despacho do controle
        ↓
    avanço do ponteiro do script
        ↓
    renderização

Somente quando essa cadeia for demonstrada um bloco será promovido a rotina de texto.
