import re
import ply.lex as lex

tokens = (
    "SELECT","WHERE","LIMIT","A",
    "VAR","QNAME","STRING","LANGTAG","INT",
    "LBRACE","RBRACE","LPAREN","RPAREN","DOT","SEMI","COMMA","STAR",
)

t_ignore = " \t\r"

# Ignorar BOM (U+FEFF) no início de ficheiros gravados com BOM
def t_BOM(t):
    r'\ufeff'
    pass

def t_COMMENT(t):
    r'\#.*'
    pass

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_SELECT(t):
    r'(?i:select)\b'
    t.type = "SELECT"; return t

def t_WHERE(t):
    r'(?i:where)\b'
    t.type = "WHERE"; return t

def t_LIMIT(t):
    r'(?i:limit)\b'
    t.type = "LIMIT"; return t

def t_A(t):
    r'\ba\b'
    t.type = "A"; return t

def t_VAR(t):
    r'\?[A-Za-z_][A-Za-z0-9_]*'
    return t

def t_QNAME(t):
    r'[A-Za-z_][A-Za-z0-9_-]*:[A-Za-z_][A-Za-z0-9._-]*'
    return t

_escape_seq = r'\\["\\ntr]'
STRING_RE = r'"(?:[^"\\]|' + _escape_seq + r')*"'
@lex.TOKEN(STRING_RE)
def t_STRING(t):
    s = t.value[1:-1]
    def unescape(m):
        return {
            r'\"': '"', r'\\': '\\', r'\n': '\n', r'\t': '\t', r'\r': '\r'
        }[m.group(0)]
    t.value = re.sub(_escape_seq, unescape, s)
    return t

def t_LANGTAG(t):
    r'@[A-Za-z]+(?:-[A-Za-z0-9]+)*'
    return t

def t_INT(t):
    r'0|[1-9][0-9]*'
    return t

t_LBRACE = r'\{'; t_RBRACE = r'\}'
t_LPAREN = r'\('; t_RPAREN = r'\)'
t_DOT = r'\.'; t_SEMI = r';'; t_COMMA = r','; t_STAR = r'\*'

def t_error(t):
    raise SyntaxError(f"[lexer] caractere inesperado '{t.value[0]}' na linha {t.lexer.lineno}")

def build_lexer(**kwargs):
    return lex.lex(reflags=re.UNICODE, **kwargs)
