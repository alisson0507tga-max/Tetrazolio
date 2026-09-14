from pathlib import Path
import math
import struct
import wave

ROOT = Path('app-src')
voice = ROOT / 'components' / 'VoiceCounter.tsx'
s = voice.read_text()

# ------------------------------------------------------------------
# 1) Buffer curto de fala: evita processar "umidade" antes de o
#    Android entregar "e percevejo" / "e dano mecanico".
# ------------------------------------------------------------------
anchor = "  const reinicioTimer = useRef<ReturnType<typeof setTimeout> | null>(null);"
insert = anchor + "\n  const falaBuffer = useRef('');\n  const falaBufferTimer = useRef<ReturnType<typeof setTimeout> | null>(null);"
if 'const falaBuffer = useRef' not in s:
    if anchor not in s:
        raise SystemExit('Anchor de refs da voz nao encontrado')
    s = s.replace(anchor, insert, 1)

old_result = """  useSpeechRecognitionEvent('result', event => {\n    if (!event.isFinal) return;\n    const transcript = event.results[0]?.transcript?.trim();\n    if (!transcript) return;\n\n    const agora = Date.now();\n    const chave = normalizar(transcript);\n    if (chave === ultimoProcessado.current && agora - ultimoProcessadoEm.current < 1500) return;\n    ultimoProcessado.current = chave;\n    ultimoProcessadoEm.current = agora;\n    executar(transcript);\n  });\n"""

new_result = r'''  function separarComandos(fala: string): string[] {
    const texto = fala.trim();
    if (!texto) return [];
    const re = /\bclasse\s*(?:1|2|3\s*r|3r|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)\b/gi;
    const matches = Array.from(texto.matchAll(re));
    if (matches.length <= 1) return [texto];

    const partes: string[] = [];
    for (let i = 0; i < matches.length; i++) {
      const inicio = matches[i].index ?? 0;
      const fim = i + 1 < matches.length ? (matches[i + 1].index ?? texto.length) : texto.length;
      const parte = texto.slice(inicio, fim).trim();
      if (parte) partes.push(parte);
    }
    return partes;
  }

  function executarSemDuplicar(comando: string) {
    const chave = normalizar(comando);
    const agora = Date.now();
    if (!chave) return;
    if (chave === ultimoProcessado.current && agora - ultimoProcessadoEm.current < 1200) return;
    ultimoProcessado.current = chave;
    ultimoProcessadoEm.current = agora;
    executar(comando);
  }

  function descarregarBuffer() {
    if (falaBufferTimer.current) {
      clearTimeout(falaBufferTimer.current);
      falaBufferTimer.current = null;
    }
    const fala = falaBuffer.current.trim();
    falaBuffer.current = '';
    if (!fala) return;
    separarComandos(fala).forEach(executarSemDuplicar);
  }

  function acumularFala(transcript: string) {
    const nova = transcript.trim();
    if (!nova) return;

    const anterior = falaBuffer.current.trim();
    if (!anterior) {
      falaBuffer.current = nova;
    } else {
      const a = normalizar(anterior);
      const n = normalizar(nova);

      // Alguns reconhecedores reenviam a frase anterior mais completa.
      // Nesse caso substitui, em vez de duplicar: "classe 2 umidade"
      // -> "classe 2 umidade e percevejo".
      if (n.startsWith(a)) {
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
    }

    if (falaBufferTimer.current) clearTimeout(falaBufferTimer.current);
    falaBufferTimer.current = setTimeout(() => {
      falaBufferTimer.current = null;
      descarregarBuffer();
    }, 800);
  }

  useSpeechRecognitionEvent('result', event => {
    if (!event.isFinal) return;
    const transcript = event.results[0]?.transcript?.trim();
    if (!transcript) return;
    acumularFala(transcript);
  });
'''

if old_result not in s:
    raise SystemExit('Handler result original nao encontrado')
s = s.replace(old_result, new_result, 1)

# Limpeza do buffer ao sair da tela.
old_cleanup = """      manterOuvindo.current = false;\n      if (reinicioTimer.current) clearTimeout(reinicioTimer.current);\n      try { ExpoSpeechRecognitionModule.abort(); } catch {}"""
new_cleanup = """      manterOuvindo.current = false;\n      if (reinicioTimer.current) clearTimeout(reinicioTimer.current);\n      if (falaBufferTimer.current) clearTimeout(falaBufferTimer.current);\n      falaBuffer.current = '';\n      try { ExpoSpeechRecognitionModule.abort(); } catch {}"""
if old_cleanup in s:
    s = s.replace(old_cleanup, new_cleanup, 1)

# Ao parar manualmente, impede que um timer pendente lance algo depois.
old_stop = """      if (reinicioTimer.current) {\n        clearTimeout(reinicioTimer.current);\n        reinicioTimer.current = null;\n      }\n      try { ExpoSpeechRecognitionModule.stop(); } catch {}"""
new_stop = """      if (reinicioTimer.current) {\n        clearTimeout(reinicioTimer.current);\n        reinicioTimer.current = null;\n      }\n      if (falaBufferTimer.current) {\n        clearTimeout(falaBufferTimer.current);\n        falaBufferTimer.current = null;\n      }\n      falaBuffer.current = '';\n      try { ExpoSpeechRecognitionModule.stop(); } catch {}"""
if old_stop in s:
    s = s.replace(old_stop, new_stop, 1)

voice.write_text(s)

# ------------------------------------------------------------------
# 2) Bip mais alto e nitido.
# ------------------------------------------------------------------
sounds = ROOT / 'assets' / 'sounds'
sounds.mkdir(parents=True, exist_ok=True)
p = sounds / 'confirm.wav'
rate = 44100
duration = 0.115
freq1 = 1180.0
freq2 = 1540.0
amp = 0.72
n = int(rate * duration)
frames = []
for i in range(n):
    t = i / rate
    fade_in = min(1.0, i / (rate * 0.004))
    fade_out = min(1.0, (n - 1 - i) / (rate * 0.018))
    env = min(fade_in, fade_out)
    # Bip brilhante de duas frequencias, curto e sem distorcao.
    mix = math.sin(2 * math.pi * freq1 * t) * 0.72 + math.sin(2 * math.pi * freq2 * t) * 0.28
    sample = int(max(-1, min(1, mix * amp * env)) * 32767)
    frames.append(struct.pack('<h', sample))
with wave.open(str(p), 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(rate)
    w.writeframes(b''.join(frames))

helper = ROOT / 'lib' / 'confirmation-sound.ts'
h = helper.read_text()
h = h.replace('confirmationPlayer.volume = 0.32;', 'confirmationPlayer.volume = 0.92;')
helper.write_text(h)

# Validacoes simples para falhar a build se a correcao nao entrou.
final_voice = voice.read_text()
for trecho in [
    'acumularFala(transcript)',
    '}, 800);',
    "if (u && p && m) return 'UPM';",
    "if (u && p) return 'UP';",
    "if (u && m) return 'UM';",
]:
    if trecho not in final_voice:
        raise SystemExit(f'Validacao v2.5.2 falhou: {trecho}')
if 'confirmationPlayer.volume = 0.92;' not in helper.read_text():
    raise SystemExit('Validacao v2.5.2 falhou: volume do bip')

print('v2.5.2 aplicada: danos combinados por frase + bip mais alto')
