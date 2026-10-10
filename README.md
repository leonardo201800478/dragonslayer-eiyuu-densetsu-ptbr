# Dragon Slayer: Eiyuu Densetsu — PT-BR

Projeto para traduzir e adaptar ao português brasileiro a versão japonesa de **Dragon Slayer: Eiyuu Densetsu (Mega Drive)**, usando ferramentas de terceiros para as tarefas que elas já executam e código Python próprio para integrar o fluxo, facilitar a tradução e validar os resultados.

A ROM original permanece local e **não é distribuída pelo repositório**.

## Nova divisão de responsabilidades

### Ferramentas de terceiros
Use as ferramentas externas já empregadas no projeto para extrair os scripts e, quando comprovadamente suportado, executar operações específicas do formato do jogo. O projeto não deve duplicar um dumper, assembler, empacotador ou inserter que já funcione para esse fluxo.

As ferramentas locais conhecidas incluem Atlas, slayer1_dumper, font_packer, asm68 e xkas_gbc. A presença desses arquivos não prova que todos sejam necessários ou compatíveis com cada etapa. Registre ferramenta, versão, parâmetros e formato gerado. Não execute operações de escrita contra a ROM original.

### Código Python do projeto
- importar e normalizar dumps de terceiros para um catálogo de tradução;
- oferecer uma interface desktop simples para tradução e adaptação PT-BR;
- preservar e validar marcadores inline, comandos e metadados disponíveis;
- apoiar glossário, revisão, busca, filtros e relatórios de QA;
- exportar materiais para revisão e devolver os arquivos ao fluxo externo somente conforme o formato suportado pela ferramenta usada;
- manter os analisadores 68000 próprios como ferramentas auxiliares para investigar lacunas, não como requisito para traduzir textos já extraídos.

**Importante:** o catálogo normalizado e o CSV exportado são formatos de trabalho. Eles não são automaticamente arquivos prontos para reinserção na ROM.

## Começar

Requisitos: Python 3.10 ou superior; no Windows, a instalação padrão do Python normalmente inclui Tkinter.

    python -m pip install -e ".[dev]"
    python -m pytest -q
    ruff check .

### Abrir a interface de tradução

    dslayer-ptbr-gui --catalog translation/catalog.json

Ou, sem instalar o comando:

    python -m dragonslayer_ptbr.translation_gui --catalog translation/catalog.json

Na interface, use **Importar dump JSON/CSV** para normalizar um dump estruturado de terceiros. Os nomes de campos mais comuns são reconhecidos, como source, original, japanese, text, translation, translated, pt_br e id. O importador não consegue inferir todos os formatos proprietários; adapte o mapeamento quando o formato da ferramenta for diferente.

### Dumps de texto em arquivos TXT

Para as ferramentas que exportam diretivas e texto em arquivos TXT, use o catalogador existente:

    python -m dragonslayer_ptbr.text.translation_workbench export --source-dir ".\ferramentas\text" --catalog ".\translation\catalog.json"

Ajuste --source-dir para a pasta real produzida pela ferramenta. O catalogador legado procura linhas com texto japonês e preserva a linha completa para revisão.

### Revisar e validar

- Edite a tradução no campo PT-BR, mantendo marcadores como <LINE>, <WAIT>, <COLOR 1E> e demais diretivas na mesma ordem.
- Use busca e o filtro de pendências para organizar o trabalho.
- Clique em **Validar catálogo** para gerar translation-qa-report.json.
- Exporte CSV quando precisar revisar em planilha ou fazer a ponte com outro processo.
- Salve cópias de trabalho; não sobrescreva dumps originais de terceiros.

O QA atual verifica presença de tradução e sequência de marcadores. Ele **não** confirma largura da caixa, suporte aos acentos na fonte, codificação final, limites de bytes, ponteiros ou funcionamento no emulador.

## Estado técnico do jogo

A análise prévia registrou uma ROM japonesa de 2 MiB, CRC32 01BC1604 e SHA-1 F67C9139BBC93F171E274A5CD3FBA66480CD8244. Shift-JIS foi identificado em regiões textuais e controles binários aparecem misturados aos scripts. Esses achados continuam úteis para diagnóstico, mas não são pré-requisitos para trabalhar nos textos que as ferramentas externas já extraíram.

O mapeamento de caracteres PT-BR, os limites de texto e a compatibilidade de reinserção precisam ser verificados com a ferramenta real e o jogo. Não assumir que CP932, UTF-8 ou uma tradução com os marcadores preservados será aceita pelo inserter.

## Documentação

- [Bancada de tradução](docs/translation-workbench.md)
- [Plano de ferramentas de terceiros e validação](docs/third-party-tooling-and-validation-plan.md)
- [Auditoria segura das ferramentas locais](docs/tooling-audit.md)
- [Revisão técnica de todas as ferramentas](docs/tooling-review-2026-10.md)
- [Resultados técnicos anteriores](docs/analysis-results.md)
- [Engenharia reversa auxiliar](docs/reverse-engineering.md)
- [Roadmap revisado](docs/project-roadmap.md)

## Princípios do projeto

1. Reutilizar ferramentas externas comprovadas em vez de reimplementar o que elas já fazem.
2. Não executar ferramentas de terceiros sem conhecer seus efeitos e arquivos de entrada/saída.
3. Nunca modificar a ROM original; operar em cópias verificadas.
4. Preservar diretivas, controles e metadados durante a tradução.
5. Não marcar uma tradução como pronta para ROM apenas porque o QA textual passou.
6. Documentar claramente quais formatos são suportados e quais ainda precisam de um adaptador específico.


## Estado verificado da bancada (10/10/2026)

- A interface Tkinter foi aberta com um catálogo de **11.037 entradas**.
- Uma tradução de teste foi salva e permaneceu preenchida após fechar e reabrir a bancada.
- O QA da entrada de teste informou que não havia divergências de marcadores.
- Na cópia de trabalho validada localmente, `python -m pytest -q` concluiu com **111 testes aprovados** e `ruff check .` retornou **All checks passed!**.
- A correção dos três avisos TRY004 em `translation_catalog.py` foi publicada na branch de trabalho.

Essas verificações confirmam o funcionamento básico da bancada e a qualidade estática do código nesse checkout. **Ainda não confirmam** o round-trip com uma ferramenta externa, a aceitação do texto pelo inserter, a renderização de caracteres PT-BR ou a execução da ROM traduzida. A tradução usada na interface foi apenas um teste de persistência, não uma validação dentro do jogo.
