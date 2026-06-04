# -*- coding: utf-8 -*-
"""Preprocess final_paper.md -> _build.md for a high-quality LaTeX build.

Transforms (none touch numbers / claims / citations):
  1. Lift the H1 title out (passed to pandoc via --metadata).
  2. Convert the 62-entry reference list into a real thebibliography block
     (raw-LaTeX fenced block), so entries no longer collapse into one paragraph.
  3. Merge each "**图 X** caption" paragraph into the following image so pandoc
     emits a proper captioned figure float (no redundant double-caption).
  4. Drop the standalone '---' section-separator rules (ugly \\rule lines).
"""
import re

SRC = 'final_paper.md'
OUT = '_build.md'

text = open(SRC, encoding='utf-8').read()
lines = text.split('\n')

# --- 2. references -> thebibliography -------------------------------------
ref_start = next(i for i, l in enumerate(lines) if l.strip() == '## 参考文献')
foot_idx = next(i for i, l in enumerate(lines) if l.startswith('*定稿'))
ref_lines = [l.strip() for l in lines[ref_start + 1:foot_idx]
             if re.match(r'^\[\d+\]', l.strip())]


def esc(t):
    # escape LaTeX specials that occur in the refs, then italicise *...*
    t = t.replace('\\', r'\textbackslash{}')
    t = t.replace('&', r'\&').replace('%', r'\%').replace('#', r'\#')
    t = t.replace('_', r'\_')
    t = re.sub(r'\*([^*]+)\*', r'\\textit{\1}', t)
    return t


bib = ['```{=latex}', r'\begin{thebibliography}{99}',
       r'\setlength{\itemsep}{2pt plus 1pt}']
for l in ref_lines:
    m = re.match(r'^\[(\d+)\]\s*(.*)$', l)
    bib.append(r'\bibitem{ref%s} %s' % (m.group(1), esc(m.group(2))))
bib += [r'\end{thebibliography}', '```']

lines = lines[:ref_start] + bib + [''] + lines[foot_idx:]
text = '\n'.join(lines)

# --- 1. lift title ---------------------------------------------------------
m = re.match(r'\A# (.*)\n', text)
title = m.group(1).strip()
text = text[m.end():]
open('_title.txt', 'w', encoding='utf-8').write(title)

# --- 4. drop standalone '---' rules (keep a blank line in place) ----------
text = re.sub(r'(?m)^---[ \t]*$', '', text)

# --- 3. merge figure captions into the image (captioned float) ------------
fig = re.compile(r'(?m)^\*\*(图 [\d\-]+)\*\*([^\n]*)\n\n!\[[^\]]*\]\(([^)]+)\)')
n_fig = len(fig.findall(text))
text = fig.sub(lambda m: '![**%s**%s](%s)' % (m.group(1), m.group(2), m.group(3)), text)

open(OUT, 'w', encoding='utf-8').write(text)
print('refs=%d figures_merged=%d title=%r' % (len(ref_lines), n_fig, title[:30]))
