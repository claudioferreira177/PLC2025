import sys
from pathlib import Path
from .lexer import build_lexer
from .parser import Parser

def dump_tokens(text: str):
    lex = build_lexer()
    lex.input(text)
    print("TOKENS:")
    while True:
        tok = lex.token()
        if not tok:
            break
        col = (tok.lexpos - lex.line_start) + 1
        val = tok.value
        print(f"  {tok.type}({val}) at {tok.lineno}:{col}")

def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("usage: python -m src.main <input-file>")
        return 2
    path = Path(argv[0])
    text = path.read_text(encoding="utf-8")
    try:
        dump_tokens(text)
        parser = Parser()
        value = parser.parse(text)
        print(f"PARSE: OK \u2192 valor = {value}")
        return 0
    except Exception as e:
        print(str(e))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
