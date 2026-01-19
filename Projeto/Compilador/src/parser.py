"""
Módulo: parser.py
Descrição: Implementa o Analisador Sintático (Parser) usando PLY.
Este módulo define a gramática da linguagem Pascal e contém a lógica para:
1. Validação da estrutura sintática.
2. Verificação semântica "on-the-fly" (tipos, declarações).
3. Geração de código assembly para a Máquina Virtual.
"""

import ply.yacc as yacc
from .pascal_analex import tokens, lexer

from .sem import (SemanticError, is_array_type, is_numeric, numeric_result, type_eq, fmt_type, fmt_sig_args, resolve_builtin_func,
)

from .codegen import gen_load_var, gen_store_var, push_default_for_type


# EXPR HELPERS
def mk_expr(t, const=None, code=""):
    """
    Cria uma estrutura de dados (dicionário) que representa uma expressão.
    Guarda o tipo (t), o valor se for constante (const) e o código assembly gerado (code).
    """
    return {"type": t, "const": const, "code": code}

def ecode(e):
    """Extrai apenas o código assembly de uma expressão ou retorna vazio."""
    return e.get("code", "") if isinstance(e, dict) else ""

def etype(e):
    """Extrai o tipo de dados (string) de uma expressão."""
    return e["type"] if isinstance(e, dict) else e

def econst(e):
    """Extrai o valor constante (se existir) de uma expressão."""
    return e.get("const") if isinstance(e, dict) else None



# RESOLUÇÃO DE IDENTIFICADORES
def resolve_var_or_index(name, idx_expr, lineno, *, want_lvalue):
    """
    Resolve o acesso a uma variável simples ou a um elemento de array.
    Verifica se a variável existe e calcula o endereço de memória.
    
    :param want_lvalue: Se True, gera código para escrita (STORE); 
                        Se False, gera código para leitura (PUSH).
    """
    info = ctx.symtab.lookup(name)
    if info is None:
        semerr(f"Variável '{name}' usada sem ter sido declarada", lineno)
    if info["kind"] != "var":
        semerr(f"'{name}' não é uma variável", lineno)

    base_t = info["type"]

    if idx_expr is None:
        return {"name": name, "type": base_t, "indexed": False}

    idx_t = etype(idx_expr)
    idx_c = econst(idx_expr)

    if idx_t != "integer":
        semerr(f"Índice de '{name}[...]' tem de ser integer (recebi {fmt_type(idx_t)})", lineno)

    # Subcaso: Indexação de STRING (Pascal strings são frequentemente tratadas como read-only)
    if base_t == "string":
        if want_lvalue:
            semerr(
                f"Não é permitido atribuir para '{name}[...]' porque '{name}' é string "
                f"(strings são read-only para indexação)",
                lineno
            )
        if idx_c is not None and idx_c < 1:
            semerr(f"Índice inválido em string: '{name}[{idx_c}]' (strings usam índices >= 1)", lineno)
        return {"name": name, "type": "char", "indexed": True, "index_expr": idx_expr, "string_indexed": True}

    # Subcaso: Indexação de ARRAY
    if not (isinstance(base_t, tuple) and base_t[0] == "array"):
        semerr(f"'{name}' não é array nem string, não pode ser indexado com [ ] (tipo: {fmt_type(base_t)})", lineno)
    
    # Verificação de limites se o índice for uma constante conhecida em tempo de compilação
    (lo, hi) = base_t[1]
    if idx_c is not None and (idx_c < lo or idx_c > hi):
        semerr(f"Índice fora do range: '{name}[{idx_c}]' mas o array é {fmt_type(base_t)}", lineno)

    return {"name": name, "type": base_t[2], "indexed": True, "index_expr": idx_expr, "array_info": base_t}


ctx = None
_parser = None


def semerr(msg, lineno=None):
    """Centraliza o lançamento de erros semânticos com indicação de linha."""
    if lineno is not None:
        raise SemanticError(f"{msg} (linha {lineno})")
    raise SemanticError(msg)


def readonly_enter(name: str, reason: str = "readonly"):
    """
    Bloqueia uma variável para escrita. 
    Usado principalmente para proteger a variável de controlo do ciclo FOR.
    """
    c, _r = ctx.readonly_counts.get(name, (0, reason))
    ctx.readonly_counts[name] = (c + 1, reason)


def readonly_exit(name: str):
    """Liberta uma variável do estado read-only."""
    v = ctx.readonly_counts.get(name)
    if not v:
        return
    c, r = v
    if c <= 1:
        ctx.readonly_counts.pop(name, None)
    else:
        ctx.readonly_counts[name] = (c - 1, r)


def is_readonly(name: str) -> bool:
    """Verifica se uma variável está atualmente protegida contra escrita."""
    v = ctx.readonly_counts.get(name)
    if not v:
        return False
    c, _ = v
    return c > 0


def semerr_if_readonly(name: str, lineno: int, *, what="alterar"):
    """Lança erro se houver tentativa de modificar uma variável protegida."""
    v = ctx.readonly_counts.get(name)
    if not v:
        return
    c, reason = v
    if c > 0:
        if reason == "for_control":
            raise SemanticError(f"Não é permitido atribuir à variável de controlo do FOR '{name}' (linha {lineno}).")
        raise SemanticError(f"Não é permitido {what} '{name}' (linha {lineno}).")


precedence = (
    ('nonassoc', 'IFX'),
    ('nonassoc', 'ELSE'),
)

def p_programa(p):
    "programa : PROGRAM ID SEMICOLON bloco DOT"

    prog = p[2]
    info = ctx.symtab.scopes[0].get(prog)
    if info is not None and info.get("kind") == "builtin_func":
        semerr(f"Nome do programa '{prog}' é reservado (builtin) e não pode ser usado", p.lineno(2))

    code = (
        "JUMP MAIN\n"
        + ctx.subprog_code
        + "MAIN:\n"
        + f"PUSHN {ctx.next_global_addr}\n"   # aloca globais primeiro
        + ctx.global_init_code               # aloca arrays e guarda o endereço em gp[addr]
        + "START\n"                      # fp fica “depois” das globais
        + p[4]["code"]
        + "STOP\n"
    )
    p[0] = code 

def p_bloco(p):
    "bloco : decls compound_stmt"
    p[0] = {"code": p[2]["code"]}


# DECLS

def p_decls_multi(p):
    "decls : decl decls"

def p_decls_empty(p):
    "decls :"

def p_decl_single1(p):
    "decl : var_section"

def p_decl_single2(p):
    "decl : subprog_decl"


# VAR DECLS
def p_var_section(p):
    "var_section : VAR var_decl_list"

def p_var_decl_list(p):
    "var_decl_list : var_decl var_decl_list_tail"

def p_var_decl_list_tail_multi(p):
    "var_decl_list_tail : var_decl var_decl_list_tail"

