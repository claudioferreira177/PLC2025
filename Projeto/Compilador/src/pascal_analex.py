import ply.lex as lex

reserved = {
    'program': 'PROGRAM',
    'begin': 'BEGIN',
    'end': 'END',
    'var': 'VAR',
    'integer': 'INTEGER',
    'boolean': 'BOOLEAN',
    'real': 'REAL',
    'char': 'CHAR',
    'string': 'STRING',
    'array': 'ARRAY',
    'of': 'OF',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'while': 'WHILE',
    'do': 'DO',
    'for': 'FOR',
    'to': 'TO',
    'downto': 'DOWNTO',
    'repeat': 'REPEAT',
    'until': 'UNTIL',
    'function': 'FUNCTION',
    'procedure': 'PROCEDURE',
    'true': 'TRUE',
    'false': 'FALSE',
    'and': 'AND',
    'or': 'OR',
    'not': 'NOT',
    'div': 'DIV',
    'mod': 'MOD',
    'readln': 'READLN',
    'writeln': 'WRITELN',
}

tokens = [
    'ID',
    'NUMBER_INT',
    'NUMBER_REAL',
    'STRING_LITERAL',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'ASSIGN',
    'EQUAL',
    'NOTEQUAL',
    'LESS',
    'LESSEQUAL',
    'GREATER',
    'GREATEREQUAL',
    'LPAREN',
    'RPAREN',
    'LBRACKET',
    'RBRACKET',
    'COLON',
    'SEMICOLON',
    'COMMA',
    'DOT',
    'RANGE',
] + list(reserved.values())

t_PLUS      = r'\+'
t_MINUS     = r'-'
t_TIMES     = r'\*'
t_DIVIDE    = r'/'

t_LESSEQUAL    = r'<='
t_GREATEREQUAL = r'>='
t_NOTEQUAL     = r'<>'
t_ASSIGN       = r':='
t_RANGE        = r'\.\.'

t_LESS         = r'<'
t_GREATER      = r'>'
t_EQUAL        = r'='
t_COLON        = r':'
t_DOT          = r'\.'

t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_LBRACKET  = r'\['
t_RBRACKET  = r'\]'
t_SEMICOLON = r';'
t_COMMA     = r','

t_ignore = ' \t'

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value.lower(), 'ID') 
    return t

def t_NUMBER_REAL(t):
    r'(\d+\.\d+([eE][+-]?\d+)?|\d+[eE][+-]?\d+)'
    t.value = float(t.value)
    return t

def t_NUMBER_INT(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_STRING_LITERAL(t):
    r"'([^'\n]|'')*'"
    t.value = t.value[1:-1].replace("''", "'")
    return t

def t_COMMENT(t):
    r'\{[\s\S]*?\}|\(\*[\s\S]*?\*\)' 
    t.lexer.lineno += t.value.count('\n')
    pass

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Caractere ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

lexer = lex.lex()
