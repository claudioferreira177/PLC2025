"""
Módulo: sem.py
Descrição: Núcleo da Análise Semântica e Verificação de Tipos.
Este módulo garante que o programa Pascal faz sentido logicamente, gerindo a
Tabela de Símbolos, resolvendo funções pré-definidas (built-ins) e validando
a compatibilidade entre tipos de dados.
"""

from __future__ import annotations


class SemanticError(Exception):
    """Exceção para erros lógicos detetados durante a análise (ex: tipos incompatíveis)."""
    pass

class SymbolTable:
    """
    Implementa uma Tabela de Símbolos baseada em pilha (stack of dicts).
    Permite a gestão de âmbitos (scopes) aninhados, suportando variáveis locais e globais.
    """
    def __init__(self):
        # O índice 0 é sempre o escopo global.
        self.scopes = [{}]

    def push(self):
        # Cria um novo nível de visibilidade (ex: ao entrar numa FUNCTION).
        self.scopes.append({})

    def pop(self):
        # Remove o nível mais interno (ex: ao sair de uma FUNCTION)
        self.scopes.pop()

    def declare(self, name, info, lineno=None, *, declaring_builtin=False):
        """
        Regista um identificador no escopo atual.
        Implementa proteção contra Shadowing de funções do sistema e 
        impede a redeclaração de variáveis no mesmo bloco.
        """
        # Proteção: utilizador não pode criar variáveis com nomes de funções built-in
        if not declaring_builtin:
            global_scope = self.scopes[0]
            b = global_scope.get(name)
            if b is not None and b.get("kind") == "builtin_func":
                line = f" (linha {lineno})" if lineno else ""
                raise SemanticError(
                    f"Identificador '{name}' é reservado (builtin) e não pode ser redeclarado{line}."
                )

        # Erro se a variável já existir no nível de profundidade atual
        scope = self.scopes[-1]
        if name in scope:
            line = f" (linha {lineno})" if lineno else ""
            raise SemanticError(f"Identificador '{name}' já declarado neste scope{line}.")
        scope[name] = info

    def lookup(self, name):
        """
        Pesquisa um nome da pilha mais interna para a mais externa.
        Retorna as informações da variável (tipo, endereço, etc.) ou None.
        """
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def depth(self):
        # Retorna o nível de aninhamento atual (0 = global).
        return len(self.scopes) - 1
    
"""
SISTEMA DE TIPOS E SOBRECARGA (OVERLOADING)
"""

SCALAR = {"integer", "real", "boolean", "char", "string"}

def is_array_type(t):
    # Identifica se um tipo é um array (representado internamente por um tuplo).
    return isinstance(t, tuple) and len(t) >= 1 and t[0] == "array"

# Definição de assinaturas de funções Built-in
# Algumas (como 'abs') têm sobrecarga: aceitam tanto Integer como Real.
BUILTIN_FUNCS = {
    # size
    "length": [
        {"params": ["string_or_array"], "ret": "integer"},
    ],

    # strings
    "concat": [
        {"params": ["string", "string"], "ret": "string"},
    ],

    # chars
    "ord": [
        {"params": ["char"], "ret": "integer"},
    ],
    "chr": [
        {"params": ["integer"], "ret": "char"},
    ],

    # numeric helpers
    "odd": [
        {"params": ["integer"], "ret": "boolean"},
    ],
    "abs": [
        {"params": ["integer"], "ret": "integer"},
        {"params": ["real"],    "ret": "real"},
    ],
    "trunc": [
        {"params": ["real"], "ret": "integer"},
    ],
    "round": [
        {"params": ["real"], "ret": "integer"},
    ],
}


def builtin_match(expected, got):
    """
    Algoritmo de matching de tipos para parâmetros de funções.
    Suporta tipos genéricos como 'numeric' ou 'string_or_array' e
    permite que um Integer seja passado onde se espera um Real.
    """
    if expected == "any":
        return True
    if expected == "numeric":
        return got in ("integer", "real")
    if expected == "array":
        return is_array_type(got)
    if expected == "string_or_array":
        return got == "string" or is_array_type(got)
    if expected == "real" and got == "integer":
        return True
    return expected == got

def resolve_builtin_func(name, args):
    """
    Dada uma chamada de função e os tipos dos argumentos passados,
    procura nos overloads disponíveis qual a versão correta a executar.
    """
    overloads = BUILTIN_FUNCS.get(name, [])
    for ov in overloads:
        params = ov["params"]
        if len(params) != len(args):
            continue
        if all(builtin_match(exp, got) for exp, got in zip(params, args)):
            return ov["ret"]
    return None

# Lista de tipos que o compilador considera como números para cálculos.
NUMERIC = ("integer", "real")

def is_numeric(t):
    """
    Verifica se um dado tipo 't' pode participar em operações aritméticas.
    """
    return t in NUMERIC

def numeric_result(t1, t2):
    """
    Implementa a regra de promoção de tipos (Type Promotion).
    Se misturarmos um inteiro com um real numa soma (ex: 5 + 2.5), 
    o resultado será sempre 'real' para evitar perda de precisão.
    """
    return "real" if (t1 == "real" or t2 == "real") else "integer"

def type_eq(t1, t2):
    """
    Verifica a compatibilidade de tipos para ATRIBUIÇÕES (:=).
    
    Regras de Pascal implementadas:
    1. Tipos idênticos são compatíveis (integer := integer).
    2. Alargamento: Um 'real' pode receber um 'integer' (conversão implícita).
    3. Restrição: Um 'integer' NÃO pode receber um 'real' (erro semântico).
    """
    if t1 == t2:
        return True
    if t1 == "real" and t2 == "integer":
        return True
    return False

def fmt_type(t):
    """
    Transforma a representação interna do compilador numa string amigável.
    Especialmente útil para imprimir erros de arrays complexos.
    Ex: converte ('array', (1, 10), 'integer') em 'array[1..10] of integer'.
    """
    if isinstance(t, tuple) and t[0] == "array":
        (lo, hi), base = t[1], t[2]
        return f"array[{lo}..{hi}] of {fmt_type(base)}"
    return str(t)

def fmt_sig_args(args):
    """
    Formata uma lista de tipos de argumentos para mensagens de erro de funções.
    Ex: [integer, real, string]
    """
    return "[" + ", ".join(fmt_type(a) for a in args) + "]"