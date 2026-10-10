# Plano de ferramentas de terceiros e validação

**Decisão de arquitetura:** reutilizar as ferramentas de terceiros para extração e operações específicas do formato quando já funcionarem; desenvolver em Python apenas a camada de integração, a experiência de tradução/adaptação PT-BR e as validações que não forem cobertas por elas.

## 1. Responsabilidades

### Ferramentas externas

As ferramentas externas são responsáveis pelas tarefas para as quais foram criadas, desde que a versão usada tenha sido validada no projeto:
- extrair os textos e metadados;
- representar controles/diretivas segundo seu próprio formato;
- empacotar fonte/recursos quando isso já fizer parte do fluxo suportado;
- reinserir scripts somente se a ferramenta documentar e comprovar essa capacidade para os arquivos do jogo.

As ferramentas locais já inventariadas incluem Atlas, slayer1_dumper, font_packer, asm68 e xkas_gbc. Não assumir que todas participam do fluxo de tradução ou que qualquer uma possa reinserir os dumps sem transformação. Registrar versões, comandos, entradas, saídas e hashes. Não executar binários desconhecidos nem operar sobre a ROM original.

### Python do projeto

O Python deve fornecer:
- importação/normalização de dumps JSON e CSV comuns;
- catalogação de TXT de ferramentas já suportadas;
- interface desktop para busca, tradução, adaptação e revisão;
- validação de marcadores e consistência dos registros;
- glossário e regras linguísticas do projeto;
- relatórios de QA e comparação antes/depois;
- adaptadores de ida e volta para formatos externos quando existir amostra real e teste de round-trip.

A análise própria de ROM/68000 continua disponível como ferramenta auxiliar para resolver lacunas não cobertas pelo dumper. Ela deixa de ser bloqueio para a tradução dos textos que já foram extraídos.

## 2. Fluxo-alvo

    ROM original (somente leitura)
        -> ferramenta externa validada
        -> dump nativo da ferramenta
        -> adaptador Python / catálogo de trabalho
        -> tradução e adaptação PT-BR
        -> QA textual e revisão humana
        -> exportação no formato nativo, se suportada
        -> ferramenta externa de reinserção, se comprovada
        -> ROM de teste separada
        -> validação binária e em emulador

O catálogo normalizado não é, por si só, um formato de inserção. Não assumir compatibilidade de Atlas, CP932, UTF-8, comandos, limites ou ponteiros sem teste explícito.

## 3. Registro obrigatório por ferramenta

Para cada ferramenta efetivamente usada, manter:
- nome e versão/commit;
- sistema operacional e dependências;
- comando executado e parâmetros;
- hash da ROM de entrada;
- caminho e formato da saída;
- tratamento de diretivas, controles e metadados;
- possibilidade comprovada de importação/reinserção;
- limitações, erros conhecidos e licença.

Os executáveis e a ROM original não devem ser adicionados ao Git sem autorização/licença apropriada. Os testes Python devem funcionar sem instalar ferramentas externas e sem precisar da ROM.

## 4. Gates de validação

### Gate A — Dump utilizável
- dump real da ferramenta armazenado localmente;
- formato, codificação e marcadores identificados;
- amostra pequena reproduzível;
- origem mantida intacta.

### Gate B — Tradução sem perda estrutural
- catálogo normalizado preserva ID, arquivo/linha, texto e metadados disponíveis;
- marcadores e comandos permanecem na mesma ordem;
- dados desconhecidos não são descartados silenciosamente;
- o QA reporta pendências e divergências.

### Gate C — Round-trip para ferramenta externa
- existe um formato de entrada documentado;
- o adaptador devolve os textos ao formato esperado;
- campos não traduzíveis e comandos são preservados;
- a extração/serialização repetida não altera dados não relacionados;
- a ferramenta externa aceita o resultado em uma cópia de teste.

### Gate D — Inserção e execução
- ROM de entrada validada por hash;
- saída em caminho separado;
- diff binário explicado;
- checksum e tamanho verificados;
- jogo inicia e o texto traduzido aparece;
- controles, mensagens seguintes e fluxos relacionados continuam funcionais.

## 5. Situação técnica preexistente

A ROM de referência registrada no projeto tem 2 MiB, CRC32 01BC1604 e SHA-1 F67C9139BBC93F171E274A5CD3FBA66480CD8244. Shift-JIS foi identificado em regiões textuais e há controles binários misturados ao texto. Essas evidências continuam úteis para validar o comportamento das ferramentas, mas não justificam reimplementar a extração já realizada.

## 6. Limites atuais

A interface implementada normaliza dumps JSON/CSV comuns e oferece catalogação de TXT pelo fluxo anterior. Ainda não existe adaptador universal para formatos proprietários. O nome e a versão exata da ferramenta externa, com um exemplo de dump real, são necessários antes de declarar suporte específico ou automatizar a reinserção.

Não marcar qualquer saída como pronta para ROM apenas porque os marcadores passaram no QA textual.
