# Bancada de tradução dos scripts

Este módulo cria um catálogo editável em UTF-8 a partir dos arquivos .txt gerados pelas
ferramentas legadas. Ele preserva os comandos Atlas e os marcadores inline na cópia de
trabalho, valida que a fonte não mudou desde a exportação e nunca modifica a pasta original.

## Estado e limites

- **Confirmado:** os dumps legados contêm diretivas Atlas, texto japonês e marcadores como
  <LINE>, <COLOR 1E>, <WAIT CLEAR> e comandos de fluxo.
- **Implementado:** exportação para JSON UTF-8, aplicação por arquivo/linha, verificação
  SHA-256 da linha original e validação da sequência de marcadores <...>.
- **Ainda não confirmado:** compatibilidade de arquivos traduzidos com Atlas, codificação
  final esperada pelo Atlas, mapeamento dos caracteres PT-BR para os glifos da ROM,
  limites de tamanho e reinserção funcional.
- A saída padrão de apply é UTF-8 para revisão humana; **não deve ser tratada como pronta
  para inserção na ROM**. A opção CP932 só funciona quando todos os caracteres podem ser
  representados nessa codificação, e isso não comprova compatibilidade com a fonte ou a
  tabela de caracteres do jogo.

## 1. Exportar o catálogo

Aponte --source-dir para a pasta text extraída pelo dumper legado:

    python -m dragonslayer_ptbr.text.translation_workbench export --source-dir ".\reports\legacy-tooling-test\tools\text" --catalog ".\translation\catalog.json"

Abra translation/catalog.json no VS Code. Cada entrada tem um ID por caminho e linha,
texto original, tradução, hash da fonte, marcadores inline e status. Preencha apenas
translation; preserve todos os marcadores <...> exatamente na mesma ordem.

Exemplo de entrada:

    {
      "id": "script_0F.txt:42",
      "file": "script_0F.txt",
      "line": 42,
      "source": "こんにちは<LINE>",
      "translation": "Olá<LINE>",
      "source_sha256": "...",
      "tags": ["<LINE>"],
      "status": "PENDENTE"
    }

## 2. Gerar uma cópia de revisão

Use uma pasta de saída nova ou vazia:

    python -m dragonslayer_ptbr.text.translation_workbench apply --source-dir ".\reports\legacy-tooling-test\tools\text" --catalog ".\translation\catalog.json" --output-dir ".\reports\translation-preview"

O comando informa quantas traduções foram aplicadas e quantas entradas continuam pendentes.
Ele aborta se o texto original mudou, se os marcadores foram alterados ou se a pasta de saída
já contém arquivos. A pasta de origem permanece intacta.

## Regras para tradução

1. Traduza somente o texto natural; não traduza diretivas #WRITE, #FILL, #W08BYTE,
   #WRITEINDEX, comentários de offsets nem comandos de fluxo.
2. Preserve marcadores como <LINE>, <WAIT>, <WAIT CLEAR>, <COLOR 1E>, <CLEAR>, <JMP.L>
   e <$XX> exatamente como aparecem.
3. Não remova nem acrescente linhas. A ferramenta aplica uma tradução por linha de origem.
4. Nomes próprios, locais, itens e magias devem seguir o glossário do projeto.
5. Não execute comandos de inserção contra a ROM original. A saída desta bancada é material
   de tradução/revisão, não uma ROM corrigida.

## Próximo marco técnico

Antes de gerar arquivos para Atlas, precisamos confirmar a codificação de entrada do Atlas,
a tabela de caracteres ativa e a representação dos caracteres PT-BR. Depois, adicionaremos
um validador de tamanho por bloco e um importador compatível com o formato de inserção real.
