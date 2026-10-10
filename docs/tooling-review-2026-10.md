# Revisão técnica das ferramentas do projeto

**Data da revisão:** 10/10/2026  
**Escopo:** ferramentas presentes no repositório, scripts de uso, documentação e integração com a bancada Python.  
**Limitação:** revisão estática do conteúdo versionado no GitHub. Os executáveis não foram iniciados, os resultados não foram reproduzidos localmente nesta revisão e a ROM não foi modificada.

## Resumo executivo

O repositório contém uma cadeia de ferramentas mais completa do que a bancada por si só: Atlas 1.06 modificado, `slayer1_dumper`, `font_packer`, `asm68`, `xkas_gbc`, scripts BAT de dump/inserção, tabelas de caracteres, scripts de texto, arquivos binários auxiliares e código Python de análise.

A melhor estratégia é **integrar e validar a cadeia existente**, sem criar um inserter alternativo prematuramente. O projeto já tem os elementos para catalogar os TXT, preservar diretivas e preparar uma cópia para revisão; falta tornar a passagem entre a bancada e o formato Atlas nativo explícita e testada.

## Inventário e papel provável

| Ferramenta/artefato | Papel indicado pelos arquivos | Avaliação / ação |
|---|---|---|
| Atlas 1.06 modificado | Inserção guiada por scripts, tabelas de ponteiros/índices, PC e diretivas próprias | Prioridade alta. Identificar a versão exata e validar o formato nativo dos scripts. Não enviar o catálogo JSON/CSV diretamente ao Atlas. |
| `slayer1_dumper.exe` e fontes C++ | Dump e codificação/decodificação específica do jogo | Prioridade alta para auditoria. O próprio projeto registra pressupostos de layout e caminhos de inserção; usar cópias e testar uma amostra pequena. |
| `font_packer.exe` e fonte C++ | Dump/inserção de bitmap/fonte | Necessário para avaliar acentos e glifos PT-BR. A presença do executável não prova que ele aceite novos caracteres sem ajustar tabelas e tiles. |
| `asm68.exe` | Assemblagem 68000 usada pelo conjunto de scripts | Só usar se o fluxo comprovadamente exigir patches ASM. Validar a saída e manter o binário original de entrada. |
| `xkas_gbc.exe` | Assembler incluído no pacote | Plataforma indicada pelo nome é Game Boy Color; não assumir que seja necessário para Mega Drive. Confirmar se algum script do projeto o chama antes de mantê-lo na cadeia. |
| `insert TEXT.bat` | Executa Atlas sobre a ROM nomeada e os scripts `script_*.txt` | **Risco alto de escrita**: não executar com a ROM original. O script processa muitos arquivos individualmente e redireciona logs. Criar cópia de teste, verificar caminhos e automatizar preflight. |
| `dump TEXT.bat` | Cria pastas e chama `slayer1_dumper` com operações de dump | Testar em cópia e registrar os arquivos gerados, encoding e logs. |
| `insert BINARY.bat`, `insert FONT.bat`, `insert ASM.bat` | Inserção de recursos binários, fonte e ASM | Tratar como etapas independentes e opcionais até validar a necessidade. Fazer cópia de entrada e saída por etapa. |
| Tabelas `slayer1_table.txt` e `table/` | Mapeamento de códigos/caracteres | Comparar com a tabela de caracteres da ROM e com os glifos disponíveis. Não acrescentar acentos sem conhecer o mapeamento de bytes/tile. |
| Scripts `text/script_*.txt` | Entradas nativas para o fluxo Atlas | São o ponto de integração mais importante. Preservar diretivas, comentários, índices, ponteiros e preenchimentos. |
| Python `translation_catalog.py` | Normalização JSON/CSV, metadados e QA textual | Útil como camada de edição; QA atual não confirma limites físicos, codificação ou inserção. |
| Python `text/translation_workbench.py` | Exporta linhas japonesas dos TXT e aplica catálogo em diretório separado | Útil para round-trip de revisão. Usa CP932 como encoding de origem padrão e UTF-8 como saída padrão de revisão; isso não prova que UTF-8 seja aceito pelo Atlas. |
| Python `text/script_codec.py` | Inspeção estrutural de bytes Shift-JIS e controles | Ferramenta auxiliar; não é encoder/inserter definitivo. |
| Analisadores ROM/ponteiros/68000 | Investigação de lacunas | Manter como apoio. Não promover candidatos estatísticos a estruturas confirmadas sem evidência. |

## Evidências importantes encontradas

