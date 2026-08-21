from pathlib import Path

p = Path('app-src/components/VoiceCounter.tsx')
s = p.read_text()

# ============================================================
# v2.5.7 — COMANDO CURTO GRATUITO
# Objetivo: reduzir o esforço do reconhecedor Android.
# O número no começo vira o gatilho da contagem.
# Exemplos:
#   2 umidade e percejo e dano mecânico
#   6 umidade e percejo causa umidade
# ============================================================

# 1) A classe pode vir só pelo número/palavra no começo, sem falar "Classe".
start = s.find('function obterClasse(t: string): number | null {')
end = s.find('\nfunction obterExtra', start)
if start == -1 or end == -1:
    raise SystemExit('Função obterClasse não encontrada')

nova_obter_classe = r'''function obterClasse(t: string): number | null {
  const inicio = t.trim();

  // 3R precisa ser resolvida antes da Classe 3 comum.
  if (/^(?:classe\s*)?(?:3\s*r|3r|tres\s*r|tres\s*erre)\b/.test(inicio)) return 3;

  const mapaNumeros: Record<string, number> = {
    '1': 0, um: 0, uma: 0,
    '2': 1, dois: 1, duas: 1,
    '3': 2, tres: 2,
    '4': 4, quatro: 4,
    '5': 5, cinco: 5,
    '6': 6, seis: 6,
    '7': 7, sete: 7,
    '8': 8, oito: 8,
  };

  const m = inicio.match(/^(?:classe\s*)?(1|2|3|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)\b/);
  if (!m) return null;
  return mapaNumeros[m[1]] ?? null;
}
'''
s = s[:start] + nova_obter_classe + s[end:]

# 2) Segurança: em vez de exigir a palavra Classe, exige que a frase COMEÇE
# com um número de classe (ou mantém compatibilidade com "Classe 2...").
old_gate = r'''  if (!/^classe\b/.test(t)) {
    return { kind: 'invalid', message: 'Ignorado. Para lançar, comece falando: Classe…' };
  }
'''
new_gate = r'''  if (!/^(?:classe\s*)?(?:1|2|3\s*r|3r|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)\b/.test(t)) {
    return { kind: 'invalid', message: 'Ignorado. Para lançar, comece com o número da classe.' };
  }
'''
if old_gate not in s:
    raise SystemExit('Trava antiga de Classe não encontrada')
s = s.replace(old_gate, new_gate, 1)

# 3) Classes 6–8 podem informar a causa na MESMA frase:
# "6 umidade e percejo causa umidade".
start = s.find('function obterPrincipal(t: string): Principal | undefined {')
end = s.find('\nfunction obterDano', start)
if start == -1 or end == -1:
    raise SystemExit('Função obterPrincipal não encontrada')

nova_principal = r'''function obterPrincipal(t: string): Principal | undefined {
  if (/\b(?:principal|causa)\s+(?:umidade|u)\b/.test(t)) return 'U';
  if (/\b(?:principal|causa)\s+(?:percevejo|p)\b/.test(t)) return 'P';
  if (/\b(?:principal|causa)\s+(?:mecanico|mecanica|m)\b/.test(t)) return 'M';
  return undefined;
}
'''
s = s[:start] + nova_principal + s[end:]

# A segunda etapa continua existindo como reserva, mas aceita "causa" também.
s = s.replace(
    "if (!/^principal\\b/.test(t)) return null;",
    "if (!/^(?:principal|causa)\\b/.test(t)) return null;",
    1,
)

# 4) Variações curtas que o Android costuma produzir para percevejo.
old_percejo = ".replace(/\\b(?:percebeu|percebejo|persevejo|persebejo|percevejos)\\b/g, 'percevejo')"
new_percejo = ".replace(/\\b(?:percebeu|percebejo|persevejo|persebejo|percevejos|percejo|persejo|perceio|perseio)\\b/g, 'percevejo')"
if old_percejo in s:
    s = s.replace(old_percejo, new_percejo, 1)
elif 'percejo' not in s:
    raise SystemExit('Canonização de percevejo não encontrada')

