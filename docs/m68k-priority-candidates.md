# Análise dos candidatos a processamento de bytes 68000

## Origem e limites da evidência

Este documento registra a inspeção exploratória dos offsets `0x01E9A4`, `0x0262C0` e `0x02AF78`, feita com `inspect-m68k-targets` na ROM japonesa.

O CFG iniciado no vetor de reset contém 1.763 blocos no relatório fornecido. Nenhuma chamada direta para esses três offsets foi reconhecida nesse CFG. Isso não exclui chamadas indiretas, entradas por tabelas ou limitações do decoder; significa apenas que a ferramenta não demonstrou uma chamada direta alcançável para os offsets solicitados.

Os alvos foram forçados como entradas para inspeção. Portanto, a decodificação local pode começar no meio de uma instrução ou em bytes de dados. Nenhum dos três alvos está confirmado como início de função ou código executado.

## Candidato em 0x01E9AC

Sequência observada:

```text
0x01E9AC  MOVE.B (An)+,Dn
0x01E9AE  CMPI.B #$06,Dn
0x01E9B2  BEQ -> 0x01E9BC
0x01E9B6  MOVE.B Dn,(An)+
0x01E9B8  BRA -> 0x01E9AC
```

O caminho que não encontra `0x06` copia o byte lido para um endereço de destino e repete a leitura. Isso é compatível com um laço de cópia delimitado por `0x06`, mas também pode representar outro processamento de bytes. O relatório não mostra o corpo do destino `0x01E9BC`, nem prova que o byte de origem seja texto.

**Prioridade de investigação: alta**, porque a sequência apresenta leitura com pós-incremento, comparação explícita e um laço de cópia. A prioridade não equivale à confirmação de parser.

## Candidato em 0x02AF80

Sequência observada:

```text
0x02AF80  MOVE.B (An)+,Dn
0x02AF82  CMPI.B #$06,Dn
0x02AF86  BEQ -> 0x02AF90
0x02AF8A  MOVE.B Dn,(An)+
0x02AF8C  BRA -> 0x02AF80
```

O laço é estruturalmente semelhante ao observado em `0x01E9AC`: copia bytes até encontrar `0x06`, segundo a interpretação do fluxo decodificado. A semelhança pode indicar rotinas equivalentes, código duplicado ou coincidência de decodificação. Não há evidência suficiente para escolher entre essas possibilidades.

**Prioridade de investigação: alta**, condicionada à validação dos limites de instrução, do ponto de entrada e do destino `0x02AF90`.

## Candidato em 0x0262C4

Sequência observada:

```text
0x0262C4  MOVE.B (An)+,Dn
0x0262C6  CMPI.B #$00,Dn
0x0262CA  BEQ -> 0x0262DC
0x0262CE  CMPI.B #$06,Dn
0x0262D2  BEQ -> 0x0262DC
0x0262D6  MOVE.B Dn,(An)+
0x0262D8  BRA -> 0x0262C4
0x0262DA  MOVE.B (An)+,Dn
0x0262DC  MOVE.B Dn,(An)+
0x0262DE  CMPI.B #$00,Dn
0x0262E2  BNE -> 0x0262DA
0x0262E4  RTS
```

O fluxo decodificado sugere um laço que copia bytes comuns até encontrar `0x00` ou `0x06`. Nesse caso, o caminho especial entra em outro laço que lê e grava bytes até encontrar `0x00`, e então retorna. Essa leitura é apenas uma descrição do fluxo reportado: sem validar o ponto de entrada, a semântica das instruções e os chamadores, não se pode afirmar que seja tratamento de controles de script.

**Prioridade de investigação: média**, pois há comparações de dois valores relevantes, mas a função do segundo laço ainda é desconhecida.

## Próximas verificações recomendadas

1. Inspecionar os destinos dos desvios `0x01E9BC` e `0x02AF90` como pontos de entrada exploratórios, registrando explicitamente que isso não comprova execução.
2. Inspecionar a região imediatamente anterior a cada laço para identificar instruções completas, possíveis limites de função e preparação dos registradores de origem/destino.
3. Procurar referências diretas e indiretas aos candidatos e investigar tabelas de despacho; a ausência de chamadas diretas no CFG de reset não resolve chamadas indiretas.
4. Comparar o comportamento com os controles reais da abertura em `0x01626B–0x01668A`, especialmente `0x01`, `0x06 xx yy`, `0x0E` e `0x00`.
5. Só promover um candidato a parser quando houver uma cadeia demonstrável entre o endereço de origem dos bytes, os controles do script e o processamento/renderização de caracteres.

