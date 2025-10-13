# TP3 — Analisador Léxico (tipo SPARQL)

[![TP3 tests](https://github.com/claudioferreira177/PLC2025/actions/workflows/tp3-tests.yml/badge.svg)](https://github.com/claudioferreira177/PLC2025/actions/workflows/tp3-tests.yml)

## Autor
<img src="../img/perfil.jpg" alt="Foto de perfil" width="100" align="left">

- **Nome:** Cláudio Ferreira  
- **ID:** A108577  

<br clear="left"/>

---

## 📝 Enunciado (resumo)
Construir um analisador **léxico** para uma linguagem de query ao estilo **SPARQL**, capaz de reconhecer:
- **Palavras-chave:** `SELECT`, `WHERE`, `LIMIT` (case-insensitive) e o literal `a` (como atalho de `rdf:type`);
- **Variáveis:** `?nome`, `?desc`, `?s` …;
- **QNames:** `foaf:name`, `dbo:MusicalArtist`, etc.;
- **Strings:** `"texto"` com escapes `\" \\ \n \t \r`;
- **Tags de língua:** `@en`, `@pt-PT`;
- **Inteiros:** `0` ou `[1-9][0-9]*`;
- **Pontuação:** `{ } ( ) . ; , *`;
- **Comentários de linha:** `# ...` até ao fim da linha;
- **Espaços/brancos** ignorados, e **BOM** (`U+FEFF`) ignorado se existir.

---

## ✅ Resultado
O lexer foi implementado com **PLY** (Python) e testado com 3 casos.  
O **CI** (GitHub Actions) corre automaticamente os testes em **Windows** e **Ubuntu**.

---

## 🧩 Estrutura do Trabalho
```text
TP3/
  src/
    lexer.py      # regras PLY e regex dos tokens
    main.py       # CLI: lê o ficheiro e imprime a sequência de tokens
  tests/
    inputs/
      exemplo1.sparql
      exemplo2.sparql
      exemplo3.sparql
    expected/
      exemplo1.tokens.txt
      exemplo2.tokens.txt
      exemplo3.tokens.txt
  run.sh          # atalho para Linux/macOS
  test.ps1        # runner de testes (PowerShell / Windows)
  test.sh         # runner de testes (bash / Unix)
  requirements.txt

