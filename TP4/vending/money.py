from typing import List, Tuple

# valores em cêntimos (moedas/notas aceites para troco)
COINS = [200, 100, 50, 20, 10, 5, 2, 1]

def parse_money_list(text: str) -> int:
    """
    Converte uma lista textual de moedas/notas para total em cêntimos.
    Exemplos válidos (vírgulas ou espaços opcionais):
      "1e, 20c, 5c"  -> 125
      "2e 50c"       -> 250
      "0.7"          -> 70
    Aceita 'e'/'E' para euros, 'c'/'C' para cêntimos. Ignora espaços.
    """
    if not text:
        return 0
    total = 0
    # aceitar separadores ',' ou ';' (espelhos do enunciado)
    parts = [p.strip() for p in text.replace(";", ",").split(",") if p.strip()]
    if not parts:
        # também aceitar listas separadas por espaços sem vírgulas
        parts = text.split()

    for p in parts:
        s = p.strip().lower()
        if not s:
            continue
        if s.endswith("e"):                 # euros inteiros: "1e"
            total += int(s[:-1]) * 100
        elif s.endswith("c"):               # cêntimos: "20c"
            total += int(s[:-1])
        else:
            # número livre com ponto/virgula decimal: "0.7" ou "0,7"
            s = s.replace(",", ".")
            total += int(round(float(s) * 100))
    return total

def fmt_cents(n: int) -> str:
    """
    Formata cêntimos:
      0   -> '0c'
      60  -> '60c'
      130 -> '1e30c'
      200 -> '2e'
    Suporta negativos (para mensagens internas, se necessário).
    """
    sign = "-" if n < 0 else ""
    n = abs(n)
    euros, cents = divmod(n, 100)
    if euros and cents:
        return f"{sign}{euros}e{cents}c"
    if euros:
        return f"{sign}{euros}e"
    return f"{sign}{cents}c"

def make_change(cents: int) -> List[Tuple[int, int]]:
    """
    Decompõe 'cents' em (moeda, quantidade) por estratégia gulosa.
    Ex.: 72 -> [(50,1),(20,1),(2,1)]
    """
    change: List[Tuple[int, int]] = []
    remaining = cents
    for coin in COINS:
        q, remaining = divmod(remaining, coin)
        if q:
            change.append((coin, q))
    return change

def fmt_change(change: List[Tuple[int, int]]) -> str:
    """
    Formata a lista de troco em string legível:
      [(50,1),(20,1),(2,2)] -> '1x 50c, 1x 20c e 2x 2c'
      [] -> '0c'
    """
    if not change:
        return "0c"
    parts = [f"{q}x {fmt_cents(c)}" for c, q in change]
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " e " + parts[-1]

