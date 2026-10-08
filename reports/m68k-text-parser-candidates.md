# M68K text-parser candidate analysis

> Resultado baseado na ROM japonesa local confirmada. A análise é somente leitura; nenhuma ROM é armazenada no repositório.

## Resultado

O padrão procurado foi:

`MOVE.B (An)+,Dn`

seguido, em até 16 bytes, por:

`CMPI.B #imm,Dn`

com `imm` entre `01`, `06`, `0D` e `0E`.

Foram encontrados 6 candidatos:

| Leitura | Teste | Registrador | Controle |
|---:|---:|---:|---:|
| 0x026AE0 | 0x026AEA | D0 | 0x01 |
| 0x0308C0 | 0x0308C2 | D0 | 0x0E |
| 0x030AA4 | 0x030AAA | D0 | 0x0D |
| 0x030B46 | 0x030B4C | D0 | 0x0E |
| 0x030B6A | 0x030B70 | D0 | 0x0E |
| 0x030CBE | 0x030CC4 | D0 | 0x0D |

## Candidato principal

A faixa `0x0308C0–0x030CC4` é a mais relevante.

Em particular:

- `0x030A9C`: salva registradores, chama uma subrotina e executa `MOVE.B (A3)+,D0`, seguido de `CMPI.B #$0D,D0`.
- `0x030B42`: executa `MOVE.B (A3)+,D0`, seguido de `CMPI.B #$0E,D0`.
- `0x030B66`: executa `MOVE.B (A3)+,D0`, seguido de `CMPI.B #$0E,D0`.
- `0x030CBC`: executa `MOVE.B (A3)+,D0`, seguido de `CMPI.B #$0D,D0`.

Isso demonstra uma cadeia de processamento de bytes muito mais específica do que a busca global por `CMPI.B`.

## Limite da conclusão

Ainda não é correto chamar essa região de engine de texto.

O próximo passo deve determinar:

1. de onde `A3` recebe seu valor;
2. qual subrotina prepara/avança `A3`;
3. para onde os ramos de `0x0D` e `0x0E` levam;
4. se existe teste de `0x01` ou `0x06` na mesma máquina de estados;
5. se a rotina é alimentada por dados da região de script japonesa ou por outra estrutura do jogo.

A hipótese de trabalho passa a ser:

`fonte de dados -> A3 -> MOVE.B (A3)+ -> comparação de controle -> despacho`

Somente após confirmar essa cadeia devemos atribuir semântica aos controles e implementar o encoder/realocador.
