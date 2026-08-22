from pathlib import Path

p = Path('app-src/components/VoiceCounter.tsx')
s = p.read_text()

# ============================================================
# v2.5.10 — CORRECAO CLASSE 3 / 3R
# Problema observado em campo:
# - comando iniciado por 3 comum nao entrava em todos os regex do buffer/gatilho
# - Android podia transcrever o 3 simples como "3R" devido ao vocabulario sugerido
# Regra nova:
# - "3 ..." = Classe 3
# - "3 erre ..." / "tres erre ..." = Classe 3R
# ============================================================

# 1) Canonizacao: se o Android devolver "3R" sem a palavra falada "erre",
# tratamos como Classe 3. A Classe 3R passa a depender do termo explicito "erre".
start = s.find('function canonizarClasseFalado(texto: string) {')
end = s.find('\n}\n', start)
if start == -1 or end == -1:
    raise SystemExit('canonizarClasseFalado nao encontrada')
end += 3
nova_canon = r'''function canonizarClasseFalado(texto: string) {
  let t = normalizar(texto).replace(
    /\b(?:classe|classi|clase|crasse|crassi|crase|craci)\b/g,
    'classe',
  );

  // O reconhecedor foi observado transformando "3" em "3R".
  // Sem a palavra explicita "erre", 3R no inicio e corrigido para 3.
  const temErreExplicito = /^(?:classe\s*)?(?:3|tres)\s+erre\b/.test(t);
  if (!temErreExplicito) {
    t = t.replace(/^(classe\s*)?3\s*r\b/, (_m, prefixo) => `${prefixo ?? ''}3`);
  }

  return t;
}
'''
s = s[:start] + nova_canon + s[end:]

# 2) ObterClasse: 3R somente com "erre" explicito.
old_3r = "  // 3R precisa ser resolvida antes da Classe 3 comum.\n  if (/^(?:classe\\s*)?(?:3\\s*r|3r|tres\\s*r|tres\\s*erre)\\b/.test(inicio)) return 3;"
new_3r = "  // 3R somente quando o usuario disser explicitamente 'erre'.\n  if (/^(?:classe\\s*)?(?:3|tres)\\s+erre\\b/.test(inicio)) return 3;"
if old_3r not in s:
    raise SystemExit('Regra antiga de 3R nao encontrada')
s = s.replace(old_3r, new_3r, 1)

# 3) Corrigir todos os regex que pulavam a Classe 3 simples.
repls = {
    r"(?:1|2|3\s*r|3r|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)":
    r"(?:1|2|3|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)",
}
for old, new in repls.items():
    if old not in s:
        raise SystemExit('Regex sem Classe 3 simples nao encontrado')
    s = s.replace(old, new)

# 4) Vocabulario: retirar o vies para "3R" e reforcar Classe 3.
s = s.replace("'Classe 3R'", "'Classe 3 erre'")
s = s.replace("'3R'", "'3 erre'")

# Insere exemplos da Classe 3 no contexto, se ainda nao existirem.
anchor = "          '2 umidade', '2 umidade e percejo', '2 umidade e dano mecânico',"
if anchor in s and "'3 umidade'" not in s:
    s = s.replace(
        anchor,
        "          '2 umidade', '2 umidade e percejo', '2 umidade e dano mecânico',\n"
        "          '3 umidade', '3 umidade e percejo', '3 umidade e dano mecânico',\n"
        "          '3 umidade e percejo e dano mecânico', '3 erre umidade',",
        1,
    )

# 5) Validacoes.
for trecho in [
    "(?:3|tres)\\s+erre",
    "'3 umidade'",
    "'3 erre umidade'",
    "(?:1|2|3|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)",
    "if (u && p && m) return 'UPM';",
    "if (u && p) return 'UP';",
    "if (u && m) return 'UM';",
]:
    if trecho not in s:
        raise SystemExit(f'Validacao v2.5.10 falhou: {trecho}')

p.write_text(s)
print('v2.5.10 aplicada: Classe 3 reconhecida; 3R exige falar erre')