## Estado das conclusões

- **Confirmado pelo relatório:** os padrões de instruções acima foram decodificados nos offsets apresentados pela ferramenta.
- **Hipótese:** os dois laços que comparam `0x06` podem ser rotinas de cópia delimitada.
- **Não demonstrado:** que qualquer candidato seja o parser principal, que receba a abertura ou que seja alcançado durante a execução.
- **Próximo objetivo:** validar entradas e destinos dos desvios e rastrear como os registradores de endereço são preparados.


## Resultado da inspeção dos destinos dos desvios

O relatório seguinte examinou `0x01E9BC`, `0x02AF90` e `0x0262DC` como entradas exploratórias.

- Em `0x01E9BC` e `0x02AF90`, o decoder não reconheceu uma instrução válida.
- Em `0x0262DC`, a decodificação reproduziu o laço que grava bytes até encontrar `0x00`, seguido de `RTS`.
- Nenhum dos três offsets teve chamador direto reconhecido no CFG iniciado pelo vetor de reset.

A falha de decodificação nos dois primeiros destinos **não prova que os bytes sejam dados**. Pode indicar dados, entrada no meio de uma instrução, uma instrução 68000 ainda não suportada pelo decoder ou fluxo incorreto causado por um falso candidato. Sem os bytes brutos ao redor dos destinos, não é possível distinguir essas hipóteses.

## Melhoria no relatório de inspeção

O comando `inspect-m68k-targets` agora inclui uma janela hexadecimal bruta quando não consegue decodificar um alvo. A janela cobre até 8 bytes anteriores e 16 bytes a partir do alvo, respeitando os limites da ROM. Esses bytes são apresentados sem classificação como código ou dados.

Gere novamente o relatório:

```powershell
python -m dragonslayer_ptbr inspect-m68k-targets `
  --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" `
  --targets 0x01E9BC 0x02AF90 0x0262DC `
  --max-blocks-per-target 120 `
  --output reports/m68k-control-destinations.md
```

Envie a nova versão de `reports/m68k-control-destinations.md`. O conteúdo hexadecimal permitirá verificar se os destinos começam com uma instrução conhecida, se parecem estar no meio de uma sequência ou se precisamos ampliar o decoder. Ainda assim, a janela isolada não comprova fluxo de execução.

## Reavaliação dos destinos com os bytes brutos

O relatório fornecido para `0x01E9BC`, `0x02AF90` e `0x0262DC` permite distinguir melhor os casos.

### Destino `0x01E9BC`

Os bytes começam com `7F FF 4E 75`. `0x7FFF` não é uma codificação válida de `MOVEQ` no 68000, pois o bit 8 dessa instrução deve ser zero. Assim, o decoder interromper nesse endereço é coerente com seu comportamento conservador; não devemos interpretar `7F FF` como uma instrução válida. O `RTS` seguinte, em `0x01E9BE`, é reconhecível, mas isso não esclarece se o primeiro word é dado, preenchimento ou parte de um fluxo iniciado em outro ponto.

Em `0x01E9C0`, os bytes `48 E7 FF FE` codificam `MOVEM.L` com máscara de registradores para salvar registradores na pilha, padrão compatível com início de rotina. Isso não demonstra uma ligação de execução entre `0x01E9BC` e a rotina em `0x01E9C0`.

### Destino `0x02AF90`

Os bytes `42 00` codificam `CLR.B D0`. Em seguida, `DB FC 00 00 00 03` codifica `ADDA.L` com operando imediato e `DD FC 00 00 00 1A` codifica outra `ADDA.L` imediata. O decoder anterior não suportava essa forma de `ADDA`, motivo suficiente para interromper o fluxo mesmo diante de bytes que podem ser código válido.

O decoder foi atualizado para consumir corretamente as extensões imediatas de `ADDA.W/L` e `SUBA.W/L`, evitando perder o alinhamento em sequências desse tipo. Foram acrescentados testes para `ADDA.L`, `SUBA.W` e para a codificação inválida `7F FF`. Esses testes foram adicionados ao repositório; o resultado de CI ainda precisa ser consultado separadamente antes de declarar a suíte aprovada.

### Destino `0x0262DC`

A sequência continua consistente com `MOVE.B Dn,(An)+`, comparação com zero, desvio de retorno ao laço e `RTS`. Ela pode descrever cópia de bytes até o terminador zero, mas ainda não foi relacionada a uma entrada de script ou a uma rotina de renderização.

## Estado após esta revisão

- **Confirmado pela decodificação dos bytes:** `0x42 0x00` é `CLR.B D0`; `0xDBFC` e `0xDDFC` iniciam formas imediatas de `ADDA.L`; `0x7FFF` não é um `MOVEQ` válido no 68000.
- **Inferência:** `0x02AF90` pode ser código executável, e a falha anterior era explicada por uma instrução ainda não suportada.
- **Não demonstrado:** que `0x01E9BC` seja uma entrada válida, que as rotinas sejam alcançadas em runtime ou que qualquer uma delas processe texto.
- **Próximo passo:** executar novamente `inspect-m68k-targets` após atualizar o projeto e analisar o fluxo expandido a partir de `0x02AF90`; depois rastrear os registradores de endereço usados como origem e destino.
## Atualização após o segundo relatório

O segundo relatório informou 2.100 blocos alcançados desde o vetor de reset, mas ainda parou em `0x02AF90`. O motivo identificado é anterior às instruções `ADDA`: o decoder não reconhecia `42 00`, que corresponde a `CLR.B D0`.

O decoder foi atualizado para reconhecer `CLR.B/W/L` e consumir eventuais extensões do effective address. Foram adicionados testes para `CLR.B D0` e para a sequência `CLR.B D0; ADDA.L #$00000003,...; ADDA.L #$0000001A,...`. Os testes estão no repositório, mas ainda não se deve afirmar que passaram até conferir o CI.

