# Manual da bancada de tradução

## Finalidade

A bancada Python existe para editar e revisar traduções PT-BR. Ela **não substitui** o dumper, o Atlas ou as ferramentas de fonte e não transforma automaticamente um catálogo em uma ROM pronta.

## Iniciar

Instale as dependências de desenvolvimento e abra o catálogo:

```powershell
python -m pip install -e ".[dev]"
dslayer-ptbr-gui --catalog translation/catalog.json
```

Alternativa:

```powershell
python -m dragonslayer_ptbr.translation_gui --catalog translation/catalog.json
```

Use o caminho real do catálogo do seu checkout; não sobrescreva os dumps originais.

## Funcionalidades documentadas

- lista de entradas e indicação de pendências;
- busca por ID, arquivo, texto de origem, tradução ou contexto;
- filtro de entradas pendentes;
- origem em modo somente leitura e campo de tradução;
- persistência em catálogo JSON;
- importação de formatos genéricos JSON/CSV;
- exportação CSV UTF-8;
- QA textual e verificação de marcadores.

## Importação

O importador genérico reconhece listas JSON, objetos com chaves comuns como `entries`, `texts` ou `strings`, e CSV com cabeçalhos. Entre os nomes de campo reconhecidos estão `source`, `original`, `japanese`, `text`, `original_text`, `jp`, `translation`, `translated`, `portuguese`, `pt_br` e `target`.

Isso não significa suporte universal a formatos proprietários. Antes de declarar um dump compatível, valide uma amostra real e confirme que todos os campos importantes foram preservados.

Para catalogar TXT Atlas, existe o módulo `dragonslayer_ptbr.text.translation_workbench`. Ele seleciona linhas com caracteres japoneses e não é um parser completo da gramática Atlas. Não use sua saída como script de inserção sem um adaptador validado.

## Regras de edição

1. Altere somente o texto que foi identificado como traduzível.
2. Preserve diretivas, índices, ponteiros, comentários, preenchimentos e controles.
3. Preserve os marcadores inline exatamente e na mesma ordem.
4. Siga o glossário aprovado para nomes, lugares, itens, personagens e magias.
5. Não invente limites de caracteres ou bytes; eles precisam ser verificados no formato e na tela reais.
6. Mantenha dumps originais intactos e trabalhe em cópias.

## O que o QA significa

O QA textual pode detectar tradução ausente e divergências de marcadores. Um resultado aprovado **não** comprova que:

- os caracteres acentuados existam na fonte;
- a codificação final seja válida;
- o texto caiba na caixa;
- ponteiros e limites estejam corretos;
- Atlas aceite a saída;
- a ROM funcione no emulador.

JSON e CSV são formatos de trabalho. A exportação para inserção precisa devolver os textos ao formato nativo da ferramenta externa.

## Estado registrado

Um checkpoint anterior documentou 11.037 entradas, um teste manual de salvamento persistente, 111 testes aprovados e Ruff sem erros. Esses resultados são históricos e não foram reexecutados nesta atualização documental. Também não comprovam a inserção de texto no jogo.

## Próximo teste técnico

1. Fixar versão e comando da ferramenta que gerou um script Atlas real.
2. Escolher uma amostra pequena com texto e controles.
3. Implementar um adaptador que substitua somente os segmentos traduzíveis.
4. Exigir round-trip sem tradução e comparar os bytes do script.
5. Só então inserir uma tradução em uma cópia separada da ROM e validar no emulador.
