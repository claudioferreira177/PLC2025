import sys
from .lexer import build_lexer

TYPES_ONLY = {
    "SELECT","WHERE","LIMIT","A",
    "LBRACE","RBRACE","LPAREN","RPAREN","DOT","SEMI","COMMA","STAR",
}

def _show(v):
    if not isinstance(v, str):
        return v
    return (
        v.replace("\\", "\\\\")
         .replace("\r", "\\r")
         .replace("\n", "\\n")
         .replace("\t", "\\t")
    )

def tokenize(text: str):
    lex = build_lexer()
    lex.input(text)
    while True:
        tok = lex.token()
        if not tok:
            break
        yield tok.type, tok.value

def main():
    if len(sys.argv) < 2:
        print("Uso: python -m src.main <ficheiro>")
        raise SystemExit(2)
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    for ttype, tval in tokenize(text):
        if ttype in TYPES_ONLY:
            print(ttype)
        else:
            print(f"{ttype} {_show(tval)}")   # <— espaço simples
if __name__ == "__main__":
    main()
