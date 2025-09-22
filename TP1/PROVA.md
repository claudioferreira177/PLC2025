# Prova / Explicação

## Enunciado
Linguagem de todas as strings em `{0,1}*` que **não têm** a substring `011`.

## Intuição e construção
- Se uma string tiver **apenas 1's** (incluindo a vazia), está sempre OK → `1*`.
- Se tiver **pelo menos um 0**, a partir do **primeiro 0** temos de impedir o padrão proibido `011`.
  - Depois de um `0`, é permitido:
    - outro `0` (ficamos com `00`), ou
    - o bloco `10` (ficamos com `010` e continuamos seguros),
  - e opcionalmente **um `1` final** (…`01`) **no fim da string**.
  - Portanto, depois do primeiro `0`: `0 (0|10)* 1?`
- Antes desse primeiro `0` podemos ter qualquer número de `1`’s: `1*`.

Juntando tudo: ^1*(?:0(?:0|10)*(?:1)?)?$


## Aceites/Rejeitados
Aceites: `""` (vazia), `1`, `111`, `0`, `00`, `001`, `01`, `010`, `1010`, `1001`, `101010`.  
Rejeitados: `011`, `1011`, `0011`, `11011`, `000011`, `101011`.

