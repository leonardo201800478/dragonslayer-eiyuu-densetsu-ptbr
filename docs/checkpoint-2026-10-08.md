# Checkpoint de engenharia reversa — 2026-10-08

## Objetivo da sessão

Registrar a análise dos relatórios recentes de inspeção 68000 e deixar um ponto de retomada reproduzível para a investigação do engine de texto de *Dragon Slayer: Eiyuu Densetsu* (Mega Drive). Este checkpoint não afirma que o parser foi encontrado.

## Base de evidências

Relatórios analisados nesta sessão:

- `m68k-entry-overlaps.md`
- `m68k-register-flow(1).md`
- `m68k-target-inspection(1).md`

Os relatórios são resultados de análise estática exploratória. Os alvos podem ter sido forçados como entradas, e o decoder 68000 do projeto é parcial. Uma sequência decodificada isoladamente não prova que seja código executado em runtime.

## Resultado atual do fluxo de registradores

O relatório recente de `scan-m68k-register-flow` informa:

- 39 blocos no CFG iniciado pelo vetor de reset;
- 14 definições identificadas de registradores A0–A3;
- 2 leituras de byte reconhecidas;
- 8 chamadas `JSR` reconhecidas.

Leituras de byte listadas:

| Offset | Registrador | Forma | Registrador de dados | Origem local | Valor |
|---|---|---|---|---|---|
| `0x00B542` | A1 | `(An)` | D0 | — | — |
| `0x00CB00` | A0 | `(An)` | D2 | — | — |

Definições listadas:

| Offset | Registrador | Instrução / valor reportado |
|---|---|---|
| `0x00B544` | A3 | `LEA abs.l 0x00FF00EA` |
| `0x00B558` | A3 | `MOVEA.L/W <EA>`, origem/valor não resolvido |
| `0x00CB0A` | A2 | `MOVEA.L/W <EA>`, origem/valor não resolvido |
| `0x010736` | A1 | `LEA abs.l 0x00FF0000` |
| `0x010754` | A1 | `LEA abs.l 0x0000183E` |
| `0x010760` | A1 | `LEA abs.l 0x00FF0000` |
| `0x01076E` | A0 | `LEA abs.l 0x00010B9A` |
| `0x010774` | A1 | `LEA abs.l 0x00FF001C` |
| `0x010784` | A0 | `LEA abs.l 0x00A10003` |
| `0x0109B0` | A1 | `LEA abs.l 0x00010F32` |
| `0x0109BC` | A1 | `LEA abs.l 0x00010F54` |
| `0x0109C8` | A1 | `LEA abs.l 0x00010F76` |
| `0x0109D4` | A1 | `LEA abs.l 0x00010F98` |
| `0x0109E2` | A2 | `LEA abs.l 0x0000BC00` |

Chamadas diretas reportadas:

| Origem | Tipo | Destino |
|---|---|---|
| `0x01077A` | `JSR abs.l` | `0x00CADA` |
| `0x01078A` | `JSR abs.l` | `0x009408` |
| `0x0109AA` | `JSR abs.l` | `0x010AF2` |
| `0x0109B6` | `JSR abs.l` | `0x00B53E` |
| `0x0109C2` | `JSR abs.l` | `0x00B53E` |
| `0x0109CE` | `JSR abs.l` | `0x00B53E` |
| `0x0109DA` | `JSR abs.l` | `0x00B536` |
| `0x010B16` | `JSR abs.l` | `0x010B28` |

**Interpretação:** a cobertura é pequena demais para concluir que as rotinas candidatas são inalcançáveis. A ausência de uma origem local para as duas leituras também não prova que elas não consumam texto; significa apenas que o rastreador não conseguiu estabelecer a origem com as regras atuais.

## Inspeção dos candidatos

### Candidato `0x01E9AC`

Sequência decodificada:

```text
0x01E9AC  MOVE.B (An)+,Dn
0x01E9AE  CMPI.B #$06,Dn
0x01E9B2  BEQ -> 0x01E9BC
0x01E9B6  MOVE.B Dn,(An)+
0x01E9B8  BRA -> 0x01E9AC
```

O fluxo é compatível com um laço que lê e copia bytes até encontrar `0x06`. Ainda não há prova de que o endereço de origem aponte para script, nem de que a rotina seja alcançada em runtime.

### Candidato `0x0262C4`

Sequência decodificada:

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

O fluxo sugere um laço de cópia que reage a `0x00` e `0x06`, seguido por outro laço que grava bytes até encontrar `0x00`. É o candidato mais interessante entre os três inspecionados nesta rodada por conter comparações explícitas com os dois valores e um retorno visível. Isso é prioridade investigativa, não confirmação de parser ou de tratamento de controles.

### Candidato `0x02AF80`

Sequência decodificada:

```text
0x02AF80  MOVE.B (An)+,Dn
0x02AF82  CMPI.B #$06,Dn
0x02AF86  BEQ -> 0x02AF90
0x02AF8A  MOVE.B Dn,(An)+
0x02AF8C  BRA -> 0x02AF80
0x02AF90  CLR.B <EA>
0x02AF92  ADDA.L #$00000003,A5
0x02AF98  ADDA.L #$0000001A,A6
0x02AF9E  ADDQ/SUBQ
0x02AFA0  DBcc -> 0x02AF26
0x02AFA4  RTS
```

