import sys
from pathlib import Path
from datetime import date

from .money import parse_money_list, fmt_cents, make_change, fmt_change
from .store import Store

BANNER_DATE = date.today().isoformat()

def print_table(rows):
    if not rows:
        print("maq: (stock vazio)")
        return
    headers = ("cod", "nome", "quantidade", "preço")
    widths = [max(len(h), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]
    fmt = "  ".join(f"{{:{w}}}" for w in widths)
    print("maq:")
    print(fmt.format(*headers))
    print("-" * (sum(widths) + 2*(len(widths)-1)))
    for r in rows:
        print(fmt.format(*r))

def main():
    base = Path(__file__).resolve().parents[1]
    stock_path = base / "stock.json"
    store = Store(stock_path)

    try:
        store.load()
        print(f"maq: {BANNER_DATE}, Stock carregado, Estado atualizado.")
    except Exception as e:
        print(f"maq: {BANNER_DATE}, Aviso: não foi possível carregar o stock ({e}). A iniciar vazio.")
        store.save()

    saldo = 0
    print("maq: Bom dia. Estou disponível para atender o seu pedido.")

    while True:
        try:
            line = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            line = "SAIR"

        if not line:
            continue

        cmd, *rest = line.split(maxsplit=1)
        cmd = cmd.upper()
        arg = rest[0] if rest else ""

        if cmd == "LISTAR":
            print_table(store.table_rows())

        elif cmd == "MOEDA":
            try:
                inc = parse_money_list(arg)
                saldo += inc
                print(f"maq: Saldo = {fmt_cents(saldo)}")
            except Exception:
                print("maq: Formato de moeda inválido. Use, por exemplo: MOEDA 1e, 20c, 5c")

        elif cmd == "SELECIONAR":
            cod = arg.strip().upper()
            if not cod:
                print("maq: Indique o código do produto. Ex.: SELECIONAR A23")
                continue
            item = store.find(cod)
            if not item:
                print("maq: Produto inexistente.")
                continue
            if item.quant <= 0:
                print("maq: Produto esgotado.")
                continue
            preco = item.preco_cents
            if saldo < preco:
                print("maq: Saldo insuficiente para satisfazer o seu pedido")
                print(f"maq: Saldo = {fmt_cents(saldo)}; Pedido = {fmt_cents(preco)}")
                continue
            # efetuar venda
            item.quant -= 1
            saldo -= preco
            print(f'maq: Pode retirar o produto dispensado "{item.nome}"')
            print(f"maq: Saldo = {fmt_cents(saldo)}")

        elif cmd == "SAIR":
            if saldo > 0:
                change = make_change(saldo)
                print(f"maq: Pode retirar o troco: {fmt_change(change)}.")
            print("maq: Até à próxima")
            # persistir stock
            try:
                store.save()
            finally:
                return

        # Extra (opcional): reposição rápida via linha
        elif cmd == "ADICIONAR":
            # Formato: ADICIONAR COD;NOME;QUANT;PRECO
            try:
                cod, nome, quant, preco = [p.strip() for p in arg.split(";")]
                quant = int(quant)
                preco = float(preco)
                store.add_or_update(cod, nome, quant, preco)
                print(f"maq: Produto {cod} atualizado/adicionado.")
            except Exception:
                print("maq: Uso: ADICIONAR COD;NOME;QUANT;PRECO")

        else:
            print("maq: Comando desconhecido. Use LISTAR | MOEDA <...> | SELECIONAR <CÓDIGO> | SAIR")

if __name__ == "__main__":
    main()

