# Relatório consolidado de engenharia reversa

## 1. Identificação da ROM analisada

ROM japonesa de **Dragon Slayer: Eiyuu Densetsu**, Mega Drive/Genesis.

| Campo | Resultado |
|---|---|
| Tamanho | 2.097.152 bytes (2 MiB) |
| CRC32 | `01BC1604` |
| SHA-1 | `F67C9139BBC93F171E274A5CD3FBA66480CD8244` |
| Header Genesis | válido |
| Plataforma | Mega Drive |
| Região | Japão |

A ROM permanece local e não é distribuída pelo repositório.

---

## 2. Primeira análise estrutural

O comando utilizado foi:

```powershell
python -m dragonslayer_ptbr analyze `
  --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" `
  --report "reports/rom-analysis.json"
```

Resultado registrado:

- 8.192 blocos analisados com blocos de 0x100 bytes;
- 9.774 regiões candidatas pelo scanner ASCII inicial;
- 284 blocos classificados como `ascii_like`;
- 340 como `ff_fill`;
- 4 como `low_variation`;
- 7.528 como `mixed`;
- 36 como `zero_fill`.

Essas classificações são estatísticas e **não identificam sozinhas código, gráficos, texto ou dados comprimidos**.

---

## 3. Análise de ponteiros

A primeira varredura encontrou muitos candidatos:

| Largura | Destinos repetidos | Tabelas candidatas |
|---|---:|---:|
| 16-bit | 60.205 | 1.000 |
| 24-bit | 56.279 | 0 |
| 32-bit | 4.503 | 0 |

Esses números demonstraram principalmente o problema do método: uma ROM de Mega Drive contém muitos valores que coincidentemente apontam para dentro da imagem.

### Exemplos das primeiras tabelas 16-bit

As primeiras candidatas incluíam:

- `0x00069C`: 5 entradas, alvos entre `0x000402` e `0x00040C`;
- `0x0006AA`: 43 entradas, alvos próximos de `0x000412`–`0x00045A`;
- `0x000706`: 30 entradas;
- `0x000744`: 31 entradas;
- `0x000786`: 11 entradas;
- `0x00079C`: 6 entradas;
- `0x0007A8`: 9 entradas;
- `0x0007BA`: 4 entradas;
- `0x006BC0`: 28 entradas, com alvos na região `0x000B62`–`0x01372`.

A inspeção mostrou que várias dessas sequências são compatíveis com estruturas numéricas ou dados internos, não necessariamente tabelas de scripts.

**Conclusão:** nenhuma dessas primeiras tabelas 16-bit foi promovida a tabela de ponteiros de texto confirmada.

Por isso, `analysis/pointers.py` permanece uma ferramenta exploratória.

---

## 4. Localização direta do texto japonês

A investigação deixou de depender somente das heurísticas quando foram encontrados trechos japoneses legíveis diretamente na ROM.

### Charset

**CONFIRMADO: Shift-JIS.**

Exemplos identificados:

- `セリオス` em aproximadamente `0x016529`;
- `アクダム` em aproximadamente `0x016583`;
- `ファーレーン` na mesma região textual.

A abertura narrativa ocupa aproximadamente:

```
0x01626B – 0x01667F
```

Também foram localizadas outras regiões textuais, incluindo aproximadamente:

```
0x02DF10 – 0x02E14D
0x02EE63 – 0x02F036
0x032325 – 0x03267A
0x0338D5 – 0x0343CD
```

Essas regiões são evidência direta de dados textuais japoneses; os limites exatos de cada entrada individual ainda precisam ser determinados.

---

## 5. Controles do script

Foram observados bytes de controle misturados ao texto Shift-JIS.

### Confirmado

- `0x01` aparece como separador/quebra de linha na abertura;
- `0x06 xx yy` aparece repetidamente como estrutura de três bytes;
- `0x00` aparece como terminador em estruturas textuais;
- os bytes `0x05`, `0x07`, `0x0A`, `0x0D`, `0x0F`, `0x1E` e `0x1F` aparecem em regiões de script.

### Ainda não confirmado

O significado semântico individual de cada controle ainda não foi determinado.

Portanto, o projeto **não deve** chamar esses bytes de "delay", "retrato", "nome", "som" etc. sem rastrear a rotina 68000 que os interpreta.

O único nome seguro neste estágio é **controle**.

---

## 6. Tabela de caracteres

Foi encontrada uma estrutura importante em:

```
0x1A551A
```

A sequência contém códigos Shift-JIS como:

```
0x8140
```

e continua por repertórios de pontuação, hiragana, katakana e uma grande quantidade de kanji.

### Classificação

**CONFIRMADO:** existe uma tabela explícita de códigos Shift-JIS nessa região.

**HIPÓTESE:** essa tabela participa da infraestrutura da fonte e/ou da conversão entre códigos e glifos.

O papel exato da tabela ainda precisa ser confirmado pelo código 68000 que a consulta.

O offset foi registrado no profile do jogo como conhecimento confirmado da análise:

```python
character_table_offset: int = 0x1A551A
```

---

## 7. Decoder inicial

Foi criado:

```
src/dragonslayer_ptbr/text/script_codec.py
```

Ele:

- decodifica caracteres Shift-JIS;
- reconhece caracteres de 1 e 2 bytes;
- preserva controles de um byte;
- preserva `0x06` junto de seus dois bytes seguintes como controle estendido;
- preserva bytes desconhecidos como `RAW`;
- reconhece `0x00` como terminador;
- pode interromper a leitura no primeiro terminador;
- não altera a ROM.

O renderer transforma os controles em uma representação auditável, por exemplo:

```text
テスト<CTRL 01>ABC<CTRL 06 FE 0E><END>
```

Importante: o decoder atual é deliberadamente **estrutural**, não é ainda o decoder definitivo do engine.

---

## 8. Comando de leitura do script

A CLI possui:

```powershell
python -m dragonslayer_ptbr decode-text `
  --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" `
  --offset 0x1626B `
  --size 0x420 `
  --output reports/opening-script.txt
```

O comando é somente leitura.

Ele não:

- modifica a ROM;
- grava bytes na ROM;
- altera ponteiros;
- traduz automaticamente;
- interpreta semanticamente os controles.

---

## 9. Profile atual

O profile registra somente informações que já possuem evidência suficiente:

```python
@dataclass(frozen=True)
class DragonSlayerProfile:
    name: str = "Dragon Slayer: Eiyuu Densetsu"
    region: str = "Japan"
    platform: str = "Mega Drive"
    text_encoding: str = "shift_jis"
    extended_control_prefix: int = 0x06
    character_table_offset: int = 0x1A551A