1. `ferramentas/readme.txt` descreve o pacote como ferramenta de Dragon Slayer: Legend of Heroes I, com Atlas 1.06 modificado, dumper e font packer.
2. `ferramentas/tools/dump TEXT.bat` chama `slayer1_dumper DUMP_FILE` e `DUMP_STRINGS` usando uma cópia da ROM nomeada no comando.
3. `ferramentas/tools/insert TEXT.bat` executa Atlas sobre a ROM nomeada e dezenas de scripts `text/script_XX.txt`; portanto, é um fluxo de inserção com efeito de escrita, não um validador inofensivo.
4. `ferramentas/journal.txt` registra uso de Shift-JIS, tabelas de tradução de códigos para tiles, múltiplos tipos de fonte, scripts fragmentados e dados/controles embutidos. Essas notas são documentação histórica do pacote e precisam ser confirmadas contra a ROM e o conjunto de scripts atual.
5. O código Python atual consegue exportar e aplicar traduções por arquivo/linha com verificação do hash e do texto de origem, mas essa saída é uma cópia textual de revisão; a compatibilidade com a sintaxe nativa do Atlas ainda precisa de um teste real.

## Melhorias recomendadas por prioridade

### P0 — Segurança e reprodutibilidade

- Nunca executar scripts de inserção apontando para a ROM original.
- Criar um diretório de build por execução com cópia-base identificada por tamanho, CRC32 e SHA-1.
- Registrar em manifesto: ferramentas e versões, comando, hashes de entrada/saída, arquivos alterados e logs.
- Antes de inserir, confirmar que todos os scripts referenciados existem e que a pasta de saída é distinta da entrada.
- Fazer backup automático da ROM de teste e interromper o pipeline em caso de erro de qualquer ferramenta.
- Não versionar ROMs, executáveis redistribuíveis ou dumps protegidos sem verificar permissões/licença.

### P1 — Adaptador Atlas ↔ catálogo

- Identificar formalmente a sintaxe dos `script_*.txt` reais, incluindo diretivas de ponteiro, índices, comentários, includes e macros customizadas.
- Criar um adaptador que atualize somente o texto traduzível dentro do script original, preservando byte a byte todo o restante quando possível.
- Rejeitar alterações se o texto de origem não corresponder ao hash registrado no catálogo.
- Gerar diff legível e relatório das entradas ignoradas, duplicadas, ausentes ou alteradas.
- Adicionar fixtures pequenas derivadas de scripts reais, sem incluir ROM ou dados proprietários desnecessários.
- Testar ida e volta: script → catálogo → script, exigindo que a versão sem tradução seja idêntica à original.

### P1 — Codificação e fonte PT-BR

- Verificar a codificação real de cada arquivo TXT e não assumir que todos usam o mesmo codec.
- Fazer uma matriz dos caracteres necessários em PT-BR: á, à, â, ã, é, ê, í, ó, ô, õ, ú, ç, maiúsculas, pontuação e símbolos.
- Comparar tabela de caracteres, fonte/tile e rotina de renderização antes de decidir se algum glifo pode ser reutilizado ou precisa ser criado.
- Validar representabilidade antes de gravar CP932 ou qualquer codec do jogo; nunca substituir caracteres silenciosamente.
- Renderizar uma tela de teste com todos os caracteres necessários antes de traduzir grandes lotes.

### P2 — Qualidade da tradução

- Adicionar glossário versionado para nomes próprios, lugares, itens, magias e termos recorrentes.
- Registrar contexto e decisões de tradução por entrada.
- Melhorar QA para distinguir tags de controle de texto literal entre sinais de menor/maior.
- Incluir validação de duplicidade de IDs, campos obrigatórios, origem alterada e placeholders.
- Adicionar comparação de versões, autosave/recuperação e exportação de pendências.

### P3 — Automação de build

- Orquestrar primeiro apenas leitura/dump e QA.
- Adicionar execução das ferramentas externas por subprocesso somente depois de mapear seus argumentos e efeitos.
- Executar cada etapa em pasta temporária isolada, com timeout, captura de stdout/stderr e verificação do código de saída.
- Fazer checksum e diff binário entre ROM-base e ROM de teste.
- Rodar smoke test no emulador e manter screenshots/logs como artefatos locais da build.

## Plano de validação proposto

1. Escolher um script nativo pequeno com pelo menos um marcador e uma tradução.
2. Registrar seu hash e confirmar que o texto original aparece no jogo.
3. Gerar catálogo a partir do TXT sem modificar a origem.
4. Aplicar uma tradução de teste a uma cópia de saída.
5. Comparar o script resultante: somente os segmentos textuais esperados podem mudar.
6. Confirmar a sintaxe de Atlas e executar a inserção somente sobre uma cópia de ROM.
7. Inspecionar logs, tamanho, CRC32/SHA-1 e diff binário.
8. Testar no emulador o diálogo alterado, o diálogo seguinte e o fluxo de jogo adjacente.
9. Repetir com acentos e casos de texto maior antes de escalar.

## Conclusão

A principal oportunidade não é adicionar mais ferramentas aleatórias: é construir uma ponte segura, reversível e testada entre a bancada Python e os scripts Atlas já existentes. A prioridade imediata é auditar o script nativo e a tabela de caracteres, preparar um fixture pequeno e validar o round-trip sem tocar na ROM original.
