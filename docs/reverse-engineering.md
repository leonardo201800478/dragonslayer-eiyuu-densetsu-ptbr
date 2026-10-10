# Estratégia de engenharia reversa do texto

## Objetivo e prioridade atual

Este documento registra a engenharia reversa auxiliar de **Dragon Slayer: Eiyuu Densetsu (Mega Drive)**. Como os textos já foram extraídos por ferramentas de terceiros, a prioridade do projeto é agora a bancada de tradução/adaptação PT-BR e a integração com os formatos reais dessas ferramentas.

A análise própria de ROM, ponteiros e código 68000 deve ser usada apenas quando houver uma lacuna concreta que as ferramentas externas não resolvam. A ROM original permanece local e não é modificada durante a análise.

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

## Quando retomar a análise 68000

Retomar a investigação somente se o fluxo externo não conseguir explicar ou executar uma etapa necessária, por exemplo a codificação dos acentos, o limite de uma entrada ou a reinserção. Nesse caso:

1. registrar a lacuna observada e um caso reproduzível;
2. comparar o dump externo com os bytes da ROM local;
3. consultar desassembladores/debuggers de terceiros;
4. usar os scanners Python próprios para reduzir a área de investigação;
5. confirmar o resultado antes de alterar um adaptador ou gerar arquivos para inserção.

## Por que não ampliar o scanner textual

Uma sequência estatisticamente parecida com texto não prova que seja texto.

Da mesma forma, um valor de 16, 24 ou 32 bits que aponta para dentro da ROM não prova que seja um ponteiro de script.

O scanner deve permanecer conservador para não transformar ruído em conhecimento específico do jogo.

## Papel do decoder próprio

O decoder próprio não é o caminho principal para a extração já realizada por ferramentas externas. Ele permanece disponível para inspeção comparativa de casos não explicados. Qualquer saída dele é uma representação de análise, não um formato de inserção. Um exemplo de representação auditável:

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

## 29. Rastreamento estático de A3

Foi adicionada a ferramenta:

    src/dragonslayer_ptbr/analysis/m68k_a3_flow.py

Ela procura definições explícitas de A3 por LEA, MOVEA.L e MOVEA.W, além de usos MOVE.B (A3)+,Dn.

Novo comando:

    python -m dragonslayer_ptbr scan-a3-flow --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --output reports/m68k-a3-flow.md

### Resultado preliminar na ROM

A análise local encontrou muitos usos de (A3)+, mas a região de maior interesse apresentou uma diferença importante:

- 0x026ADA: MOVEA.L $12(A1),A3;
- 0x026AE0: MOVE.B (A3)+,D0.

Isso demonstra uma origem concreta de A3 imediatamente antes de uma rotina que compara o byte lido com 0x00 até 0x05. Esse bloco continua sendo CANDIDATO, porque a comparação aparenta ser um dispatcher de estados e não há ainda ligação com o protocolo textual da abertura.

Na família 0x0308xx–0x030cxx, o uso de (A3)+ ocorre sem uma definição local próxima de A3. A definição estática anterior mais próxima é 0x0309EE, onde aparece LEA abs.l 0x00FF20AE,A3. Isso constitui evidência contra a interpretação imediata dessa família como parser de script: A3 pode estar apontando para uma estrutura de RAM do jogo.

Outra ocorrência relevante é 0x02B344:

    LEA $0001(A3),A3
    MOVE.B (A3)+,D0

Ela demonstra consumo sequencial de um byte a partir de um A3 recebido de contexto anterior, mas a rotina que fornece esse A3 ainda não foi identificada.

### Estado da hipótese

DESCARTADO como conclusão: MOVE.B (A3)+,D0 + CMPI.B não é suficiente para identificar o engine de texto.

CANDIDATO: 0x02B344 merece rastreamento adicional porque há alteração explícita do ponteiro A3 imediatamente antes da leitura.

CANDIDATO: 0x026ADA–0x026AE0 demonstra uma cadeia completa de definição de A3 → leitura → despacho, mas ainda não foi ligada ao texto.

O próximo passo deve ser encontrar os chamadores indiretos ou tabelas de entrada dessas rotinas e, principalmente, verificar se A3 pode ser alimentado por dados derivados da região 0x01626B.