```

O profile ainda **não** contém:

- endereço definitivo da rotina de texto;
- tabela definitiva de ponteiros;
- formato definitivo dos ponteiros;
- tabela completa de controles;
- localização definitiva de todos os scripts;
- formato da fonte;
- algoritmo de compressão;
- rotina de realocação.

Esses itens só devem entrar depois da validação no código 68000.

---

## 10. Trilha B — pesquisa de ferramentas históricas

A investigação externa encontrou referências históricas a um **starter pack/toolchain de Dragon Slayer: The Legend of Heroes II para Mega Drive/Genesis**.

Discussões da comunidade indicam que esse material contém ferramentas Windows para:

- dump de assets;
- dump dos dados de script;
- investigação do formato da ROM.

Também foi relatado que um pesquisador conseguiu portar parte de um helper desse material para Python moderno e obter um dump dos dados de script.

O material histórico ainda não foi recuperado de forma suficiente para ser usado como implementação do projeto.

Portanto:

**Classificação: REFERÊNCIA.**

Não foram importados offsets ou formatos desse material para o profile do jogo.

---

## 11. Referência técnica: Lord Monarch

O projeto de tradução de **Lord Monarch: Tokoton Sentou Densetsu**, outro título Dragon Slayer/Falcom para Mega Drive, forneceu uma referência metodológica importante.

As notas de engenharia reversa desse projeto descrevem:

- máquina de estados para diálogos;
- caracteres de 1 e 2 bytes;
- aproximadamente 20 códigos de controle;
- códigos de quebra de linha, atraso, retratos e outras funções;
- códigos capazes de executar ASM, chamar subrotinas ou alterar fluxo;
- referências por ponteiros de 4 bytes, 2 bytes, absolutos, relativos e tabelas;
- scripts fragmentados na ROM;
- análise das referências com Ghidra;
- extrator/importador que realoca scripts e corrige referências;
- necessidade de otimização/reempacotamento de recursos para acomodar a tradução;
- implementação de VWF para ampliar a capacidade horizontal do texto.

Essa referência é útil para orientar a investigação, mas **não prova que Eiyuu Densetsu utilize o mesmo engine ou os mesmos formatos**.

**Classificação: REFERÊNCIA.**

---

## 12. O que já foi descartado

### Scanner ASCII como solução de extração

**DESCARTADO como método definitivo.**

Ele é útil para encontrar regiões iniciais, mas o jogo utiliza Shift-JIS e controles binários. Portanto, uma busca somente por ASCII não consegue representar o script real.

### Candidatos estatísticos de ponteiros como ponteiros de script

**DESCARTADO como confirmação automática.**

Os milhares de candidatos 16/24/32-bit demonstram que apontar para dentro da ROM não basta para identificar uma referência de script.

### Assumir o engine de Lord Monarch

**DESCARTADO como fato.**

Lord Monarch continua como referência metodológica, não como especificação de Eiyuu Densetsu.

### Inserção de tradução neste estágio

**DESCARTADO temporariamente.**

Ainda não temos informação suficiente para realizar uma inserção segura.

---

## 13. Estado atual por componente

| Componente | Estado |
|---|---|
| Identificação da ROM | **CONFIRMADO** |
| Header Mega Drive | **CONFIRMADO** |
| Charset Shift-JIS | **CONFIRMADO** |
| Regiões de texto | **CONFIRMADO** |
| Controle 0x01 | **CONFIRMADO como controle/separador** |
| Estrutura 0x06 xx yy | **CONFIRMADO como controle de 3 bytes; sem semântica** |
| Terminador 0x00 | **CONFIRMADO em estruturas observadas** |
| Tabela Shift-JIS em 0x1A551A | **CONFIRMADO** |
| Significado completo dos controles | **HIPÓTESE / não resolvido** |
| Tabela de ponteiros de script | **NÃO RESOLVIDA** |
| Rotina 68000 de texto | **NÃO RESOLVIDA** |
| Formato lógico das entradas | **NÃO RESOLVIDO** |
| Fonte/glifos | **PARCIALMENTE LOCALIZADOS; função ainda não resolvida** |
| Encoder | **NÃO IMPLEMENTADO** |
| Realocação | **NÃO IMPLEMENTADA** |
| Patch PT-BR | **NÃO IMPLEMENTADO** |

---

## 14. Próxima etapa técnica

A próxima etapa não deve ampliar indiscriminadamente os scanners heurísticos.

O foco deve ser a análise do código Motorola 68000:

```text
ROM
 │
 ├── código 68000
 │
 ├── referências à tabela 0x1A551A
 │
 ├── referências às regiões de script
 │
 └── JSR/JMP/LEA/MOVE relacionados
          │
          ▼
    rotina de processamento
          │
          ├── leitura de caractere
          ├── interpretação de controle
          ├── acesso à fonte
          └── avanço/posicionamento
                    │
                    ▼
             formato do script
                    │
                    ▼
              tabela de ponteiros
                    │
                    ▼
             extrator definitivo
```

A meta imediata é encontrar **uma única cadeia de evidência completa**, desde uma entrada de texto até a rotina que a imprime.

Depois disso será possível generalizar para o restante do jogo.

---

## 15. Critério de segurança para a tradução

Nenhum código de escrita deverá ser criado antes de confirmar:

1. charset;
2. terminador;
3. controles;
4. limite das entradas;
5. referências/ponteiros;
6. mecanismo de seleção dos scripts;
7. capacidade de armazenamento;
8. comportamento da rotina de impressão.

Somente então o projeto poderá evoluir para:

```text
dump
  ↓
tradução PT-BR
  ↓
encoder
  ↓
controle de tamanho
  ↓
realocação
  ↓
correção de ponteiros
  ↓
ROM traduzida
  ↓
