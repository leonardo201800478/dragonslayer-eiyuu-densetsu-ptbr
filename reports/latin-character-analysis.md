# Análise dos caracteres latinos

A ROM analisada contém uma tabela de caracteres em `0x1A551A`.

A faixa observada até `0x1A62D2` possui **1756 entradas de 16 bits**.

## Resultado para PT-BR

A tabela já contém códigos latinos de um byte na faixa `0xC0–0xDF`, incluindo:

`À Á Â Ã Ç É Ê Í Ó Ô Õ Ú`

Os minúsculos acentuados necessários não aparecem na tabela:

`à á â ã ç é ê í ó ô õ ú`

Isso é importante porque demonstra que o formato interno não pode ser tratado como Shift-JIS puro em todas as situações. Há uma tabela proprietária que contém códigos japoneses de dois bytes e códigos latinos de um byte.

## Consequência para a tradução

Existem duas estratégias tecnicamente plausíveis:

1. **Reaproveitar entradas da tabela** que não sejam necessárias ao jogo e associá-las aos códigos `E0–FF`, adicionando os glifos correspondentes.
2. **Estender a tabela/fonte**, caso a rotina de busca exija uma quantidade ou organização fixa de entradas.

A primeira alternativa é potencialmente a mais simples, mas só deve ser aplicada depois de localizar a rotina 68000 que consulta a tabela. Não devemos substituir um código japonês apenas porque ele não apareceu nas 47 regiões textuais detectadas.

## Próxima investigação

A prioridade passou a ser:

```
código do texto
    ↓
rotina de conversão/busca
    ↓
índice da tabela
    ↓
endereço do glifo
    ↓
renderização
```

Somente após confirmar essa cadeia será criado o patch de fonte.
