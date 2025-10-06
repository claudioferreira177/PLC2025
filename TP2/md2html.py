import re
import sys
import html

HEADER_RE = re.compile(r'^(#{1,6})\s+(.*)$')
OL_ITEM_RE = re.compile(r'^\s*\d+\.\s+(.*)$')
IMG_RE   = re.compile(r'!\[([^\]]*)\]\(([^)\s]+)\)')
LINK_RE  = re.compile(r'\[([^\]]+)\]\(([^)\s]+)\)')
BOLD_RE  = re.compile(r'\*\*(.+?)\*\*')
ITAL_RE  = re.compile(r'(?<!\*)\*(?!\s)(.+?)\*(?!\*)')  # evita conflitos com **

def convert_inline(text: str) -> str:
    text = html.escape(text)
  
    text = IMG_RE.sub(r'<img src="\2" alt="\1" />', text)

    text = LINK_RE.sub(r'<a href="\2">\1</a>', text)

    text = BOLD_RE.sub(r'<b>\1</b>', text)

    text = ITAL_RE.sub(r'<i>\1</i>', text)

    return text

def markdown_to_html(lines):
    out = []
    in_ol = False 

    def close_ol():
        nonlocal in_ol
        if in_ol:
            out.append('</ol>')
            in_ol = False

    for raw in lines:
        line = raw.rstrip('\n')

        if not line.strip():
            close_ol()
            continue

        m = HEADER_RE.match(line)
        if m:
            close_ol()
            level = len(m.group(1))
            content = convert_inline(m.group(2).strip())
            out.append(f'<h{level}>{content}</h{level}>')
            continue

        m = OL_ITEM_RE.match(line)
        if m:
            if not in_ol:
                out.append('<ol>')
                in_ol = True
            content = convert_inline(m.group(1).strip())
            out.append(f'  <li>{content}</li>')
            continue
        else:
            close_ol()
        content = convert_inline(line.strip())
        out.append(f'<p>{content}</p>')

    close_ol()
    return '\n'.join(out) + '\n'

def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.readlines()

    html_out = markdown_to_html(lines)
    sys.stdout.write(html_out)

if __name__ == '__main__':
    main()