# 5) O separador/buffer também precisa reconhecer comandos iniciados só por número.
old_sep = r"const re = /\bclasse\s*(?:1|2|3\s*r|3r|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)\b/gi;"
new_sep = r"const re = /\b(?:classe\s*)?(?:1|2|3\s*r|3r|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)\b/gi;"
if old_sep not in s:
    raise SystemExit('Regex de separarComandos não encontrada')
s = s.replace(old_sep, new_sep, 1)

old_same_a = r"const classeA = a.match(/^classe\s+(?:1|2|3\s*r|3r|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)\b/)?.[0];"
new_same_a = r"const classeA = a.match(/^(?:classe\s*)?(?:1|2|3\s*r|3r|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)\b/)?.[0];"
old_same_n = r"const classeN = n.match(/^classe\s+(?:1|2|3\s*r|3r|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)\b/)?.[0];"
new_same_n = r"const classeN = n.match(/^(?:classe\s*)?(?:1|2|3\s*r|3r|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)\b/)?.[0];"
if old_same_a not in s or old_same_n not in s:
    raise SystemExit('Regex do buffer por classe não encontrada')
s = s.replace(old_same_a, new_same_a, 1).replace(old_same_n, new_same_n, 1)

# 6) Vocabulário curto e exemplos exatos do uso real.
ctx_anchor = "          'umidade e percevejo', 'umidade e dano mecânico', 'percevejo e dano mecânico',\n          'umidade percevejo dano mecânico',"
ctx_new = "          '1', '2', '3', '3R', '4', '5', '6', '7', '8',\n          '2 umidade', '2 umidade e percejo', '2 umidade e dano mecânico',\n          '2 umidade e percejo e dano mecânico',\n          '6 umidade e percejo causa umidade',\n          '7 umidade e dano mecânico causa mecânico',\n          '8 umidade percejo dano mecânico causa percejo',\n          'umidade e percevejo', 'umidade e dano mecânico', 'percevejo e dano mecânico',\n          'umidade percevejo dano mecânico',"
if ctx_anchor in s:
    s = s.replace(ctx_anchor, ctx_new, 1)
else:
    raise SystemExit('ContextualStrings de danos não encontrado')

# 7) Interface explicando o padrão novo.
s = s.replace(
    'Toque uma vez em OUVIR. Para contabilizar, cada comando deve começar com “Classe”. Ex.:',
    'Toque uma vez em OUVIR. Para contabilizar, comece pelo número da classe. Ex.:',
)
s = s.replace('“Classe 4 umidade”', '“2 umidade e percejo”')
s = s.replace('“Classe 7 UP, principal umidade”', '“6 umidade e percejo causa umidade”')
s = s.replace('Diga a classe completa. Ex.: Classe 4 umidade.', 'Comece pelo número. Ex.: 2 umidade e percejo.')
s = s.replace('Diga uma nova Classe para continuar.', 'Diga um novo número de classe para continuar.')
s = s.replace('principal umidade, principal percevejo ou principal mecânico', 'causa umidade, causa percejo ou causa mecânico')
s = s.replace('principal umidade ou principal percevejo', 'causa umidade ou causa percejo')
s = s.replace('principal umidade ou principal mecânico', 'causa umidade ou causa mecânico')

# 8) Um pouco mais ágil sem sacrificar a união de 2–3 danos.
s = s.replace(
    'const esperaMs = terminaComE ? 650 : (isFinal ? 280 : 430);',
    'const esperaMs = terminaComE ? 500 : (isFinal ? 220 : 340);',
    1,
)

# Validações obrigatórias.
for trecho in [
    "(?:principal|causa)",
    "comece com o número da classe",
    "2 umidade e percejo e dano mecânico",
    "6 umidade e percejo causa umidade",
    "const esperaMs = terminaComE ? 500 : (isFinal ? 220 : 340);",
    "if (u && p && m) return 'UPM';",
    "if (u && p) return 'UP';",
    "if (u && m) return 'UM';",
]:
    if trecho not in s:
        raise SystemExit(f'Validação v2.5.7 falhou: {trecho}')

p.write_text(s)
print('v2.5.7 aplicada: comando curto por número + causa na mesma frase + resposta mais rápida')
