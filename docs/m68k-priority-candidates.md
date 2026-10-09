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
