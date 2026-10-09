# Plano de validação e ferramentas de terceiros

**Status:** plano de trabalho aprovado para investigação; ferramentas ainda não foram executadas contra a ROM neste checkpoint.  
**Última revisão documental:** 2026-10-09.

## 1. Objetivo

Organizar a próxima etapa de engenharia reversa de *Dragon Slayer: Eiyuu Densetsu* (Mega Drive), priorizando evidência reproduzível e ferramentas externas que reduzam as limitações do decoder 68000 próprio.

O objetivo imediato não é traduzir ou modificar a ROM. É demonstrar uma cadeia verificável:

`seleção do script → referência/endereço → leitura do byte → identificação de controles → processamento de caracteres → consulta da fonte/renderização`

A ROM original deve permanecer local, somente leitura e fora do Git. Todas as ferramentas de terceiros são auxiliares; nenhuma saída externa, por si só, confirma a função de uma rotina específica deste jogo.

## 2. Baseline do projeto

### Evidências já registradas

- ROM Mega Drive japonesa: 2.097.152 bytes (2 MiB).
- CRC32: `01BC1604`.
- SHA-1: `F67C9139BBC93F171E274A5CD3FBA66480CD8244`.
- 47 regiões classificadas como fortemente sustentadas como texto japonês.
- Shift-JIS confirmado para as regiões textuais identificadas.
- Abertura investigada aproximadamente em `0x01626B–0x01668A`.
- `0x01` é separador/quebra na abertura.
- `0x06 xx yy` é comando de três bytes; sua semântica ainda não foi demonstrada.
- `0x0E` foi observado como controle e `0x00` como terminador em estruturas examinadas.
- Tabela explícita de códigos Shift-JIS observada em `0x1A551A–0x1A62D2`; sua função no acesso aos glifos ainda não foi comprovada.
- O decoder e o CFG próprios são parciais e exploratórios.
- Os relatórios históricos mostram contagens de CFG divergentes (incluindo 39/43/44 e cerca de 1.763/2.100 blocos). Esses números não devem ser comparados sem reproduzir os comandos, o commit, a ROM e os parâmetros.
- A última execução de CI consultada reprovou `test_scan_address_references_accepts_custom_targets`; o CI precisa ser executado novamente após a correção. Não considerar a suíte verde sem consultar o resultado real.

### Hipóteses que continuam abertas

- Quais candidatos 68000 são realmente alcançados durante a execução.
- Qual rotina consome as entradas textuais.
- Como são interpretados os controles.
- Como os bytes de caracteres são convertidos em índices e glifos.
- Como cada entrada é selecionada e referenciada.
- Se existe compressão, realocação necessária ou restrição de tamanho para textos.

## 3. Avaliação das ferramentas externas

As ferramentas abaixo foram selecionadas para complementar — não substituir automaticamente — as ferramentas Python do projeto.

