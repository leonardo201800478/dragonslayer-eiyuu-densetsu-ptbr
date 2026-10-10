# Roadmap e estado do projeto

## Objetivo

Entregar uma tradução PT-BR funcional de *Dragon Slayer: Eiyuu Densetsu* (Mega Drive), reutilizando Atlas e as ferramentas específicas do jogo. O projeto Python não deve recriar um dumper ou inserter já existente sem uma lacuna comprovada.

## Estado resumido

| Área | Estado | Evidência / próximo passo |
|---|---|---|
| Bancada Tkinter | Implementada | Reexecutar testes no checkout atual |
| Catálogo JSON e importação JSON/CSV genérica | Implementados | Validar com dump real do jogo e preservar metadados |
| Classificação e auditoria lexical de marcadores Atlas | Auxiliar implementado | Não equivale a interpretar a semântica das diretivas |
| Extração por ferramenta externa | Ferramentas presentes | Registrar versão, comando e saída reproduzível |
| Adaptador catálogo ↔ script Atlas nativo | Pendente de validação | Primeiro marco técnico prioritário |
| Fonte e caracteres PT-BR | Pendente | Fazer matriz de glifos e teste visual |
| Inserção em ROM de teste | Não comprovada ponta a ponta | Executar apenas em cópia isolada |
| Validação no emulador | Pendente para tradução PT-BR | Confirmar texto, controles e diálogos subsequentes |
| Expansão de caixa/página | Investigação pendente | Não assumir que seja necessária ou possível antes dos testes de comprimento |

Os documentos registram anteriormente 11.037 entradas, 111 testes aprovados e Ruff sem erros. Esses dados são um checkpoint histórico, não uma afirmação de que os testes atuais foram executados.

## Prioridades

### P0 — Provar o fluxo real antes de ampliar o código

1. Identificar as versões exatas de Atlas e `slayer1_dumper` usadas localmente.
2. Selecionar um script nativo pequeno que contenha texto e ao menos um marcador.
3. Guardar uma fixture mínima e licenciável, sem ROM nem conteúdo desnecessário.
4. Definir quais campos do script podem ser traduzidos e quais devem permanecer idênticos.
5. Criar testes de ida e volta: script → catálogo → script, sem tradução, deve preservar a entrada byte a byte sempre que o formato permitir.

**Critério de conclusão:** round-trip reproduzível, com diff vazio ou diferenças justificadas exclusivamente pela serialização documentada.

### P1 — Tradução e QA

- Revisar os campos normalizados contra um dump real.
- Preservar IDs, metadados, diretivas, comentários, controles e campos desconhecidos.
- Validar caracteres PT-BR contra a tabela e a fonte reais; rejeitar substituições silenciosas.
- Acrescentar glossário e notas de contexto apenas se ajudarem a revisão do texto.
- Produzir relatório de pendências e comparação antes/depois.

**Critério de conclusão:** lote real revisado sem perda de registros ou alterações estruturais não autorizadas.

### P2 — Build de teste segura

- Criar diretório de build separado e registrar hash da ROM de entrada.
- Confirmar a presença dos scripts e arquivos exigidos antes de iniciar.
- Executar as ferramentas externas por etapas, com logs e interrupção em caso de erro.
- Gerar hash e diff da ROM de saída.
- Não permitir que comandos automatizados apontem para a ROM original.

**Critério de conclusão:** build reproduzível e auditável em uma cópia, sem modificar a entrada.

### P3 — Validação no emulador

- Confirmar que o jogo inicia.
- Conferir o diálogo traduzido, os marcadores, a página seguinte e o fluxo adjacente.
- Testar acentos, pontuação e textos maiores.
- Só investigar alteração de fonte, buffer ou caixa quando um caso real demonstrar a necessidade.

**Critério de conclusão:** evidência reproduzível do texto traduzido no jogo, acompanhada de hashes, logs e capturas.

## O que não fazer agora

- Não criar um substituto para Atlas ou `slayer1_dumper` sem provar uma limitação concreta.
- Não interpretar marcadores apenas pelo nome ou pela aparência.
- Não expandir caixas nem alterar ponteiros com base em hipóteses.
- Não executar `insert TEXT.bat` nem outros scripts de inserção sobre a ROM original.
- Não apagar ferramentas de análise só por parecerem experimentais: primeiro verificar referências, testes e utilidade para uma pendência definida.

## Definição de pronto

O projeto não está concluído quando o catálogo salva ou o QA textual passa. Está concluído quando uma tradução passa pelo formato nativo, é inserida numa cópia segura e aparece corretamente no emulador sem quebrar os controles ou diálogos seguintes.
