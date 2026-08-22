from pathlib import Path
import math
import struct
import wave

ROOT = Path('app-src')
voice = ROOT / 'components' / 'VoiceCounter.tsx'
s = voice.read_text()

# ============================================================
# v2.5.8 hotfix — impedir contagem/bip duplicado
# - resultado parcial continua aparecendo no balao OUVI
# - parcial NAO dispara contabilizacao
# - somente resultado final agenda o lancamento
# - se o reconhecedor encerrar sem enviar final, o evento end faz um flush unico
# - bip passa a ser um unico tom curto
# ============================================================

old_timer = r'''    if (falaBufferTimer.current) clearTimeout(falaBufferTimer.current);
    const normalizada = normalizar(falaBuffer.current);
    const terminaComE = /\be$/.test(normalizada);
    const esperaMs = terminaComE ? 420 : (isFinal ? 140 : 280);
    falaBufferTimer.current = setTimeout(() => {
      falaBufferTimer.current = null;
      descarregarBuffer();
    }, esperaMs);
  }
'''
new_timer = r'''    if (falaBufferTimer.current) {
      clearTimeout(falaBufferTimer.current);
      falaBufferTimer.current = null;
    }

    // Resultado parcial serve somente para atualizar o buffer e o balao OUVI.
    // Nao contabiliza. Isso impede a mesma fala de entrar uma vez no parcial
    // e outra vez quando o Android envia a transcricao final.
    if (!isFinal) return;

    const normalizada = normalizar(falaBuffer.current);
    const terminaComE = /\be$/.test(normalizada);
    const esperaMs = terminaComE ? 360 : 110;
    falaBufferTimer.current = setTimeout(() => {
      falaBufferTimer.current = null;
      descarregarBuffer();
    }, esperaMs);
  }
'''
if old_timer not in s:
    raise SystemExit('Timer v2.5.8 nao encontrado para hotfix de duplicidade')
s = s.replace(old_timer, new_timer, 1)

# Se o Android encerrar uma sessao sem marcar o ultimo resultado como final,
# faz um unico flush do buffer antes do reinicio automatico. Se ja existe timer
# de final, nao agenda outro.
old_end = r'''  useSpeechRecognitionEvent('end', () => {
    setEscutando(false);
    if (manterOuvindo.current) {
      setMensagem('Continuando a ouvir…');
      agendarReinicio();
    }
  });
'''
new_end = r'''  useSpeechRecognitionEvent('end', () => {
    setEscutando(false);

    if (falaBuffer.current.trim() && !falaBufferTimer.current) {
      falaBufferTimer.current = setTimeout(() => {
        falaBufferTimer.current = null;
        descarregarBuffer();
      }, 90);
    }

    if (manterOuvindo.current) {
      setMensagem('Continuando a ouvir…');
      agendarReinicio();
    }
  });
'''
if old_end not in s:
    raise SystemExit('Handler end continuo nao encontrado')
s = s.replace(old_end, new_end, 1)

voice.write_text(s)

# Bip unico: um tom apenas, curto e nitido.
sounds = ROOT / 'assets' / 'sounds'
sounds.mkdir(parents=True, exist_ok=True)
p = sounds / 'confirm.wav'
rate = 44100
duration = 0.085
freq = 1450.0
amp = 0.78
n = int(rate * duration)
frames = []
for i in range(n):
    t = i / rate
    fade_in = min(1.0, i / (rate * 0.003))
    fade_out = min(1.0, (n - 1 - i) / (rate * 0.014))
    env = min(fade_in, fade_out)
    sample = int(math.sin(2 * math.pi * freq * t) * amp * env * 32767)
    frames.append(struct.pack('<h', sample))
with wave.open(str(p), 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(rate)
    w.writeframes(b''.join(frames))

final = voice.read_text()
for trecho in [
    'if (!isFinal) return;',
    'const esperaMs = terminaComE ? 360 : 110;',
    'if (falaBuffer.current.trim() && !falaBufferTimer.current)',
    'descarregarBuffer();',
]:
    if trecho not in final:
        raise SystemExit(f'Validacao hotfix bip unico falhou: {trecho}')

print('v2.5.8 hotfix aplicado: parcial nao conta, final conta uma vez, bip unico')
