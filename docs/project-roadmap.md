# Roadmap do projeto

## 1. Objetivo do roadmap

Levar o projeto do estado atual de engenharia reversa até o primeiro **teste controlado de tradução PT-BR**, com uma ROM de teste que:

- mantenha a ROM japonesa original intacta;
- preserve todos os controles necessários;
- não corrompa scripts adjacentes;
- mantenha referências/ponteiros válidos;
- permita iniciar o jogo e atravessar a área traduzida;
- possa ser comparada byte a byte com a ROM original;
- tenha validações automáticas antes de qualquer teste no emulador.

O primeiro teste não será uma tradução completa. Será um **vertical slice mínimo e reversível**, preferencialmente uma pequena sequência de diálogo já totalmente compreendida.

---

## 2. Estado atual

### CONFIRMADO

- ROM japonesa Mega Drive/Genesis com 2 MiB.
- CRC32: `01BC1604`.
- SHA-1: `F67C9139BBC93F171E274A5CD3FBA66480CD8244`.
- Header Mega Drive válido.
- Texto japonês identificado em múltiplas regiões.
- **Shift-JIS confirmado** para os trechos japoneses encontrados.
- Controles binários aparecem misturados ao texto.
- `0x01` está confirmado como separador/quebra na abertura.
- `0x06 xx yy` está confirmado como comando de três bytes, mas sua semântica ainda não foi resolvida.
- `0x0E` aparece como controle.
- `0x00` aparece como terminador em estruturas observadas.
- Tabela explícita de códigos de caracteres em `0x1A551A`, observada até `0x1A62D2`.
- A tabela contém códigos latinos maiúsculos acentuados, mas os minúsculos acentuados portugueses observados não estão presentes.
- Existem 47 regiões fortemente sustentadas como texto japonês.
- O decoder estrutural já consegue atravessar a abertura preservando os controles.

### NÃO RESOLVIDO

- Rotina 68000 definitiva do engine de texto.
- Gramática completa dos controles.
- Limite exato de cada entrada de script.
- Forma como o jogo seleciona cada script.
- Tabela/formato definitivo de ponteiros.
- Relação exata entre código de caractere, índice e glifo.
- Formato completo da fonte.
- Compressão/descompressão, caso exista para algum recurso.
- Estratégia segura de realocação.
- Encoder/importador definitivo.
- Patch PT-BR.

**Regra:** nenhum item não resolvido deve ser convertido em comportamento de escrita da ROM apenas por inferência estatística.

---

## 3. Fases e gates

O projeto será executado em fases. Cada fase possui um **gate de saída**. Só avançamos quando o gate estiver satisfeito.

### Fase 0 — Integridade e baseline

**Objetivo:** garantir que todas as análises futuras partam sempre do mesmo dump.

Tarefas:

- registrar tamanho, CRC32 e SHA-1;
- manter a ROM original fora do Git;
- gerar um baseline imutável;
- garantir que ferramentas de análise são somente leitura;
- executar a suíte de testes Python.

**Gate 0:**

- hashes da ROM conferidos;
- testes passando;
- nenhuma ferramenta de análise modifica a ROM.

---

### Fase 1 — Inventário completo de texto

**Objetivo:** transformar as 47 regiões encontradas em um inventário lógico.

Tarefas:

1. identificar início/fim de cada região;
2. separar entradas individuais;
3. registrar terminadores;
4. registrar todos os controles e suas posições;
5. classificar cada região por contexto:
   - abertura;
   - diálogo;
   - itens;
   - magias;
   - sistema;
   - minijogos;
   - final;
6. detectar padrões de tamanho;
7. produzir um inventário determinístico.

Formato mínimo:

| Região | Entrada | Offset | Tamanho | Contexto | Controles | Terminador |
|---|---|---:|---:|---|---|---|

**Gate 1:**

Uma entrada conhecida pode ser extraída do offset correto e reproduzida exatamente em bytes, incluindo controles e terminador.

---

### Fase 2 — Reconstrução do protocolo de script

**Objetivo:** descobrir como o jogo interpreta os bytes.

Tarefas:

- continuar o inventário de `0x01`, `0x06 xx yy`, `0x0E`, `0x00` e demais bytes de controle;
- comparar os controles entre abertura, diálogos, itens/magias, sistema e minijogos;
- identificar quais comandos têm comprimento fixo ou variável;
- determinar quais comandos alteram posição, fluxo, estado, janela ou apresentação;
- nunca atribuir nomes sem evidência de execução.

A investigação deve chegar a uma gramática semelhante a:

`TEXTO | CONTROLE_1 | CONTROLE_2 | ... | END`

mas os tokens concretos só serão definidos após rastreamento.

**Gate 2:**

Uma entrada completa pode ser tokenizada e reconstruída byte a byte sem perda.

---

### Fase 3 — Localização do engine 68000

**Objetivo:** obter a cadeia de execução que liga script, controles e fonte.

Esta é a principal fase atual.

