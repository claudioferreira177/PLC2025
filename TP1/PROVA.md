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

Juntando tudo, com âncoras para casar a **linha inteira**: ^1*(?:0(?:0|10)*(?:1)?)?$


## Aceites/Rejeitados
Aceites: `""` (vazia), `1`, `111`, `0`, `00`, `001`, `01`, `010`, `1010`, `1001`, `101010`.  
Rejeitados: `011`, `1011`, `0011`, `11011`, `000011`, `101011`.

## DFA mínimo
Estados = maior sufixo da entrada que é também prefixo de `011`:
- `q0` (ε), `q1` (`0`), `q2` (`01`), `q3` (dead/erro — já vimos `011`).
Transições:
- `q0 --0--> q1`, `q0 --1--> q0`
- `q1 --0--> q1`, `q1 --1--> q2`
- `q2 --0--> q1`, `q2 --1--> q3`
- `q3 --0/1--> q3`
Aceites: `q0, q1, q2`. Rejeita: `q3`.

Ficheiro DOT: [`dfa.dot`](./dfa.dot).