## Atualização — checkpoint do fluxo 68000

A análise passou a utilizar o vetor de reset real como ponto de entrada e agora possui um CFG conservador com 43 blocos e 155 instruções reconhecidas no último relatório analisado.

Chamadas relevantes incluem 0x0109AA → 0x010AF2, três chamadas de 0x0109xx para 0x00B53E e uma chamada para 0x00B536. Algumas rotinas alcançadas terminam em RTS, permitindo acompanhar chamadas e retornos.

O decoder foi ampliado somente quando os bytes reais encontrados no fluxo exigiram cobertura. Nesta etapa foram adicionados BTST imediato, MOVE.W SR,<EA> e NEGX.B/W/L, além do suporte anterior a LEA absoluto para todos os registradores de endereço.

A presença isolada de MOVE.B (An)+,Dn ou CMPI.B #imm,Dn continua insuficiente para classificar uma rotina como parser. A promoção exige uma cadeia de execução que conecte dados de script, leitura sequencial, identificação de caracteres/controles e processamento/renderização.

O próximo passo permanece o rastreamento de A0–A3, leituras de bytes e chamadas dentro dos blocos alcançáveis, cruzando os resultados com as regiões textuais e a tabela 0x1A551A.


## 30. Rastreamento conservador de A0-A3

Foi adicionada a ferramenta:

    src/dragonslayer_ptbr/analysis/m68k_register_flow.py

e o comando:

    python -m dragonslayer_ptbr scan-m68k-register-flow --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --output reports/m68k-register-flow.md

O rastreamento parte do CFG alcançável pelo vetor de reset e procura, dentro de cada bloco básico:

- definições constantes de A0-A3 por LEA abs.l;
- definições relativas por LEA d16(PC);
- MOVEA.L/W com imediato;
- redefinições de A0-A3 por MOVEA;
- leituras MOVE.B (A0-A3) e (A0-A3)+;
- chamadas JSR.

A origem só é associada a uma leitura quando está no mesmo bloco básico e não houve JSR entre a definição e a leitura. Não há propagação artificial através de fronteiras de blocos ou chamadas.

**Objetivo desta etapa:** reduzir a busca por rotinas que consomem bytes sequencialmente e identificar candidatos em que o ponteiro de dados tenha uma origem concreta.

**Limite:** mesmo uma associação A3 → MOVE.B (A3)+ não prova que os dados sejam texto. A promoção para engine de texto continua dependendo da correlação com controles 0x01/0x06/0x0E/0x00 e com a renderização/fonte.



## 31. Resultado do rastreamento conservador de A0-A3

O relatório gerado pela execução de `scan-m68k-register-flow` registrou:

- **1.763 blocos** no grafo de fluxo de controle analisado;
- **391 definições** de A0-A3;
- **38 leituras de byte** por `MOVE.B (An)` ou `MOVE.B (An)+`;
- **332 chamadas JSR** identificadas.

Entre as 38 leituras, **12** receberam uma origem constante local dentro do mesmo bloco básico. Exemplos:

| Leitura | Registrador | Definição local | Valor atribuído |
|---:|---|---:|---:|
| `0x0026E0` | A1 | `0x0026CC` | `0x000A286E` |
| `0x002D92` | A0 | `0x002D7E` | `0x00002E1E` |
| `0x006112` | A0 | `0x0060FE` | `0x000063FC` |
| `0x006140` | A0 | `0x00612C` | `0x0002165A` |
| `0x011118` | A3 | `0x011110` | `0x000111A8` |
| `0x0111E8` | A0 | `0x0111D4` | `0x00011254` |
| `0x02DE1A` | A0 | `0x02DE06` | `0x0002DE7A` |

Essas associações confirmam somente a origem estática local do registrador. **Não demonstram que os destinos contenham texto.** As outras 26 leituras não receberam uma origem constante local; isso pode ocorrer porque o endereço vem de contexto anterior, de uma instrução não modelada, de outra região ou de uma chamada.

### Chamadas para priorizar

O relatório mostra chamadas repetidas para alguns alvos:

