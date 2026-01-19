"""
Módulo: run_tests.py
Descrição: Motor de testes automatizados para o compilador Pascal.
Este script percorre as pastas de casos de teste, executa o compilador e 
compara os resultados obtidos com os resultados esperados, gerando um resumo final.
"""

import sys
from pathlib import Path

# Definição de caminhos base do projeto
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import json
from src.compiler import compile_source


TESTS_DIR = ROOT / "tests"
OK_DIR = TESTS_DIR / "cases" / "ok" # Ficheiros .pas que devem compilar
ERR_DIR = TESTS_DIR / "cases" / "error" # Ficheiros .pas que devem gerar erro
MANIFEST = TESTS_DIR / "manifests" / "error_cases.json" # Lista de erros esperados
OUT_VM = ROOT / "out_vm" # Destino dos ficheiros .vm gerados


def read_text(path: Path) -> str:
    """
    Carrega o ficheiro JSON que mapeia cada ficheiro de erro à mensagem 
    de erro esperada. Suporta formatos de dicionário ou lista.
    """
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    """
    Escreve uma string num ficheiro. Cria a diretoria pai caso não exista.
    :param path: Caminho de destino (Path object).
    :param text: Conteúdo a ser escrito (código Assembly VM).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_error_manifest() -> dict[str, str]:
    """
    Aceita 2 formatos:
    1) Dict: {"T1.pas": "substring", ...}
    2) Lista: [{"file":"T1.pas","contains":"substring"}, ...]
    """
    data = json.loads(read_text(MANIFEST))

    if isinstance(data, dict):
        return {str(k): str(v) for k, v in data.items()}

    if isinstance(data, list):
        out = {}
        for item in data:
            if isinstance(item, dict) and "file" in item and "contains" in item:
                out[str(item["file"])] = str(item["contains"])
        return out

    raise RuntimeError("error_cases.json tem de ser dict ou lista de {file, contains}.")


def run_ok_cases() -> tuple[int, int]:
    """
    Executa os testes positivos.
    Para cada ficheiro em 'cases/ok/':
    1. Tenta compilar o código Pascal.
    2. Se tiver sucesso, guarda o código Assembly gerado na pasta 'out_vm'.
    3. Se falhar, reporta um FAIL inesperado.
    """
    ok_files = sorted(OK_DIR.glob("*.pas"))
    passed = 0
    failed = 0

    for f in ok_files:
        name = f.name
        src = read_text(f)

        try:
            vm_code = compile_source(src)  # deve devolver string com VM
            out_path = OUT_VM / (f.stem + ".vm")
            write_text(out_path, vm_code)
            print(f"OK: {name}  ->  [VM guardada em out_vm/{out_path.name}]")
            passed += 1
        except Exception as e:
            print(f"FAIL: {name}  ->  erro inesperado: {e}")
            failed += 1

    return passed, failed


def run_error_cases() -> tuple[int, int]:
    """
    Executa os testes negativos.
    Para cada ficheiro em 'cases/error/':
    1. Tenta compilar o código (que se sabe estar errado).
    2. Verifica se o compilador lançou uma exceção.
    3. Valida se a mensagem de erro contém a substring definida no manifest.
    
    Exemplo: Se o teste 'tipo_errado.pas' falhar, o script verifica se a 
    mensagem de erro menciona "incompatível", conforme definido no JSON.
    """
    manifest = load_error_manifest()
    err_files = sorted(ERR_DIR.glob("*.pas"))
    passed = 0
    failed = 0

    for f in err_files:
        name = f.name
        src = read_text(f)

        expected_substr = manifest.get(name)
        if not expected_substr:
            print(f"FAIL: {name}  ->  não existe entrada no manifest (error_cases.json)")
            failed += 1
            continue

        try:
            compile_source(src)
            print(f"FAIL: {name}  ->  era esperado erro, mas compilou OK")
            failed += 1
        except Exception as e:
            msg = str(e)
            if expected_substr in msg:
                print(f"OK (erro esperado): {name}")
                passed += 1
            else:
                print("ERRO DIFERENTE DO ESPERADO")
                print(f"  Teste: {name}")
                print(f"  Esperava conter: {expected_substr}")
                print(f"  Recebi: {msg}")
                failed += 1

    return passed, failed


def main() -> None:
    """
    Função principal que coordena a execução dos testes, realiza verificações
    de diretórios e imprime o resumo final (Passou vs Falhou).
    Se algum teste falhar, o script termina com código de saída 1 (erro).
    """
    # sanity checks (mensagens úteis)
    if not OK_DIR.exists():
        raise RuntimeError(f"Diretoria inexistente: {OK_DIR}")
    if not ERR_DIR.exists():
        raise RuntimeError(f"Diretoria inexistente: {ERR_DIR}")
    if not MANIFEST.exists():
        raise RuntimeError(f"Manifest inexistente: {MANIFEST}")

    print("\n" + "#" * 70)
    print("# OK CASES")
    print("#" * 70)
    ok_pass, ok_fail = run_ok_cases()

    print("\n" + "#" * 70)
    print("# ERROR CASES")
    print("#" * 70)
    err_pass, err_fail = run_error_cases()

    print("\n" + "#" * 70)
    print("# RESUMO")
    print("#" * 70)
    print(f"OK cases   : {ok_pass} passed, {ok_fail} failed")
    print(f"Error cases: {err_pass} passed, {err_fail} failed")

    total_fail = ok_fail + err_fail
    if total_fail > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()