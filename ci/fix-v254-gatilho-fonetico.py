from pathlib import Path

p = Path('app-src/components/VoiceCounter.tsx')
s = p.read_text()

# Aceita variações comuns que o reconhecimento pode produzir para a palavra
# "classe" (ex.: crasse/crassi/classi), mas canoniza tudo para "classe".
anchor = """function normalizar(texto: string) {\n  return texto\n    .normalize('NFD')\n    .replace(/[\\u0300-\\u036f]/g, '')\n    .toLowerCase()\n    .replace(/[.,;:!?()]/g, ' ')\n    .replace(/\\s+/g, ' ')\n    .trim();\n}\n"""
helper = anchor + """\nfunction canonizarClasseFalado(texto: string) {\n  return normalizar(texto).replace(\n    /\\b(?:classe|classi|clase|crasse|crassi|crase|craci)\\b/g,\n    'classe',\n  );\n}\n"""
if 'function canonizarClasseFalado' not in s:
    if anchor not in s:
        raise SystemExit('Funcao normalizar nao encontrada')
    s = s.replace(anchor, helper, 1)

# Toda interpretação passa primeiro pela canonização fonética.
s = s.replace(
    "  const t = normalizar(texto);",
    "  const t = canonizarClasseFalado(texto);",
    1,
)

# O buffer também guarda a versão canonizada. Isso preserva a separação de
# comandos consecutivos mesmo se o Android escrever "crassi 2".
s = s.replace(
    "    const nova = transcript.trim();",
    "    const nova = canonizarClasseFalado(transcript.trim());",
    1,
)

# Contexto extra para ajudar o reconhecedor a preferir a palavra correta.
old_ctx = """          'Classe 1', 'Classe 2', 'Classe 3', 'Classe 3R', 'Classe 4', 'Classe 5',\n          'Classe 6', 'Classe 7', 'Classe 8', 'umidade', 'percevejo', 'mecânico',"""
new_ctx = """          'Classe 1', 'Classe 2', 'Classe 3', 'Classe 3R', 'Classe 4', 'Classe 5',\n          'Classe 6', 'Classe 7', 'Classe 8', 'classe', 'crasse', 'crassi',\n          'umidade', 'percevejo', 'mecânico',"""
if old_ctx in s:
    s = s.replace(old_ctx, new_ctx, 1)

# Validações: mantém a trava de segurança e garante a canonização.
for trecho in [
    'function canonizarClasseFalado',
    "const t = canonizarClasseFalado(texto);",
    "const nova = canonizarClasseFalado(transcript.trim());",
    "if (!/^classe\\b/.test(t))",
    "if (u && p && m) return 'UPM';",
    "if (u && p) return 'UP';",
    "if (u && m) return 'UM';",
]:
    if trecho not in s:
        raise SystemExit(f'Validacao 2.5.4 falhou: {trecho}')

p.write_text(s)
print('v2.5.4 aplicada: gatilho Classe tolerante a crasse/crassi/classi, mantendo segurança')
