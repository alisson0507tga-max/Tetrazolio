from pathlib import Path
import re

p = Path('app-src/app/(tabs)/relatorio.tsx')
s = p.read_text()

# ============================================================
# v2.5.14 — IMPRESSAO/PDF SEM DUPLO DISPARO
# Problema observado no Android:
#   Another print request is already in progress
# Causa: um segundo toque consegue entrar enquanto a primeira solicitacao
# de impressao ainda esta ativa.
# Regra: somente uma solicitacao de impressao por vez.
# ============================================================

LOCK_NAME = 'impressaoPdfEmAndamento'

# 1) Trava em nivel de modulo: funciona mesmo antes de um rerender do React.
if f'let {LOCK_NAME} = false;' not in s:
    lines = s.splitlines()
    last_import = max(i for i, line in enumerate(lines) if line.startswith('import '))
    lines.insert(last_import + 1, '')
    lines.insert(last_import + 2, f'let {LOCK_NAME} = false;')
    s = '\n'.join(lines) + ('\n' if s.endswith('\n') else '')

# 2) Localiza a funcao de impressao pelo proprio tratamento de erro exibido
# no aparelho. Fazemos isso para nao depender do nome da funcao.
error_pos = s.find('Erro ao imprimir')
if error_pos == -1:
    raise SystemExit('Nao foi localizado o tratamento "Erro ao imprimir" no Relatorio')

prefix = s[:error_pos]
patterns = [
    re.compile(r'async\s+function\s+([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{', re.M),
    re.compile(r'const\s+([A-Za-z_$][\w$]*)\s*=\s*async\s*\([^)]*\)\s*=>\s*\{', re.M),
    re.compile(r'const\s+([A-Za-z_$][\w$]*)\s*=\s*async\s*[A-Za-z_$][\w$]*\s*=>\s*\{', re.M),
]

best = None
for pat in patterns:
    matches = list(pat.finditer(prefix))
    if matches:
        m = matches[-1]
        if best is None or m.start() > best.start():
            best = m

if best is None:
    raise SystemExit('Nao foi possivel localizar a funcao async de impressao')

func_name = best.group(1)
open_brace = best.end() - 1

# Scanner simples de TS/JS para achar a chave que fecha a funcao, ignorando
# strings, templates e comentarios.
def find_matching_brace(text: str, start: int) -> int:
    depth = 0
    i = start
    quote = None
    line_comment = False
    block_comment = False
    escape = False
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ''

        if line_comment:
            if c == '\n':
                line_comment = False
            i += 1
            continue
        if block_comment:
            if c == '*' and n == '/':
                block_comment = False
                i += 2
                continue
            i += 1
            continue
        if quote:
            if escape:
                escape = False
            elif c == '\\':
                escape = True
            elif c == quote:
                quote = None
            i += 1
            continue

        if c == '/' and n == '/':
            line_comment = True
            i += 2
            continue
        if c == '/' and n == '*':
            block_comment = True
            i += 2
            continue
        if c in ('\"', "'", '`'):
            quote = c
            i += 1
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise SystemExit('Chave final da funcao de impressao nao encontrada')

close_brace = find_matching_brace(s, open_brace)
body = s[open_brace + 1:close_brace]

if f'if ({LOCK_NAME})' not in body:
    guard = f'''\n    if ({LOCK_NAME}) {{\n      showToast('⏳ Aguarde: o PDF já está sendo gerado.');\n      return;\n    }}\n    {LOCK_NAME} = true;\n    try {{'''
    footer = f'''\n    }} finally {{\n      {LOCK_NAME} = false;\n    }}\n  '''
    s = s[:open_brace + 1] + guard + body + footer + s[close_brace:]

# 3) Validacoes: a funcao precisa continuar contendo a chamada de impressao
# e o tratamento existente; nenhuma regra de analise e tocada.
func_start = best.start()
check_end = min(len(s), func_start + 12000)
chunk = s[func_start:check_end]
for trecho in [
    f'if ({LOCK_NAME})',
    f'{LOCK_NAME} = true',
    f'{LOCK_NAME} = false',
    'Erro ao imprimir',
]:
    if trecho not in chunk:
        raise SystemExit(f'Validacao v2.5.14 falhou: {trecho}')

p.write_text(s)
print(f'v2.5.14 aplicada: funcao {func_name} protegida contra impressao simultanea')
