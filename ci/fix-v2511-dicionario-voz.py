from pathlib import Path

p = Path('app-src/components/VoiceCounter.tsx')
s = p.read_text()

# ============================================================
# v2.5.11 — DICIONARIO FONETICO DA VOZ
# Problema observado em campo:
# - usuario fala "umidade" e Android pode transcrever "unidade" / "unidades"
# - a correcao da Classe 3 substituiu a funcao de canonizacao e acabou
#   removendo alguns aliases tecnicos das versoes anteriores
# Regra:
# - o balao OUVI continua mostrando o texto bruto do Android
# - internamente, aliases conhecidos viram os termos tecnicos corretos
# - a trava por numero da classe continua impedindo conversa comum de contar
# ============================================================

old = r'''function canonizarClasseFalado(texto: string) {
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

new = r'''function canonizarClasseFalado(texto: string) {
  let t = normalizar(texto)
    .replace(/\b(?:classe|classi|clase|crasse|crassi|crase|craci)\b/g, 'classe')
    // O Android frequentemente troca "umidade" por palavras muito parecidas.
    .replace(/\b(?:humidade|humanidade|humildade|unidade|unidades|umidades|um idade)\b/g, 'umidade')
    // Variacoes observadas/esperadas para percevejo.
    .replace(/\b(?:percebeu|percebejo|persevejo|persebejo|percevejos|percejo|persejo|perceio|perseio)\b/g, 'percevejo')
    // Variacoes curtas para dano mecanico.
    .replace(/\b(?:mecano|mecanica)\b/g, 'mecanico');

  // O reconhecedor foi observado transformando "3" em "3R".
  // Sem a palavra explicita "erre", 3R no inicio e corrigido para 3.
  const temErreExplicito = /^(?:classe\s*)?(?:3|tres)\s+erre\b/.test(t);
  if (!temErreExplicito) {
    t = t.replace(/^(classe\s*)?3\s*r\b/, (_m, prefixo) => `${prefixo ?? ''}3`);
  }

  return t;
}
'''

if old not in s:
    raise SystemExit('Canonizador v2.5.10 nao encontrado')
s = s.replace(old, new, 1)

# Reforco de contexto: ajuda o Android a preferir o termo tecnico, mas o parser
# continua preparado caso ele devolva unidade/unidades.
ctx_old = "          'Classe 6', 'Classe 7', 'Classe 8', 'classe', 'crasse', 'crassi',\n          'umidade', 'percevejo', 'mecânico',"
ctx_new = "          'Classe 6', 'Classe 7', 'Classe 8', 'classe', 'crasse', 'crassi',\n          'umidade', 'umidade', 'percevejo', 'mecânico',"
if ctx_old in s:
    s = s.replace(ctx_old, ctx_new, 1)

# Tambem reforca exemplos reais da Classe 3.
anchor = "          '3 umidade', '3 umidade e percejo', '3 umidade e dano mecânico',"
if anchor in s and "'3 unidades'" not in s:
    s = s.replace(
        anchor,
        "          '3 umidade', '3 unidades', '3 umidade e percejo', '3 umidade e dano mecânico',",
        1,
    )

for trecho in [
    'unidade|unidades|umidades',
    "'umidade')",
    'percejo|persejo|perceio|perseio',
    "'percevejo')",
    "'mecanico')",
    "(?:3|tres)\\s+erre",
    "if (u && p && m) return 'UPM';",
    "if (u && p) return 'UP';",
    "if (u && m) return 'UM';",
]:
    if trecho not in s:
        raise SystemExit(f'Validacao v2.5.11 falhou: {trecho}')

p.write_text(s)
print('v2.5.11 aplicada: unidade/unidades viram umidade e dicionario tecnico restaurado')
