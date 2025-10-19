# TP4 — Máquina de Vending

## Autor
<img src="../img/perfil.jpg" alt="Foto de perfil" width="100" align="left">

- **Nome:** Cláudio Ferreira  
- **ID:** A108577  

<br clear="left"/>

---

## Objetivo
Simular uma máquina de vending com **stock persistente em JSON**, aceitando comandos do utilizador:
- `LISTAR` — lista produtos (código, nome, quantidade, preço);
- `MOEDA <lista>` — insere moedas/notas (`1e, 20c, 5c`, também aceita `0.7`);
- `SELECIONAR <CÓDIGO>` — tenta dispensar o produto (verifica saldo e stock);
- `SAIR` — devolve o troco e guarda o stock atualizado em `stock.json`.

---

## Estrutura
```text
TP4/
  README.md
  requirements.txt
  stock.json
  vending/
    __init__.py
    main.py
    money.py
    store.py
```

---

## Execução
```bash
cd TP4
python -m pip install -r requirements.txt   # (ou: python3 -m pip ...)
python -m vending.main
```

---

## Sessão de exemplo
```text
maq: 2025-10-19, Stock carregado, Estado atualizado.
maq: Bom dia. Estou disponível para atender o seu pedido.
>> LISTAR
maq:
cod  nome         quantidade  preço
---- ------------ ----------  -----
A23  água 0.5L    8           0.70
B10  sumo lata    5           1.20
C05  bolacha      10          0.50
>> MOEDA 1e, 20c, 5c, 5c
maq: Saldo = 1e30c
>> SELECIONAR A23
maq: Pode retirar o produto dispensado "água 0.5L"
maq: Saldo = 60c
>> SAIR
maq: Pode retirar o troco: 1x 50c e 1x 10c.
maq: Até à próxima
```

---

## Notas

- **Moedas e valores:** trabalhamos sempre em **cêntimos** (inteiros). Exemplos: `130 -> 1e30c`, `60 -> 60c`.
- **Comando `MOEDA`:** aceita `1e`, `20c`, `2e 50c`, `0.7` ou `0,7` (vírgulas/; opcionais).
- **Troco:** cálculo guloso com moedas euro padrão; saída legível (ex.: `1x 50c e 1x 10c`).
- **Comandos principais:** `LISTAR`, `MOEDA <...>`, `SELECIONAR <CÓDIGO>`, `SAIR`.  
  *(Opcional)* `ADICIONAR COD;NOME;QUANT;PRECO` para repor/introduzir artigos.
- **Persistência:** `stock.json` é carregado no arranque e gravado ao **SAIR**.
- **Mensagens:** respostas da máquina começam por `maq:`; erros comuns tratados (formato de moeda, produto inexistente/esgotado, saldo insuficiente).
- **Compatibilidade:** Python 3.11+, funciona em Windows/Linux/macOS sem dependências externas.
