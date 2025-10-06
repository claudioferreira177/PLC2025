#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversor minimalista de Markdown -> HTML (TP2)

Funcionalidades:
- Cabeçalhos: #, ##, ###
- Bold: **texto**
- Itálico: *texto*
- Lista numerada: "1. item", "2. item", ...
- Link: [texto](url)
- Imagem: ![alt](url)
- Outras linhas viram <p>...</p>

Uso:
    python3 md2html.py exemplo.md > exemplo.html
"""

import re
import sys
from pathlib import Path


# ---------- helpers de inline (ordem importa) ----------

IMG_RE   = re.compile(r'!\[([^\]]+)\]\(([^)]+)\)')              # ![alt](url)
LINK_RE  = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')               # [texto](url)
BOLD_RE  = re.compile(r'\*\*([^\*]+)\*\*')                      # **texto**
ITAL_RE  = re.compile(r'(?<!\*)\*([^*\n]+)\*(?!\*)')            # *texto* (evita **)

def render_inline(text: str) -> str:
    """Aplica transformações inline: imagens, links, bold, itálico."""
    # 1) imagens
    text = IMG_RE.sub(r'<img src="\2" alt="\1"/>', text)
    # 2) links
    text = LINK_RE.sub(r'<a href="\2">\1</a>', text)
    # 3) bold
    text = BOLD_RE.sub(r'<b>\1</b>', text)
    # 4) itálico
    text = ITAL_RE.sub(r'<i>\1</i>', text)
    return text


# ---------- linhas em bloco ----------

HDR_RE = re.compile(r'^(#{1,3})\s+(.*)$')            # #, ##, ### cabeçalhos
OLI_RE = re.compile(r'^\s*\d+\.\s+(.*)$')            # 1. Item

def md_to_html(lines):
    """Converte um iterável de linhas Markdown em HTML (lista de linhas HTML)."""
    html = []
    in_olist = False

    def close_olist():
        nonlocal in_olist
        if in_olist:
            html.append('</ol>')
            in_olist = False

    for raw in lines:
        line = raw.rstrip('\n')

        # Linha vazia fecha parágrafos e listas
        if not line.strip():
            close_olist()
            # linha vazia -> quebra de bloco; não gera tag
            continue

        # Cabeçalhos (#, ##, ###)
        m = HDR_RE.match(line)
        if m:
            close_olist()
            level = len(m.group(1))
            content = render_inline(m.group(2).strip())
            html.append(f'<h{level}>{content}</h{level}>')
            continue

        # Lista numerada
        m = OLI_RE.match(line)
        if m:
            if not in_olist:
                html.append('<ol>')
                in_olist = True
            content = render_inline(m.group(1).strip())
            html.append(f'<li>{content}</li>')
            continue

        # Parágrafo normal
        close_olist()
        html.append(f'<p>{render_inline(line.strip())}</p>')

    # fechar lista se terminar dentro dela
    close_olist()
    return html


# ---------- CLI ----------

def main():
    if len(sys.argv) != 2:
        print("Uso: python3 md2html.py <ficheiro.md>", file=sys.stderr)
        sys.exit(1)

    md_path = Path(sys.argv[1])
    if not md_path.is_file():
        print(f"Erro: ficheiro não encontrado: {md_path}", file=sys.stderr)
        sys.exit(2)

    with md_path.open('r', encoding='utf-8') as f:
        lines = f.readlines()

    html_lines = md_to_html(lines)
    # opcional: embrulhar num HTML mínimo
    print("<!DOCTYPE html>")
    print("<html lang='pt'>")
    print("<meta charset='utf-8'/>")
    print("<body>")
    print("\n".join(html_lines))
    print("</body>")
    print("</html>")


if __name__ == '__main__':
    main()