def p_var_decl_list_tail_single_empty(p):
    "var_decl_list_tail :"

def p_var_decl(p):
    "var_decl : id_list COLON tipo SEMICOLON"

    ids = p[1]  # p[1] contém a lista de identificadores (nome e linha) vinda da regra id_list
    t = p[3] # p[3] contém o tipo (ex: 'integer', 'real', ou tuplo de array)

    # Verifica se estamos dentro de um subprograma (depth > 0) ou no escopo global (depth == 0)
    in_subprog = (ctx.symtab.depth() > 0)

    # Itera sobre cada nome na lista (ex: para 'a, b : integer', processa 'a' e depois 'b')
    for (name, line) in ids:
        if not in_subprog:
            # Atribui o próximo endereço disponível no Global Pointer (GP)
            addr = ctx.next_global_addr
            ctx.next_global_addr += 1
            # PUSHI: empilha tamanho | ALLOCN: aloca na heap | STOREG: guarda ponteiro na var global
            ctx.symtab.declare(name, {"kind": "var", "type": t, "level": "global", "addr": addr}, lineno=line)

            # Se a variável for um ARRAY, gera código para alocação dinâmica na Heap
            if is_array_type(t):
                (lo, hi) = t[1]
                size = hi - lo + 1
                ctx.global_init_code += f"PUSHI {size}\nALLOCN\nSTOREG {addr}\n"

        else:
            # Segurança: verifica se a pilha de endereços locais existe
            if not ctx.next_local_addr_stack:
                semerr("Erro interno: declaração local fora de subprograma (ctx.next_local_addr_stack vazio).", line)

            # Atribui o endereço relativo ao Frame Pointer (FP) atual (topo da stack de endereços)
            addr = ctx.next_local_addr_stack[-1]
            ctx.next_local_addr_stack[-1] += 1
            ctx.symtab.declare(name, {"kind": "var", "type": t, "level": "local", "addr": addr}, lineno=line)

            # Se for um ARRAY local, gera código de alocação para ser executado ao entrar na função
            if is_array_type(t):
                (lo, hi) = t[1]
                size = hi - lo + 1
                if not ctx.local_init_code_stack:
                    semerr("Erro interno: ctx.local_init_code_stack vazio ao declarar array local.", line)
                # O código de alocação é acumulado para ser inserido no início do corpo da função
                ctx.local_init_code_stack[-1] += f"PUSHI {size}\nALLOCN\nSTOREL {addr}\n"


def p_id_list(p):
    "id_list : ID id_list_tail"
    p[0] = [(p[1], p.lineno(1))] + p[2]

def p_id_list_tail_multi(p):
    "id_list_tail : COMMA ID id_list_tail"
    p[0] = [(p[2], p.lineno(2))] + p[3]

def p_id_list_tail_empty(p):
    "id_list_tail :"
    p[0] = []



# TYPES
def p_tipo_integer(p):
    "tipo : INTEGER"
    p[0] = "integer"

def p_tipo_real(p):
    "tipo : REAL"
    p[0] = "real"

def p_tipo_boolean(p):
    "tipo : BOOLEAN"
    p[0] = "boolean"

def p_tipo_char(p):
    "tipo : CHAR"
    p[0] = "char"

def p_tipo_string(p):
    "tipo : STRING"
    p[0] = "string"

def p_tipo_array_type(p):
    "tipo : array_type"
    p[0] = p[1]

def p_array_type(p):
    "array_type : ARRAY LBRACKET range RBRACKET OF tipo"
    p[0] = ("array", p[3], p[6])

def p_range(p):
    "range : NUMBER_INT RANGE NUMBER_INT"
    lo, hi = p[1], p[3]
    if lo > hi:
        semerr(f"Range inválido: {lo}..{hi} (limite inferior maior que superior)", p.lineno(1))
    p[0] = (lo, hi)



# SUBPROGRAMS (function / procedure)
def p_subprog_decl_single1(p):
    "subprog_decl : function_decl"

def p_subprog_decl_single2(p):
    "subprog_decl : procedure_decl"



# FUNCTION
def p_function_header(p):
    "function_header : FUNCTION ID LPAREN param_list_opt RPAREN COLON tipo SEMICOLON"
    ctx.pending_func_header = {
        "name": p[2],
        "params": p[4],
        "ret": p[7],
        "lineno": p.lineno(2)
    }

def p_func_enter(p):
    "func_enter :"

    h = ctx.pending_func_header
    ctx.pending_func_header = None
    if h is None:
        semerr("Erro interno: func_enter sem function_header (ctx.pending_func_header=None)")

    name = h["name"]
    params = h["params"] or []
    ret_t = h["ret"]
    line = h["lineno"]
    k = len(params)

    # declara função no scope atual (global)
    ctx.symtab.declare(name, {"kind": "func", "params": params, "ret": ret_t, "label": name}, lineno=line)

    # entra scope do corpo
    ctx.symtab.push()

    # init locals: função reserva fp[0] para retorno
    ctx.next_local_addr_stack.append(1)      # próximo local livre
    ctx.local_init_code_stack.append("")     # init code de arrays locais

    # variável implícita de retorno: fp[0]
    ctx.symtab.declare(name, {"kind": "var", "type": ret_t, "level": "local", "addr": 0}, lineno=line)

    # regra forte: nenhum parâmetro pode ter o mesmo nome da função
    for (varname, t, vline) in params:
        if varname == name:
            semerr(
                f"Parâmetro '{varname}' não pode ter o mesmo nome da função '{name}' (colide com a variável de retorno)",
                vline
            )

    # params: offsets negativos fp[-k .. -1]
    for i, (varname, t, vline) in enumerate(params):
        addr = i - k
        ctx.symtab.declare(varname, {"kind": "var", "type": t, "level": "local", "addr": addr}, lineno=vline)

    ctx.current_subprog.append(("func", name, line, k))
    ctx.func_return_assigned.append(False)


def p_function_decl(p):
    "function_decl : function_header func_enter bloco SEMICOLON"

    assigned = ctx.func_return_assigned.pop()
    kind, fname, fline, k = ctx.current_subprog.pop()

    # obter nº de slots de locals (inclui retorno em 0)
    nlocals = ctx.next_local_addr_stack.pop()
    local_init = ctx.local_init_code_stack.pop()

    # sair scope do corpo
    ctx.symtab.pop()

    if not assigned:
        semerr(f"Função '{fname}' não atribui valor de retorno (ex: {fname} := ...)", fline)

    # Convenção:
    # Caller empilha: [ret_slot][args...], CALL
    # Callee no fim guarda fp[0] em fp[-(k+1)] (slot do caller) e RETURN
    code = ""
    code += f"{fname}:\n"
    code += f"PUSHN {nlocals}\n"
    code += local_init
    code += p[3]["code"]
    code += "PUSHL 0\n"
    code += f"STOREL {- (k + 1)}\n"
    code += "RETURN\n"

    ctx.subprog_code += code



