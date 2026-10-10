# Arquitetura de integração e validação

## Decisão central

Reutilizar as ferramentas específicas do jogo e escrever Python somente para o trabalho que falta: bancada de tradução, normalização, QA, adaptadores e automação segura. Não construir um inserter alternativo enquanto Atlas puder cumprir essa função.

A documentação do repositório identifica Atlas 1.06 modificado, `slayer1_dumper`, `font_packer`, `asm68`, `xkas_gbc` e scripts BAT. A presença desses arquivos não comprova que todos sejam necessários nem que todos funcionem no ambiente atual.

## Divisão de responsabilidades

| Componente | Responsabilidade | Limite atual |
|---|---|---|
| `slayer1_dumper` | Dump e operações específicas do jogo | Validar versão, parâmetros, codificação e comportamento real |
| Atlas 1.06 modificado | Inserção por scripts, diretivas, índices e ponteiros | Formato nativo deve ser preservado; ainda falta validar o round-trip com a bancada |
| `font_packer` | Processamento de recursos de fonte | Não há prova de que os glifos PT-BR necessários estejam disponíveis |
| `asm68` / `xkas_gbc` | Montagem de código quando exigida pelo fluxo | Não executar nem incluir na build sem identificar a dependência concreta |
| Bancada Python | Edição, busca, persistência e revisão | Não é inserter de ROM |
| Catálogo Python | Formato de trabalho normalizado | Não é formato nativo Atlas |
| Classificador/auditor Atlas | Inventário lexical de marcadores | Não executa diretivas, não calcula ponteiros e não prova semântica |
| Analisadores 68000 | Investigar lacunas técnicas | Resultados exploratórios não são prova de rotina de texto |

## Pipeline pretendido

```text
ROM original (somente leitura)
  → ferramenta externa de dump
  → script/dump nativo + metadados
  → adaptador Python
  → catálogo de tradução
  → QA e revisão humana
  → exportador para o formato nativo
  → preflight de scripts e diretivas
  → ferramenta externa de inserção em ROM de teste
  → hashes, diff binário e logs
  → validação no emulador
```

Não se deve passar JSON/CSV genérico diretamente ao Atlas. O adaptador precisa operar sobre amostras reais dos scripts nativos e preservar todo o conteúdo que não seja explicitamente traduzível.

## Gates de validação

### Gate A — Dump reproduzível

Registrar ferramenta e versão, sistema operacional, comando, hash da entrada, codificação, formato e arquivos de saída. A extração deve ser reproduzível numa cópia de trabalho.

### Gate B — Round-trip do script

- Preservar diretivas, índices, ponteiros, comentários, preenchimentos e metadados.
- Bloquear aplicação quando o texto de origem tiver mudado desde a importação.
- Testar script → catálogo → script sem tradução.
- Comparar bytes antes/depois e explicar cada diferença.

### Gate C — Texto PT-BR representável

- Criar matriz dos caracteres usados pela tradução.
- Verificar tabela de caracteres, fonte e tiles reais.
- Rejeitar caracteres não representáveis em vez de substituí-los silenciosamente.
- Testar quebra de linha e textos longos em exemplos pequenos.

### Gate D — Inserção isolada

- Verificar o hash da ROM-base e criar cópia separada.
- Validar todos os arquivos e caminhos antes de executar ferramentas.
- Interromper em erro e guardar logs.
- Calcular tamanho, CRC32, SHA-1 e diff binário.
- Confirmar que a ROM original permanece inalterada.

### Gate E — Funcionamento no jogo

Confirmar início do jogo, texto traduzido visível, controles preservados, página seguinte e diálogos adjacentes. A aprovação de testes Python não substitui esta validação.

## Segurança operacional

- Nunca executar `ferramentas/tools/insert TEXT.bat` contra a ROM original.
- Não automatizar os BATs antes de confirmar todos os caminhos, efeitos de escrita e códigos de saída.
- Não versionar ROMs, executáveis ou dumps protegidos sem verificar licença e permissões.
- Manter artefatos de build fora do catálogo de tradução e da árvore de fontes.
- Registrar resultados como **confirmado**, **hipótese** ou **pendente**.

## Evidências técnicas atuais

O baseline documentado da ROM é 2 MiB, CRC32 `01BC1604` e SHA-1 `F67C9139BBC93F171E274A5CD3FBA66480CD8244`. Há texto Shift-JIS em regiões conhecidas e controles misturados ao texto. Esses dados ajudam a validar o fluxo, mas não provam que o catálogo atual seja compatível com o Atlas.

O estado histórico documentado da bancada registra 11.037 entradas, 111 testes aprovados e Ruff sem erros. Isso não demonstra que a tradução tenha sido inserida ou exibida no jogo.

## Próxima ação técnica

Implementar somente o adaptador mínimo entre uma fixture de script Atlas real e o catálogo. A primeira meta é um round-trip sem tradução. Não expandir a investigação de 68000, fonte ou caixas até que esse teste mostre uma limitação concreta que exija pesquisa adicional.