validação automática
```

A prioridade é produzir uma ROM traduzida funcional, não apenas um dump textual que pareça correto.


---

## 16. Evidência prática do primeiro dump da abertura

A primeira execução real do decoder sobre:

```text
offset = 0x1626B
size   = 0x420
```

produziu uma narrativa japonesa coerente do início ao fim da região principal.

O dump contém, entre outros trechos, referências a:

- イセルハーサ;
- ファーレーン;
- アスエル王;
- 首都ルディア;
- セリオス王子;
- アクダム;
- サースアイ島;
- エルアスタ.

Isso constitui evidência prática de que o decoder está atravessando corretamente caracteres Shift-JIS de 1 e 2 bytes e preservando os controles sem deslocar o alinhamento do texto.

### Padrões observados

O comando `0x01` aparece repetidamente entre linhas:

```text
...ことかも知れない。 01 遠い未来...
...豊かな 01 自然に恵まれた...
...国だったが、 01 心優しき...
```

A repetição e o contexto narrativo permitem classificar `0x01` como:

**CONFIRMADO — separador/quebra de linha do texto da abertura.**

O padrão `06 FE 0E` aparece em transições narrativas, por exemplo após:

```text
...過ごしていた。
...混戦状態がつづいた。
...殺害されていたのである。
...政務を行うと言うのである。
```

Classificação atual:

**CONFIRMADO — comando de três bytes.**

**HIPÓTESE — comando associado à transição/estado de apresentação do texto.**

A função semântica não será nomeada até ser localizada no código 68000.

Também foi observado:

```text
06 00 FE
0E
01 01 01 01 01
```

em uma transição da abertura, além de:

```text
06 08 06
```

próximo ao encerramento da região.

Isso demonstra que `0x06` inicia comandos de comprimento superior a um byte e que `0x0E` também pode aparecer isoladamente. O decoder atual preserva esses bytes, mas ainda não representa uma gramática completa do protocolo.

### Final da região decodificada

O final produzido pelo comando contém:

```text
それから約１０年の歳月が流れた。<CTRL 06 08 06>/9<END><RAW FF><CTRL 01>z#
```

A presença de `FF` e de bytes posteriores ao `END` indica que os `0x420` bytes abrangem dados adjacentes à estrutura textual principal.

Portanto, o limite `0x1668B` usado no primeiro teste é um **limite de investigação**, não o tamanho confirmado da entrada de script.

---

## 17. Scanner de controles

Foi adicionado:

```
src/dragonslayer_ptbr/analysis/script_controls.py
```

O scanner:

- percorre uma região já selecionada;
- reconhece Shift-JIS sem quebrar o alinhamento;
- registra controles com seus offsets absolutos;
- preserva os bytes originais;
- gera relatório determinístico em Markdown;
- não atribui semântica aos comandos;
- não modifica a ROM.

Uso:

```powershell
python -m dragonslayer_ptbr scan-controls `
  --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" `
  --offset 0x1626B `
  --size 0x420 `
  --output reports/script-controls.md
```

Esse relatório será usado como evidência para a próxima etapa: localizar no código 68000 as rotinas que consomem os controles.

---

## 18. Nova hipótese de investigação

O objetivo imediato deixou de ser simplesmente localizar texto.

Agora a investigação deve responder:

1. qual rotina recebe o endereço da sequência textual;
2. como ela lê um caractere Shift-JIS;
3. onde testa `0x01`;
4. onde testa `0x06`;
5. como determina o comprimento dos comandos iniciados por `0x06`;
6. onde trata `0x0E`;
7. onde reconhece `0x00`;
8. como a rotina acessa a tabela de caracteres em `0x1A551A`;
9. como o código seleciona a próxima entrada de script.

A evidência do dump torna essas perguntas mais precisas e reduz a necessidade de heurística.

---

## 19. Próxima etapa: análise 68000

A próxima investigação deverá partir das referências ao código e aos dados, procurando uma cadeia de execução semelhante a:

```text
seleção da entrada
      ↓
endereço do script
      ↓
leitura de byte
      ↓
teste de controle
      ├── 0x00
      ├── 0x01
      ├── 0x06
      └── 0x0E
      ↓
rotina de renderização
      ↓
