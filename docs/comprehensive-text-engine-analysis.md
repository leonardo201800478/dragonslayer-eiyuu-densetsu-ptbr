# Plano de análise abrangente para localizar o engine de texto

## Objetivo

Encontrar evidência técnica nova e relevante para ligar os textos japoneses já identificados ao código 68000 que os consome. Esta análise deve produzir candidatos verificáveis, não apenas grandes listas de coincidências.

A ROM original deve permanecer somente leitura. Nenhuma rotina, controle, ponteiro ou formato será marcado como confirmado apenas por proximidade estatística.

## Estado inicial conhecido

A investigação registrada no projeto já sustenta:

- ROM japonesa Mega Drive de 2 MiB; CRC32 `01BC1604`, SHA-1 `F67C9139BBC93F171E274A5CD3FBA66480CD8244`.
- Texto Shift-JIS em várias regiões, incluindo a abertura aproximada `0x01626B–0x01668A`.
- `0x01` atua como separador/quebra na abertura.
- `0x06 xx yy` é um comando de três bytes, mas a semântica permanece desconhecida.
- `0x0E` aparece como controle e `0x00` como terminador observado.
- Uma tabela explícita de códigos Shift-JIS começa em `0x1A551A`; seu papel no acesso à fonte ainda não foi provado.
- A travessia conservadora mais recente do CFG, relatada no histórico do projeto, alcançou apenas 39 blocos. Alvos forçados podem começar dentro de dados ou no meio de instruções.
- Os candidatos `0x01E9C0`, `0x01E9E4`, `0x01EA5E` e `0x02930A` continuam exploratórios. A ausência de chamadas diretas reconhecidas não prova que sejam inacessíveis.

## Pergunta central

Precisamos provar a cadeia:

`seleção de script → endereço-base → leitura de byte → classificação do controle → rotina de caracteres/controles → consulta da fonte ou desenho`

Uma rotina só deve ser promovida a **candidata forte** quando houver mais de uma linha independente de evidência. A confirmação exige fluxo de execução plausível e uma relação demonstrável com dados conhecidos.

## Estratégia de pesquisa por camadas

### Camada A — Garantir que os resultados sejam comparáveis

Antes de comparar relatórios:

1. confirmar que o arquivo da ROM tem o tamanho esperado;
2. confirmar CRC32 e SHA-1;
3. registrar o commit atual do código;
4. executar os testes do decoder;
5. guardar a saída completa dos comandos, incluindo erros e contagens.

Não comparar contagens de CFG de commits diferentes como se fossem um experimento controlado. Se uma contagem mudar, repetir os dois comandos no mesmo arquivo de ROM e registrar o commit, o primeiro opcode que interrompe o fluxo e o motivo da parada.

### Camada B — Construir um inventário de dados textuais

Executar o scanner japonês e gerar um inventário de regiões. Depois comparar as regiões com as ocorrências dos controles, registrando para cada trecho:

- início e fim observados;
- tamanho em bytes;
- proporção de caracteres Shift-JIS válidos;
- frequências e offsets de `0x01`, `0x06`, `0x0E`, `0x00` e outros bytes de controle;
- sequências repetidas de controle;
- possíveis limites, sem presumir que toda região seja uma entrada única.

A abertura é o caso de referência porque contém texto legível e ocorrências repetidas de `06 FE 0E`. Use também outras regiões japonesas para verificar se os padrões se repetem fora da abertura.

### Camada C — Procurar padrões de código que combinem leitura e controle

Os padrões de maior valor são:

1. leitura sequencial de byte, por exemplo `MOVE.B (An)+,Dn`;
2. comparação do mesmo registrador com `0x01`, `0x06`, `0x0E` ou `0x00`;
3. ramificações condicionais logo após a comparação;
4. incremento/ajuste do ponteiro de leitura;
5. caminho especial para `0x06` que consuma mais dois bytes;
6. retorno ao laço de leitura;
7. chamadas a outras rotinas depois de reconhecer caracteres ou controles.

Um único `CMPI.B` não é suficiente: esses valores são comuns em código e dados. Dar prioridade a blocos que mostrem uma sequência coerente de leitura, teste, ramificação e continuação.