# PROCEDURE
def p_procedure_header(p):
    "procedure_header : PROCEDURE ID LPAREN param_list_opt RPAREN SEMICOLON"
    ctx.pending_proc_header = {
        "name": p[2],
        "params": p[4],
        "lineno": p.lineno(2)
    }

def p_proc_enter(p):
    "proc_enter :"

    h = ctx.pending_proc_header
    ctx.pending_proc_header = None
    if h is None:
        semerr("Erro interno: proc_enter sem procedure_header (ctx.pending_proc_header=None)")

    name = h["name"]
    params = h["params"] or []
    line = h["lineno"]
    k = len(params)

    ctx.symtab.declare(name, {"kind": "proc", "params": params, "label": name}, lineno=line)

    ctx.symtab.push()

    # init locals: procedure não tem retorno implícito
    ctx.next_local_addr_stack.append(0)
    ctx.local_init_code_stack.append("")

    # params: offsets negativos fp[-k .. -1]
    for i, (varname, t, vline) in enumerate(params):
        addr = i - k
        ctx.symtab.declare(varname, {"kind": "var", "type": t, "level": "local", "addr": addr}, lineno=vline)

    ctx.current_subprog.append(("proc", name, line, k))


def p_procedure_decl(p):
    "procedure_decl : procedure_header proc_enter bloco SEMICOLON"

    kind, pname, pline, k = ctx.current_subprog.pop()

    nlocals = ctx.next_local_addr_stack.pop()
    local_init = ctx.local_init_code_stack.pop()

    ctx.symtab.pop()

    code = ""
    code += f"{pname}:\n"
    code += f"PUSHN {nlocals}\n"
    code += local_init
    code += p[3]["code"]
    code += "RETURN\n"

    ctx.subprog_code += code



# PARAMS
def p_param_list_opt_single(p):
    "param_list_opt : param_list"
    p[0] = p[1]

def p_param_list_opt_empty(p):
    "param_list_opt :"
    p[0] = []

def p_param_list(p):
    "param_list : param param_list_tail"
    p[0] = p[1] + p[2]

def p_param_list_tail_multi(p):
    "param_list_tail : SEMICOLON param param_list_tail"
    p[0] = p[2] + p[3]

def p_param_list_tail_empty(p):
    "param_list_tail :"
    p[0] = []

def p_param(p):
    "param : id_list COLON tipo"
    ids, t = p[1], p[3]
    p[0] = [(name, t, line) for (name, line) in ids]



# COMPOUND (begin..end)
def p_compound_stmt(p):
    "compound_stmt : BEGIN stmt_list_opt END"
    p[0] = {"code": p[2]["code"] if p[2] is not None else ""}

def p_stmt_list_opt_single(p):
    "stmt_list_opt : stmt_list"
    p[0] = p[1]

def p_stmt_list_opt_empty(p):
    "stmt_list_opt :"
    p[0] = {"code": ""}

def p_stmt_list(p):
    "stmt_list : stmt stmt_list_tail"
    p[0] = {"code": p[1]["code"] + p[2]["code"]}

def p_stmt_list_tail_multi(p):
    "stmt_list_tail : SEMICOLON stmt stmt_list_tail"
    p[0] = {"code": p[2]["code"] + p[3]["code"]}

def p_stmt_list_tail_single(p):
    "stmt_list_tail : SEMICOLON"
    p[0] = {"code": ""}

def p_stmt_list_tail_empty(p):
    "stmt_list_tail :"
    p[0] = {"code": ""}



# STATEMENTS
def p_stmt_single1(p):
    "stmt : assign_stmt"
    p[0] = p[1]

def p_stmt_single2(p):
    "stmt : if_stmt"
    p[0] = p[1]

def p_stmt_single3(p):
    "stmt : while_stmt"
    p[0] = p[1]

def p_stmt_single4(p):
    "stmt : for_stmt"
    p[0] = p[1]

def p_stmt_single5(p):
    "stmt : repeat_stmt"
    p[0] = p[1]

def p_stmt_single6(p):
    "stmt : compound_stmt"
    p[0] = p[1]

def p_stmt_single7(p):
    "stmt : proc_call"
    p[0] = p[1]



# ASSIGN
def p_assign_stmt(p):
    "assign_stmt : lvalue ASSIGN expr"
    left = p[1]
    right = p[3]

    left_name = left["name"]
    left_t = left["type"]
    left_indexed = left["indexed"]

    # marcar retorno atribuído se for "fname := ..."
    if ctx.current_subprog and ctx.current_subprog[-1][0] == "func":
        fname = ctx.current_subprog[-1][1]
        if (not left_indexed) and left_name == fname:
            ctx.func_return_assigned[-1] = True

    right_t = etype(right)

    if not left_indexed:
        semerr_if_readonly(left_name, p.lineno(2), what="atribuir")

    if isinstance(left_t, tuple) and left_t[0] == "array":
        semerr("Não podes atribuir diretamente a um array inteiro (falta índice)", p.lineno(2))

    if left_t == right_t:
        pass
    elif left_t == "real" and right_t == "integer":
        pass
    else:
        semerr(f"Atribuição incompatível: {fmt_type(left_t)} := {fmt_type(right_t)}", p.lineno(2))

    info = ctx.symtab.lookup(left_name)

    # x := expr
    if not left_indexed:
        code = ecode(right) + gen_store_var(info)
        p[0] = {"code": code}
        return

    # v[i] := expr  (array only; strings lvalue blocked earlier)
    arr_t = info["type"]
    if not (isinstance(arr_t, tuple) and arr_t[0] == "array"):
        semerr(f"'{left_name}' não é array (erro interno no assign indexado)", p.lineno(1))

    (lo, hi) = arr_t[1]
    idx = left["index_expr"]

    code = ""
    code += gen_load_var(info)    # base address
    code += ecode(idx)            # índice i

    # bounds check dinâmico
    code += f"CHECK {lo}, {hi}\n"

    # converter índice para offset 0-based do array
    if lo != 0:
        code += f"PUSHI {lo}\nSUB\n"

    code += ecode(right)          # rhs
    code += "STOREN\n"

    p[0] = {"code": code}



# VAR / LVALUE
def p_var_ref_single(p):
    "var_ref : ID"
    p[0] = resolve_var_or_index(p[1], None, p.lineno(1), want_lvalue=False)

def p_var_ref_multi(p):
    "var_ref : ID LBRACKET expr RBRACKET"
    p[0] = resolve_var_or_index(p[1], p[3], p.lineno(1), want_lvalue=False)

def p_lvalue_single(p):
    "lvalue : ID"
    p[0] = resolve_var_or_index(p[1], None, p.lineno(1), want_lvalue=True)