consulta à fonte/tabela de caracteres
```

Nenhuma rotina será marcada como "engine de texto" apenas por aparência. Será necessário obter uma cadeia de referências consistente.

---

## 20. Estado após o primeiro dump real

| Item | Estado |
|---|---|
| Texto japonês da abertura | **CONFIRMADO** |
| Shift-JIS | **CONFIRMADO** |
| Quebra/separador `0x01` | **CONFIRMADO** |
| Comando `06 xx yy` | **CONFIRMADO** |
| `06 FE 0E` recorrente | **CONFIRMADO como comando; função desconhecida** |
| `06 00 FE` | **CONFIRMADO como comando; função desconhecida** |
| `06 08 06` | **CONFIRMADO como comando; função desconhecida** |
| `0x0E` isolado | **CONFIRMADO como controle; função desconhecida** |
| `0x00` | **CONFIRMADO em estrutura observada** |
| Limite exato da abertura | **AINDA NÃO CONFIRMADO** |
| Rotina 68000 | **AINDA NÃO LOCALIZADA** |
| Ponteiros dos scripts | **AINDA NÃO LOCALIZADOS** |
| Encoder | **NÃO IMPLEMENTADO** |
| Inserção PT-BR | **NÃO INICIADA** |


---

## 21. Resultado do mapa de controles da abertura

O comando `scan-controls` foi executado sobre:

```
0x01626B – 0x01668A
```

e encontrou **42 ocorrências de controle**.

### Frequência

| Sequência | Ocorrências |
|---|---:|
| `01` | 33 |
| `06 FE 0E` | 5 |
| `00` | 1 |
| `06 00 FE` | 1 |
| `06 08 06` | 1 |
| `0E` | 1 |

### Offsets

Os cinco comandos `06 FE 0E` estão em:

```
0x0162F1
0x016399
0x016459
0x016515
0x0165F7
```

Os demais comandos especiais observados são:

```
0x016658 : 06 00 FE
0x01665B : 0E
0x016681 : 06 08 06
0x016686 : 00
0x016688 : 01
```

Os separadores `01` aparecem desde `0x01628B` até `0x016688`.

### Regularidade dos blocos

Entre ocorrências consecutivas de `01`, há vários intervalos de aproximadamente:

```
0x20 = 32 bytes
0x21 = 33 bytes
```

Também aparecem intervalos próximos, como 29, 31, 34 e 35 bytes, enquanto os intervalos de 1–3 bytes ficam concentrados na sequência especial próxima ao final:

```
0x016658  06 00 FE
0x01665B  0E
0x01665C  01
0x01665D  01
0x01665E  01
0x01665F  01
0x016660  01
```

Esse padrão é compatível com uma estrutura de **linhas/blocos de apresentação com largura limitada**, mas isso ainda é uma **HIPÓTESE**. Não deve ser interpretado como confirmação de que o jogo utiliza exatamente 32 ou 33 bytes por linha.

### Evidência particularmente forte

A sequência:

```
0x016658  06 00 FE
0x01665B  0E
0x01665C  01
0x01665D  01
0x01665E  01
0x01665F  01
0x016660  01
```

mostra que cinco `0x01` podem ocorrer consecutivamente depois de comandos especiais.

Isso indica que `0x01` deve ser interpretado como **controle de apresentação**, e não simplesmente como parte de uma codificação Shift-JIS.

### Interpretação atual

A classificação dos controles passa a ser:

| Sequência | Classificação | Função |
|---|---|---|
| `01` | **CONFIRMADO — controle** | contexto indica quebra/separação de linha |
| `06 FE 0E` | **CONFIRMADO — comando 3 bytes** | função ainda desconhecida |
| `06 00 FE` | **CONFIRMADO — comando 3 bytes** | função ainda desconhecida |
| `06 08 06` | **CONFIRMADO — comando 3 bytes** | função ainda desconhecida |
| `0E` | **CONFIRMADO — controle** | função ainda desconhecida |
| `00` | **CONFIRMADO — terminador observado** | encerramento da estrutura observada |

Não foi atribuído significado semântico aos comandos `0x06` ou `0x0E`.

---

## 22. Consequência para a engenharia reversa

O mapa de controles permite uma estratégia mais precisa para a análise 68000.

Em vez de procurar genericamente por "texto", devemos procurar uma rotina que:

1. recebe ou calcula o endereço de uma sequência em torno de `0x01626B`;
2. lê bytes sequencialmente;
3. diferencia caracteres Shift-JIS de bytes de controle;
4. trata especificamente `0x01`;
5. reconhece `0x06` e consome os dois bytes seguintes;
6. trata `0x0E`;
7. encerra a estrutura ao encontrar `0x00`;
8. eventualmente consulta a tabela de caracteres em `0x1A551A`.

A ocorrência repetida de `06 FE 0E` é particularmente útil como assinatura de dados para confirmar se uma rotina encontrada realmente processa esse protocolo.

---

## 23. Próxima investigação: limites reais das entradas

Ainda não devemos considerar toda a faixa `0x01626B–0x01668A` uma única entrada.

A próxima tarefa é separar:

```
entrada / bloco
    ├── linhas
    ├── comandos
    └── terminador
```

e determinar se os cinco `06 FE 0E` representam:

- páginas de texto;
- mudança de janela;
- espera/avanço;
- troca de estado;
- chamada de evento;
- ou outra função.

Essa distinção será feita somente através do código 68000.

---

## 24. Regra para o encoder

A regularidade de aproximadamente 32–33 bytes por linha **não deve ser usada ainda como limite rígido para o texto PT-BR**.

O encoder futuro precisa reproduzir a lógica real do jogo:

- se `0x01` for quebra automática, calcular a quebra;
- se houver largura fixa de janela, respeitar a largura;
- se `06 FE 0E` alterar o estado de apresentação, preservá-lo;
- se existirem limites de página, preservar a estrutura;
- manter os comandos não textuais intactos.

Somente depois dessa confirmação será possível saber se uma tradução PT-BR pode simplesmente substituir as strings ou se precisará de reflow/reempacotamento.

---

## 25. Novo estado da investigação

A abertura agora fornece uma assinatura suficientemente rica para procurar o engine:

```
Shift-JIS
  +
01
  +
06 FE 0E
  +
06 00 FE
  +
0E
  +