Referências:
- [Decoder 68000](../src/dragonslayer_ptbr/analysis/m68k_code.py)
- [Testes do decoder](../tests/test_m68k_code.py)

Depois de atualizar o checkout local, execute novamente `inspect-m68k-targets` nos três destinos. O objetivo imediato é verificar se a decodificação de `0x02AF90` avança além de `CLR.B D0` e das duas instruções `ADDA.L`. A sequência decodificada ainda precisa ser validada como código e relacionada a chamadores antes de inferir sua função.
## Atualização após a inspeção de cinco alvos

O relatório mais recente contém 2.100 blocos alcançados a partir do vetor de reset e examina os alvos 0x01E9BC, 0x01E9C0, 0x02AF26, 0x02AF90 e 0x0262DC. Os resultados exigem uma ressalva importante: o CFG iniciado artificialmente em 0x02AF26 chega a 0x02AF94, enquanto a decodificação iniciada separadamente em 0x02AF90 interpreta 0x02AF92 como ADDA.L #$00000003,A5.

### Sobreposição suspeita na região 0x02AF90

A instrução iniciada em 0x02AF92 ocupa seis bytes, de 0x02AF92 a 0x02AF97. Portanto, 0x02AF94 cai dentro do operando imediato dessa instrução. O relatório do fluxo iniciado em 0x02AF26 chega exatamente a esse endereço por meio do desvio condicional em 0x02AF2C.

Se as duas decodificações estiverem corretas, o fluxo aparenta entrar no meio de uma instrução, o que é um sinal forte de que pelo menos uma das hipóteses de entrada/alinhamento precisa ser revista. Não devemos concluir que 0x02AF90 seja uma rotina validada apenas porque o decoder consegue decodificar seus bytes isoladamente. É necessário conferir os bytes e o fluxo em torno de 0x02AF20 e 0x02AF90, idealmente com um desassembler 68000 independente.

### Sobre 0x01E9C0

A sequência 48 E7 FF FE é compatível com MOVEM.L salvando registradores na pilha. Em seguida há outra instrução MOVEM e uma chamada absoluta a 0x02930A. A região contém laços com leitura e escrita de bytes e chamadas a 0x01EA5E, tornando-a um candidato de análise mais rico do que a janela isolada em 0x01E9BC.

