# Investigação: limites e possível expansão das caixas de diálogo

## Objetivo

Determinar, com evidência direta do jogo, se é possível aumentar a área de diálogo ou a quantidade de texto exibido por página em **Dragon Slayer: Eiyuu Densetsu (Mega Drive)**. Este documento é um plano de investigação; não afirma que a expansão já foi demonstrada.

## Estado confirmado no projeto

- A ROM de referência analisada tem 2 MiB, CRC32 `01BC1604` e SHA-1 `F67C9139BBC93F171E274A5CD3FBA66480CD8244`.
- O charset Shift-JIS foi identificado em regiões textuais.
- A região aproximada `0x01626B–0x01667F` contém texto da abertura.
- Controles de um byte e controles estendidos `0x06 xx yy` aparecem misturados ao texto, mas a semântica de vários controles não foi confirmada.
- Existe uma tabela de códigos Shift-JIS em `0x1A551A`; a rotina que a consulta ainda não foi localizada.
- O decoder e o classificador existentes são ferramentas de leitura/análise. Não provam os limites visuais nem produzem arquivos prontos para inserção.

Consulte também [Estratégia de engenharia reversa do texto](reverse-engineering.md) e [Relatório consolidado](analysis-results.md).

## Perguntas que precisam ser respondidas

1. Qual rotina 68000 consome os bytes de texto e interpreta os controles?
2. Como o jogo mapeia os códigos de caracteres para glifos/tilemaps?
3. Onde são definidos a posição inicial, a largura e a altura da caixa, o espaçamento e a quantidade de linhas?
4. A quebra de linha é explícita no script, automática por largura ou uma combinação?
5. Há limite de bytes por entrada, buffer temporário ou página, independentemente do tamanho visual da caixa?
6. A moldura é um elemento gráfico independente, um tilemap ou parte de uma composição fixa?
7. A fonte e a tabela de caracteres permitem os glifos portugueses necessários?

## Procedimento seguro

### Fase 1 — Estabelecer um caso de referência

- Usar a ROM local validada por hash, sempre em modo somente leitura.
- Escolher uma mensagem curta e reproduzível nos scripts já extraídos.
- Registrar o arquivo/linha do dump, bytes correspondentes quando conhecidos, controles presentes e captura de tela do emulador.
- Não assumir que linhas do dump correspondem individualmente a páginas exibidas.

### Fase 2 — Rastrear a rotina de texto

- Abrir uma cópia de análise da ROM no Ghidra ou em outro desassemblador/debugger 68000.
- Inspecionar referências à tabela em `0x1A551A` e confirmar, pelo código que a acessa, seu papel real.
- Usar breakpoints/watchpoints no debugger quando possível para rastrear a leitura dos bytes da mensagem até a rotina que desenha cada glifo.
- Registrar endereços, instruções e evidências reproduzíveis; não transformar candidatos estatísticos em fatos confirmados.
- Identificar as condições que encerram uma linha/página e a lógica que avança o diálogo.

### Fase 3 — Separar limites de texto e limites gráficos

Medir e documentar separadamente:

- largura útil da caixa em pixels/tiles;
- altura útil e número de linhas;
- largura/altura dos glifos e espaçamento;
- marcadores de quebra, espera, paginação e término;
- tamanho máximo do buffer e formato de armazenamento;
- tabelas/ponteiros e restrições de realocação, caso sejam relevantes para a ferramenta de inserção.

A capacidade visual e o limite de armazenamento são problemas distintos. Não aumentar o tamanho de uma entrada antes de saber qual deles está sendo atingido.

### Fase 4 — Avaliar alternativas

Avaliar nesta ordem:

1. Reescrita e quebra de linhas dentro da caixa original.
2. Reutilização de glifos existentes para caracteres PT-BR, se visualmente aceitável.
3. Ajustes na rotina de paginação/impressão sem alterar a moldura.
4. Expansão da área gráfica, se as rotinas e o layout permitirem.
5. Alterações maiores na fonte/tabela de caracteres somente com um plano de compatibilidade testável.

A ordem é uma prioridade de menor para maior risco, não uma garantia de que todas as opções sejam possíveis.

## Critérios mínimos para um protótipo de expansão

- O texto de referência continua sendo exibido corretamente.
- Quebras de linha, espera, avanço de página, nomes e demais controles preservam seu comportamento observado.
- Mensagens seguintes e caminhos alternativos continuam funcionais.
- O patch altera apenas os bytes esperados; tamanho, checksum e diff são registrados.
- O protótipo é aplicado somente a uma ROM de teste separada da original.
- O teste é reproduzido no emulador e acompanhado de capturas antes/depois.
- Existe procedimento de reversão e nenhum script de inserção é executado contra a ROM original.

## Estado atual e decisão

**Estado: investigação pendente; expansão não confirmada.**

Até a rotina de renderização e os limites de buffer serem identificados, a bancada deve continuar respeitando os limites originais como padrão. Em paralelo, o projeto pode catalogar casos de texto que não cabem em português, sem truncar ou modificar automaticamente o conteúdo.

Não se deve inferir a semântica de `<JMP.L>`, `<$XX>` ou outros marcadores apenas pela forma do dump. O classificador lexical não substitui a análise do código 68000.