00
```

Isso é muito mais útil para a análise estática do que procurar somente sequências de caracteres japoneses.

O próximo alvo técnico passa a ser a **rotina 68000 que interpreta essa assinatura**.


---

## 26. Início da análise estática 68000

A investigação passou a uma etapa dedicada a referências do código Motorola 68000.

Foi criada:

    src/dragonslayer_ptbr/analysis/m68k_references.py

A ferramenta procura representações big-endian dos dois alvos confirmados mais importantes:

    0x01626B  região da abertura/script investigada
    0x1A551A  tabela de caracteres Shift-JIS

São examinadas representações de 24 e 32 bits. Quando os dois bytes imediatamente anteriores aos quatro bytes do alvo correspondem a um opcode absoluto conhecido, a ocorrência recebe uma classificação instrucional.

Formatos atualmente reconhecidos:

    LEA abs.l
    PEA abs.l
    JSR abs.l
    JMP abs.l
    MOVEA.L #imm,An

### Estado

**CONFIRMADO:** a ferramenta de busca está implementada no projeto.

**AINDA NÃO CONFIRMADO:** quais ocorrências encontradas na ROM pertencem efetivamente ao engine de texto.

A ROM original não está armazenada no GitHub e permanece local. Portanto, a execução da nova análise deve ser feita sobre o mesmo dump local já validado anteriormente.

### Comando

    python -m dragonslayer_ptbr scan-refs --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --output reports/m68k-references.md

O relatório produzido deverá ser analisado procurando principalmente:

- referências instrucionais à abertura;
- referências instrucionais à tabela 0x1A551A;
- proximidade entre referências;
- possíveis blocos de código compartilhando essas referências.

A ferramenta é deliberadamente conservadora: uma referência literal não é considerada automaticamente ponteiro de script, e o scanner não substitui um desassembler.


---

## 27. Mapa consolidado das regiões de texto japonês

A nova varredura dedicada a Shift-JIS foi adicionada em:

```
src/dragonslayer_ptbr/analysis/japanese_text.py
```

Ela não procura ASCII de forma isolada. O algoritmo:

1. valida sequências de caracteres Shift-JIS de 1 e 2 bytes;
2. aceita `0x01` como controle de um byte;
3. aceita `0x06 xx yy` como controle de três bytes;
4. interrompe a região diante de bytes que não pertencem à gramática conhecida;
5. calcula a proporção de caracteres hiragana/katakana/kanji;
6. ignora a região conhecida da tabela de caracteres em `0x1A551A`;
7. agrupa regiões contíguas;
8. produz offsets, tamanho, quantidade de caracteres e controles.

O resultado atual é de **47 regiões candidatas fortemente sustentadas por texto japonês legível**.

### 27.1 Regiões identificadas

| Offset | Fim | Caracteres | Controles | Classificação investigativa |
|---:|---:|---:|---:|---|
| `0x003657` | `0x003687` | 24 | 1 | interface/mensagem |
| `0x0041C3` | `0x0041F2` | 24 | 2 | interface/mensagem |
| `0x01626A` | `0x01665B` | 518 | 34 | abertura |
| `0x01F6EA` | `0x01F74A` | 49 | 2 | diálogo |
| `0x026230` | `0x026294` | 45 | 7 | sistema/salvamento |
| `0x02DF10` | `0x02DF51` | 31 | 1 | diálogo/final |
| `0x02DF52` | `0x02DFDD` | 67 | 5 | diálogo/final |
| `0x02DFDE` | `0x02E05D` | 62 | 4 | diálogo/final |
| `0x02E05E` | `0x02E0EB` | 73 | 5 | diálogo/final |
| `0x02E0EC` | `0x02F151` | vários | vários | bloco de final |
| `0x030349` | `0x030383` | 31 | 1 | minijogo |
| `0x030384` | `0x0303B7` | 25 | 1 | minijogo |
| `0x03045A` | `0x0304A1` | 37 | 2 | minijogo |
| `0x0304FC` | `0x030545` | 37 | 2 | minijogo |
| `0x030616` | `0x03064B` | 28 | 1 | minijogo |
| `0x0306D4` | `0x03071D` | 37 | 2 | minijogo |
| `0x03072D` | `0x030756` | 22 | 1 | minijogo |
| `0x030780` | `0x0307B2` | 26 | 1 | minijogo |
| `0x03105E` | `0x03108A` | 23 | 2 | minijogo |
| `0x0310A1` | `0x0310D2` | 25 | 1 | minijogo |
| `0x0310D3` | `0x0310FE` | 21 | 2 | minijogo |
| `0x031100` | `0x031154` | 43 | 2 | minijogo |
| `0x031155` | `0x03117E` | 21 | 1 | minijogo |
| `0x031220` | `0x031248` | 20 | 1 | minijogo |
| `0x031249` | `0x031282` | 31 | 1 | minijogo |
| `0x031283` | `0x0312B7` | 26 | 1 | minijogo |
| `0x0312B8` | `0x0312EA` | 26 | 1 | minijogo |
| `0x0312EB` | `0x03131B` | 22 | 2 | minijogo |
| `0x032325` | `0x032390` | 52 | 3 | minijogo/regras |
| `0x032391` | `0x0323D2` | 33 | 1 | minijogo/regras |
| `0x0323D3` | `0x03242F` | 47 | 2 | minijogo/regras |
| `0x032447` | `0x03249C` | 42 | 2 | minijogo/regras |
| `0x032529` | `0x032563` | 28 | 2 | minijogo/regras |
| `0x032565` | `0x0325A5` | 32 | 2 | minijogo/regras |
| `0x0325E8` | `0x032620` | 29 | 1 | minijogo/regras |
| `0x032648` | `0x03267D` | 26 | 2 | minijogo/regras |
| `0x0338B2` | `0x033FB9` | 833 | 122 | itens/magias |
| `0x033FF8` | `0x034113` | 105 | 32 | itens/magias |
| `0x02F05C` | `0x02F0B7` | 45 | 3 | diálogo/final |
| `0x02F0FB` | `0x02F185` | 67 | 5 | diálogo/final |
| `0x02F191` | `0x02F1DD` | 36 | 4 | diálogo/final |

> Nota: a classificação acima é investigativa. Ela descreve o conteúdo observado, não afirma como o engine categoriza os dados internamente.

### 27.2 Exemplos de conteúdo

A região de abertura contém:

```
はるかなる昔、いや、もしかしたら
遠い未来のことかも知れない。

「イセルハーサ」と呼ばれる豊かな
自然に恵まれた世界があった。

イセルハーサのほぼ中央に位置する
ファーレーン王国は、国土が狭いこ
ともあって、まずしい国だったが、
心優しきアスエル王の統治のもと、
人々は平和な日々を過ごしていた。
```

O bloco de itens/magias contém sequências reconhecíveis como:

```
何もない
ナイフ
幅広のつるぎ
小型のつるぎ
青銅のつるぎ
鉄のやり
```

Isso demonstra que a extração já alcança dados de gameplay e não somente a introdução.

---

## 28. Evidência detalhada da abertura

A região investigada começa em aproximadamente:

```
0x01626B
```

O decoder produz texto japonês coerente, intercalado com controles.

### 28.1 Estrutura observada

A assinatura mais forte atualmente é:

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

Essa assinatura ocorre dentro de texto narrativo real.

### 28.2 Controles mapeados

Na região investigada foram encontradas **42 ocorrências**:

| Sequência | Quantidade |
|---|---:|
| `01` | 33 |
| `06 FE 0E` | 5 |
| `06 00 FE` | 1 |
| `06 08 06` | 1 |
| `0E` | 1 |
| `00` | 1 |

Offsets importantes:

```
0x0162F1  06 FE 0E
0x016399  06 FE 0E
0x016459  06 FE 0E
0x016515  06 FE 0E
0x0165F7  06 FE 0E

0x016658  06 00 FE
0x01665B  0E
0x016681  06 08 06
0x016686  00
```

Os `0x01` aparecem repetidamente entre linhas da narrativa.

### 28.3 O que pode e não pode ser concluído

Podemos afirmar:

- `0x01` é usado como controle no texto;
- `0x06 xx yy` forma uma unidade de três bytes;
- `0x06 FE 0E` é recorrente em transições narrativas;
- `0x00` aparece como terminador da estrutura observada;
- `0x0E` também pode ocorrer isoladamente.

Não podemos afirmar ainda:

- que `06 FE 0E` significa espera;
- que `06 FE 0E` significa troca de página;
- que `06 00 FE` significa encerramento;
- que `0x0E` seja mudança de janela;
- que `0x01` seja necessariamente uma quebra de linha lógica em todas as regiões.

Essas semânticas exigem rastreamento do código 68000.

---

## 29. Análise 68000 — resultados e correções metodológicas

A análise estática inicialmente procurou referências literais aos offsets de texto e da tabela de caracteres. O resultado foi:

```
opening_script:
0 referências diretas confirmadas

