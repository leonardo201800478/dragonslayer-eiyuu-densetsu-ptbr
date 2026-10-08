# Dragon Slayer: Eiyuu Densetsu — Tradução PT-BR

Projeto comunitário para organizar uma tradução em português brasileiro de **Dragon Slayer: Eiyuu Densetsu**, na versão de Mega Drive, e disponibilizar ferramentas Python para aplicar patches em cópias legais do jogo.

> **Estado:** estrutura inicial. Ainda não há tradução, offsets verificados ou patch do jogo neste repositório.

## O que este projeto inclui

- Uma ferramenta Python para aplicar alterações binárias descritas em um manifesto JSON.
- Verificação dos bytes originais em cada offset antes de gravar, para evitar aplicar um patch sobre uma ROM inesperada.
- Validação de limites, tamanho e sobreposição das alterações.

A ferramenta é genérica: ela **não extrai textos automaticamente** nem presume conhecer o formato interno do jogo. Os offsets, a codificação de texto e as rotinas de compressão/controle precisam ser pesquisados e documentados antes de criar patches específicos.

## Requisitos

- Python 3.10 ou superior
- Uma cópia da ROM obtida legalmente. A ROM não é distribuída aqui e não deve ser enviada ao repositório.

## ROM original local

Coloque sua cópia legal da ROM em `roms/original/`. Essa pasta contém instruções e é ignorada pelo Git, portanto a ROM não será incluída em commits. Consulte `roms/original/README.md` antes de adicionar arquivos.

O código deste repositório está sob a licença MIT (`LICENSE`). Ela não licencia a ROM nem concede direitos sobre o jogo ou outros materiais de terceiros.

## Instalação e uso

Na raiz do projeto:

```bash
python -m pip install .
python -m dragon_slayer_ptbr apply --rom roms/original/jogo.bin --manifest translation/patch.json --output jogo-ptbr.bin
```

A ferramenta nunca sobrescreve o arquivo de entrada. Se os bytes encontrados não corresponderem aos bytes originais declarados, a execução falha e nenhum arquivo de saída é gerado.

## Formato do manifesto

Cada alteração especifica o offset em decimal e os bytes originais e substitutos em hexadecimal. Os bytes substitutos devem ter o mesmo comprimento dos bytes originais; expansões de texto exigem uma estratégia específica do jogo e não são suportadas por esta base.

```json
{
  "patches": [
    {
      "offset": 256,
      "original": "414243",
      "replacement": "58595A",
      "description": "Exemplo ilustrativo — não é texto do jogo"
    }
  ]
}
```

O manifesto de exemplo real do repositório está vazio em `translation/patch.json`: não representa uma tradução aplicável.

## Desenvolvimento e testes

```bash
python -m pip install -e ".[dev]"
pytest
```

## Como contribuir

1. Documente a origem e a versão da ROM usada na pesquisa, mas nunca publique a ROM ou seus dados.
2. Registre apenas offsets e dados mínimos necessários ao patch; valide cada alteração em uma cópia local da sua ROM.
3. Descreva a codificação, limitações de espaço, ponteiros e qualquer rotina específica que tenha sido confirmada.
4. Inclua testes para alterações e casos de incompatibilidade.
5. Não envie dumps de texto, imagens, músicas, scripts ou outros materiais protegidos sem autorização.

Contribuições de código neste repositório são licenciadas sob MIT (veja `LICENSE`). Essa licença não concede direitos sobre o jogo, marcas ou materiais protegidos de terceiros.
