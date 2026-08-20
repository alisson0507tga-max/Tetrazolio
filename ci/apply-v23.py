from pathlib import Path
import math
import re
import struct
import wave

ROOT = Path('app-src')

# 1) Som curto de confirmacao
sounds = ROOT / 'assets' / 'sounds'
sounds.mkdir(parents=True, exist_ok=True)
p = sounds / 'confirm.wav'
rate = 44100
duration = 0.085
freq = 880.0
amp = 0.20
n = int(rate * duration)
frames = []
for i in range(n):
    t = i / rate
    fade_in = min(1.0, i / (rate * 0.008))
    fade_out = min(1.0, (n - 1 - i) / (rate * 0.012))
    env = min(fade_in, fade_out)
    v = math.sin(2 * math.pi * freq * t) * 0.85 + math.sin(2 * math.pi * freq * 2 * t) * 0.15
    sample = int(max(-1, min(1, v * amp * env)) * 32767)
    frames.append(struct.pack('<h', sample))
with wave.open(str(p), 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(rate)
    w.writeframes(b''.join(frames))

sound_helper = ROOT / 'lib' / 'confirmation-sound.ts'
sound_helper.parent.mkdir(parents=True, exist_ok=True)
sound_helper.write_text("""import { createAudioPlayer } from 'expo-audio';

let confirmationPlayer: ReturnType<typeof createAudioPlayer> | null = null;

function getConfirmationPlayer() {
  if (!confirmationPlayer) {
    confirmationPlayer = createAudioPlayer(require('../assets/sounds/confirm.wav'));
    confirmationPlayer.volume = 0.32;
  }
  return confirmationPlayer;
}

export function tocarSomConfirmacao() {
  try {
    const player = getConfirmationPlayer();
    void player.seekTo(0);
    player.play();
  } catch {
    // Feedback sonoro nunca pode impedir a contagem.
  }
}
""")

# 2) Rebaixar topo do Relatorio
report = ROOT / 'app' / '(tabs)' / 'relatorio.tsx'
s = report.read_text()
old = "contentContainerStyle={{ padding: 10, paddingBottom: insets.bottom + 100 }}"
new = "contentContainerStyle={{\n          paddingHorizontal: 10,\n          paddingTop: insets.top + 10,\n          paddingBottom: insets.bottom + 100,\n        }}"
if old in s:
    s = s.replace(old, new, 1)
elif 'paddingTop: insets.top + 10' not in s:
    raise SystemExit('Nao foi possivel localizar o topo do Relatorio')
report.write_text(s)

# 3) Bip depois de lancamento simples aceito
card = ROOT / 'components' / 'CardClasse.tsx'
s = card.read_text()
anchor = "import { ModalDanoMultiplo } from './ModalDanoMultiplo';\n"
if 'confirmation-sound' not in s:
    if anchor not in s:
        raise SystemExit('Import anchor CardClasse nao encontrado')
    s = s.replace(anchor, anchor + "import { tocarSomConfirmacao } from '@/lib/confirmation-sound';\n", 1)
target = "    dispatch({ type: 'ADICIONAR', rep, classe: classeIdx, tipo });\n    \n    // Só uma nova semente"
if 'tocarSomConfirmacao();' not in s:
    if target not in s:
        raise SystemExit('Dispatch CardClasse nao encontrado')
    s = s.replace(target, "    dispatch({ type: 'ADICIONAR', rep, classe: classeIdx, tipo });\n    tocarSomConfirmacao();\n    \n    // Só uma nova semente", 1)
card.write_text(s)

# 4) Bip depois de confirmar causa principal em dano multiplo
modal = ROOT / 'components' / 'ModalDanoMultiplo.tsx'
s = modal.read_text()
anchor = "import { CONFIG, getTotalRep } from '@/lib/tetrazolio-store';\n"
if 'confirmation-sound' not in s:
    if anchor not in s:
        raise SystemExit('Import anchor ModalDanoMultiplo nao encontrado')
    s = s.replace(anchor, anchor + "import { tocarSomConfirmacao } from '@/lib/confirmation-sound';\n", 1)
target = "    dispatch({ type: 'ADICIONAR', rep, classe, tipo, danoPrincipal: letra });\n    showToast"
if 'tocarSomConfirmacao();' not in s:
    if target not in s:
        raise SystemExit('Dispatch ModalDanoMultiplo nao encontrado')
    s = s.replace(target, "    dispatch({ type: 'ADICIONAR', rep, classe, tipo, danoPrincipal: letra });\n    tocarSomConfirmacao();\n    showToast", 1)
modal.write_text(s)

# 5) Icone aprovado, incluindo adaptive icon sem borda branca
cfg = ROOT / 'app.config.ts'
lines = cfg.read_text().splitlines()

# Icone principal
for i, line in enumerate(lines):
    if line.startswith('  icon:'):
        lines[i] = '  icon: "./assets/images/tetrazolio-icon.png",'
        break
else:
    raise SystemExit('Icone principal nao encontrado')

# Bloco adaptiveIcon: localizar pela chave, independente de espacos/conteudo interno
start = None
end = None
for i, line in enumerate(lines):
    if line.strip() == 'adaptiveIcon: {':
        start = i
        base_indent = len(line) - len(line.lstrip())
        for j in range(i + 1, len(lines)):
            if lines[j].strip() == '},' and (len(lines[j]) - len(lines[j].lstrip())) == base_indent:
                end = j
                break
        break

if start is None or end is None:
    raise SystemExit('Bloco adaptiveIcon nao encontrado')

indent = ' ' * (len(lines[start]) - len(lines[start].lstrip()))
new_block = [
    f'{indent}adaptiveIcon: {{',
    f'{indent}  backgroundColor: "#00351c",',
    f'{indent}  foregroundImage: "./assets/images/tetrazolio-icon.png",',
    f'{indent}}},',
]
lines[start:end + 1] = new_block
cfg.write_text('\n'.join(lines) + '\n')

print('Melhorias v2.3 aplicadas com sucesso')
