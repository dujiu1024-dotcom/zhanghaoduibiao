#!/usr/bin/env python3
import re, sys

src = sys.argv[1]
dst = sys.argv[2]
lines = open(src, encoding='utf-8').read().splitlines()

def esc(s):
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    s = re.sub(r'`([^`]*)`', r'\1', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    return s

def cells(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]

out = []
i = 0
skipped_title = False
while i < len(lines):
    line = lines[i]
    s = line.strip()

    if not s:
        i += 1
        continue

    if s.startswith('# ') and not skipped_title:
        skipped_title = True
        i += 1
        continue

    if s.startswith('### '):
        out.append(f'<h2>{esc(s[4:])}</h2>')
        i += 1
        continue
    if s.startswith('## '):
        out.append(f'<h1>{esc(s[3:])}</h1>')
        i += 1
        continue
    if s.startswith('# '):
        out.append(f'<h1>{esc(s[2:])}</h1>')
        i += 1
        continue

    if s == '---':
        out.append('<hr/>')
        i += 1
        continue

    if s.startswith('|'):
        block = []
        while i < len(lines) and lines[i].strip().startswith('|'):
            block.append(lines[i].strip())
            i += 1
        rows = [r for r in block if not re.match(r'^\|[\s:|-]+\|$', r)]
        if not rows:
            continue
        header = cells(rows[0])
        body = [cells(r) for r in rows[1:]]
        t = ['<table><thead><tr>']
        for c in header:
            t.append(f'<th><p>{esc(c)}</p></th>')
        t.append('</tr></thead><tbody>')
        for row in body:
            t.append('<tr>')
            for c in row:
                t.append(f'<td><p>{esc(c)}</p></td>')
            t.append('</tr>')
        t.append('</tbody></table>')
        out.append(''.join(t))
        continue

    if s.startswith('> '):
        block = []
        while i < len(lines) and lines[i].strip().startswith('> '):
            block.append(esc(lines[i].strip()[2:]))
            i += 1
        out.append('<blockquote>' + ''.join(f'<p>{b}</p>' for b in block) + '</blockquote>')
        continue

    if re.match(r'^- \[[ x]\] ', s):
        out.append(f'<checkbox done="false">{esc(s[6:])}</checkbox>')
        i += 1
        continue

    if s.startswith('- '):
        block = []
        while i < len(lines) and lines[i].strip().startswith('- ') and not lines[i].strip().startswith('- ['):
            block.append(lines[i].strip()[2:])
            i += 1
        out.append('<ul>' + ''.join(f'<li>{esc(b)}</li>' for b in block) + '</ul>')
        continue

    if re.match(r'^\d+\. ', s):
        block = []
        while i < len(lines) and re.match(r'^\d+\. ', lines[i].strip()):
            block.append(re.sub(r'^\d+\. ', '', lines[i].strip()))
            i += 1
        out.append('<ol>' + ''.join(f'<li>{esc(b)}</li>' for b in block) + '</ol>')
        continue

    out.append(f'<p>{esc(s)}</p>')
    i += 1

open(dst, 'w', encoding='utf-8').write('\n'.join(out))
print(f'wrote {dst}, blocks={len(out)}')
