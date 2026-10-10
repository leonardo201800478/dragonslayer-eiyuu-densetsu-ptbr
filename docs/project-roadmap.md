# Roadmap revisado do projeto

## Objetivo

Concluir uma tradução PT-BR com uma experiência de trabalho clara e segura, aproveitando as ferramentas de terceiros que já extraem os textos. O código Python não deve duplicar recursos externos sem necessidade: sua função é conectar o fluxo, facilitar a tradução/adaptação e validar as lacunas que restarem.

## Fase 1 — Fixar o fluxo externo real

- registrar nome, versão e comandos das ferramentas efetivamente usadas;
- guardar exemplos pequenos de entrada e saída, sem adicionar ROM ou conteúdo protegido ao Git;
- documentar como controles, diretivas, offsets e IDs são representados;
- identificar qual ferramenta, se alguma, importa/reinsere os textos;
- separar as etapas que já funcionam das etapas manuais.

**Gate 1:** existe uma amostra real e reproduzível do dump e a equipe sabe qual ferramenta é responsável por cada operação.

## Fase 2 — Bancada de tradução PT-BR

Implementado nesta etapa:
- interface desktop Tkinter;
- importação de JSON/CSV com campos comuns;
- normalização em catálogo JSON;
- lista de entradas, busca e filtro de pendências;
- edição de tradução com a origem em modo somente leitura;
- salvamento, exportação CSV e QA de marcadores.

Próximas melhorias:
- glossário editável para nomes, lugares, itens, magias e termos recorrentes;
- notas de contexto e decisões de tradução;
- comparação de versões e identificação de entradas alteradas;
- autosave e proteção contra perda de alterações;
- apoio à revisão por lotes e exportação de pendências.

**Gate 2:** a equipe consegue traduzir e revisar um lote real sem alterar o dump original e sem perder marcadores ou metadados.

## Fase 3 — Adaptadores de ida e volta

- implementar adaptadores específicos, não heurísticas genéricas, para o formato real de cada ferramenta;
- preservar comentários, comandos, offsets, alinhamento e campos desconhecidos;
- verificar integridade do texto de origem antes de aplicar traduções;
- testar round-trip em fixtures pequenas;
- impedir que um catálogo de revisão seja confundido com um arquivo pronto para inserção.

**Gate 3:** um pequeno conjunto traduzido volta ao formato nativo e é aceito pela ferramenta externa em uma cópia de teste.

## Fase 4 — Adaptação linguística e visual PT-BR

- estabelecer glossário de nomes próprios, locais, itens, personagens, magias e sistemas;
- definir convenções de pontuação, tratamento, pronomes e tom;
- testar acentos e caracteres disponíveis na fonte real;
- avaliar comprimento em bytes e largura visual por contexto, sem impor limites não comprovados;
- registrar alternativas quando a frase em português não couber.

**Gate 4:** tradução aprovada linguisticamente e representável pela fonte/codec real, com restrições visuais documentadas.

## Fase 5 — Inserção e validação do jogo

Só avançar quando a ferramenta de inserção e seu formato estiverem confirmados:
- operar em cópia de ROM com hash conhecido;
- gerar saída separada;
- revisar diff binário e referências;
- iniciar no emulador e testar os diálogos modificados, controles e mensagens seguintes;
- manter procedimento reproduzível para regenerar a ROM de teste.

**Gate 5:** o texto PT-BR aparece corretamente no jogo e as rotinas próximas continuam funcionais.

## Ferramentas próprias de engenharia reversa

Os módulos de análise de ROM, tabela de caracteres e código 68000 permanecem no repositório para diagnosticar problemas que os terceiros não resolvam. Eles são ferramentas auxiliares, não a etapa obrigatória anterior a cada tradução.

## Regras permanentes

- ROM original sempre somente leitura e fora do Git.
- Não distribuir ROM, executáveis ou assets de terceiros sem permissão.
- Não afirmar compatibilidade sem teste na versão exata da ferramenta.
- Não perder silenciosamente marcadores, metadados ou dados desconhecidos.
- QA textual não equivale a validação de inserção.
- Preferir logs, fixtures pequenas e testes automatizados.


## Atualização de progresso — 10/10/2026

### Verificado
- A bancada Tkinter abriu um catálogo de **11.037 entradas**.
- Uma tradução de teste foi salva e persistiu após fechar e reabrir a interface.
- O QA da entrada testada não detectou divergências nos marcadores.
- Os testes locais concluíram com **111 aprovados**.
- `ruff check .` retornou `All checks passed!`.

### Ainda não concluído
- Confirmar a pasta, versão e formato nativo da ferramenta que gerou os TXT/dumps.
- Executar aplicação das traduções em cópia separada dos scripts reais.
- Demonstrar round-trip para o formato esperado pela ferramenta externa.
- Verificar suporte a caracteres PT-BR, limites de tamanho e largura visual.
- Gerar uma ROM de teste apenas quando o método de inserção estiver comprovado, e testar no emulador.

A entrada usada na interface foi um teste de persistência, não uma tradução confirmada dentro do jogo. O QA textual não deve ser interpretado como aprovação para inserção na ROM.
