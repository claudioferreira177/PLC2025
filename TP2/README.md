# 🧩 TP2 — Conversor de Markdown para HTML

## 👨‍💻 Autor
<img src="../img/perfil.jpg" alt="Foto de perfil" width="100" align="left">

- **Nome:** Cláudio Ferreira  
- **ID:** A108577  

<br clear="left"/>

---

## 📝 Enunciado
Criar em **Python** um pequeno conversor de **Markdown para HTML**, capaz de traduzir os elementos descritos na secção *"Basic Syntax"* da [Markdown Cheat Sheet](https://www.markdownguide.org/cheat-sheet/).

O programa deve ler um ficheiro `.md` e gerar o ficheiro `.html` correspondente, convertendo corretamente:
- Cabeçalhos (`#`, `##`, `###`)
- Texto em **negrito** (`**texto**`)
- Texto em *itálico* (`*texto*`)
- Listas numeradas (`1. item`)
- Links (`[texto](url)`)
- Imagens (`![alt](url)`)

---

## ⚙️ Estrutura do Trabalho

📁 **TP2/**  
├── `md2html.py` → Script Python que converte Markdown para HTML.  
├── `exemplo.md` → Ficheiro Markdown de teste (baseado nos exemplos do professor).  
├── `exemplo.html` → Saída gerada automaticamente a partir de `exemplo.md`.  
└── `README.md` → Documento explicativo do TP2 (este ficheiro).  

---

## 🚀 Execução

Para gerar o HTML a partir do Markdown:

```bash
python md2html.py exemplo.md exemplo.html