Entretanto, a inspeção forçada não prova que 0x01E9C0 seja uma entrada real. O alvo 0x01E9BC continua começando com 7F FF, que não é um MOVEQ válido no 68000, e não há chamada direta reconhecida no CFG de reset para esse endereço.

### Estado das hipóteses

- **Observado no relatório:** há laços com MOVE.B (An)+,Dn e MOVE.B Dn,(An)+ perto de 0x01E9E4; a região chama 0x01EA5E e 0x02930A.
- **Sinal de alerta:** o destino 0x02AF94 sobrepõe o operando imediato da instrução que começa em 0x02AF92 quando se aceita a decodificação local de 0x02AF90.
- **Ainda não demonstrado:** que os laços sejam parser de texto, que os bytes de entrada venham de um script ou que a rotina esteja alcançável em runtime.
- **Próximo passo recomendado:** validar a região 0x01E9C0 com uma segunda implementação de desassemblagem e rastrear os registradores que alimentam as leituras de byte; tratar 0x02AF90 como ambíguo até resolver a sobreposição de fluxo.

## Auditoria reproduzível de entradas sobrepostas

Foi adicionada a ferramenta `audit-m68k-entry-overlaps`, que compara o fluxo 68000 decodificado a partir de várias entradas candidatas independentes e sinaliza quando uma entrada cai dentro dos bytes de uma instrução reconhecida a partir de outra entrada.

O conjunto padrão inclui `0x02AF20`, `0x02AF90` e `0x02AF94`. O resultado é um diagnóstico de ambiguidade, não uma prova de execução nem de parser. O relatório inclui os bytes brutos de cada instrução e representa o intervalo como `[início, fim)`: o endereço final é exclusivo (por exemplo, uma instrução de seis bytes iniciada em `0x02AF92` termina no limite `0x02AF98`, ocupando os bytes até `0x02AF97`). Isso evita confundir o limite final com o último byte da instrução.

```powershell
python -m dragonslayer_ptbr audit-m68k-entry-overlaps --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --output reports/m68k-entry-overlaps.md
```

Para limitar a comparação:

```powershell
python -m dragonslayer_ptbr audit-m68k-entry-overlaps --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --entries 0x2AF20 0x2AF90 0x2AF94
```

A validação decisiva continua sendo comparar `0x02AF20–0x02AFA6` com um segundo disassembler 68000 e verificar as chamadas reais no fluxo alcançável.


## Atualização: discrepância na cobertura do CFG

O relatório recente de `inspect-m68k-targets` informa 44 blocos alcançados desde o vetor de reset, enquanto relatórios anteriores registravam aproximadamente 2.100. Essa diferença precisa ser explicada antes de interpretar a ausência de chamadores diretos. Pode decorrer de versão do código, configuração ou ROM diferente; a causa ainda não está confirmada.

A inspeção forçada de `0x01E9C0` continua mostrando laços com `MOVE.B (An)+,Dn`, chamada para `0x01EA5E`, gravação de bytes e instruções `DBcc`. Isso é compatível com processamento sequencial de dados, mas não confirma um parser. `0x01EA5E` contém comparações e desvios, sem demonstrar que os valores correspondem aos controles textuais `0x01`, `0x06`, `0x0E` e `0x00`. `0x02930A` continua com decodificação interrompida.

### Próxima etapa: reproduzir a cobertura antes de inferir semântica

Execute os três comandos no mesmo checkout e usando a mesma ROM:

```powershell
python -m dragonslayer_ptbr inspect-m68k-targets --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --targets 0x01E9C0 0x01E9E4 0x01EA5E 0x02930A --max-blocks-per-target 120 --output reports/m68k-text-processing-region.md
python -m dragonslayer_ptbr scan-reachable-text --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --output reports/m68k-reachable-text.md
python -m dragonslayer_ptbr audit-m68k-entry-overlaps --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --output reports/m68k-entry-overlaps.md
```

Se a contagem de 44 blocos persistir, investigar o vetor de reset, o primeiro opcode desconhecido no fluxo e as instruções de inicialização reconhecidas. A ausência de chamadores diretos no CFG incompleto não demonstra que os alvos sejam inalcançáveis.

**Estado:** a hipótese de processamento de bytes permanece aberta; o parser não foi confirmado. Nenhuma alteração deve ser feita na ROM original até validar o CFG e rastrear os registradores de origem/destino com uma segunda implementação de desassemblagem 68000.