| Ferramenta | Uso proposto | Prioridade | Limites / cautelas |
|---|---|---|---|
| [sega2asm](https://github.com/hansbonini/sega2asm) | Desassemblagem/splitting específico para Mega Drive; rotular segmentos de código e dados; explorar tabelas de ponteiros e charmap; extrair gráficos quando suportado | **P1 — primeira comparação estática** | Exige configuração de segmentos e hints; resultados dependem da classificação correta. Requer Go 1.21+ conforme o README consultado. Há relato público de erros de desassemblagem em instruções do código de inicialização; usar apenas como uma das referências e inspecionar os bytes originais. |
| [Oxore m68k-disasm](https://github.com/Oxore/m68k-disasm) | Segunda implementação 68000; comparar limites de instrução, branches e alvos; potencial uso de PC trace | **P1 — segunda comparação estática** | Build CMake/C++; o próprio projeto informa que Windows não é seu ambiente mais testado. Sem PC trace, desassemblar uma ROM inteira pode interpretar dados como código. |
| [BlastEm](https://github.com/libretro/blastem) | Debugger do Mega Drive para breakpoints, execução passo a passo, inspeção de registradores e memória durante a abertura | **P2 — evidência dinâmica** | A documentação consultada descreve debugger interativo; watchpoints/tracepoints não são suportados em todas as interfaces. Confirmar capacidades na build utilizada. |
| [MAME Debugger](https://docs.mamedev.org/debugger/index.html) | Alternativa para breakpoints, memória e disassemblagem durante execução | **P2 — alternativa dinâmica** | Configuração e comandos diferem do BlastEm; registrar versão e sistema em uso. |
| [Ghidra](https://ghidra-sre.org/) | Análise estática interativa, referências cruzadas, funções, tabelas e fluxo de controle, quando o processor module/linguagem aplicável estiver configurado corretamente | **P3 — apoio opcional** | Requer configurar corretamente a imagem e o mapeamento de endereços. Não assumir que endereços de ROM e endereços de CPU são idênticos sem validar o mapeamento. |

### Decisão de integração

- **Não adicionar dependências obrigatórias ao Python** para essas ferramentas.
- Não embutir executáveis de terceiros no repositório nem exigir sua instalação para executar `pytest`.
- Registrar ferramenta, versão/commit, sistema operacional, comandos e hash da ROM usada.
- Salvar relatórios derivados em `reports/`; manter binários, ROM original e arquivos temporários locais.
- Antes de adotar uma ferramenta, revisar licença, dependências e instruções de build no repositório oficial.
- Utilizar a saída externa como evidência comparativa; quando houver divergência, inspecionar bytes brutos e resolver a causa antes de classificar o trecho.

## 4. Plano de execução

### Etapa A — Estabilizar o baseline

1. Confirmar tamanho, CRC32 e SHA-1 da ROM local.
2. Registrar o commit do projeto e as versões de Python, pytest e Ruff.
3. Corrigir o teste de referências de endereços que falha no CI. O contrato deve esclarecer se referências de 3 e 4 bytes sobrepostas são entradas distintas ou se devem ser deduplicadas; não apenas alterar o número esperado sem justificar.
4. Executar:
   ```powershell
   python -m pytest -q
   ruff check .
   ```
5. Reexecutar CI em Python 3.13 e 3.14 e registrar o resultado real.

**Gate A:** CI verde e baseline reproduzível. Até isso ocorrer, nenhuma contagem nova deve ser declarada como validada.

### Etapa B — Reproduzir e explicar a divergência do CFG

1. Executar os comandos atuais de CFG/fluxo de registradores com a mesma ROM, checkout e parâmetros.
2. Guardar comandos completos, saída, primeiro opcode não reconhecido e razão de parada.
3. Comparar os relatórios de 39/43/44 e 1.763/2.100 blocos, determinando quais vieram de comandos, commits ou modos de análise diferentes.
4. Se a divergência persistir na mesma configuração, criar teste de regressão mínimo para o ponto onde os fluxos divergem.

**Gate B:** cada contagem relevante tem comando, commit e configuração associados; diferenças inexplicadas ficam explicitamente marcadas como pendentes.

### Etapa C — Comparar desassemblagem independente

Priorizar inicialmente os intervalos que envolvem os candidatos registrados no projeto, sem os promover a funções confirmadas:

- `0x01E9A4–0x01E9C8`;
- `0x0262C0–0x0262E8`;
- `0x02AF20–0x02AFA6`;
- quando necessário, os blocos chamadores dos alvos `0x001D1E`, `0x001EC0` e `0x00D8F0`.

Procedimento:

1. Exportar os bytes exatos de cada intervalo a partir da ROM validada.
2. Desassemblar o mesmo intervalo com o decoder próprio, sega2asm e Oxore.
3. Registrar bytes, tamanho de cada instrução, mnemônico, destino de branch e divergências.
4. Usar contexto anterior e posterior suficiente para não começar arbitrariamente no meio de uma instrução.
5. Distinguir instrução validamente decodificada de instrução realmente alcançada pelo CFG.
6. Não inferir a semântica de parser somente por encontrar comparações com `0x01`, `0x06`, `0x0E` ou `0x00`.

**Artefato esperado:** `reports/m68k-third-party-comparison.md` (gerado após a execução real, não preenchido com resultados presumidos).

**Gate C:** divergências críticas de tamanho de instrução e destinos dos branches estão explicadas; candidatos continuam rotulados como hipóteses até evidência de execução.

### Etapa D — Obter evidência dinâmica

Usar BlastEm primeiro; usar MAME como alternativa se a build ou o debugger não permitirem a observação necessária.

1. Iniciar a ROM original no debugger.
2. Registrar build/versão, configuração regional e caminho de execução usado para chegar à abertura.
3. Colocar breakpoints somente em endereços previamente validados como limites plausíveis de instrução.
4. Observar PC, registradores de endereço/dados e bytes de memória antes e depois de operações relevantes.
5. Se houver suporte na build, registrar trace de PC durante a abertura. Não presumir que a build tenha watchpoints/tracepoints.
6. Correlacionar os eventos com os bytes conhecidos na região `0x01626B–0x01668A`.
7. Guardar capturas/logs suficientes para outra pessoa repetir o experimento.

**Gate D:** pelo menos uma rotina é observada em execução e existe evidência ligando seus dados de entrada a uma região textual conhecida. Se isso não ocorrer, registrar o experimento negativo sem declarar a rotina inacessível.

### Etapa E — Comprovar o mapeamento código → índice → glifo

1. Investigar como a tabela em `0x1A551A` é acessada ou transformada.
2. Localizar dados gráficos candidatos e confirmar sua organização com visualização de tiles, quando aplicável.
3. Construir uma matriz rastreável para os caracteres necessários em português: código de entrada, índice calculado, glifo e evidência.
4. Para `õ, Õ, À, à, ã, é, í, ó, Ó`, distinguir claramente:
   - mapeamento esperado no codec Python;
   - existência de código correspondente na tabela do jogo;
   - existência de glifo apropriado;
   - exibição correta no emulador.
5. Não afirmar que um caractere foi adicionado ao jogo somente porque existe no inventário do teste Python.
6. Reaproveitar glifos/índices apenas quando isso não alterar caracteres originais necessários; considerar alteração da fonte só depois de compreender o lookup e o armazenamento.

**Gate E:** mapeamento de caracteres usado pelo primeiro teste está documentado e é demonstrável na renderização.

### Etapa F — Primeiro teste reversível, ainda sem tradução ampla

Somente depois dos Gates A–E:

1. Escolher uma entrada curta e compreendida.
2. Extrair bytes, controles e terminador.
3. Verificar round-trip byte a byte sem alterações.
4. Preparar uma cópia da entrada em japonês e provar realocação/referência, caso seja necessária.
5. Gerar a primeira ROM de teste apenas numa saída separada.
6. Validar limites, referências, sobreposições e regiões alteradas.
7. Testar no emulador e confirmar que o texto seguinte e o fluxo do jogo continuam funcionando.
8. Só então substituir o texto por uma frase PT-BR e repetir as verificações.

**Gate F — M1: Primeiro Texto PT-BR Executável:** o texto é exibido corretamente, controles e fluxo continuam funcionando, as alterações binárias são auditáveis e a geração é reproduzível.

## 5. Matriz de evidência

Cada candidato ou conclusão relevante deve ser registrado com estes campos:

| Campo | Conteúdo |
|---|---|
| ID / status | ID estável e estado: CONFIRMADO, HIPÓTESE, REFERÊNCIA ou DESCARTADO |
| ROM | Tamanho, CRC32 e SHA-1 |
| Código | Commit e versão do decoder |
| Offset | Endereço/offset e intervalo bruto inspecionado |
| Evidência estática | Bytes, instruções, CFG, chamadores e referências |
| Ferramentas externas | Nome, versão/commit e configuração |
| Evidência dinâmica | PC, registradores, breakpoint/trace e cenário de execução |
| Conclusão | O que a evidência demonstra e o que permanece desconhecido |
| Próximo experimento | A menor verificação capaz de distinguir as hipóteses |

A ausência de resultado deve ser descrita como “não observado pela ferramenta/configuração”, não como prova de inexistência ou inacessibilidade.

## 6. Condições que bloqueiam a escrita da ROM

Não iniciar encoder de produção, realocação nem patch até que:

- [ ] CI esteja verde;
- [ ] discrepância de CFG esteja explicada ou isolada por configuração;
- [ ] a rotina de leitura de pelo menos uma entrada esteja sustentada por evidência estática e/ou dinâmica;
- [ ] o formato da entrada, terminador e controles esteja documentado;
- [ ] a referência da entrada esteja comprovada;
- [ ] código → índice → glifo esteja demonstrado para os caracteres usados;
- [ ] round-trip byte a byte passe;
- [ ] a escrita ocorra somente numa cópia;
- [ ] validação de ponteiros, limites e sobreposição passe;
- [ ] o teste no emulador seja reproduzível.

## 7. Referências externas consultadas

- [sega2asm — Sega Genesis / Mega Drive disassembler and splitter](https://github.com/hansbonini/sega2asm): desassemblagem 68000/Z80, segmentação, charmap TBL, tabelas de ponteiros e extração gráfica. O issue [#2](https://github.com/hansbonini/sega2asm/issues/2) reporta erros em instruções de inicialização; isso reforça a necessidade de comparação independente.
- [Oxore m68k-disasm](https://github.com/Oxore/m68k-disasm): desassemblador 68000 com saída voltada a remontagem e suporte a tabela de PC trace.
- [BlastEm — debugger](https://github.com/libretro/blastem): debugger interativo com breakpoints, execução passo a passo e inspeção de memória/registradores.
- [MAME Debugger documentation](https://docs.mamedev.org/debugger/index.html): debugger interativo, janelas de memória e desassemblagem.
- [Ghidra](https://ghidra-sre.org/): plataforma de engenharia reversa para complementar referências cruzadas e análise de fluxo, condicionada à configuração correta da arquitetura/mapeamento.

Os links são referências de projeto/documentação, não evidência de que as ferramentas tenham sido instaladas ou executadas nesta ROM.

## 8. Próxima sessão recomendada

Ordem de trabalho:

1. corrigir e executar o teste que falha; verificar CI;
2. reproduzir o baseline de CFG;
3. instalar/compilar **uma ferramenta por vez**, começando por sega2asm e Oxore;
4. comparar os intervalos prioritários e registrar diferenças;
5. só então decidir qual debugger usar para o rastreamento dinâmico.

Não adicionar as ferramentas externas como dependências obrigatórias do projeto Python. O avanço deve ser medido por evidência nova, não pelo número de ferramentas instaladas ou de candidatos encontrados.
