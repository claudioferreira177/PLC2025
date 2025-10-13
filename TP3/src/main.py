import sys
from .lexer import build_lexer

def tokenize(text: str):
    lex = build_lexer()
    lex.input(text)
    toks = []
    while True:
        tok = lex.token()
        if not tok: break
        toks.append((tok.type, tok.value))
    return toks

def main():
    if len(sys.argv) < 2:
        print("Uso: python -m src.main <ficheiro>")
        raise SystemExit(2)
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    for ttype, tval in tokenize(text):
        shown = tval.replace("\n","\\n") if isinstance(tval,str) else tval
        print(f"{ttype}\t{shown}")

if __name__ == "__main__":
    main()