def p_lvalue_indexed(p):
    "lvalue : ID LBRACKET expr RBRACKET"
    p[0] = resolve_var_or_index(p[1], p[3], p.lineno(1), want_lvalue=True)



# IF / WHILE / FOR / REPEAT
def p_if_stmt_no_else(p):
    "if_stmt : IF expr THEN stmt %prec IFX"
    cond, then = p[2], p[4]

    if etype(cond) != "boolean":
        semerr(f"IF exige condição boolean, recebi {fmt_type(etype(cond))}", p.lineno(1))

    Lend = ctx.cg.new_label("IFEND")
    code = ecode(cond) + f"JZ {Lend}\n" + then["code"] + f"{Lend}:\n"
    p[0] = {"code": code}

def p_if_stmt_with_else(p):
    "if_stmt : IF expr THEN stmt ELSE stmt"
    cond, then, els = p[2], p[4], p[6]

    if etype(cond) != "boolean":
        semerr(f"IF exige condição boolean, recebi {fmt_type(etype(cond))}", p.lineno(1))

    Lelse = ctx.cg.new_label("IFELSE")
    Lend = ctx.cg.new_label("IFEND")
    code = (
        ecode(cond) + f"JZ {Lelse}\n" +
        then["code"] + f"JUMP {Lend}\n" +
        f"{Lelse}:\n" + els["code"] +
        f"{Lend}:\n"
    )
    p[0] = {"code": code}

def p_while_stmt(p):
    "while_stmt : WHILE expr DO stmt"
    cond, body = p[2], p[4]

    if etype(cond) != "boolean":
        semerr(f"WHILE exige condição boolean, recebi {fmt_type(etype(cond))}", p.lineno(1))

    Lstart = ctx.cg.new_label("WSTART")
    Lend = ctx.cg.new_label("WEND")
    code = (
        f"{Lstart}:\n" +
        ecode(cond) + f"JZ {Lend}\n" +
        body["code"] +
        f"JUMP {Lstart}\n" +
        f"{Lend}:\n"
    )
    p[0] = {"code": code}

def p_for_dir_single1(p):
    "for_dir : TO"
    p[0] = "TO"

def p_for_dir_single2(p):
    "for_dir : DOWNTO"
    p[0] = "DOWNTO"

def p_for_stmt(p):
    "for_stmt : FOR ID ASSIGN expr for_dir expr DO for_enter stmt for_exit"
    varname = p[2]
    start = p[4]
    direction = p[5]
    endexpr = p[6]
    body = p[9]
    id_line = p.lineno(2)

    info = ctx.symtab.lookup(varname)
    if info is None:
        semerr(f"Variável '{varname}' usada no FOR sem ter sido declarada", id_line)
    if info["kind"] != "var":
        semerr(f"'{varname}' no FOR não é uma variável", id_line)
    if info["type"] != "integer":
        semerr(f"Variável de controlo do FOR tem de ser integer (recebi {fmt_type(info['type'])})", id_line)

    if etype(start) != "integer":
        semerr(f"Início do FOR tem de ser integer (recebi {fmt_type(etype(start))})", id_line)
    if etype(endexpr) != "integer":
        semerr(f"Fim do FOR tem de ser integer (recebi {fmt_type(etype(endexpr))})", id_line)

    Lstart = ctx.cg.new_label("FORSTART")
    Lbody  = ctx.cg.new_label("FORBODY")
    Lend   = ctx.cg.new_label("FOREND")

    code = ""
    code += ecode(start) + gen_store_var(info)

    code += f"{Lstart}:\n"
    code += gen_load_var(info) + ecode(endexpr)
    if direction == "TO":
        code += "SUP\n"   # i > end ?
    else:
        code += "INF\n"   # i < end ?
    code += f"JZ {Lbody}\n"
    code += f"JUMP {Lend}\n"

    code += f"{Lbody}:\n"
    code += body["code"]

    code += gen_load_var(info)
    code += "PUSHI 1\n"
    code += "ADD\n" if direction == "TO" else "SUB\n"
    code += gen_store_var(info)

    code += f"JUMP {Lstart}\n"
    code += f"{Lend}:\n"

    p[0] = {"code": code}


def p_for_enter(p):
    "for_enter :"
    # Aqui o ID do FOR está a -6 nesta produção:
    # FOR ID ASSIGN expr for_dir expr DO for_enter ...
    varname = p[-6]
    readonly_enter(varname, reason="for_control")

def p_for_exit(p):
    "for_exit :"
    # Aqui o ID do FOR está a -8 nesta produção:
    # ... DO for_enter stmt for_exit
    varname = p[-8]
    readonly_exit(varname)


def p_repeat_stmt(p): 
    "repeat_stmt : REPEAT stmt_list_opt UNTIL expr" 
    cond = p[4] 
    body = p[2]

    if etype(cond) != "boolean": 
        semerr(f"UNTIL exige condição boolean, recebi {fmt_type(etype(cond))}", p.lineno(3)) 
    
    Lstart = ctx.cg.new_label("RSTART") 
    code = "" 
    code += f"{Lstart}:\n" 
    code += body["code"] 
    code += ecode(cond) 
    code += f"JZ {Lstart}\n" 
    p[0] = {"code": code}


# PROC CALLS / IO
def p_proc_call_single(p):
    "proc_call : ID"
    name = p[1]

    info = ctx.symtab.lookup(name)
    if info is None:
        semerr(f"'{name}' chamado sem ter sido declarado", p.lineno(1))

    if info["kind"] == "var":
        semerr(f"'{name}' é uma variável e não pode ser chamada como procedure", p.lineno(1))

    if info["kind"] == "func":
        semerr(f"Função '{name}' não pode ser chamada como statement; usa o valor numa expressão", p.lineno(1))

    if info["kind"] == "builtin_func":
        semerr(f"Função builtin '{name}' não pode ser chamada como statement; usa o valor numa expressão", p.lineno(1))

    if info["kind"] != "proc":
        semerr(f"'{name}' não é procedure", p.lineno(1))

    params = info["params"]
    if len(params) != 0:
        semerr(f"Procedure '{name}' exige {len(params)} args; usa '{name}(...)'", p.lineno(1))

    # codegen: CALL procedure sem args
    code = f"PUSHA {info.get('label', name)}\nCALL\n"
    p[0] = {"code": code}


