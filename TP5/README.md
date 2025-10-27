# TP5 — Analisador Léxico e Sintático (Expressões)

## Autor
<img src="../img/perfil.jpg" alt="Foto de perfil" width="100" align="left">

- **Nome:** Cláudio Ferreira  
- **ID:** A108577  

<br clear="left"/>

---

## Objetivo
Implementar um analisador **léxico** e **sintático** para expressões aritméticas com inteiros e parênteses.  
Operadores: `+ - * /` (com **menos unário**) e `()`.

---

## Gramática (informal)
```text
E → E + T | E - T | T
T → T * F | T / F | F
F → -F | ( E ) | INT
```

---

## Execução
```bash
cd TP5
python -m pip install -r requirements.txt
python -m src.main tests/inputs/ok1.txt
```

---

### Saída (exemplo)
- Lista de **tokens** reconhecidos (tipo/lexema/posição)
- Resultado **parse: OK** (com valor avaliado) ou **erro** detalhado

```text
TOKENS:
  INT(3) at 1:1
  PLUS(+) at 1:3
  INT(4) at 1:5
PARSE: OK → valor = 7
```


