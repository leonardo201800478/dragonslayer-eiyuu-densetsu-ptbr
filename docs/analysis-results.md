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