def p_proc_call_multi1(p):
    "proc_call : ID LPAREN arg_list_opt RPAREN"
    name = p[1]
    args_expr = p[3]
    args_t = [etype(e) for e in args_expr]

    info = ctx.symtab.lookup(name)
    if info is None:
        semerr(f"'{name}' chamado sem ter sido declarado", p.lineno(1))

    if info["kind"] == "var":
        semerr(f"'{name}' é uma variável e não pode ser chamada como procedure", p.lineno(1))

    if info["kind"] == "builtin_func":
        semerr(f"Função builtin '{name}' não pode ser chamada como statement; usa o valor numa expressão", p.lineno(1))

    if info["kind"] == "func":
        semerr(f"Função '{name}' não pode ser chamada como statement; usa o valor numa expressão", p.lineno(1))

    if info["kind"] != "proc":
        semerr(f"'{name}' não é procedure", p.lineno(1))

    params = info["params"]
    if len(args_t) != len(params):
        semerr(f"'{name}' espera {len(params)} args, recebi {len(args_t)}: {fmt_sig_args(args_t)}", p.lineno(1))

    for i, (got_t, param) in enumerate(zip(args_t, params), start=1):
        _param_name, param_t, _pline = param
        if not type_eq(param_t, got_t):
            semerr(
                f"Arg {i} de '{name}' incompatível: espera {fmt_type(param_t)}, recebi {fmt_type(got_t)}",
                p.lineno(1)
            )

    code = ""
    # gerar args na ordem certa + conversão integer->real quando necessário
    for e, (_pname, param_t, _pline) in zip(args_expr, params):
        got_t = etype(e)
        code += ecode(e)
        if param_t == "real" and got_t == "integer":
            code += "ITOF\n"

    code += f"PUSHA {info.get('label', name)}\nCALL\n"
    code += f"POP {len(args_expr)}\n"  # limpar args
    p[0] = {"code": code}



def p_proc_call_multi2(p):
    "proc_call : WRITELN args_opt"
    exprs = p[2]
    code = ""
    for e in exprs:
        t = etype(e)
        if is_array_type(t):
            semerr("WRITELN não aceita arrays", p.lineno(1))
        code += ecode(e)
        if t == "integer":
            code += "WRITEI\n"
        elif t == "real":
            code += "WRITEF\n"
        elif t == "string":
            code += "WRITES\n"
        elif t == "char":
            code += "WRITECHR\n"
        elif t == "boolean":
            code += "WRITEI\n"
    code += "WRITELN\n"
    p[0] = {"code": code}


def p_proc_call_multi3(p):
    "proc_call : READLN read_args_opt"
    lvals = p[2]
    code = ""
    for lv in lvals:
        info = ctx.symtab.lookup(lv["name"])
        t = lv["type"]

        if is_array_type(t) and not lv["indexed"]:
            semerr("READLN não pode ler para um array inteiro", p.lineno(1))

        if not lv["indexed"]:
            # PROIBIR mexer no contador do FOR dentro do corpo
            semerr_if_readonly(lv["name"], p.lineno(1), what="ler (READLN)")

            code += "READ\n"
            if t == "integer":
                code += "ATOI\n"
            elif t == "real":
                code += "ATOF\n"
            code += gen_store_var(info)

        else:

            if info["type"] == "string":
                semerr(f"READLN não pode ler para '{lv['name']}[...]' porque é string (read-only)", p.lineno(1))

            # também deve respeitar readonly para variáveis diretas (já tratado acima)
            arr_t = info["type"]
            (lo, hi) = arr_t[1]
            idx = lv["index_expr"]

            code += gen_load_var(info)
            code += ecode(idx)

            # bounds check dinâmico
            code += f"CHECK {lo}, {hi}\n"

            if lo != 0:
                code += f"PUSHI {lo}\nSUB\n"

            code += "READ\n"
            if t == "integer":
                code += "ATOI\n"
            elif t == "real":
                code += "ATOF\n"
            code += "STOREN\n"


    p[0] = {"code": code}


def p_read_args_opt_multi(p):
    "read_args_opt : LPAREN read_var_list RPAREN"
    p[0] = p[2]

def p_read_args_opt_empty(p):
    "read_args_opt :"
    p[0] = []

def p_read_var_list_single(p):
    "read_var_list : lvalue"
    p[0] = [p[1]]

def p_read_var_list_multi(p):
    "read_var_list : lvalue COMMA read_var_list"
    p[0] = [p[1]] + p[3]


def p_args_opt_multi(p):
    "args_opt : LPAREN arg_list_opt RPAREN"
    p[0] = p[2]

def p_args_opt_empty(p):
    "args_opt :"
    p[0] = []

def p_arg_list_opt_single(p):
    "arg_list_opt : arg_list"
    p[0] = p[1]

def p_arg_list_opt_empty(p):
    "arg_list_opt :"
    p[0] = []

def p_arg_list(p):
    "arg_list : expr arg_list_tail"
    p[0] = [p[1]] + p[2]

def p_arg_list_tail_multi(p):
    "arg_list_tail : COMMA expr arg_list_tail"
    p[0] = [p[2]] + p[3]

def p_arg_list_tail_empty(p):
    "arg_list_tail :"
    p[0] = []



# EXPRESSIONS
def arith_codegen(op_int, op_float, e1, e2, t1, t2):
    out_t = numeric_result(t1, t2)
    code = ""
    code += ecode(e1)
    if out_t == "real" and t1 == "integer":
        code += "ITOF\n"
    code += ecode(e2)
    if out_t == "real" and t2 == "integer":
        code += "ITOF\n"
    code += (op_float if out_t == "real" else op_int)
    return out_t, code

def p_expr(p):
    "expr : or_expr"
    p[0] = p[1]

def p_or_expr_single(p):
    "or_expr : and_expr"
    p[0] = p[1]

def p_or_expr_multi(p):
    "or_expr : or_expr OR and_expr"
    if etype(p[1]) != "boolean" or etype(p[3]) != "boolean":
        semerr(f"OR exige boolean, recebi {fmt_type(etype(p[1]))} OR {fmt_type(etype(p[3]))}", p.lineno(2))

    c1, c2 = econst(p[1]), econst(p[3])
    const = (c1 or c2) if (c1 is not None and c2 is not None) else None

    Ltrue = ctx.cg.new_label("OR_TRUE")
    Lend  = ctx.cg.new_label("OR_END")

    code = ""
    code += ecode(p[1])            # avalia lhs
    code += f"JZ {Ltrue}\n"        # se lhs == 0, precisa avaliar rhs
    # lhs != 0 -> resultado true sem avaliar rhs
    code += "PUSHI 1\n"
    code += f"JUMP {Lend}\n"
    code += f"{Ltrue}:\n"
    code += ecode(p[3])            # resultado = rhs
    code += f"{Lend}:\n"

    p[0] = mk_expr("boolean", const, code)


def p_and_expr_single(p):
    "and_expr : rel_expr"
    p[0] = p[1]