- `0x001D1E` — chamado por diversos pontos, inclusive em regiões `0x011xxx` e `0x02Cxxx`;
- `0x001EC0` — também chamado repetidamente nas mesmas famílias de regiões;
- `0x00D8F0` — chamado de vários pontos próximos entre `0x00D1D4` e `0x00D256`.

Esses endereços são **CANDIDATOS para inspeção do fluxo e das instruções**, não parsers confirmados. O próximo passo é descrever os blocos de entrada e saída desses alvos e identificar quais registradores e argumentos são preparados pelos chamadores.

### Limites e diferença em relação à análise anterior

Este relatório tem uma cobertura de CFG muito maior que o checkpoint anterior documentado (43 blocos e 155 instruções reconhecidas). Os números não devem ser comparados como se fossem a mesma execução: o relatório anterior era um recorte de análise e este resultado cobre 1.763 blocos.

O rastreador é intencionalmente conservador e limpa as associações locais em chamadas `JSR`. Assim, uma leitura sem origem local não é evidência de ausência de ponteiro de texto; significa apenas que o rastreador ainda não consegue provar a origem com as regras atuais.

### Próxima ação

1. Desassemblar os blocos em torno de `0x001D1E`, `0x001EC0` e `0x00D8F0`.
2. Mapear os registradores preparados imediatamente antes das chamadas e observados após o retorno.
3. Cruzar esses caminhos com a leitura dos bytes da abertura em `0x01626B)–`0x01668A` e com os controles `0x01`, `0x06 xx yy`, `0x0E` e `0x00`.
4. Comparar os resultados com o candidato previamente documentado em `0x026ADA`–`0x026AE0`, sem promovê-lo a parser enquanto a conexão com o script não for demonstrada.


## 32. Inspeção dos alvos de chamada candidatos

Foi adicionada a ferramenta `src/dragonslayer_ptbr/analysis/m68k_target_inspector.py` e o comando:

```powershell
python -m dragonslayer_ptbr inspect-m68k-targets --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md"
```

Por padrão, o relatório `reports/m68k-target-inspection.md` inspeciona os alvos `0x001D1E`, `0x001EC0` e `0x00D8F0`. Para informar outros offsets:

```powershell
python -m dragonslayer_ptbr inspect-m68k-targets --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --targets 0x1D1E 0x1EC0 0xD8F0 --output reports/m68k-target-inspection.md
```

O relatório reúne:
- chamadas diretas reconhecidas no CFG iniciado pelo vetor de reset;
- instruções e bytes de cada bloco chamador encontrado;
- fluxo decodificado ao iniciar uma análise separada em cada alvo;
- avisos quando o decoder não reconhece instruções no offset.

O início de uma análise em um alvo é intencional: permite inspecionar uma rotina mesmo que o CFG principal não a alcance devido a limitações do decoder. **Isso não prova que o alvo seja código executado em runtime.** Chamadas indiretas como `JSR (An)` permanecem sem destino resolvido. O relatório também não atribui semântica de parser a uma rotina sem demonstrar a ligação com scripts, controles e renderização.


## 33. Correção do padrão de leitura no scanner de candidatos a parser

A revisão dos opcodes do 68000 revelou uma inconsistência no scanner
`scan-text-parser-candidates`: o código e a descrição diziam procurar
`MOVE.B (An)+,Dn`, mas a máscara usada aceitava o modo de endereçamento
`(An)` sem pós-incremento.

A máscara foi corrigida para reconhecer o padrão `MOVE.B (An)+,Dn`.
Os testes agora distinguem explicitamente:

- `MOVE.B (A3)+,D0` — deve ser detectado;
- `MOVE.B (A3),D0` — não deve ser classificado como leitura com pós-incremento;
- leitura e comparação em registradores diferentes — não devem ser associadas.

Esta correção melhora a confiabilidade do scanner, mas não identifica por si só
o engine de texto. O scanner ainda busca padrões binários na ROM inteira e pode
encontrar bytes que coincidam com instruções em áreas de dados. Os resultados
continuam sendo candidatos até serem cruzados com o fluxo de controle alcançável
e com evidências do protocolo textual.


## 34. Cruzamento de leitura e controles no CFG alcançável

Foi adicionada a análise `m68k_reachable_text.py` e o comando:

```powershell
python -m dragonslayer_ptbr scan-reachable-text --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --output reports/m68k-reachable-text.md
```

Diferente do scanner amplo `scan-text-parser-candidates`, esta ferramenta primeiro constrói o grafo de fluxo de controle a partir do vetor de reset e só avalia instruções cujos offsets aparecem nos blocos reconhecidos. Procura `MOVE.B (An)+,Dn` seguido, dentro do mesmo bloco e em uma distância limitada, por `CMPI.B #controle,Dn` para os valores `0x01`, `0x06`, `0x0E` e `0x00`.

