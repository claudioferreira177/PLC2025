# Processamento de Linguagens e Compiladores - Trabalho Prático

**Realizado por:**
- Cláudio Rafael Oliveira Ferreira (A108577)

<img width="180" height="180" alt="image" src="https://github.com/claudioferreira177/PLC2025/blob/main/img/perfil.jpg?raw=true" />

- Marco António Ferreira Abreu (A108578)

<img width="180" height="180" alt="image" src="https://github.com/MarcoAbreu11/PLC2025/blob/main/Imagem/minha_imagem.jpg?raw=true" />

- Nelson Daniel Araújo Sousa (A109068)

<img width="180" height="180" alt="image" src="https://github.com/user-attachments/assets/37338582-83b4-4b7d-933b-ecc82cbd9d91" />

## Objetivo
Este projeto é um compilador funcional para um subconjunto da linguagem **Pascal**, desenvolvido em Python utilizando a biblioteca **PLY (Python Lex-Yacc)**. O sistema traduz código fonte Pascal para instruções assembly compatíveis com uma **Máquina Virtual (VM)** baseada em pilha.



## Funcionalidades Suportadas

* **Tipagem:** Suporte para tipos `integer`, `real`, `boolean`, `char` e `string`.
* **Estruturas de Dados:** Arrays multidimensionais com verificação estática de limites de índice.
* **Controlo de Fluxo:** * Condicionais: `if-then-else`.
    * Ciclos: `while-do`, `repeat-until`, `for-to` e `for-downto`.
* **Subprogramas:** Suporte completo para `procedure` e `function` com variáveis locais, parâmetros e recursividade.
* **Análise Semântica:** Promoção automática de tipos (coerção de integer para real), gestão de escopo (variáveis locais/globais) e proteção de variáveis de controlo de loops.
* **Funções Nativas (Built-ins):** `writeln`, `readln`, `length`, `abs`, `concat`, `sqr`, `sqrt`, `trunc` e `round`.

## Estrutura do Repositório
Dentro da pasta do Compilador temos:
* `src/`: Pasta com o código fonte do compilador.
    * `pascal_analex.py`: Lexer (Analisador Léxico).
    * `parser.py`: Parser (Analisador Sintático) e Geração de Código.
    * `sem.py`: Verificador Semântico e Tabela de Símbolos.
    * `codegen.py`: Emissor de instruções da VM.
    * `context.py`: Gestão de estado do compilador.
* `tests/`: Sistema de testes automatizados.
    * `cases/`: Exemplos de código Pascal para validação.
    * `run_tests.py`: Script para execução de testes de regressão.
* `main.py`: Interface de linha de comando para compilação.

## Como Executar

### Pré-requisitos
É necessário ter o Python 3.8 ou superior instalado e a biblioteca `ply`:
```bash
pip install ply
```

### Compilar um ficheiro .pas
Para compilar e gerar o código assembly:
```bash
python main.py caminho/para/teu_ficheiro.pas
```

### Correr os testes automáticos
Para validar se o compilador está a funcionar corretamente:
```bash
python tests/run_tests.py
```
## Arquitetura da Máquina Virtual
O compilador gera código para uma máquina baseada em pilha. O layout de memória divide-se em:
- Área Global: Variáveis globais acedidas via PUSHG / STOREG.
- Stack Frames: Geridos em chamadas de subprogramas via PUSHL / STOREL.

## Motivo
Este projeto foi realizado para fins académicos na unidade curricular de Processamento de Linguagens e Compiladores.