def p_and_expr_multi(p):
    "and_expr : and_expr AND rel_expr"
    if etype(p[1]) != "boolean" or etype(p[3]) != "boolean":
        semerr(f"AND exige boolean, recebi {fmt_type(etype(p[1]))} AND {fmt_type(etype(p[3]))}", p.lineno(2))

    c1, c2 = econst(p[1]), econst(p[3])
    const = (c1 and c2) if (c1 is not None and c2 is not None) else None

    Lfalse = ctx.cg.new_label("AND_FALSE")
    Lend   = ctx.cg.new_label("AND_END")

    code = ""
    code += ecode(p[1])            # lhs
    code += f"JZ {Lfalse}\n"       # se lhs == 0 -> false sem avaliar rhs
    code += ecode(p[3])            # resultado = rhs
    code += f"JUMP {Lend}\n"
    code += f"{Lfalse}:\n"
    code += "PUSHI 0\n"
    code += f"{Lend}:\n"

    p[0] = mk_expr("boolean", const, code)


def p_rel_expr(p):
    "rel_expr : add_expr rel_opt"
    left = p[1]
    left_t = etype(left)
    opt = p[2]

    if opt is None:
        p[0] = left
        return

    op, right, op_line = opt
    right_t = etype(right)

    if op in ("=", "<>"):
        if is_array_type(left_t) or is_array_type(right_t):
                semerr(f"Comparação inválida: não é permitido comparar array com '{op}'", op_line)

        if not (left_t == right_t or (is_numeric(left_t) and is_numeric(right_t))):
                semerr(f"Comparação inválida: {fmt_type(left_t)} {op} {fmt_type(right_t)}", op_line)

        # const folding
        c1, c2 = econst(left), econst(right)
        const = None
        if c1 is not None and c2 is not None:
            const = (c1 == c2) if op == "=" else (c1 != c2)

        # codegen (com promoção int->real quando necessário)
        code = ""
        if is_numeric(left_t) and is_numeric(right_t) and left_t != right_t:
            code += ecode(left)
            if left_t == "integer":
                code += "ITOF\n"
            code += ecode(right)
            if right_t == "integer":
                code += "ITOF\n"
        else:
            code += ecode(left) + ecode(right)

        code += "EQUAL\n"
        if op == "<>":
            code += "NOT\n"

        p[0] = mk_expr("boolean", const, code)
        return

    if not (is_numeric(left_t) and is_numeric(right_t)):
        semerr(f"Comparação '{op}' exige números, recebi {fmt_type(left_t)} {op} {fmt_type(right_t)}", op_line)

    c1, c2 = econst(left), econst(right)
    const = None
    if c1 is not None and c2 is not None:
        if op == "<":
            const = (c1 < c2)
        elif op == "<=":
            const = (c1 <= c2)
        elif op == ">":
            const = (c1 > c2)
        elif op == ">=":
            const = (c1 >= c2)

    use_float = (left_t == "real" or right_t == "real")
    if use_float:
        code = ecode(left)
        if left_t == "integer":
            code += "ITOF\n"
        code += ecode(right)
        if right_t == "integer":
            code += "ITOF\n"
        if op == "<":
            code += "FINF\n"
        elif op == "<=":
            code += "FINFEQ\n"
        elif op == ">":
            code += "FSUP\n"
        elif op == ">=":
            code += "FSUPEQ\n"
    else:
        code = ecode(left) + ecode(right)
        if op == "<":
            code += "INF\n"
        elif op == "<=":
            code += "INFEQ\n"
        elif op == ">":
            code += "SUP\n"
        elif op == ">=":
            code += "SUPEQ\n"

    p[0] = mk_expr("boolean", const, code)

def p_rel_opt_multi(p):
    "rel_opt : relop add_expr"
    (op, op_line) = p[1]
    p[0] = (op, p[2], op_line)

def p_rel_opt_empty(p):
    "rel_opt :"
    p[0] = None

def p_relop_single1(p):
    "relop : EQUAL"
    p[0] = ("=", p.lineno(1))

def p_relop_single2(p):
    "relop : NOTEQUAL"
    p[0] = ("<>", p.lineno(1))

def p_relop_single3(p):
    "relop : LESS"
    p[0] = ("<", p.lineno(1))

def p_relop_single4(p):
    "relop : LESSEQUAL"
    p[0] = ("<=", p.lineno(1))

def p_relop_single5(p):
    "relop : GREATER"
    p[0] = (">", p.lineno(1))

def p_relop_single6(p):
    "relop : GREATEREQUAL"
    p[0] = (">=", p.lineno(1))

def p_add_expr_single(p):
    "add_expr : mul_expr"
    p[0] = p[1]

def p_add_expr_multi1(p):
    "add_expr : add_expr PLUS mul_expr"
    t1, t2 = etype(p[1]), etype(p[3])
    if not (is_numeric(t1) and is_numeric(t2)):
        semerr("Operador '+' exige números", p.lineno(2))
    c1, c2 = econst(p[1]), econst(p[3])
    const = (c1 + c2) if (c1 is not None and c2 is not None) else None
    out_t, code = arith_codegen("ADD\n", "FADD\n", p[1], p[3], t1, t2)
    p[0] = mk_expr(out_t, const, code)

def p_add_expr_multi2(p):
    "add_expr : add_expr MINUS mul_expr"
    t1, t2 = etype(p[1]), etype(p[3])
    if not (is_numeric(t1) and is_numeric(t2)):
        semerr("Operador '-' exige números", p.lineno(2))
    c1, c2 = econst(p[1]), econst(p[3])
    const = (c1 - c2) if (c1 is not None and c2 is not None) else None
    out_t, code = arith_codegen("SUB\n", "FSUB\n", p[1], p[3], t1, t2)
    p[0] = mk_expr(out_t, const, code)

def p_mul_expr_single(p):
    "mul_expr : unary_expr"
    p[0] = p[1]

def p_mul_expr_multi1(p):
    "mul_expr : mul_expr TIMES unary_expr"
    t1, t2 = etype(p[1]), etype(p[3])
    if not (is_numeric(t1) and is_numeric(t2)):
        semerr("Operador '*' exige números", p.lineno(2))
    c1, c2 = econst(p[1]), econst(p[3])
    const = (c1 * c2) if (c1 is not None and c2 is not None) else None
    out_t, code = arith_codegen("MUL\n", "FMUL\n", p[1], p[3], t1, t2)
    p[0] = mk_expr(out_t, const, code)

def p_mul_expr_multi2(p):
    "mul_expr : mul_expr DIVIDE unary_expr"
    t1, t2 = etype(p[1]), etype(p[3])
    if not (is_numeric(t1) and is_numeric(t2)):
        semerr("Operador '/' exige números", p.lineno(2))
    c1, c2 = econst(p[1]), econst(p[3])
    const = None
    if c1 is not None and c2 is not None:
        if c2 == 0:
            semerr("Divisão por zero em expressão constante", p.lineno(2))
        const = c1 / c2
    code = ecode(p[1])
    if t1 == "integer":
        code += "ITOF\n"
    code += ecode(p[3])
    if t2 == "integer":
        code += "ITOF\n"
    code += "FDIV\n"
    p[0] = mk_expr("real", const, code)