O relatório inclui bloco, offset da leitura, offset do teste, registrador de endereço, registrador de dados e controle comparado. O teste unitário garante também que um padrão binário fora dos blocos fornecidos não seja incluído.

**Limites:** o CFG depende de um decoder parcial, e bytes de dados podem ocasionalmente ser alcançados por um fluxo incorreto. A associação no mesmo bloco não prova que o ponteiro contenha script nem que o teste faça parte do engine de texto. O resultado é um filtro mais forte para priorização, não uma confirmação semântica.



## 35. Experimento exploratório com Engine9000 e retorno à análise estática

O Engine9000 foi usado durante uma batalha e na tela de vitória para tentar observar a execução em runtime. O experimento foi interrompido por baixo retorno prático: os logs registraram acessos à interface do Z80, mas não demonstraram relação direta com o processamento de texto.

### Evidências observadas

- Um watchpoint de leitura foi cadastrado em `0x016529`, endereço que contém o nome japonês `セリオス`. Nenhum disparo foi confirmado.
- Um breakpoint foi cadastrado em `0x00D49A`; os avisos seguintes não demonstraram que o 68000 tenha sido interrompido nesse endereço.
- Um breakpoint em `0x0262C4` foi aceito, mas não houve evidência de que o endereço tenha sido alcançado durante a situação observada.
- Na tela de vitória, estavam visíveis as mensagens `EP 4 が かくとく。` e `4 Gold 手に入れました。`.
- Capturas distintas mostraram PCs como `0x016A78` e `0x00D64C`; não constituem um rastreamento contínuo da mesma rotina.
- A memória em `0x016A00` e os bytes a partir de `0x00D510` foram inspecionados visualmente. Isso não confirmou se todos os bytes observados eram código executado nem identificou uma rotina de texto.
- Os logs `68k z80 read with no bus` e `write with no bus or reset` mencionaram acessos a `0xA04000`–`0xA04003`. A relação desses acessos com o texto não foi demonstrada; podem estar associados à interface do Z80/subsistema de áudio.

### Conclusão

O experimento não identificou o parser de texto em runtime. O cadastro de um breakpoint, por si só, não demonstra que ele foi atingido. Os endereços e avisos observados devem permanecer como pistas exploratórias, não como descobertas confirmadas.

### Decisão de método

Pausar o rastreamento interativo com Engine9000 por enquanto e retornar ao método estático reproduzível:

1. Executar os scanners 68000 existentes sobre a ROM original.
2. Priorizar blocos alcançáveis a partir do vetor de reset e leituras sequenciais de bytes associadas a comparações com `0x01`, `0x06`, `0x0E` e `0x00`.
3. Cruzar os candidatos com a região textual `0x01626B–0x01668A` e a tabela Shift-JIS em `0x1A551A`.
4. Classificar conclusões como CONFIRMADO, HIPÓTESE ou DESCARTADO; não promover um candidato a parser apenas por semelhança de instruções.

Comandos para retomar a análise estática:

```powershell
python -m dragonslayer_ptbr scan-reachable-text --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --output reports/m68k-reachable-text.md
python -m dragonslayer_ptbr scan-m68k-register-flow --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --output reports/m68k-register-flow.md
python -m dragonslayer_ptbr inspect-m68k-targets --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --output reports/m68k-target-inspection.md
```

Este checkpoint registra observações exploratórias e a decisão de método; não confirma uma rotina de texto nem altera a ROM.
