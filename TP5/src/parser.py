import ply.yacc as yacc
from .lexer import tokens, build_lexer

# Precedências/associatividade: da mais baixa (em cima) para a mais alta (em baixo)
precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'UMINUS'),
)


class Parser:
    def __init__(self):
        self.lexer = build_lexer()
        self.parser = yacc.yacc(module=self, start='expr', debug=False, write_tables=False)

    # expr → expr + term | expr - term | term
    def p_expr_bin(self, p):
        '''expr : expr PLUS term
                | expr MINUS term'''
        if p[2] == '+':
            p[0] = p[1] + p[3]
        else:
            p[0] = p[1] - p[3]

    def p_expr_term(self, p):
        'expr : term'
        p[0] = p[1]

    # term → term * factor | term / factor | factor
    def p_term_bin(self, p):
        '''term : term TIMES factor
                | term DIVIDE factor'''
        if p[2] == '*':
            p[0] = p[1] * p[3]
        else:
            if p[3] == 0:
                raise ZeroDivisionError("[parser] divisão por zero")
            p[0] = int(p[1] / p[3])  # resultado inteiro (trunc)

    def p_term_factor(self, p):
        'term : factor'
        p[0] = p[1]

    # factor → -factor | ( expr ) | INT
    def p_factor_uminus(self, p):
        'factor : MINUS factor %prec UMINUS'
        p[0] = -p[2]

    def p_factor_group(self, p):
        'factor : LPAREN expr RPAREN'
        p[0] = p[2]

    def p_factor_int(self, p):
        'factor : INT'
        p[0] = p[1]

    def p_error(self, p):
        if p is None:
            raise SyntaxError("[parser] fim de entrada inesperado")
        col = (p.lexpos - self.lexer.line_start) + 1
        raise SyntaxError(f"[parser] token inesperado '{p.value}' ({p.type}) na linha {p.lineno} coluna {col}")

    def parse(self, text: str) -> int:
        self.lexer.input(text)
        return self.parser.parse(lexer=self.lexer)