Tarefas:

1. identificar blocos de código 68000;
2. reconhecer limites básicos por `BSR`, `JSR`, `JMP`, `RTS`;
3. reduzir falsos positivos de regiões de dados;
4. rastrear leituras `MOVE.B`;
5. rastrear origem dos registradores de endereço;
6. seguir transformações de índices:
   - `MOVEQ`;
   - `EXT`;
   - `LSL/ASL`;
   - `MULU`;
   - `ANDI`;
   - `ADDI`;
   - somas com bases;
7. investigar especialmente acessos próximos de `0x1A551A`;
8. rastrear comparações com `0x01`, `0x06), `0x0E) e `0x00);
9. localizar chamadas de subrotinas envolvidas;
10. reconstruir pelo menos uma cadeia completa.

A análise de `MOVE.B (An,Dn.W/L),Dm` deve ser feita apenas dentro de blocos de código identificados, pois o scanner global produz milhares de falsos positivos.

**Gate 3:**

Existe pelo menos uma cadeia comprovada:

`seleção do script → endereço/dado do script → leitura do byte → teste de controle → processamento → acesso à fonte/renderização`.

---

### Fase 4 — Fonte, códigos e encoder

**Objetivo:** transformar a descoberta do engine em um codec seguro.

Tarefas:

- confirmar como o código de caractere é convertido em índice/glifo;
- determinar se a tabela `0x1A551A` é tabela de lookup, repertório, índice ou outra estrutura;
- localizar os glifos;
- determinar como caracteres latinos são renderizados;
- decidir como representar:
  - `á à â ã`;
  - `é ê`;
  - `í`;
  - `ó ô õ`;
  - `ú`;
  - `ç`;
  - maiúsculas correspondentes;
- preferir reaproveitamento de entradas existentes quando isso não quebrar o mapeamento;
- só estender/substituir a tabela se a rotina de lookup e o espaço de armazenamento permitirem.

Depois disso:

- implementar encoder reversível;
- validar `decode(encode(texto)));
- preservar controles;
- rejeitar caracteres sem mapeamento;
- produzir erro explícito em vez de gerar bytes inválidos.

**Gate 4:**

Um conjunto de strings japonesas conhecidas é decodificado e reencodado produzindo exatamente os mesmos bytes originais.

---

### Fase 5 — Ponteiros e seleção de scripts

**Objetivo:** descobrir como cada entrada é localizada pelo jogo.

Tarefas:

- rastrear quem fornece o endereço do script;
- identificar ponteiros absolutos, relativos ou índices, sem assumir formato;
- validar candidatos contra chamadas reais do engine;
- identificar tabelas, bases e offsets;
- mapear cada entrada para sua referência;
- descobrir se scripts estão fragmentados;
- documentar regras de alinhamento e limites.

A análise estatística de ponteiros atual continua sendo somente auxiliar. Os candidatos 16-bit, 24-bit e 32-bit não devem ser promovidos sem confirmação no código.

**Gate 5:**

Para pelo menos um script, deve ser possível:

`ID/contexto → referência real → offset do script → leitura correta → terminador`.

Idealmente, o mecanismo deve funcionar para uma pequena família de scripts antes de qualquer escrita.

---

### Fase 6 — Realocação segura

**Objetivo:** permitir texto maior sem corromper dados adjacentes.

Somente iniciar depois dos Gates 3, 4 e 5.

Tarefas:

1. mapear regiões livres ou recursos que possam ser realocados;
2. definir alinhamento;
3. calcular tamanho físico de cada script;
4. criar allocator determinístico;
5. copiar scripts para novas posições;
6. atualizar somente as referências comprovadamente associadas;
7. gerar mapa:
   - origem;
   - destino;
   - tamanho;
   - referências alteradas;
8. impedir sobreposição;
9. validar todos os destinos dentro da ROM;
10. gerar ROM de teste separada.

Importante: **não assumir ainda que as caixas precisam permanecer do tamanho original**. Primeiro será necessário saber como o renderer determina largura, altura, quebra e posicionamento.

**Gate 6:**

Uma cópia de um script, ainda em japonês, pode ser realocada e executada exatamente como antes.

Esse é um teste crítico: prova que a infraestrutura de inserção funciona antes de introduzir tradução.

---

### Fase 7 — Primeiro vertical slice PT-BR

**Objetivo:** realizar o primeiro teste de tradução real com risco mínimo.

Escolha:

- uma pequena entrada;
- controles totalmente conhecidos;
- ponteiro conhecido;
- encoder validado;
- espaço de destino controlado.

Procedimento:

1. extrair a entrada original;
2. criar tradução PT-BR;
3. preservar controles;
4. codificar;
5. verificar tamanho;
6. realocar somente se necessário;
7. corrigir a referência;
8. gerar ROM de teste;
9. comparar estrutura original × modificada;
10. validar automaticamente;
11. abrir no emulador;
12. executar exatamente o fluxo que usa a entrada.

