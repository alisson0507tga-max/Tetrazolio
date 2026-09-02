from pathlib import Path

p = Path('app-src/components/VoiceCounter.tsx')
s = p.read_text()

# ============================================================
# v2.5.5
# - Classes 6/7/8 com dano múltiplo passam a usar duas etapas.
# - Primeira fala registra os danos em espera.
# - Segunda fala curta escolhe a causa principal.
# - Conversa paralela continua protegida: a resposta principal precisa
#   começar com "principal".
# - Melhora tolerância a transcrições comuns dos termos técnicos.
# ============================================================

# 1) Canonização de termos técnicos que o Android pode transcrever parecido.
old_canon = """function canonizarClasseFalado(texto: string) {\n  return normalizar(texto).replace(\n    /\\b(?:classe|classi|clase|crasse|crassi|crase|craci)\\b/g,\n    'classe',\n  );\n}\n"""
new_canon = """function canonizarClasseFalado(texto: string) {\n  return normalizar(texto)\n    .replace(/\\b(?:classe|classi|clase|crasse|crassi|crase|craci)\\b/g, 'classe')\n    .replace(/\\b(?:humidade|humanidade|um idade)\\b/g, 'umidade')\n    .replace(/\\b(?:percebeu|percebejo|persevejo|percevejos)\\b/g, 'percevejo');\n}\n\nfunction obterRespostaPrincipal(texto: string): Principal | null {\n  const t = canonizarClasseFalado(texto);\n  // Segurança: enquanto aguarda a causa da morte, só aceita resposta\n  // iniciada por \"principal\". Uma conversa comum com a palavra umidade\n  // ou percevejo não fecha a semente sem querer.\n  if (!/^principal\\b/.test(t)) return null;\n  if (/\\bumidade\\b/.test(t)) return 'U';\n  if (/\\bpercevejo\\b/.test(t)) return 'P';\n  if (/\\bmecanico\\b|\\bmecanica\\b|\\bdano\\s+mecanico\\b/.test(t)) return 'M';\n  return null;\n}\n\nfunction principalPertenceAoDano(tipo: Tipo, principal: Principal) {\n  if (tipo === 'UP') return principal === 'U' || principal === 'P';\n  if (tipo === 'UM') return principal === 'U' || principal === 'M';\n  if (tipo === 'UPM') return true;\n  return false;\n}\n"""
if old_canon not in s:
    raise SystemExit('Canonização v2.5.4 não encontrada')
s = s.replace(old_canon, new_canon, 1)

# 2) Estado/ref da semente aguardando causa principal.
anchor_refs = "  const falaBufferTimer = useRef<ReturnType<typeof setTimeout> | null>(null);"
insert_refs = anchor_refs + "\n  const pendenciaPrincipal = useRef<{ classe: number; tipo: Tipo } | null>(null);\n  const [aguardandoPrincipal, setAguardandoPrincipal] = useState(false);"
if 'const pendenciaPrincipal = useRef' not in s:
    if anchor_refs not in s:
        raise SystemExit('Refs do buffer não encontradas')
    s = s.replace(anchor_refs, insert_refs, 1)

# 3) Antes de interpretar um comando normal, resolver a segunda etapa.
old_exec = """  function executar(texto: string) {\n    const parsed = parseCommand(texto);\n"""
new_exec = """  function executar(texto: string) {\n    const pendencia = pendenciaPrincipal.current;\n    if (pendencia) {\n      const t = canonizarClasseFalado(texto);\n\n      if (/^cancelar\\b/.test(t)) {\n        pendenciaPrincipal.current = null;\n        setAguardandoPrincipal(false);\n        setMensagem('Causa principal cancelada. Diga uma nova Classe para continuar.');\n        showToast('↩️ Lançamento pendente cancelado');\n        try { ExpoSpeechRecognitionModule.stop(); } catch {}\n        return;\n      }\n\n      const principal = obterRespostaPrincipal(t);\n      if (!principal) {\n        setMensagem('Aguardando causa principal. Diga: principal umidade, principal percevejo ou principal mecânico.');\n        return;\n      }\n\n      if (!principalPertenceAoDano(pendencia.tipo, principal)) {\n        setMensagem('Essa causa não está entre os danos informados. Diga uma causa principal válida.');\n        return;\n      }\n\n      const totalAntes = getTotalRep(estado.dados, rep);\n      dispatch({\n        type: 'ADICIONAR',\n        rep,\n        classe: pendencia.classe,\n        tipo: pendencia.tipo,\n        danoPrincipal: principal,\n      });\n      ultimaClasse.current = pendencia.classe;\n      pendenciaPrincipal.current = null;\n      setAguardandoPrincipal(false);\n      feedbackOk(`Classe ${CONFIG.NOMES[pendencia.classe]}: ${pendencia.tipo}, principal ${principal} • ${totalAntes + 1}/${CONFIG.MAX_TOTAL}`);\n      // Reinicia a sessão para voltar do modelo de palavra curta ao modelo\n      // de frase completa na próxima semente.\n      try { ExpoSpeechRecognitionModule.stop(); } catch {}\n      return;\n    }\n\n    const parsed = parseCommand(texto);\n"""
if old_exec not in s:
    raise SystemExit('Função executar não encontrada')
