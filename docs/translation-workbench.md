# Bancada de tradução e adaptação PT-BR

## Objetivo

As ferramentas externas continuam sendo a fonte dos dumps e, quando compatível, da reinserção. Esta bancada não substitui Atlas, dumper ou inserter: normaliza formatos comuns para facilitar a tradução, mantém metadados disponíveis e executa QA textual.

## Interface desktop

Instale o projeto e abra um catálogo:

    python -m pip install -e ".[dev]"
    dslayer-ptbr-gui --catalog translation/catalog.json

Ou execute:

    python -m dragonslayer_ptbr.translation_gui --catalog translation/catalog.json

A interface inclui:
- lista de entradas com indicação de pendência;
- busca por ID, arquivo, origem, tradução ou contexto;
- filtro de entradas pendentes;
- painel de origem somente leitura e campo de tradução;
- salvamento de catálogo JSON;
- importação de dumps estruturados JSON/CSV;
- exportação CSV UTF-8;
- relatório de QA textual.

## Importar dados de ferramentas externas

Na interface, escolha **Importar dump JSON/CSV**. A importação reconhece listas JSON ou objetos contendo entries, texts ou strings, além de CSV com cabeçalhos. Campos de origem reconhecidos: source, original, japanese, text, original_text e jp. Campos de tradução reconhecidos: translation, translated, portuguese, pt_br e target. Para IDs, reconhece id, key, label e name.

O importador preserva os campos originais de cada registro e acrescenta os campos normalizados source, translation, tags, source_sha256 e status. Isso permite manter metadados do dumper quando estão presentes. Formatos proprietários ou estruturas diferentes exigirão um adaptador específico; não presumir que todos os dumps são reconhecidos.

Para diretórios de TXT com diretivas Atlas, o catalogador anterior continua disponível:

    python -m dragonslayer_ptbr.text.translation_workbench export --source-dir ".\ferramentas\text" --catalog ".\translation\catalog.json"

Ajuste o caminho à saída real do dumper. O catalogador TXT atual seleciona linhas com caracteres japoneses; linhas compostas apenas por diretivas ou outros alfabetos podem precisar de um adaptador adicional.

## Regras de tradução

1. Traduza somente o texto natural. Não traduza diretivas Atlas, comentários, offsets ou comandos de fluxo.
2. Preserve os marcadores inline exatamente e na mesma ordem, por exemplo <LINE>, <WAIT>, <WAIT CLEAR>, <COLOR 1E>, <CLEAR>, <JMP.L> e <$XX>.
3. Preserve os nomes próprios, locais, itens, personagens e magias conforme o glossário do projeto.
4. Adapte a frase ao português brasileiro natural, em vez de fazer tradução literal quando isso comprometer clareza ou espaço.
5. Não invente limite de caracteres ou bytes: a largura da caixa e o formato físico precisam ser medidos no fluxo real.
6. Mantenha os dumps originais intactos e trabalhe em catálogos/cópias.

## QA e limites

O QA verifica se a tradução está preenchida, se a sequência de marcadores é idêntica e se há sinais básicos de texto inválido. O relatório inclui rom_insertion_ready=false deliberadamente.

Passar no QA não comprova:
- suporte a acentos pela fonte ou tabela de caracteres;
- comprimento em bytes no formato final;
- largura visual ou quebra de linha;
- validade de ponteiros e limites;
- aceitação pelo inserter;
- funcionamento no emulador.

A saída normalizada JSON/CSV é material de trabalho humano. Para devolver os textos à ferramenta externa, é necessário usar o formato de entrada que essa ferramenta documenta ou criar um adaptador testado para ela. Não alimentar o Atlas ou outro inserter com o catálogo normalizado sem conversão explícita.

## Próximas melhorias

- adaptadores específicos para os formatos reais usados pelo projeto, depois de fixar versões e exemplos de entrada/saída;
- glossário editável integrado à interface;
- validação de tamanho e largura quando as regras da ferramenta e da caixa forem conhecidas;
- diff de alterações e verificação de hash da origem;
- exportação de volta ao formato de origem com teste de round-trip;
- testes automatizados contra fixtures pequenas, sem ROM proprietária no repositório.


## Estado de verificação atual

Verificação manual registrada em 10/10/2026:

- a interface abriu o catálogo com **11.037 entradas**;
- uma tradução de teste foi salva, a aplicação foi fechada e a tradução continuou presente após reabertura;
- o QA da entrada selecionada informou que não havia divergências de marcadores;
- a suíte local concluiu com **111 testes aprovados**;
- `ruff check .` concluiu com `All checks passed!`.

Isso valida o salvamento básico e os testes automatizados no checkout usado. Não significa que todas as 11.037 entradas foram revisadas, nem que o catálogo possa ser inserido diretamente na ROM. A aplicação em cópia dos TXT, a exportação para o formato nativo da ferramenta externa e o teste no emulador continuam pendentes.

### Próximo teste reproduzível

1. Identificar a pasta e a versão exatas da ferramenta que produziu os TXT e registrar um pequeno exemplo real.
2. Manter os TXT originais intactos e exportar um catálogo de teste.
3. Aplicar uma tradução somente em uma cópia de saída, verificando identidade das entradas e preservação dos marcadores.
4. Comparar a saída com o formato esperado pela ferramenta externa; não presumir que JSON/CSV normalizado seja aceito diretamente.
5. Só depois de confirmar o adaptador, testar a ferramenta externa em uma cópia separada e, por fim, validar visualmente no emulador.