character_table:
0 referências diretas confirmadas
```

Isso não invalida os dados; indica que o engine provavelmente não utiliza esses endereços como constantes literais nas formas procuradas.

### 29.1 Candidatos de parser

Foi criado:

```
analysis/m68k_text_parser_candidates.py
```

O scanner procura:

```
MOVE.B (An)+,Dn
        ↓
CMPI.B #controle,Dn
```

Os candidatos encontrados foram:

| Leitura | Teste | Registrador | Controle |
|---:|---:|---:|---:|
| `0x026AE0` | `0x026AEA` | D0 | `0x01` |
| `0x0308C0` | `0x0308C2` | D0 | `0x0E` |
| `0x030AA4` | `0x030AAA` | D0 | `0x0D` |
| `0x030B46` | `0x030B4C` | D0 | `0x0E` |
| `0x030B6A` | `0x030B70` | D0 | `0x0E` |
| `0x030CBE` | `0x030CC4` | D0 | `0x0D` |

Esses seis candidatos foram investigados manualmente.

### 29.2 Família 0x0308xx–0x030cxx

A investigação mostrou que várias dessas rotinas chamam:

```
0x0309EA
```

A rotina em `0x0309EA` contém:

```
LEA $00FF20AE,A3
```

Ou seja, A3 recebe um endereço de **RAM**, não uma região de script da ROM.

Consequentemente, os candidatos:

```
0x0308C0
0x030AA4
0x030B46
0x030B6A
0x030CBE
```

não devem ser classificados como parser de texto.

Esse é um resultado negativo importante: **aparência de parser não basta**.

### 29.3 Cadeia 0x026ADA

Foi encontrada:

```
0x026ADA: MOVEA.L $0012(A1),A3
0x026AE0: MOVE.B (A3)+,D0
```

seguida de comparações com valores `00..05`.

A cadeia é:

```
estrutura apontada por A1
        ↓
A3 = *(A1 + $12)
        ↓
MOVE.B (A3)+,D0
        ↓
dispatcher 00..05
```

Isso é uma cadeia legítima de acesso indireto, mas o contexto ainda aponta mais para **estado/dispatcher** do que para protocolo textual.

### 29.4 Acesso 0x02B344

Também foi observado:

```
LEA $0001(A3),A3
MOVE.B (A3)+,D0
```

Isso demonstra que existem rotinas que avançam explicitamente um ponteiro antes de consumir bytes.

Continua sendo candidato para investigação, mas ainda não há ligação comprovada com o script.

---

## 30. Fluxo A3

Foi criado:

```
analysis/m68k_a3_flow.py
```

Objetivo:

- localizar `LEA ...,A3`;
- localizar `MOVEA.L ...,A3`;
- localizar `MOVEA.W ...,A3`;
- localizar `MOVE.B (A3)+,Dn`;
- relacionar usos à definição anterior mais próxima.

A análise demonstrou que simplesmente procurar o uso mais próximo não é suficiente para provar fluxo de execução.

O caso mais importante até agora é:

```
0x0309EA
    ↓
LEA $00FF20AE,A3
    ↓
rotinas 0x0308xx–0x030cxx
    ↓
MOVE.B (A3)+,D0
```

Como `0x00FF20AE` está na RAM, essa família foi rebaixada como candidata ao parser de texto.

### Conclusão

O rastreamento A3 precisa evoluir de proximidade estática para:

- blocos básicos;
- fluxo de controle;
- chamadas/retornos;
- definições dominantes;
- propagação de registradores.

---

## 31. Acessos indexados

Foi criado:

```
analysis/m68k_indexed_reads.py
```

para localizar:

```
MOVE.B (An,Dn.W),Dm
MOVE.B (An,Dn.L),Dm
```

Uma correção importante foi feita durante a implementação: no 68000, a seleção do registrador de índice e o bit W/L pertencem à **palavra de extensão**, e não ao opcode principal.

Depois da correção, a busca bruta encontrou aproximadamente:

```
7.038 ocorrências
```

### Interpretação

Esse número é alto demais para ser interpretado diretamente.

Foram encontradas ocorrências em regiões de dados, inclusive próximas da tabela de fonte em `0x1A551A`.

Isso prova que uma busca binária pela codificação da instrução produz muitos falsos positivos quando não existe um desassembler/controle de fluxo.

### Consequência

O scanner indexado é uma ferramenta de coleta, não uma prova de execução.

O próximo filtro deve reconhecer regiões de código por:

- `BSR`;
- `JSR`;
- `JMP`;
- `RTS`;
- fluxo de branches;
- prólogos/epílogos;
- consistência das instruções.

Somente depois deve-se analisar os acessos indexados dentro desses blocos.

---

## 32. Tabela de caracteres — estado atual

A região:

```
0x1A551A
```

permanece uma das pistas centrais.

Ela contém:

- `0x8140`;
- pontuação;
- hiragana;
- katakana;
- grande sequência de kanji.

O fato de não existir referência literal direta ao endereço não elimina seu papel.

As hipóteses principais agora são:

1. endereço base obtido de uma tabela intermediária;
2. endereço calculado por registrador;
3. endereço relativo a PC;
4. ponteiro armazenado em estrutura;
5. índice transformado antes do acesso;
6. tabela acessada por cópia/mapeamento de dados.

Nenhuma dessas hipóteses deve ser promovida a fato até que o código seja localizado.

---

## 33. Relação entre texto e fonte

O estado atual permite estabelecer a seguinte relação conceitual:

```
dados textuais Shift-JIS
        │
        ▼
código de interpretação
        │
        ├── caracteres de 1 byte
        ├── caracteres de 2 bytes
        └── controles
                │
                ▼
        conversão para índice/glifo
                │
                ▼
        tabela/fonte em 0x1A551A
