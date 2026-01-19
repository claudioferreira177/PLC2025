"""
Módulo: codegen.py
Descrição: Este módulo é responsável pela geração de instruções Assembly para a Máquina Virtual.
Faz a ponte entre a análise semântica e o ficheiro executável final (.vm), gerindo a 
pilha, endereçamento de variáveis e controlo de fluxo (labels).
"""

class CodeGen:
    """
    Classe principal de acumulação e gestão de código assembly.
    Mantém o estado dos labels para garantir que saltos (JUMP/JZ) 
    nunca colidam entre diferentes estruturas de controlo (como IFs e WHILEs).
    """
    def __init__(self):
        self.lines = [] # Lista que armazena sequencialmente as instruções geradas
        self.lbl = 0 # Contador para garantir a unicidade de labels

    def emit(self, s: str):
        """
        Adiciona uma instrução ou um bloco de código bruto à lista de saída.
        """
        self.lines.append(s)

    def new_label(self, prefix="L"):
        """
        Gera um identificador de label único (ex: L1, L2, L3).
        É fundamental para implementar estruturas de decisão e ciclos,
        garantindo que cada salto aponte para o destino correto.
        """
        self.lbl += 1
        prefix = "".join(ch for ch in prefix if ch.isalnum())  # remove '_' e outros chars
        if not prefix:
            prefix = "L"
        return f"{prefix}{self.lbl}"


    def emit_label(self, lab: str):
        """
        Escreve a definição de um label no código (ex: 'L1:').
        Utilizado como destino de instruções JUMP ou JZ.
        """
        self.emit(f"{lab}:")

    def get(self) -> str:
        """
        Compila todas as linhas armazenadas numa única string formatada,
        pronta para ser escrita num ficheiro .vm.
        """
        return "\n".join(self.lines) + "\n"
    

def gen_load_var(info):
    """
    Abstração para carregar o valor de uma variável para o topo da pilha.
    Decide entre PUSHG (Global) ou PUSHL (Local) consultando a tabela de símbolos.
    :param info: Dicionário contendo 'level' (escopo) e 'addr' (endereço na stack).
    """
    if info["level"] == "global":
        return f"PUSHG {info['addr']}\n"
    else:
        return f"PUSHL {info['addr']}\n"

def gen_store_var(info):
    """
    Abstração para armazenar o valor do topo da pilha numa variável.
    Decide entre STOREG (Global) ou STOREL (Local) baseado no escopo.
    :param info: Dicionário contendo 'level' e 'addr'.
    """
    if info["level"] == "global":
        return f"STOREG {info['addr']}\n"
    else:
        return f"STOREL {info['addr']}\n"

def push_default_for_type(t):
    """
    Implementa a 'Stack Discipline'. 
    Reserva um espaço padrão na pilha antes da execução de subprogramas 
    ou para inicialização de variáveis, evitando corrupção de memória.
    - real: 0.0
    - string: ""
    - boolean/int/char: 0
    """
    if t == "real":
        return "PUSHF 0.0\n"
    if t == "string":
        return 'PUSHS ""\n'
    if t == "char":
        return "PUSHI 0\n"
    if t == "boolean":
        return "PUSHI 0\n"
    return "PUSHI 0\n"