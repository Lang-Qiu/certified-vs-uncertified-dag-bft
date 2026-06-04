# -*- coding: utf-8 -*-
"""Post-process final_paper.tex after pandoc: make long \texttt{} paths/identifiers
breakable so they never overflow the right margin (user task 7)."""
import re

F = 'final_paper.tex'
t = open(F, encoding='utf-8').read()


def brk(m):
    s = m.group(1)
    s = s.replace(r'\_', r'\_\allowbreak{}')   # underscore first (it's a 2-char token)
    s = s.replace('/', r'/\allowbreak{}')
    s = s.replace('.', r'.\allowbreak{}')
    s = s.replace('-', r'-\allowbreak{}')
    return r'\texttt{' + s + '}'


t2, n = re.subn(r'\\texttt\{([^{}]*)\}', brk, t)
open(F, 'w', encoding='utf-8').write(t2)
print(f'made {n} \\texttt{{}} spans breakable')
