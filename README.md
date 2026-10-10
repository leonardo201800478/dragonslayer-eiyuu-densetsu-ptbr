# Dragon Slayer: Eiyuu Densetsu — tradução PT-BR

Projeto para traduzir e adaptar ao português brasileiro a versão japonesa de **Dragon Slayer: Eiyuu Densetsu (Mega Drive)**.

**Princípio de arquitetura:** reutilizar as ferramentas específicas do jogo para extração, fonte e inserção. O Python deve cuidar da bancada de tradução, da integração entre formatos, do QA e da automação segura que ainda não exista nas ferramentas externas.

A ROM original não é distribuída pelo repositório. Nenhuma etapa de inserção deve apontar para ela.

## Estado real do projeto

- A bancada Tkinter e o catálogo de tradução estão implementados.
- A documentação registra um catálogo de trabalho com 11.037 entradas e uma execução anterior com 111 testes aprovados e Ruff sem erros. Esses números são históricos e não substituem uma execução no checkout atual.
- O projeto contém scripts Atlas, `slayer1_dumper` e `font_packer`.
- **Ainda não está comprovado** o ciclo completo catálogo → script Atlas → ROM de teste → texto visível no emulador.
- O suporte a todos os caracteres PT-BR e a expansão de caixas/limites de texto continua em investigação.

Veja [o estado e as próximas etapas](docs/project-roadmap.md) e [o fluxo técnico e os critérios de validação](docs/third-party-tooling-and-validation-plan.md).

## Responsabilidades

### Ferramentas externas

- Extrair scripts e metadados no formato específico do jogo.
- Executar a inserção de texto e recursos quando o fluxo tiver sido validado.
- Processar fontes/tiles com o empacotador existente, se ele suportar os glifos necessários.

A presença de um executável não prova que ele seja necessário, compatível ou seguro para todas as etapas. Não executar scripts de inserção contra a ROM original.

### Código Python

- Oferecer a interface de tradução e manter o catálogo.
- Preservar IDs, metadados e conteúdo não traduzível.
- Validar marcadores, campos obrigatórios, alterações de origem e caracteres não representáveis.
- Integrar o catálogo aos scripts nativos Atlas por um adaptador testado.
- Orquestrar builds isoladas, logs, hashes e relatórios de diferenças.
- Investigar internamente o formato do jogo somente quando as ferramentas externas não responderem a uma questão necessária.

O catálogo JSON e o CSV são formatos de trabalho; não são, por si só, formatos de inserção.

## Requisitos

- Python 3.10 ou superior.
- Windows recomendado para o conjunto legado de ferramentas.
- Tkinter disponível na instalação do Python.

## Instalação e verificações

No PowerShell, na raiz do repositório:

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
ruff check .
```

## Abrir a bancada

```powershell
dslayer-ptbr-gui --catalog translation/catalog.json
```

Alternativa:

```powershell
python -m dragonslayer_ptbr.translation_gui --catalog translation/catalog.json
```

Use o caminho do catálogo de trabalho que existe no seu checkout. Não sobrescreva dumps originais; mantenha cópias de trabalho e backups.

## Fluxo de trabalho

1. Extrair os textos usando a ferramenta externa documentada.
2. Importar uma amostra real para a bancada.
3. Traduzir e revisar sem modificar o dump de origem.
4. Exportar para o formato nativo Atlas usando o adaptador específico.
5. Comparar o script antes/depois e bloquear alterações inesperadas.
6. Executar as ferramentas de inserção somente sobre uma cópia da ROM.
7. Validar checksum, diff binário, início do jogo, diálogo alterado e diálogos seguintes.
8. Registrar ferramentas, versões, comandos e resultados.

Não declarar a tradução pronta até que o último passo seja demonstrado no emulador.

## Documentação

- [Roadmap e estado atual](docs/project-roadmap.md)
- [Arquitetura e validação com ferramentas externas](docs/third-party-tooling-and-validation-plan.md)
- [Bancada de tradução](docs/translation-workbench.md)
- [Auditoria segura das ferramentas](docs/tooling-audit.md)
- [Classificador lexical Atlas](docs/atlas-segment-classifier.md)
- [Engenharia reversa do texto](docs/reverse-engineering.md)
- [Investigação das caixas de diálogo](docs/dialog-box-expansion-investigation.md)

## Segurança e distribuição

Não versionar ROMs, dumps protegidos ou executáveis de terceiros sem confirmar permissões e licenças. Os relatórios devem distinguir claramente fatos confirmados, hipóteses e tarefas pendentes.
