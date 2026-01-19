"""
Módulo: context.py
Descrição: Gere o estado e o contexto de compilação.
Este módulo utiliza Dataclasses para manter o rasto de endereços, blocos de código
pendentes e estados de subprogramas (funções/procedimentos), permitindo o suporte
a âmbitos aninhados e verificação de retorno de funções.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class CompilerContext:
    """
    Objeto central que armazena o estado do compilador durante a análise.
    Funciona como uma 'memória partilhada' entre o Parser, o Semântico e o Gerador de Código.
    """

    # Objetos Core
    symtab: Any # Referência para a Tabela de Símbolos (SymbolTable)
    cg: Any # Referência para o Gerador de Código (CodeGen)

    # Parser "Pendentes"
    # Guardam cabeçalhos de subprogramas enquanto o corpo ainda não foi processado
    pending_func_header: Optional[Any] = None
    pending_proc_header: Optional[Any] = None

    # Alocação de Globais / Locais
    next_global_addr: int = 0
    # Pilhas para suportar funções dentro de funções (âmbitos aninhados)
    next_local_addr_stack: list[int] = field(default_factory=list)
    local_init_code_stack: list[str] = field(default_factory=list)

    # Acumulação de Código
    global_init_code: str = "" # Código de inicialização para o bloco principal
    subprog_code: str = "" # Código gerado para funções e procedimentos

    # Rastreio de Subprogramas
    current_subprog: list[Any] = field(default_factory=list) # Pilha de subprogramas ativos
    func_return_assigned: list[bool] = field(default_factory=list) # Garante que funções retornam valor

    # Rastreador de strings e constantes (read-only)
    readonly_counts: dict = field(default_factory=dict)

    def reset(self):
        """
        Limpa todo o estado de compilação, exceto as referências core (symtab/cg).
        Essencial para reiniciar o compilador entre diferentes ficheiros de teste.
        """
        self.pending_func_header = None
        self.pending_proc_header = None

        self.next_global_addr = 0
        self.next_local_addr_stack.clear()
        self.local_init_code_stack.clear()

        self.global_init_code = ""
        self.subprog_code = ""

        self.current_subprog.clear()
        self.func_return_assigned.clear()
        self.readonly_counts.clear()