```

Essa arquitetura é uma **hipótese de trabalho**, não uma descrição confirmada do engine.

O objetivo da próxima etapa é localizar a instrução que fecha essa cadeia.

---

## 34. O que já pode ser utilizado na tradução

Neste momento já é possível preparar material de tradução sem modificar a ROM:

### Seguro

- dump UTF-8 das regiões confirmadas;
- preservação de controles;
- catálogo de strings;
- identificação de nomes próprios;
- separação de itens, magias, diálogos e mensagens;
- criação de arquivos de tradução paralelos;
- preparação de testes de round-trip do codec.

### Ainda não seguro

- substituir bytes diretamente;
- alterar tamanho das strings;
- realocar scripts;
- modificar ponteiros;
- definir tamanho máximo de uma linha;
- remover controles;
- traduzir `0x06 xx yy` para outra sequência.

---

## 35. Risco principal atual

O maior risco não é mais o charset.

O Shift-JIS está suficientemente confirmado.

O maior risco agora é **estrutura de armazenamento e execução**:

```
qual entrada aponta para qual texto?
qual rotina lê a entrada?
qual é o terminador real?
quais controles existem?
como o texto é convertido para glifo?
há tabelas intermediárias?
há compressão?
há fragmentação?
```

A resposta a essas perguntas determinará se o projeto terá um patch simples ou um sistema de realocação/reconstrução.

---

## 36. Critério de promoção de evidência

A partir desta etapa, cada descoberta deve receber uma das classificações:

### CONFIRMADO

Há evidência direta e reproduzível na ROM/código.

Exemplos:

- Shift-JIS;
- regiões textuais;
- `0x01` como controle observado;
- `06 xx yy` como sequência de três bytes;
- tabela em `0x1A551A`.

### FORTE EVIDÊNCIA

Há múltiplas ocorrências consistentes, mas ainda falta rastreamento de execução.

Exemplos:

- relação entre controles e apresentação;
- possível utilização da tabela Shift-JIS para fonte;
- possíveis estruturas de entradas.

### HIPÓTESE

Explicação plausível ainda não comprovada.

Exemplos:

- `06 FE 0E` como troca de página;
- largura lógica de aproximadamente 32 bytes;
- tabela de ponteiros 16-bit;
- engine compartilhado com outro jogo.

### DESCARTADO/REBAIXADO

Uma hipótese foi testada e perdeu sustentação.

Exemplos:

- candidatos `0x0308xx–0x030cxx` como parser de texto;
- scanner indexado bruto como prova de código;
- referências literais diretas à tabela como único mecanismo de acesso.

---

## 37. Estado geral após a documentação

```
[CONFIRMADO]
ROM japonesa
    ↓
Shift-JIS
    ↓
47 regiões de texto
    ↓
controles binários
    ↓
tabela Shift-JIS em 0x1A551A

[EM INVESTIGAÇÃO]
    ↓
rotina 68000 de interpretação
    ↓
estrutura de entradas
    ↓
ponteiros
    ↓
conversão para glifo

[A FAZER]
    ↓
extrator completo
    ↓
encoder
    ↓
tradução PT-BR
    ↓
realocação
    ↓
patch
    ↓
validação em emulador/hardware
```

O projeto não deve avançar para escrita da ROM antes de fechar pelo menos a primeira cadeia completa:

```
entrada de script
→ rotina 68000
→ interpretação do caractere/controle
→ acesso à fonte
→ encerramento da entrada
```

Essa cadeia será a referência para generalizar o extrator para as demais regiões.


---

## 17. Análise dos caracteres latinos e acentuação PT-BR

A investigação da tabela localizada em `0x1A551A` produziu uma descoberta relevante.

O intervalo observado até `0x1A62D2` contém **1756 entradas de 16 bits** e não é composto somente por códigos Shift-JIS japoneses. Há também códigos latinos de um byte.

A tabela contém, entre outros, os códigos:

```text
00C0 À
00C1 Á
00C2 Â
00C3 Ã
00C7 Ç
00C9 É
00CA Ê
00CD Í
00D3 Ó
00D4 Ô
00D5 Õ
00DA Ú
```

Por outro lado, os códigos necessários para os minúsculos acentuados portugueses não aparecem:

```text
00E0 à
00E1 á
00E2 â
00E3 ã
00E7 ç
00E9 é
00EA ê
00ED í
00F3 ó
00F4 ô
00F5 õ
00FA ú
```

### Consequência

A hipótese anterior de que seria necessário criar toda a acentuação a partir de uma tabela Shift-JIS nova foi refinada.

O jogo possui uma tabela de caracteres **híbrida/proprietária**, com códigos japoneses de dois bytes e códigos latinos de um byte.

Isso abre uma possibilidade particularmente interessante para a tradução PT-BR: os minúsculos acentuados podem potencialmente receber códigos de um byte já aceitos pela rotina, desde que consigamos identificar entradas substituíveis ou estender a tabela sem quebrar o mecanismo de lookup.

Ainda não é seguro escolher quais caracteres japoneses podem ser substituídos. A ausência de um código nas 47 regiões textuais detectadas não prova que ele nunca seja usado pelo jogo.

### Próxima cadeia de evidência

A investigação agora deve localizar:

```
código do script
    ↓
rotina de leitura/conversão
    ↓
consulta à tabela 0x1A551A
    ↓
índice do glifo
    ↓
endereço/formato da fonte
    ↓
renderização
```

Somente depois dessa confirmação será criado o patch de fonte PT-BR.

O catálogo programático foi adicionado em:

```
src/dragonslayer_ptbr/analysis/character_table.py
```

com testes em:

```
tests/test_character_table.py
```

e relatório dedicado em:

```
reports/latin-character-analysis.md
```

Nenhuma dessas alterações modifica a ROM original.


---

## 38. Roadmap operacional até o primeiro teste PT-BR

O projeto agora possui um roadmap formal em:

`docs/project-roadmap.md`

A sequência obrigatória é:

1. **Integridade/baseline** — hashes, testes e proteção da ROM original.
2. **Inventário completo de texto** — transformar as regiões encontradas em entradas lógicas.
3. **Protocolo de script** — determinar a gramática real de caracteres, controles e terminadores.
4. **Engine 68000** — localizar a cadeia de execução que lê o script e acessa a fonte.
5. **Fonte + encoder** — fechar o mapeamento código → glifo e implementar round-trip sem perda.
6. **Ponteiros/seleção** — comprovar como cada script é localizado.
7. **Realocação** — somente após provar escrita segura; primeiro testar realocação de texto japonês.
8. **Vertical slice PT-BR** — alterar uma única entrada pequena e totalmente compreendida.
9. **Validação no emulador** — verificar inicialização, mensagem traduzida, controles, texto seguinte e continuidade do jogo.
10. **Expansão gradual** — somente depois do primeiro teste executável.

### Gate para iniciar a tradução de fato

A tradução PT-BR só começa quando houver, para pelo menos uma entrada:

`extração → decode → tradução → encode → referência/realocação → patch → validação → execução`.

O primeiro teste será chamado **M1 — Primeiro Texto PT-BR Executável**.

Até esse marco, o código de escrita deve permanecer separado das ferramentas de análise e nenhuma alteração deve ser aplicada à ROM original.


---

## 39. Início da análise de fluxo 68000

A investigação passou a utilizar o vetor de reset real da ROM como ponto de entrada.

O vetor encontrado no cabeçalho Mega Drive contém:

```
PC inicial = 0x010620
```

Os primeiros bytes executáveis nessa posição são:

```
0x010620  4A B9 00 A1 00 08
0x010626  66 06
0x010628  4A 79 00 A1 00 0C
0x01062E  66 7C
0x010630  4B FA 00 7C
0x010634  4C 9D 00 E0
...
```

Isso é uma evidência importante porque permite deixar de tratar a ROM inteira como um conjunto indiferenciado de bytes e começar o rastreamento por um ponto de execução real.

### Analisador criado

Foi adicionado:

```
src/dragonslayer_ptbr/analysis/m68k_code.py
```

com testes em:

```
tests/test_m68k_code.py
```

e comando:

```powershell
python -m dragonslayer_ptbr scan-m68k-code `
  --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" `
  --output reports/m68k-code-flow.md
