from pathlib import Path

p = Path('app-src/components/VoiceCounter.tsx')
s = p.read_text()

# Estado do modo contínuo: o usuário toca uma vez para iniciar e uma vez para parar.
s = s.replace(
    "  const [escutando, setEscutando] = useState(false);\n  const [mensagem, setMensagem] = useState('Toque no microfone e fale o resultado.');",
    "  const [escutando, setEscutando] = useState(false);\n  const [modoAtivo, setModoAtivo] = useState(false);\n  const [mensagem, setMensagem] = useState('Toque no microfone uma vez para iniciar a contagem por voz.');",
    1,
)

s = s.replace(
    "  const ultimoProcessadoEm = useRef(0);",
    "  const ultimoProcessadoEm = useRef(0);\n  const manterOuvindo = useRef(false);\n  const reinicioTimer = useRef<ReturnType<typeof setTimeout> | null>(null);",
    1,
)

s = s.replace(
    "  const border = escutando ? '#d32f2f' : '#1b5e20';",
    "  const border = modoAtivo ? '#d32f2f' : '#1b5e20';",
    1,
)

# O comando falado "parar" também encerra de verdade o modo contínuo.
s = s.replace(
    "    if (parsed.kind === 'stop') {\n      ExpoSpeechRecognitionModule.stop();\n      setMensagem('Modo voz parado.');\n      return;\n    }",
    "    if (parsed.kind === 'stop') {\n      manterOuvindo.current = false;\n      setModoAtivo(false);\n      if (reinicioTimer.current) { clearTimeout(reinicioTimer.current); reinicioTimer.current = null; }\n      ExpoSpeechRecognitionModule.stop();\n      setMensagem('Modo voz parado.');\n      return;\n    }",
    1,
)

old_events = """  useSpeechRecognitionEvent('start', () => {\n    setEscutando(true);\n    setMensagem('Ouvindo… fale o resultado.');\n  });\n\n  useSpeechRecognitionEvent('end', () => {\n    setEscutando(false);\n  });\n\n  useSpeechRecognitionEvent('error', event => {\n    if (event.error === 'aborted') return;\n    setMensagem(`Erro de voz: ${event.message || event.error}`);\n  });\n"""
new_events = """  useSpeechRecognitionEvent('start', () => {\n    setEscutando(true);\n    setModoAtivo(true);\n    setMensagem('Ouvindo continuamente… fale o resultado.');\n  });\n\n  useSpeechRecognitionEvent('end', () => {\n    setEscutando(false);\n    if (manterOuvindo.current) {\n      setMensagem('Continuando a ouvir…');\n      agendarReinicio();\n    }\n  });\n\n  useSpeechRecognitionEvent('error', event => {\n    if (event.error === 'aborted') return;\n    if (manterOuvindo.current && (event.error === 'no-speech' || event.error === 'network')) {\n      setMensagem('Continuando a ouvir…');\n      agendarReinicio();\n      return;\n    }\n    setMensagem(`Erro de voz: ${event.message || event.error}`);\n  });\n"""
if old_events not in s:
    raise SystemExit('Bloco de eventos de voz não encontrado')
s = s.replace(old_events, new_events, 1)

old_cleanup = """  useEffect(() => {\n    return () => {\n      try { ExpoSpeechRecognitionModule.abort(); } catch {}\n    };\n  }, []);\n"""
new_cleanup = """  useEffect(() => {\n    return () => {\n      manterOuvindo.current = false;\n      if (reinicioTimer.current) clearTimeout(reinicioTimer.current);\n      try { ExpoSpeechRecognitionModule.abort(); } catch {}\n    };\n  }, []);\n"""
if old_cleanup not in s:
    raise SystemExit('Cleanup de voz não encontrado')
s = s.replace(old_cleanup, new_cleanup, 1)

# Substitui a função de toggle por uma versão que mantém uma sessão lógica ativa.
start = s.find("  async function toggleVoz() {")
end_marker = "\n\n  return (\n    <View style={[styles.box"
end = s.find(end_marker, start)
if start == -1 or end == -1:
    raise SystemExit('Função toggleVoz não encontrada')

new_toggle = r'''  function iniciarReconhecimento() {
    if (!manterOuvindo.current) return;
    try {
      ExpoSpeechRecognitionModule.start({
        lang: 'pt-BR',
        interimResults: false,
        continuous: true,
        maxAlternatives: 1,
        contextualStrings: [
          'Classe 1', 'Classe 2', 'Classe 3', 'Classe 3R', 'Classe 4', 'Classe 5',
          'Classe 6', 'Classe 7', 'Classe 8', 'umidade', 'percevejo', 'mecânico',
          'UP', 'UM', 'UPM', 'SE', 'SA', 'HE', 'SD', 'principal umidade',
          'principal percevejo', 'principal mecânico', 'desfazer', 'quantas',
        ],
        androidIntentOptions: {
          EXTRA_LANGUAGE_MODEL: 'web_search',
        },
      });
    } catch {
      agendarReinicio();
    }
  }

  function agendarReinicio() {
    if (!manterOuvindo.current) return;
    if (reinicioTimer.current) clearTimeout(reinicioTimer.current);
    reinicioTimer.current = setTimeout(() => {
      reinicioTimer.current = null;
      if (manterOuvindo.current) iniciarReconhecimento();
    }, 350);
  }

  async function toggleVoz() {
    if (modoAtivo || manterOuvindo.current) {
      manterOuvindo.current = false;
      setModoAtivo(false);
      setEscutando(false);
      if (reinicioTimer.current) {
        clearTimeout(reinicioTimer.current);
        reinicioTimer.current = null;
      }
      try { ExpoSpeechRecognitionModule.stop(); } catch {}
      setMensagem('Modo voz parado. Toque em OUVIR para iniciar novamente.');
      return;
    }

    if (!ExpoSpeechRecognitionModule.isRecognitionAvailable()) {
      setMensagem('Reconhecimento de voz não disponível neste aparelho.');
      return;
    }

    const permissao = await ExpoSpeechRecognitionModule.requestPermissionsAsync();
    if (!permissao.granted) {
      setMensagem('Permissão do microfone não foi liberada.');
      return;
    }

    manterOuvindo.current = true;
    setModoAtivo(true);
    setMensagem('Iniciando modo de escuta contínua…');
    iniciarReconhecimento();
  }'''

s = s[:start] + new_toggle + s[end:]

# O botão continua mostrando PARAR mesmo nos pequenos reinícios automáticos do Android.
s = s.replace(
    "style={[styles.button, { backgroundColor: escutando ? '#d32f2f' : '#1b5e20' }]}",
    "style={[styles.button, { backgroundColor: modoAtivo ? '#d32f2f' : '#1b5e20' }]}",
    1,
)
s = s.replace(
    "<Text style={styles.buttonText}>{escutando ? '⏹ PARAR' : '🎙️ OUVIR'}</Text>",
    "<Text style={styles.buttonText}>{modoAtivo ? '⏹ PARAR' : '🎙️ OUVIR'}</Text>",
    1,
)

# Texto de ajuda coerente com o comportamento real.
s = s.replace(
    "<Text style={[styles.example, { color: sub }]}>Ex.:",
    "<Text style={[styles.example, { color: sub }]}>Toque uma vez em OUVIR; depois é só falar. Ex.:",
    1,
)

p.write_text(s)
print('Modo de voz contínuo corrigido: um toque para iniciar, um toque para parar')
