from pathlib import Path

p = Path('app-src/components/VoiceCounter.tsx')
s = p.read_text()

# ============================================================
# v2.5.6
# - transcrição parcial ao vivo em um balão
# - reconhecimento reage a resultados interim, não só ao final
# - debounce muito menor para lançamento rápido
# - mantém buffer suficiente para UP / UM / UPM
# - melhora revisões do reconhecedor na mesma Classe
# ============================================================

# 1) Estado visual do que o Android está ouvindo.
anchor_refs = "  const [aguardandoPrincipal, setAguardandoPrincipal] = useState(false);"
new_refs = anchor_refs + "\n  const [falaAoVivo, setFalaAoVivo] = useState('');\n  const falaVisualTimer = useRef<ReturnType<typeof setTimeout> | null>(null);"
if 'const [falaAoVivo, setFalaAoVivo]' not in s:
    if anchor_refs not in s:
        raise SystemExit('Estado aguardandoPrincipal não encontrado')
    s = s.replace(anchor_refs, new_refs, 1)

# 2) Mostrar exatamente a transcrição recebida, por alguns instantes.
anchor_exec = "  function executar(texto: string) {"
helper = r'''  function mostrarFalaAoVivo(texto: string) {
    const limpa = texto.trim();
    if (!limpa) return;
    setFalaAoVivo(limpa);
    if (falaVisualTimer.current) clearTimeout(falaVisualTimer.current);
    falaVisualTimer.current = setTimeout(() => {
      falaVisualTimer.current = null;
      setFalaAoVivo('');
    }, 1700);
  }

'''
if 'function mostrarFalaAoVivo' not in s:
    if anchor_exec not in s:
        raise SystemExit('Função executar não encontrada')
    s = s.replace(anchor_exec, helper + anchor_exec, 1)

# 3) Aceitar mais erros comuns do reconhecimento nos termos técnicos.
old_canon_line = ".replace(/\\b(?:humidade|humanidade|um idade)\\b/g, 'umidade')\n    .replace(/\\b(?:percebeu|percebejo|persevejo|percevejos)\\b/g, 'percevejo');"
new_canon_line = ".replace(/\\b(?:humidade|humanidade|humildade|unidade|um idade)\\b/g, 'umidade')\n    .replace(/\\b(?:percebeu|percebejo|persevejo|persebejo|percevejos)\\b/g, 'percevejo')\n    .replace(/\\b(?:mecano|mecanica)\\b/g, 'mecanico');"
if old_canon_line in s:
    s = s.replace(old_canon_line, new_canon_line, 1)

# 4) Buffer preparado para resultados parciais. Quando o reconhecedor revisa
# a mesma Classe, usamos a versão mais nova em vez de lançar a anterior.
old_acum_header = "  function acumularFala(transcript: string) {\n    const nova = canonizarClasseFalado(transcript.trim());"
new_acum_header = "  function acumularFala(transcript: string, isFinal: boolean) {\n    const nova = canonizarClasseFalado(transcript.trim());"
if old_acum_header not in s:
    raise SystemExit('Cabeçalho acumularFala não encontrado')
s = s.replace(old_acum_header, new_acum_header, 1)

old_branch = r'''      if (n.startsWith(a)) {
        falaBuffer.current = nova;
      } else if (a.startsWith(n)) {
        // Resultado mais curto/repetido: mantem a versao mais completa.
      } else if (/\bclasse\b/.test(n) && /\bclasse\b/.test(a)) {
        // Comecou uma nova semente/comando. Fecha a anterior imediatamente.
        descarregarBuffer();
        falaBuffer.current = nova;
      } else {
        // Fragmento da mesma fala: ex. "classe 2 umidade" + "e percevejo".
        falaBuffer.current = `${anterior} ${nova}`.trim();
      }
'''
new_branch = r'''      if (n.startsWith(a)) {
        falaBuffer.current = nova;
      } else if (a.startsWith(n)) {
        // Resultado mais curto/repetido: mantém a versão mais completa.
      } else {
        const classeA = a.match(/^classe\s+(?:1|2|3\s*r|3r|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)\b/)?.[0];
        const classeN = n.match(/^classe\s+(?:1|2|3\s*r|3r|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)\b/)?.[0];

        if (classeA && classeN && classeA === classeN) {
          // Revisão parcial da MESMA semente: fica com o texto mais recente.
          falaBuffer.current = nova;
        } else if (classeA && classeN && classeA !== classeN) {
          // Começou uma nova semente antes do timer: fecha a anterior.
          descarregarBuffer();
          falaBuffer.current = nova;
        } else {
          // Fragmento da mesma fala: "classe 2 umidade" + "e percevejo".
          falaBuffer.current = `${anterior} ${nova}`.trim();
        }
      }
'''
if old_branch not in s:
    raise SystemExit('Lógica antiga do buffer não encontrada')
s = s.replace(old_branch, new_branch, 1)