```

O analisador atualmente reconhece um subconjunto conservador de instruções 68000, incluindo:

- `RTS`, `RTE`, `RTR`;
- `BRA`, `BSR` e condicionais;
- `JSR abs.l` e `JMP abs.l`;
- `LEA`;
- `TAS`;
- `MOVEQ`;
- leituras `MOVE.B`;
- `MOVEA`;
- `CMPI`;
- `MOVEM`;
- `DBcc`;
- operações imediatas e shifts em formas reconhecidas.

O objetivo não é substituir um desassembler completo. Quando o opcode não é reconhecido, o bloco é encerrado em vez de adivinhar seu tamanho.

### Critério de interpretação

Os blocos produzidos pelo analisador são classificados como **evidência de fluxo candidato**, não como prova absoluta de código.

A próxima etapa será usar esses blocos para filtrar:

- `MOVE.B (An)+,Dn`;
- `MOVE.B (An,Dn.W/L),Dm`;
- comparações com `0x01`;
- comparações com `0x06`;
- comparações com `0x0E`;
- tratamento de `0x00`;
- chamadas `JSR/BSR`.

O objetivo é encontrar uma cadeia de execução que tenha relação comprovada com as regiões textuais já identificadas.

### Observação importante

A análise inicial mostrou que o ponto de entrada começa com instruções que não estavam cobertas pelo scanner anterior, como `TAS abs.l`. Por isso, o novo decodificador está sendo ampliado incrementalmente.

Isso é intencional: é preferível ampliar a cobertura de instruções conforme surgem evidências reais na ROM do que implementar um desassembler especulativo e produzir um CFG aparentemente completo, porém incorreto.

---

## 40. Próximo cruzamento de evidências

Com o fluxo 68000 inicial disponível, a próxima investigação será:

```
blocos de código alcançáveis
        ↓
leituras MOVE.B
        ↓
CMPI #controle
        ↓
branches/JSR/BSR
        ↓
origem dos registradores A0–A3
        ↓
dados apontados
        ↓
regiões de texto
```

Em paralelo, será feita a correlação com a tabela `0x1A551A`.

O objetivo não é encontrar simplesmente uma instrução que "pareça" ser parser, mas obter uma cadeia reproduzível desde a leitura de dados até o processamento do texto.

## 41. Atualização final da análise M68K — CFG e rotinas alcançáveis

A análise de fluxo 68000 foi ampliada a partir do vetor de reset real (0x010620) e alcançou um conjunto maior de rotinas.

- 43 blocos básicos;
- 155 instruções reconhecidas;
- blocos não sobrepostos;
- chamadas absolutas identificadas;
- destinos de JSR incorporados ao CFG;
- retornos RTS identificados.

### Cadeias de código observadas

Chamadas confirmadas pelo CFG atual:

0x01077A → JSR 0x00CADA
0x01078A → JSR 0x009408
0x0109AA → JSR 0x010AF2
0x0109B6 → JSR 0x00B53E
0x0109C2 → JSR 0x00B53E
0x0109CE → JSR 0x00B53E
0x0109DA → JSR 0x00B536
0x010B16 → JSR 0x010B28

As rotinas 0x009408 e 0x00B53E terminam em RTS no CFG atual. Isso é evidência de fluxo de execução real, mas ainda não prova relação com o engine de texto.

### Ampliação incremental do decoder

Durante o avanço do CFG foram encontrados opcodes reais que interrompiam blocos. O decoder agora possui suporte e testes para:

- BTST #imm,<EA>;
- LEA abs.l,A0–A7;
- MOVE.W SR,<EA>;
- NEGX.B/W/L <EA>.

O último caso surgiu em 0x010B3A, onde 0x4000 interrompia a função iniciada em 0x010B28. A implementação de NEGX permanece conservadora e só aceita extensões de effective address já suportadas pelo decoder.

### Rotina 0x0109A2

O CFG mostra uma rotina com múltiplas chamadas: 0x0109AA → 0x010AF2, três chamadas para 0x00B53E e uma chamada para 0x00B536. A rotina merece investigação futura, mas não foi classificada como rotina de texto.

### Classificação

- CONFIRMADO: vetor de reset em 0x010620.
- CONFIRMADO: CFG alcança múltiplas subrotinas por JSR absoluto.
- CONFIRMADO: novas formas 68000 foram validadas diretamente pelos bytes da ROM.
- FORTE EVIDÊNCIA: algumas famílias de rotinas formam cadeias de chamada reais.
- HIPÓTESE: qualquer uma dessas cadeias ser o parser/renderizador de texto.
- REBAIXADO: tratar MOVE.B + CMPI.B isoladamente como parser.

### Ponto de retomada

A próxima investigação deve rastrear origem dos registradores A0–A3, leituras MOVE.B, comparações com 0x01/0x06/0x0E/0x00 e chamadas que manipulam ponteiros, cruzando esses dados com as regiões textuais e com a tabela 0x1A551A.

Nenhuma alteração da ROM original foi realizada.
