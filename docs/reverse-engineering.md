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
