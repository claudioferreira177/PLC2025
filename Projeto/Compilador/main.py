"""
Módulo: main.py
Descrição: Ponto de entrada principal do Compilador Pascal.
Este script permite ao utilizador compilar um ficheiro .pas via linha de comandos,
exibindo o código assembly gerado para a Máquina Virtual (VM) no terminal.
"""

import sys
from src.compiler import compile_source

def main():
    """
    Função principal que gere o fluxo de execução via terminal.
    
    Fluxo:
    1. Valida os argumentos da linha de comandos.
    2. Lê o ficheiro de origem (.pas).
    3. Chama o pipeline de compilação.
    4. Imprime o resultado final (código VM).
    """

    # Verifica se o utilizador passou o caminho do ficheiro como argumento
    # Exemplo esperado: python main.py testes/meu_programa.pas
    if len(sys.argv) != 2:
        print("Uso: python main.py <ficheiro.pas>")
        raise SystemExit(1)

    # Recupera o caminho do ficheiro do primeiro argumento da lista sys.argv
    path = sys.argv[1]
    # Abre o ficheiro Pascal para leitura com codificação UTF-8
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    # Invoca o compilador (compiler.py) para processar o código fonte
    # Esta função coordena o Lexer, Parser, Semântico e CodeGen
    vm_code = compile_source(source)
    print(vm_code)

if __name__ == "__main__":
    main()
