from pathlib import Path

p = Path('app-src/components/VoiceCounter.tsx')
s = p.read_text()

# ============================================================
# v2.5.13 — separar corretamente Classe 3 e Classe 3R
# Evidencia do teste em campo:
# - Android transcreveu literalmente "classe 3R percevejo"
# - o app converteu 3R para Classe 3
# Regra final:
# - 3 / tres = Classe 3
# - 3R / 3 R / 3 erre / tres erre = Classe 3R
# ============================================================

# 1) Não rebaixar mais uma transcrição 3R correta para Classe 3.
old_demote = r'''  // O reconhecedor foi observado transformando "3" em "3R".
  // Sem a palavra explicita "erre", 3R no inicio e corrigido para 3.
  const temErreExplicito = /^(?:classe\s*)?(?:3|tres)\s+erre\b/.test(t);
  if (!temErreExplicito) {
    t = t.replace(/^(classe\s*)?3\s*r\b/, (_m, prefixo) => `${prefixo ?? ''}3`);
  }

'''
if old_demote not in s:
    raise SystemExit('Regra que convertia 3R em Classe 3 nao encontrada')
s = s.replace(old_demote, '', 1)

# 2) ObterClasse resolve 3R antes do 3 comum.
old_3r = "  // 3R somente quando o usuario disser explicitamente 'erre'.\n  if (/^(?:classe\\s*)?(?:3|tres)\\s+erre\\b/.test(inicio)) return 3;"
new_3r = "  // Classe 3R: aceita tanto a transcricao '3R' quanto '3 erre'.\n  if (/^(?:classe\\s*)?(?:3\\s*r|3r|3\\s+erre|tres\\s+erre)\\b/.test(inicio)) return 3;"
if old_3r not in s:
    raise SystemExit('Regra v2.5.10 de 3R nao encontrada')
s = s.replace(old_3r, new_3r, 1)

# 3) Gatilho, separador e buffer também precisam aceitar 3R, sem perder o 3 simples.
plain = r'(?:1|2|3|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)'
with_3r = r'(?:3\s*r|3r|3\s+erre|tres\s+erre|1|2|3|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)'
count = s.count(plain)
if count < 3:
    raise SystemExit(f'Esperava pelo menos 3 regex de classe; achei {count}')
s = s.replace(plain, with_3r)

# 4) Reforça exemplos falados sem voltar a enviesar o Android para 3R em todo "3".
anchor = "          '3 umidade', '3 unidades', '3 umidade e percejo', '3 umidade e dano mecânico',"
if anchor in s and "'3 erre percevejo'" not in s:
    s = s.replace(
        anchor,
        "          '3 umidade', '3 unidades', '3 umidade e percejo', '3 umidade e dano mecânico',\n"
        "          '3 erre umidade', '3 erre percevejo', '3 erre dano mecânico',",
        1,
    )

# 5) Validações das duas classes.
for trecho in [
    "(?:3\\s*r|3r|3\\s+erre|tres\\s+erre)",
    "'3 erre percevejo'",
    "'3 umidade'",
    "if (u && p && m) return 'UPM';",
    "if (u && p) return 'UP';",
    "if (u && m) return 'UM';",
]:
    if trecho not in s:
        raise SystemExit(f'Validacao v2.5.13 falhou: {trecho}')

p.write_text(s)
print('v2.5.13 aplicada: 3 fica Classe 3; 3R/3 erre fica Classe 3R')