def p_mul_expr_multi3(p):
    "mul_expr : mul_expr DIV unary_expr"
    t1, t2 = etype(p[1]), etype(p[3])
    if t1 != "integer" or t2 != "integer":
        semerr("Operador 'div' exige integer", p.lineno(2))
    c1, c2 = econst(p[1]), econst(p[3])
    const = None
    if c1 is not None and c2 is not None:
        if c2 == 0:
            semerr("Divisão por zero em expressão constante (div)", p.lineno(2))
        const = c1 // c2
    code = ecode(p[1]) + ecode(p[3]) + "DIV\n"
    p[0] = mk_expr("integer", const, code)

def p_mul_expr_multi4(p):
    "mul_expr : mul_expr MOD unary_expr"
    t1, t2 = etype(p[1]), etype(p[3])
    if t1 != "integer" or t2 != "integer":
        semerr("Operador 'mod' exige integer", p.lineno(2))
    c1, c2 = econst(p[1]), econst(p[3])
    const = None
    if c1 is not None and c2 is not None:
        if c2 == 0:
            semerr("Divisão por zero em expressão constante (mod)", p.lineno(2))
        const = c1 % c2
    code = ecode(p[1]) + ecode(p[3]) + "MOD\n"
    p[0] = mk_expr("integer", const, code)

def p_unary_expr_multi1(p):
    "unary_expr : MINUS unary_expr"
    t = etype(p[2])
    if t not in ("integer", "real"):
        semerr("Operador unário '-' exige integer ou real", p.lineno(1))
    c = econst(p[2])
    const = (-c) if c is not None else None
    if t == "integer":
        code = "PUSHI 0\n" + ecode(p[2]) + "SUB\n"
    else:
        code = "PUSHF 0.0\n" + ecode(p[2]) + "FSUB\n"
    p[0] = mk_expr(t, const, code)

def p_unary_expr_multi2(p):
    "unary_expr : NOT unary_expr"
    if etype(p[2]) != "boolean":
        semerr(f"NOT exige boolean, recebi {fmt_type(etype(p[2]))}", p.lineno(1))
    c = econst(p[2])
    const = (not c) if c is not None else None
    code = ecode(p[2]) + "NOT\n"
    p[0] = mk_expr("boolean", const, code)

def p_unary_expr_single(p):
    "unary_expr : primary"
    p[0] = p[1]



# PRIMARY
def p_primary_single1(p):
    "primary : NUMBER_REAL"
    p[0] = mk_expr("real", p[1], f"PUSHF {p[1]}\n")

def p_primary_single2(p):
    "primary : NUMBER_INT"
    p[0] = mk_expr("integer", p[1], f"PUSHI {p[1]}\n")

def p_primary_single3(p):
    "primary : STRING_LITERAL"
    s = p[1]
    lit = s.replace('"', '\\"')
    if len(s) == 1:
        code = f"PUSHI {ord(s)}\n"
        p[0] = mk_expr("char", ord(s), code)
        return
    else:
        code = f'PUSHS "{lit}"\n'
        p[0] = mk_expr("string", s, code)

def p_primary_single4(p):
    "primary : TRUE"
    p[0] = mk_expr("boolean", True, "PUSHI 1\n")

def p_primary_single5(p):
    "primary : FALSE"
    p[0] = mk_expr("boolean", False, "PUSHI 0\n")

def p_primary_single6(p):
    "primary : var_ref"
    vr = p[1]
    info = ctx.symtab.lookup(vr["name"])

    if not vr["indexed"]:
        p[0] = mk_expr(vr["type"], None, gen_load_var(info))
        return

    idx = vr["index_expr"]
    base_t = info["type"]

    if base_t == "string":
        code = gen_load_var(info) + ecode(idx) + "PUSHI 1\nSUB\nCHARAT\n"
        p[0] = mk_expr("char", None, code)
        return

    if not (isinstance(base_t, tuple) and base_t[0] == "array"):
        semerr("Erro interno: indexação em não-array/não-string", p.lineno(1))

    (lo, hi) = base_t[1]
    elem_t = base_t[2]

    code = ""
    code += gen_load_var(info)   # base address
    code += ecode(idx)           # índice i (ainda 1-based ou com lo)

    # bounds check dinâmico
    code += f"CHECK {lo}, {hi}\n"

    # converter índice para offset 0-based do array
    if lo != 0:
        code += f"PUSHI {lo}\nSUB\n"

    code += "LOADN\n"
    p[0] = mk_expr(elem_t, None, code)