### Camada D — Separar código provável de dados e entradas artificiais

Usar o CFG do vetor de reset como uma fonte de evidência, mas não como verdade completa, pois o decoder é parcial. Para cada candidato:

- inspecionar bytes brutos e instruções decodificadas;
- registrar a primeira instrução não reconhecida e seu opcode;
- verificar se os destinos de branch caem em limites plausíveis;
- auditar sobreposição de entradas;
- distinguir chamadas diretas de chamadas indiretas;
- nunca interpretar um fluxo iniciado artificialmente como prova de que o jogo o executa.

Quando possível, comparar o trecho com um segundo disassembler 68000. Divergência de comprimento de instrução ou alvo de branch deve bloquear a classificação até ser resolvida.

### Camada E — Rastrear registradores como ponteiros

Para candidatos de leitura sequencial, reconstruir localmente como os registradores de endereço são definidos e usados. Procurar:

- `LEA`, `MOVEA` e carregamentos de imediato;
- `MOVE.B (An)+,Dn` e leituras indexadas;
- somas/subtrações de offsets;
- chamadas `JSR`/`BSR` e retornos;
- uso de `A0–A3` dentro de um mesmo bloco e nos chamadores conhecidos.

A definição estática mais próxima de um registrador não prova fluxo de dados. Uma relação ganha força quando a definição chega a uma leitura dentro de um bloco coerente, sem uma redefinição intermediária.

### Camada F — Investigar a tabela de caracteres

A tabela em `0x1A551A` é um alvo importante, mas a ausência de referências literais diretas não elimina seu uso. Procurar evidência de acesso indireto:

- base de endereço calculada;
- índice de caractere derivado dos bytes lidos;
- operações de escala, como deslocamentos ou multiplicações;
- leitura de palavra na tabela;
- segundo acesso a dados de glifo/fonte usando o valor obtido.

A prova ideal não é somente uma instrução que aponte para a tabela: é uma cadeia que parta de um byte do texto, gere um índice, consulte a tabela e alcance dados de glifo ou uma rotina de desenho.

### Camada G — Classificar os achados

Cada achado deve receber uma classificação explícita:

- **CONFIRMADO**: bytes/instruções e fluxo suficientes demonstram a função.
- **CANDIDATO FORTE**: duas ou mais evidências independentes convergem, mas falta confirmar execução ou destino final.
- **HIPÓTESE**: padrão compatível, ainda com explicações alternativas.
- **DESCARTADO**: teste reproduzível demonstrou incompatibilidade.
- **INCONCLUSIVO**: decoder, fluxo ou dados insuficientes para decidir.

Para cada candidato, salvar offset, bytes brutos, decodificação, motivo da classificação, evidências contrárias e próximo teste capaz de falsificá-lo.

## Execução reproduzível no Windows / VS Code

Execute no diretório do projeto, com a ROM original no caminho local indicado. Os comandos abaixo usam subcomandos já presentes na CLI atual.

```powershell
python -m pytest tests/test_m68k_code.py -q

python -m dragonslayer_ptbr scan-japanese-text `
  --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" `
  --output reports/japanese-text-regions.md

python -m dragonslayer_ptbr scan-controls `
  --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" `
  --offset 0x1626B --size 0x420 `
  --output reports/opening-controls.md

python -m dragonslayer_ptbr scan-text-parser-candidates `
  --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" `
  --output reports/m68k-text-parser-candidates.md

python -m dragonslayer_ptbr scan-reachable-text `
  --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" `
  --output reports/m68k-reachable-text.md

python -m dragonslayer_ptbr scan-m68k-register-flow `
  --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" `
  --output reports/m68k-register-flow.md

python -m dragonslayer_ptbr scan-a3-flow `
  --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" `
  --output reports/m68k-a3-flow.md

python -m dragonslayer_ptbr scan-indexed-reads `
  --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" `
  --output reports/m68k-indexed-reads.md

python -m dragonslayer_ptbr scan-m68k-code `
  --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" `
  --output reports/m68k-code-flow.md