# 5) Resposta rápida: final normalmente fecha em ~280 ms; parcial estabilizado
# em ~430 ms. Se terminar em "e", espera um pouco mais pelo próximo dano.
old_timer = r'''    if (falaBufferTimer.current) clearTimeout(falaBufferTimer.current);
    falaBufferTimer.current = setTimeout(() => {
      falaBufferTimer.current = null;
      descarregarBuffer();
    }, 1050);
  }
'''
new_timer = r'''    if (falaBufferTimer.current) clearTimeout(falaBufferTimer.current);
    const normalizada = normalizar(falaBuffer.current);
    const terminaComE = /\be$/.test(normalizada);
    const esperaMs = terminaComE ? 650 : (isFinal ? 280 : 430);
    falaBufferTimer.current = setTimeout(() => {
      falaBufferTimer.current = null;
      descarregarBuffer();
    }, esperaMs);
  }
'''
if old_timer not in s:
    raise SystemExit('Timer 1050 ms não encontrado')
s = s.replace(old_timer, new_timer, 1)

# 6) Não ignorar resultados parciais: o balão acompanha a fala e o buffer
# decide quando a frase estabilizou.
old_result = r'''  useSpeechRecognitionEvent('result', event => {
    if (!event.isFinal) return;
    const transcript = event.results[0]?.transcript?.trim();
    if (!transcript) return;
    acumularFala(transcript);
  });
'''
new_result = r'''  useSpeechRecognitionEvent('result', event => {
    const transcript = event.results[0]?.transcript?.trim();
    if (!transcript) return;
    mostrarFalaAoVivo(transcript);
    acumularFala(transcript, event.isFinal);
  });
'''
if old_result not in s:
    raise SystemExit('Handler result v2.5.5 não encontrado')
s = s.replace(old_result, new_result, 1)

# 7) Pedir transcrição parcial ao mecanismo Android.
s = s.replace('      interimResults: false,', '      interimResults: true,', 1)

# Mais contexto para combinações de 2 e 3 danos.
ctx_anchor = "          'principal umidade', 'principal percevejo', 'principal mecânico', 'cancelar',\n          'desfazer', 'quantas',"
ctx_new = "          'umidade e percevejo', 'umidade e dano mecânico', 'percevejo e dano mecânico',\n          'umidade percevejo dano mecânico',\n          'principal umidade', 'principal percevejo', 'principal mecânico', 'cancelar',\n          'desfazer', 'quantas',"
if ctx_anchor in s:
    s = s.replace(ctx_anchor, ctx_new, 1)

# 8) Balão logo abaixo do cabeçalho da voz.
jsx_anchor = "      </View>\n      <Text style={[styles.example, { color: sub }]}>"
jsx_new = r'''      </View>
      {falaAoVivo ? (
        <View style={[styles.speechBubble, { backgroundColor: dark ? '#292929' : '#eef7ee' }]}>
          <Text style={[styles.speechLabel, { color: sub }]}>OUVI</Text>
          <Text style={[styles.speechText, { color: text }]} numberOfLines={2}>“{falaAoVivo}”</Text>
        </View>
      ) : null}
      <Text style={[styles.example, { color: sub }]}>
'''
if 'styles.speechBubble' not in s:
    if jsx_anchor not in s:
        raise SystemExit('Âncora JSX do balão não encontrada')
    s = s.replace(jsx_anchor, jsx_new, 1)

# Como o replace acima abriu a tag em linha própria, remover eventual "<>" duplicado
# não é necessário; apenas garantir que o conteúdo existente siga normalmente.

style_anchor = "  buttonText: { color: '#fff', fontSize: 12, fontWeight: '900' },\n  example: { fontSize: 10, marginTop: 8, lineHeight: 14 },"
style_new = "  buttonText: { color: '#fff', fontSize: 12, fontWeight: '900' },\n  speechBubble: { marginTop: 9, borderRadius: 12, paddingHorizontal: 11, paddingVertical: 8 },\n  speechLabel: { fontSize: 9, fontWeight: '900', marginBottom: 2 },\n  speechText: { fontSize: 13, fontWeight: '700', lineHeight: 17 },\n  example: { fontSize: 10, marginTop: 8, lineHeight: 14 },"
if style_anchor not in s:
    raise SystemExit('Âncora de estilos do balão não encontrada')
s = s.replace(style_anchor, style_new, 1)

# 9) Limpeza do timer visual ao desmontar.
cleanup_anchor = "      if (falaBufferTimer.current) clearTimeout(falaBufferTimer.current);\n      falaBuffer.current = '';"
cleanup_new = "      if (falaBufferTimer.current) clearTimeout(falaBufferTimer.current);\n      if (falaVisualTimer.current) clearTimeout(falaVisualTimer.current);\n      falaBuffer.current = '';"
if cleanup_anchor in s:
    s = s.replace(cleanup_anchor, cleanup_new, 1)

# Validações para não gerar APK sem a experiência rápida.
for trecho in [
    'interimResults: true',
    'mostrarFalaAoVivo(transcript)',
    'acumularFala(transcript, event.isFinal)',
    'const esperaMs = terminaComE ? 650 : (isFinal ? 280 : 430);',
    'styles.speechBubble',
    'umidade e percevejo',
    "if (u && p && m) return 'UPM';",
    "if (u && p) return 'UP';",
    "if (u && m) return 'UM';",
]:
    if trecho not in s:
        raise SystemExit(f'Validação v2.5.6 falhou: {trecho}')

p.write_text(s)
print('v2.5.6 aplicada: voz em tempo real + balão + resposta rápida + UP/UM/UPM')
