from pathlib import Path

p = Path('app-src/components/VoiceCounter.tsx')
s = p.read_text()

old = """  if (/\\bparar(?:\\s+voz)?\\b/.test(t)) return { kind: 'stop' };\n  if (/\\bdesfazer\\b|\\bvoltar\\s+ultimo\\b/.test(t)) return { kind: 'undo' };\n  if (/\\bquantas\\b|\\bquanto\\s+tem\\b|\\bcontagem\\b/.test(t)) return { kind: 'count' };\n\n  const classe = obterClasse(t);\n"""
new = """  if (/\\bparar(?:\\s+voz)?\\b/.test(t)) return { kind: 'stop' };\n  if (/\\bdesfazer\\b|\\bvoltar\\s+ultimo\\b/.test(t)) return { kind: 'undo' };\n  if (/\\bquantas\\b|\\bquanto\\s+tem\\b|\\bcontagem\\b/.test(t)) return { kind: 'count' };\n\n  // Segurança contra conversa paralela: lançamento só é aceito se o comando\n  // COMEÇAR com \"Classe\". Palavras soltas como umidade, percevejo ou\n  // mecânico ficam totalmente ignoradas, mesmo se houver uma classe anterior.\n  if (!/^classe\\b/.test(t)) {\n    return { kind: 'invalid', message: 'Ignorado. Para lançar, comece falando: Classe…' };\n  }\n\n  const classe = obterClasse(t);\n"""

if old not in s:
    raise SystemExit('Ponto do gatilho de classe nao encontrado')
s = s.replace(old, new, 1)

# Não reaproveitar a última classe para um lançamento novo. Isso impede que
# uma conversa com palavras técnicas seja aplicada à semente anterior.
old2 = """    let classe = parsed.classe;\n    if (classe == null) classe = ultimaClasse.current;\n    if (classe == null) {\n      setMensagem('Diga a classe primeiro. Ex.: Classe 4 umidade.');\n      return;\n    }\n"""
new2 = """    const classe = parsed.classe;\n    if (classe == null) {\n      setMensagem('Comando ignorado. Diga a classe completa. Ex.: Classe 4 umidade.');\n      return;\n    }\n"""

if old2 not in s:
    raise SystemExit('Fallback de ultima classe nao encontrado')
s = s.replace(old2, new2, 1)

# Texto da interface explicando a trava.
s = s.replace(
    'Toque uma vez em OUVIR; depois é só falar. Ex.:',
    'Toque uma vez em OUVIR. Para contabilizar, cada comando deve começar com “Classe”. Ex.:',
)

# Validações para a build falhar caso a trava não entre.
for trecho in [
    "if (!/^classe\\b/.test(t))",
    "const classe = parsed.classe;",
    "Comando ignorado. Diga a classe completa.",
]:
    if trecho not in s:
        raise SystemExit(f'Validacao 2.5.3 falhou: {trecho}')

p.write_text(s)
print('v2.5.3 aplicada: gatilho Classe obrigatório para evitar lançamentos acidentais')