python -m dragonslayer_ptbr audit-m68k-entry-overlaps `
  --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" `
  --output reports/m68k-entry-overlaps.md
```

Se algum comando falhar, não ignore o erro nem trate o relatório antigo como se tivesse sido atualizado. Guarde o comando, traceback e versão/commit do projeto. Os comandos são independentes; a falha de um não deve invalidar os relatórios realmente gerados pelos outros.

## Como combinar os resultados

Depois de executar os comandos, cruze os resultados manualmente com esta matriz:

| Sinal | Valor probatório | Limitação |
|---|---|---|
| Leitura sequencial + comparação de controle | Médio | Pode ocorrer em rotinas não textuais |
| Vários controles no mesmo laço | Alto | Ainda exige verificar limites e fluxo |
| Caminho específico para `0x06` consumindo dois bytes adicionais | Alto | O decoder precisa reconhecer corretamente os comprimentos |
| Registrador-base rastreado até região japonesa conhecida | Muito alto | Exige ligação demonstrável entre base e fluxo |
| Referência à tabela `0x1A551A` | Médio | A tabela pode ter outro papel |
| Índice derivado do caractere + lookup de tabela + acesso a glifo | Muito alto | Precisa de evidência coerente em instruções e dados |
| Chamada direta encontrada no CFG do reset | Alto para alcançabilidade | A ausência não prova inacessibilidade |
| Fluxo que só existe ao forçar um offset como entrada | Baixo | Pode começar no meio de uma instrução ou em dados |
| Bytes parecidos com opcode isolado | Baixo | ROMs de dados geram falsos positivos |

A prioridade não é o candidato com mais coincidências, mas o candidato com a cadeia mais completa e menos suposições.

## Primeiro objetivo concreto

O próximo resultado útil deve ser uma ficha do **primeiro candidato que apresente leitura sequencial, comparação de controle e ramificação coerente**, contendo:

1. offset inicial e bytes brutos;
2. instruções reconhecidas com tamanho e destino;
3. primeiro ponto de parada do decoder, se houver;
4. referências de chamada e registradores de endereço;
5. quais controles são testados e como o fluxo prossegue;
6. se `0x06` aparenta consumir os dois bytes seguintes;
7. relação — ou ausência de relação — com a tabela `0x1A551A`;
8. comparação com um segundo disassembler;
9. conclusão classificada e próximo teste falsificável.

## Critério de sucesso

Esta análise será considerada produtiva quando reduzir o conjunto de candidatos e entregar pelo menos uma cadeia verificável entre dados de texto conhecidos e código 68000 plausivelmente responsável por processá-los. Gerar mais ocorrências sem aumentar a qualidade das ligações não conta como progresso.

Nenhuma tradução, realocação, gravação de ponteiros ou alteração da ROM deve começar com base apenas neste relatório.


## Integração do plano de ferramentas externas — 2026-10-09

A execução desta análise deve seguir o plano versionado em [third-party-tooling-and-validation-plan.md](third-party-tooling-and-validation-plan.md). A prioridade é comparar o decoder próprio com sega2asm e Oxore m68k-disasm, depois buscar evidência dinâmica em BlastEm ou MAME.

Antes de comparar novas contagens de CFG, reproduzir o baseline com a mesma ROM, commit e parâmetros. Os relatórios históricos apresentam contagens divergentes, e a causa ainda não deve ser presumida. O teste `test_scan_address_references_accepts_custom_targets` também precisa ser corrigido e validado por uma execução real de CI.

Os intervalos `0x01E9A4–0x01E9C8`, `0x0262C0–0x0262E8` e `0x02AF20–0x02AFA6` são alvos de comparação, não funções confirmadas. Para cada um, registrar bytes brutos, alinhamento, comprimento das instruções, destinos de branch e eventuais diferenças entre ferramentas.

Não iniciar encoder de produção, realocação ou patch até demonstrar a relação entre uma entrada conhecida, sua leitura em runtime e o processamento/renderização. O fato de um teste reconhecer os códigos dos caracteres portugueses não comprova que a ROM possua os glifos correspondentes.
