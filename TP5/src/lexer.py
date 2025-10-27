import ply.lex as lex

# ------------------------
# Tokens
# ------------------------
tokens = (
    "INT",
    "PLUS", "MINUS", "TIMES", "DIVIDE",
    "LPAREN", "RPAREN",
)

t_PLUS   = r'\+'
t_MINUS  = r'-'
t_TIMES  = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'

# ignorar espaços e tabs
t_ignore = ' \t'

def t_INT(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    # coluna aproximada (mantemos simples para este TP)
    col = (t.lexpos - getattr(t.lexer, "line_start", 0)) + 1
    raise SyntaxError(f"[lexer] caractere inesperado '{t.value[0]}' na linha {t.lexer.lineno} coluna {col}")

# ------------------------
# Helper para construir lexer
# ------------------------
def build_lexer(**kwargs):
    lexer = lex.lex(reflags=lex.re.UNICODE, **kwargs)
    # marcar início da linha para cálculo de colunas
    lexer.line_start = 0

    orig_input = lexer.input
    def _input(data: str):
        lexer.lineno = 1
        lexer.line_start = 0
        orig_input(data)
    lexer.input = _input

    orig_token = lexer.token
    def _token():
        tok = orig_token()
        if tok:
            # atualizar início da linha para a coluna correta
            prev_nl = tok.lexer.lexdata.rfind('\n', 0, tok.lexpos)
            lexer.line_start = 0 if prev_nl < 0 else prev_nl + 1
        return tok
    lexer.token = _token

    return lexer