s = s.replace(old_exec, new_exec, 1)

# 4) Classes 6-8 com múltiplos danos: não rejeitar; abrir etapa da causa principal.
old_multi = """    if (classe >= 6 && ['UP', 'UM', 'UPM'].includes(parsed.tipo) && !parsed.principal) {\n      setMensagem('Para Classe 6 a 8 com dano múltiplo, diga o principal.');\n      showToast('⚠️ Ex.: Classe 7 UP, principal umidade');\n      return;\n    }\n"""
new_multi = """    if (classe >= 6 && ['UP', 'UM', 'UPM'].includes(parsed.tipo) && !parsed.principal) {\n      pendenciaPrincipal.current = { classe, tipo: parsed.tipo };\n      setAguardandoPrincipal(true);\n      const opcoes = parsed.tipo === 'UP'\n        ? 'principal umidade ou principal percevejo'\n        : parsed.tipo === 'UM'\n          ? 'principal umidade ou principal mecânico'\n          : 'principal umidade, principal percevejo ou principal mecânico';\n      setMensagem(`Classe ${CONFIG.NOMES[classe]}: ${parsed.tipo}. Qual foi a causa principal? Diga ${opcoes}.`);\n      showToast(`🎙️ Agora diga a causa principal: ${opcoes}`);\n      if (Platform.OS !== 'web') Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);\n      // Força uma nova sessão. Na próxima abertura usaremos web_search,\n      // que é melhor para a resposta curta \"principal + causa\".\n      try { ExpoSpeechRecognitionModule.stop(); } catch {}\n      return;\n    }\n"""
if old_multi not in s:
    raise SystemExit('Regra antiga de dano múltiplo 6-8 não encontrada')
s = s.replace(old_multi, new_multi, 1)

# 5) Modelo de linguagem dinâmico: frase normal = free_form; resposta curta = web_search.
old_model = "          EXTRA_LANGUAGE_MODEL: 'web_search',"
new_model = "          EXTRA_LANGUAGE_MODEL: pendenciaPrincipal.current ? 'web_search' : 'free_form',"
if old_model not in s:
    raise SystemExit('Modelo de linguagem Android não encontrado')
s = s.replace(old_model, new_model, 1)

# 6) Contexto com as respostas da segunda etapa.
old_ctx = """          'principal percevejo', 'principal mecânico', 'desfazer', 'quantas',\n"""
new_ctx = """          'principal umidade', 'principal percevejo', 'principal mecânico', 'cancelar',\n          'desfazer', 'quantas',\n"""
if old_ctx in s:
    s = s.replace(old_ctx, new_ctx, 1)

# 7) Dar um pouco mais de tempo para fechar UP/UM/UPM antes de processar.
s = s.replace('    }, 800);', '    }, 1050);', 1)

# 8) Ao parar manualmente ou sair da tela, limpar qualquer pendência.
cleanup_anchor = "      falaBuffer.current = '';\n      try { ExpoSpeechRecognitionModule.abort(); } catch {}"
cleanup_new = "      falaBuffer.current = '';\n      pendenciaPrincipal.current = null;\n      try { ExpoSpeechRecognitionModule.abort(); } catch {}"
if cleanup_anchor in s:
    s = s.replace(cleanup_anchor, cleanup_new, 1)

stop_anchor = "      falaBuffer.current = '';\n      try { ExpoSpeechRecognitionModule.stop(); } catch {}"
stop_new = "      falaBuffer.current = '';\n      pendenciaPrincipal.current = null;\n      setAguardandoPrincipal(false);\n      try { ExpoSpeechRecognitionModule.stop(); } catch {}"
if stop_anchor in s:
    s = s.replace(stop_anchor, stop_new, 1)

# 9) Mostrar visualmente quando o app está esperando a causa da morte.
old_title = "<Text style={[styles.title, { color: text }]}>🎙️ CONTAGEM POR VOZ</Text>"
new_title = "<Text style={[styles.title, { color: text }]}>{aguardandoPrincipal ? '🎯 CAUSA PRINCIPAL' : '🎙️ CONTAGEM POR VOZ'}</Text>"
if old_title in s:
    s = s.replace(old_title, new_title, 1)

# Validações para não gerar APK sem a lógica nova.
for trecho in [
    'function obterRespostaPrincipal',
    'principalPertenceAoDano',
    'const pendenciaPrincipal = useRef',
    'Qual foi a causa principal?',
    "EXTRA_LANGUAGE_MODEL: pendenciaPrincipal.current ? 'web_search' : 'free_form'",
    '}, 1050);',
    "'🎯 CAUSA PRINCIPAL'",
]:
    if trecho not in s:
        raise SystemExit(f'Validação v2.5.5 falhou: {trecho}')

p.write_text(s)
print('v2.5.5 aplicada: causa principal em 2 etapas + reconhecimento técnico melhorado')
