# Auditoria segura das ferramentas locais

Este procedimento inventaria o pacote `ferramentas/` e verifica a identidade da ROM sem executar binários de terceiros e sem escrever na ROM.

## Executar

Na raiz do repositório, com o ambiente virtual ativado:

```powershell
python -m dragonslayer_ptbr.tooling_audit --tools-dir ferramentas --rom "caminho/para/ROM.bin" --output reports/tooling-audit.json
python -m pytest tests/test_tooling_audit.py -q
ruff check src/dragonslayer_ptbr/tooling_audit.py tests/test_tooling_audit.py
```

A ROM esperada é identificada por tamanho de 2 MiB, CRC32 `01BC1604` e SHA-1 `F67C9139BBC93F171E274A5CD3FBA66480CD8244`. Divergência significa apenas que o arquivo não corresponde ao baseline esperado; não se deve substituir os hashes esperados para fazer o teste passar.

## O que a auditoria verifica

- presença dos executáveis conhecidos (Atlas, slayer1_dumper, font_packer, asm68 e xkas_gbc);
- arquivos presentes na pasta de ferramentas;
- sinais no fonte do `slayer1_dumper` de escrita direta na ROM e de offsets/intervalos rígidos;
- tamanho, CRC32 e SHA-1 da ROM opcional.

## Limites e segurança

A auditoria é estática: **não executa** `.exe`, `.bat`, Atlas, assemblers ou o dumper. A presença de um arquivo não comprova compatibilidade com o sistema operacional nem com esta revisão da ROM. O dumper legado tem caminhos de inserção que abrem a ROM para escrita e pressupostos específicos de layout; não o execute sobre a ROM original.

O relatório é um inventário, não uma validação da extração ou da recompressão. A validação funcional ainda exige comparar saídas em uma cópia de trabalho, provar a reversibilidade dos bytes e inspecionar a ROM resultante antes de qualquer teste em emulador.