def p_primary_single7(p):
    "primary : ID LPAREN arg_list_opt RPAREN"
    name = p[1]
    args_expr = p[3]
    args_t = [etype(e) for e in args_expr]

    info = ctx.symtab.lookup(name)
    if info is None:
        semerr(f"Função '{name}' chamada sem ter sido declarada", p.lineno(1))

    if info["kind"] == "var":
        semerr(f"'{name}' é uma variável e não pode ser chamada como função", p.lineno(1))

    # BUILTINS
    if info["kind"] == "builtin_func":
        ret = resolve_builtin_func(name, args_t)
        if ret is None:
            semerr(
                f"Chamada inválida a '{name}': argumentos {fmt_sig_args(args_t)} não correspondem a nenhuma assinatura",
                p.lineno(1)
            )

        # length(x)
        if name == "length":
            if len(args_expr) != 1:
                semerr("length(...) espera 1 argumento", p.lineno(1))
            t0 = args_t[0]
            e0 = args_expr[0]

            if t0 == "string":
                code = ecode(e0) + "STRLEN\n"
                p[0] = mk_expr("integer", None, code)
                return

            if is_array_type(t0):
                (lo, hi) = t0[1]
                size = hi - lo + 1
                # NÃO avaliar o array (evita lixo na stack)
                code = f"PUSHI {size}\n"
                p[0] = mk_expr("integer", size, code)
                return

            semerr(f"length(...) só aceita string ou array, recebi {fmt_type(t0)}", p.lineno(1))

        # concat(s1,s2) 
        if name == "concat":
            if len(args_expr) != 2:
                semerr("concat(s1,s2) espera 2 argumentos", p.lineno(1))
            if args_t[0] != "string" or args_t[1] != "string":
                semerr(f"concat(...) espera (string,string), recebi {fmt_sig_args(args_t)}", p.lineno(1))
            code = ecode(args_expr[0]) + ecode(args_expr[1]) + "CONCAT\n"
            p[0] = mk_expr("string", None, code)
            return

        # ord(c) 
        # Na tua VM, char já é um inteiro ASCII no topo da stack.
        if name == "ord":
            if len(args_expr) != 1:
                semerr("ord(...) espera 1 argumento", p.lineno(1))
            if args_t[0] != "char":
                semerr(f"ord(...) espera char, recebi {fmt_type(args_t[0])}", p.lineno(1))
            code = ecode(args_expr[0])  # no-op
            p[0] = mk_expr("integer", econst(args_expr[0]), code)
            return

        # chr(i)
        # Também é no-op: tratamos char como inteiro ASCII.
        # Mas fazemos CHECK 0..255 por robustez.
        if name == "chr":
            if len(args_expr) != 1:
                semerr("chr(...) espera 1 argumento", p.lineno(1))
            if args_t[0] != "integer":
                semerr(f"chr(...) espera integer, recebi {fmt_type(args_t[0])}", p.lineno(1))
            code = ecode(args_expr[0]) + "CHECK 0, 255\n"
            p[0] = mk_expr("char", None, code)
            return

        # odd(i)
        if name == "odd":
            if len(args_expr) != 1:
                semerr("odd(...) espera 1 argumento", p.lineno(1))
            if args_t[0] != "integer":
                semerr(f"odd(...) espera integer, recebi {fmt_type(args_t[0])}", p.lineno(1))
            # odd(x) := (x mod 2) <> 0
            code = (
                ecode(args_expr[0]) +
                "PUSHI 2\nMOD\n" +
                "PUSHI 0\nEQUAL\nNOT\n"
            )
            p[0] = mk_expr("boolean", None, code)
            return

        # trunc(r)
        if name == "trunc":
            if len(args_expr) != 1:
                semerr("trunc(...) espera 1 argumento", p.lineno(1))
            if args_t[0] != "real":
                semerr(f"trunc(...) espera real, recebi {fmt_type(args_t[0])}", p.lineno(1))
            code = ecode(args_expr[0]) + "FTOI\n"
            p[0] = mk_expr("integer", None, code)
            return

        # round(r)
        # round(x) = FTOI(x + 0.5) se x>=0, senão FTOI(x - 0.5)
        if name == "round":
            if len(args_expr) != 1:
                semerr("round(...) espera 1 argumento", p.lineno(1))
            if args_t[0] != "real":
                semerr(f"round(...) espera real, recebi {fmt_type(args_t[0])}", p.lineno(1))

            Lpos = ctx.cg.new_label("ROUND_POS")
            Lend = ctx.cg.new_label("ROUND_END")

            code = ""
            code += ecode(args_expr[0])     # x
            code += "DUP 1\n"               # x x
            code += "PUSHF 0.0\n"           # x x 0.0
            code += "FINF\n"                # x (x<0.0)?
            code += f"JZ {Lpos}\n"          # se não é negativo -> pos

            # negativo: x - 0.5
            code += "PUSHF 0.5\n"
            code += "FSUB\n"
            code += "FTOI\n"
            code += f"JUMP {Lend}\n"

            # positivo: x + 0.5
            code += f"{Lpos}:\n"
            code += "PUSHF 0.5\n"
            code += "FADD\n"
            code += "FTOI\n"

            code += f"{Lend}:\n"
            p[0] = mk_expr("integer", None, code)
            return

        # abs(x)
        if name == "abs":
            if len(args_expr) != 1:
                semerr("abs(...) espera 1 argumento", p.lineno(1))

            t0 = args_t[0]
            e0 = args_expr[0]

            if t0 == "integer":
                Lok = ctx.cg.new_label("ABS_I_OK")
                Lend = ctx.cg.new_label("ABS_I_END")

                code = ""
                code += ecode(e0)            # x
                code += "DUP 1\n"            # x x
                code += "PUSHI 0\n"          # x x 0
                code += "INF\n"              # x (x<0)?
                code += f"JZ {Lok}\n"        # se não é negativo

                # negativo: 0 - x
                code += "PUSHI 0\n"
                code += "SWAP\n"
                code += "SUB\n"
                code += f"JUMP {Lend}\n"

                code += f"{Lok}:\n"
                code += f"{Lend}:\n"
                p[0] = mk_expr("integer", None, code)
                return

            if t0 == "real":
                Lok = ctx.cg.new_label("ABS_F_OK")
                Lend = ctx.cg.new_label("ABS_F_END")

                code = ""
                code += ecode(e0)            # x
                code += "DUP 1\n"            # x x
                code += "PUSHF 0.0\n"        # x x 0.0
                code += "FINF\n"             # x (x<0)?
                code += f"JZ {Lok}\n"        # se não é negativo

                # negativo: 0.0 - x
                code += "PUSHF 0.0\n"
                code += "SWAP\n"
                code += "FSUB\n"
                code += f"JUMP {Lend}\n"

                code += f"{Lok}:\n"
                code += f"{Lend}:\n"
                p[0] = mk_expr("real", None, code)
                return

            semerr(f"abs(...) espera integer ou real, recebi {fmt_type(t0)}", p.lineno(1))

        semerr(f"Builtin '{name}' não suportado (erro interno)", p.lineno(1))

    #  USER-DEFINED
    if info["kind"] == "proc":
        semerr(f"Procedure '{name}' não pode ser usada como expressão (não devolve valor)", p.lineno(1))

    if info["kind"] != "func":
        semerr(f"'{name}' não é function", p.lineno(1))

    params = info["params"]
    if len(args_t) != len(params):
        semerr(f"'{name}' espera {len(params)} args, recebi {len(args_t)}: {fmt_sig_args(args_t)}", p.lineno(1))

    for i, (got_t, param) in enumerate(zip(args_t, params), start=1):
        _param_name, param_t, _pline = param
        if not type_eq(param_t, got_t):
            semerr(
                f"Arg {i} de '{name}' incompatível: espera {fmt_type(param_t)}, recebi {fmt_type(got_t)}",
                p.lineno(1)
            )

    # CODEGEN: slot retorno tipado + args + CALL ; POP args ; retorno fica no topo
    k = len(args_expr)
    code = push_default_for_type(info["ret"])   # slot correto para o tipo de retorno

    # gerar args na ordem certa + conversão integer->real quando necessário
    for e, (_pname, param_t, _pline) in zip(args_expr, params):
        got_t = etype(e)
        code += ecode(e)
        if param_t == "real" and got_t == "integer":
            code += "ITOF\n"

    code += f"PUSHA {info.get('label', name)}\nCALL\n"
    code += f"POP {k}\n"  # limpar args; o retorno (caller slot) fica no topo

    p[0] = mk_expr(info["ret"], None, code)




def p_primary_single8(p):
    "primary : LPAREN expr RPAREN"
    p[0] = p[2]

# SYNTAX ERR
class SyntaxParseError(Exception):
    pass

def p_error(p):
    if p:
        raise SyntaxParseError(f"Erro sintático no token {p.type} ({p.value}) na linha {p.lineno}")
    else:
        raise SyntaxParseError("Erro sintático no fim do input")

def build_parser(_ctx):
    global ctx, _parser
    ctx = _ctx
    if _parser is None:
        _parser = yacc.yacc(start="programa")
    return _parser, lexer