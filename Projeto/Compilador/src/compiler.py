"""
Módulo: compiler.py
Descrição: Atua como o ponto de entrada principal para a lógica de compilação.
Este ficheiro configura o contexto, inicializa as funções pré-definidas (built-ins)
e coordena a interação entre o Lexer e o Parser.
"""

from .context import CompilerContext
from .sem import SymbolTable, BUILTIN_FUNCS
from .codegen import CodeGen
from .parser import build_parser
from .pascal_analex import lexer


def init_builtins(ctx: CompilerContext):
    """
    Regista as funções nativas da linguagem (ex: write, writeln, read) 
    na Tabela de Símbolos. Isto permite que o analisador semântico 
    as reconheça como identificadores válidos desde o início.
    """
    for name in BUILTIN_FUNCS:
        ctx.symtab.declare(name, {"kind": "builtin_func"}, lineno=0, declaring_builtin=True)

def compile_source(source: str) -> str:
    """
    Coordena o pipeline de compilação para transformar o código fonte em Assembly VM.
    
    1. Instancia a Tabela de Símbolos (st) e o Gerador de Código (gen).
    2. Cria o Contexto do Compilador (_ctx) que partilha estes objetos entre as fases.
    3. Inicializa os built-ins e configura o Parser e o Lexer.
    4. Executa o parse, que despoleta a geração de código via regras da gramática.
    
    :param source: String contendo o código Pascal.
    :return: String com o código assembly final gerado.
    """

    # Inicialização das estruturas base
    st = SymbolTable()
    gen = CodeGen()
    _ctx = CompilerContext(symtab=st, cg=gen)

    # Garante que o estado do contexto está limpo (ex: contadores de endereços)
    _ctx.reset()
    init_builtins(_ctx)

    # Constrói o parser injetando o contexto para que as ações semânticas 
    # tenham acesso à tabela de símbolos e ao gerador de código.
    parser, _lexer = build_parser(_ctx)

    # Reinicia a contagem de linhas para mensagens de erro precisas
    _lexer.lineno = 1

    # O parser.parse retorna a string final acumulada pelo CodeGen
    return parser.parse(source, lexer=_lexer)