O primeiro teste deve ser pequeno o suficiente para que qualquer diferença possa ser auditada manualmente.

**Gate 7 — primeiro teste seguro:**

- ROM inicializa;
- jogo entra normalmente;
- entrada traduzida é exibida;
- controles continuam funcionando;
- texto seguinte continua correto;
- não há travamento;
- nenhuma região não relacionada foi alterada;
- checksum/hash da ROM de teste é registrado;
- patch/diff da alteração é reproduzível.

---

### Fase 8 — Expansão para diálogos e dados de jogo

Depois do primeiro vertical slice:

- ampliar para outras entradas;
- validar nomes;
- validar itens;
- validar magias;
- validar mensagens de sistema;
- validar minijogos;
- validar final;
- construir testes específicos por contexto;
- identificar limites de caixa e largura;
- avaliar necessidade de VWF somente se o renderer demonstrar essa limitação.

---

### Fase 9 — Pipeline completo de tradução

Quando a infraestrutura estiver comprovada:

`ROM original`
→ `extract`
→ `translation/`
→ `encode`
→ `allocate`
→ `patch references`
→ `validate`
→ `ROM de teste`

Cada etapa deverá ser determinística e reproduzível.

---

## 4. Critérios de segurança antes da primeira tradução

Não será permitido gerar a primeira ROM traduzida enquanto qualquer um destes itens estiver sem solução:

- [ ] formato real do script conhecido;
- [ ] terminador conhecido;
- [ ] controles preservados;
- [ ] limites das entradas conhecidos;
- [ ] rotina de leitura identificada;
- [ ] método de seleção do script identificado;
- [ ] referência/ponteiro de pelo menos uma entrada comprovado;
- [ ] encoder reversível;
- [ ] mecanismo de escrita isolado da ROM original;
- [ ] realocação testada em japonês, se necessária;
- [ ] validação de sobreposição;
- [ ] validação de referências;
- [ ] ROM original preservada;
- [ ] teste automatizado cobrindo a transformação.

---

## 5. Estratégia de testes

### Testes unitários

Cobrir:

- Shift-JIS de 1 byte;
- Shift-JIS de 2 bytes;
- controles;
- terminador;
- caracteres inválidos;
- tabela de caracteres;
- encoder/decoder;
- limites de região;
- ponteiros;
- allocator.

### Testes de round-trip

Para cada entrada conhecida:

`bytes originais → decode → encode → bytes originais`

Resultado esperado: **igualdade byte a byte**.

### Testes de patch

Para uma ROM de teste:

- verificar tamanho;
- verificar regiões modificadas;
- verificar que somente os offsets esperados foram alterados;
- verificar que nenhum destino aponta para fora da ROM;
- verificar que nenhum bloco foi sobreposto.

### Teste no emulador

O teste manual só começa depois de os testes binários passarem.

A sequência deve ser registrada por contexto, por exemplo:

1. inicialização;
2. entrada no fluxo;
3. exibição da mensagem;
4. avanço;
5. mensagem seguinte;
6. saída da janela;
7. continuação do jogo.

---

## 6. Regra para expansão de texto

O projeto não adotará ainda um limite artificial de tamanho igual ao japonês.

Existem três níveis:

### Nível A — mesma área

Usar quando a tradução cabe no espaço original.

### Nível B — realocação

Usar quando o texto cresce, mas o renderer continua compatível.

### Nível C — alteração do renderer

Somente se a largura/altura da janela, quebra automática, fonte ou VWF forem realmente limitantes.

A ordem é deliberada: **primeiro resolver armazenamento e referências; depois alterar apresentação**.

---

## 7. Marco de entrada na tradução

O projeto estará oficialmente pronto para iniciar a tradução de testes quando o seguinte fluxo estiver funcional:

`extract`
→ `decode`
→ `edit PT-BR`
→ `encode`
→ `allocate`
→ `patch`
→ `validate`
→ `build test ROM`

E, para pelo menos uma entrada:

`ROM japonesa`
→ `extrator`
→ `texto`
→ `tradução`
→ `ROM modificada`
→ `execução no emulador`
→ `continuação normal do jogo`.

Esse será o **Marco M1 — Primeiro Texto PT-BR Executável**.

---

## 8. Próxima tarefa imediata

A próxima tarefa técnica deve ser a **Fase 3 — localização do engine 68000**, começando por:

1. identificar blocos de código;
2. filtrar os `MOVE.B (An,Dn.W/L),Dm` para esses blocos;
3. rastrear origem de `An) e `Dn);
4. cruzar com testes de `0x01`, `0x06`, `0x0E) e `0x00);
5. rastrear chamadas `JSR/BSR);
6. procurar a primeira cadeia que conecte script e tabela `0x1A551A);
7. documentar candidatos com classificação **CONFIRMADO / REFERÊNCIA / HIPÓTESE / DESCARTADO**.

Não iniciar ainda encoder de escrita, realocação ou patch da ROM.