O começo parece um laço de cópia delimitado por `0x06`, mas a interpretação do trecho seguinte depende da validade do ponto de entrada e do decoder. O relatório de auditoria assinala que `0x02AF94` cai dentro da instrução de seis bytes iniciada em `0x02AF92` (`ADDA.L #$00000003,A5`). Essa sobreposição é uma ambiguidade real entre fluxos decodificados, não prova de código sobreposto em runtime. Pode indicar entrada incorreta, dados interpretados como código, fluxo de controle alternativo ou limitação do decoder.

## Limitações que permanecem abertas

1. O CFG alcançável a partir do vetor de reset contém apenas 39 blocos no relatório mais recente; a ausência de chamadores diretos reconhecidos não é conclusiva.
2. O inspetor identifica chamadores diretos reconhecidos como `JSR abs.l` e `BSR`; chamadas indiretas como `JSR (An)` não têm destino resolvido.
3. O decoder ainda produz mnemônicos genéricos e não reconhece integralmente o conjunto de instruções 68000.
4. Relatórios históricos apresentaram contagens muito diferentes de blocos (incluindo aproximadamente 2.100, 44, 43 e 39). A causa da discrepância ainda não foi estabelecida; não assumir que a correção de `BTST` a explicou.
5. Nenhuma evidência atual conecta definitivamente os candidatos à região de abertura `0x01626B–0x01668A`, à tabela Shift-JIS em `0x1A551A) ou à renderização dos caracteres.
6. A ROM original deve permanecer sem alterações enquanto os caminhos, controles, ponteiros e limites de instrução não forem validados.

## Estado das conclusões

### Confirmado pelos relatórios fornecidos

- Os padrões de instrução descritos foram emitidos pelo decoder nos offsets listados.
- O relatório de fluxo de registradores contém 39 blocos, 14 definições A0–A3, duas leituras de byte e oito chamadas `JSR`.
- A auditoria identificou `0x02AF94` dentro da instrução decodificada a partir de `0x02AF92`.

### Hipóteses de trabalho

- `0x01E9AC) e `0x02AF80) podem ser laços de cópia delimitados por `0x06`.
- `0x0262C4) pode implementar processamento de bytes com tratamento especial de `0x00` e `0x06`.
- `0x0262C4) é o primeiro alvo a aprofundar na próxima sessão; `0x01E9AC) fica como segundo alvo. `0x02AF80) permanece ambíguo até resolver a sobreposição.

### Não demonstrado

- Que qualquer candidato seja o parser principal.
- Que qualquer alvo seja alcançado durante a execução normal do jogo.
- Que os bytes lidos sejam dados de script.
- Que os valores comparados representem exatamente os controles textuais já observados.
- Que qualquer rotina esteja ligada à renderização/fonte Shift-JIS.

## Plano para a próxima sessão

1. Reproduzir as contagens do CFG no mesmo checkout e na mesma ROM; guardar as saídas completas e a primeira instrução que interrompe a travessia.
2. Executar uma segunda implementação de disassemblagem 68000 sobre as regiões `0x01E9A4–0x01E9C8`, `0x0262C0–0x0262E8` e `0x02AF20–0x02AFA6`, comparando bytes, tamanhos de instrução e destinos.
3. Inspecionar os registradores antes dos laços, para identificar como os ponteiros de origem e destino são preparados.
4. Investigar referências diretas e indiretas, tabelas de despacho e chamadas `JSR (An)` que o inspetor atual não resolve.
5. Correlacionar os caminhos com os controles reais encontrados em `0x01626B–0x01668A`: `0x01`, `0x06 xx yy`, `0x0E) e `0x00`, sem assumir sua semântica além do que os dados sustentam.
6. Só depois de demonstrar a cadeia leitura → controle → avanço de ponteiro → processamento/renderização considerar uma implementação de tradução ou qualquer patch da ROM.

## Comandos para retomada

Execute no checkout do projeto, usando a ROM original local:

```powershell
python -m dragonslayer_ptbr scan-m68k-register-flow --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --output reports/m68k-register-flow.md

python -m dragonslayer_ptbr inspect-m68k-targets --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --targets 0x01E9AC 0x0262C4 0x02AF80 --output reports/m68k-target-inspection.md

python -m dragonslayer_ptbr audit-m68k-entry-overlaps --rom "roms/original/Dragon Slayer - Eiyuu Densetsu (Japan).md" --entries 0x02AF20 0x02AF90 0x02AF94 --output reports/m68k-entry-overlaps.md

python -m pytest -q
```

Não declarar os testes aprovados nem a divergência do CFG resolvida sem consultar a saída real dos comandos.

## Referências no repositório

- [Estratégia de engenharia reversa](reverse-engineering.md)
- [Candidatos 68000 prioritários](m68k-priority-candidates.md)
- [Análise abrangente do engine de texto](comprehensive-text-engine-analysis.md)
- [Decoder 68000](../src/dragonslayer_ptbr/analysis/m68k_code.py)
- [Inspetor de alvos 68000](../src/dragonslayer_ptbr/analysis/m68k_target_inspector.py)
- [CLI](../src/dragonslayer_ptbr/cli.py)

---

**Encerramento da sessão:** documentação registrada em 2026-10-08. Nenhum parser foi confirmado e nenhuma alteração foi feita na ROM. Próxima ação: validar os fluxos com um disassembler independente antes de avançar a hipótese de engine de texto.
