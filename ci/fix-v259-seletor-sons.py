from pathlib import Path
import math
import struct
import wave

ROOT = Path('app-src')
sounds = ROOT / 'assets' / 'sounds'
sounds.mkdir(parents=True, exist_ok=True)
rate = 44100


def tone(freq=1000, dur=0.08, amp=0.7, kind='sine', freq2=None, sweep=None):
    n = int(rate * dur)
    frames = []
    for i in range(n):
        t = i / rate
        f = freq if sweep is None else sweep[0] + (sweep[1] - sweep[0]) * (i / max(1, n - 1))
        if kind == 'square':
            v = 1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0
        elif kind == 'triangle':
            v = 2 / math.pi * math.asin(math.sin(2 * math.pi * f * t))
        else:
            v = math.sin(2 * math.pi * f * t)
        if freq2:
            v = 0.72 * v + 0.28 * math.sin(2 * math.pi * freq2 * t)
        fade_in = min(1.0, i / (rate * 0.003))
        fade_out = min(1.0, (n - 1 - i) / (rate * 0.012))
        env = min(fade_in, fade_out)
        sample = int(max(-1, min(1, v * amp * env)) * 32767)
        frames.append(struct.pack('<h', sample))
    return b''.join(frames)


def silence(dur):
    return b'\x00\x00' * int(rate * dur)


def save(name, data):
    p = sounds / name
    with wave.open(str(p), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(data)


def tt(*args, **kwargs):
    return tone(*args, **kwargs)

samples = [
    ('som01.wav', tt(1050,.075,.78)),
    ('som02.wav', tt(1650,.070,.72)),
    ('som03.wav', tt(620,.085,.78)),
    ('som04.wav', tt(2100,.035,.65,'square')),
    ('som05.wav', tt(900,.045,.60,'triangle')),
    ('som06.wav', tt(1750,.120,.55,freq2=2450)),
    ('som07.wav', tt(2250,.130,.48,freq2=3100)),
    ('som08.wav', tt(720,.055,.75,freq2=1080)),
    ('som09.wav', tt(480,.065,.72,'triangle')),
    ('som10.wav', tt(1350,.060,.70,'square')),
    ('som11.wav', tt(1450,.080,.78,freq2=1950)),
    ('som12.wav', tt(1180,.070,.76,'square',freq2=1600)),
    ('som13.wav', tt(980,.055,.68)),
    ('som14.wav', tt(1300,.110,.45)),
    ('som15.wav', tt(1550,.090,.84)),
    ('som16.wav', tt(500,.025,.72,'square') + silence(.018) + tt(1450,.070,.70)),
    ('som17.wav', tt(1320,.050,.72) + silence(.040) + tt(1320,.050,.72)),
    ('som18.wav', tt(800,.110,.72,sweep=(800,1800))),
    ('som19.wav', tt(1800,.110,.72,sweep=(1800,750))),
    ('som20.wav', tt(1200,.065,.70,'square')),
    ('som21.wav', tt(1150,.090,.62)),
    ('som22.wav', tt(1650,.050,.68) + silence(.025) + tt(1320,.040,.45)),
    ('som23.wav', tt(2050,.032,.55,'square')),
    ('som24.wav', tt(760,.045,.80,'square')),
    ('som25.wav', tt(1850,.060,.58)),
    ('som26.wav', tt(1250,.085,.70,freq2=1500)),
    ('som27.wav', tt(900,.090,.68,sweep=(900,2200))),
    ('som28.wav', tt(1900,.100,.52,freq2=2500)),
    ('som29.wav', tt(680,.045,.72,'triangle')),
    ('som30.wav', tt(1500,.028,.72,'square')),
]
for name, data in samples:
    save(name, data)

# Helper de áudio com 30 opções estáticas para o Metro empacotar todos os WAVs.
helper = ROOT / 'lib' / 'confirmation-sound.ts'
helper.write_text(r'''import { createAudioPlayer } from 'expo-audio';

export const SOUND_OPTIONS = [
  { id: 1, name: 'Bip seco' },
  { id: 2, name: 'Bip agudo' },
  { id: 3, name: 'Bip grave' },
  { id: 4, name: 'Click digital' },
  { id: 5, name: 'Click mecânico' },
  { id: 6, name: 'Ping metálico' },
  { id: 7, name: 'Ping de vidro' },
  { id: 8, name: 'Pop eletrônico' },
  { id: 9, name: 'Ploc curto' },
  { id: 10, name: 'Blip digital' },
  { id: 11, name: 'Beep scanner' },
  { id: 12, name: 'Beep caixa' },
  { id: 13, name: 'Botão eletrônico' },
  { id: 14, name: 'Confirmação suave' },
  { id: 15, name: 'Confirmação forte' },
  { id: 16, name: 'Click + bip' },
  { id: 17, name: 'Bip duplo rápido' },
  { id: 18, name: 'Bip crescente' },
  { id: 19, name: 'Bip descendente' },
  { id: 20, name: 'Tom quadrado' },
  { id: 21, name: 'Tom senoidal' },
  { id: 22, name: 'Radar' },
  { id: 23, name: 'Terminal' },
  { id: 24, name: 'Contador industrial' },
  { id: 25, name: 'Balança digital' },
  { id: 26, name: 'Máquina laboratório' },
  { id: 27, name: 'Leitor óptico' },
  { id: 28, name: 'Equipamento' },
  { id: 29, name: 'Marcador' },
  { id: 30, name: 'Ultracurto' },
] as const;

const SOURCES: Record<number, any> = {
  1: require('../assets/sounds/som01.wav'), 2: require('../assets/sounds/som02.wav'),
  3: require('../assets/sounds/som03.wav'), 4: require('../assets/sounds/som04.wav'),
  5: require('../assets/sounds/som05.wav'), 6: require('../assets/sounds/som06.wav'),
  7: require('../assets/sounds/som07.wav'), 8: require('../assets/sounds/som08.wav'),
  9: require('../assets/sounds/som09.wav'), 10: require('../assets/sounds/som10.wav'),
  11: require('../assets/sounds/som11.wav'), 12: require('../assets/sounds/som12.wav'),
  13: require('../assets/sounds/som13.wav'), 14: require('../assets/sounds/som14.wav'),
  15: require('../assets/sounds/som15.wav'), 16: require('../assets/sounds/som16.wav'),
  17: require('../assets/sounds/som17.wav'), 18: require('../assets/sounds/som18.wav'),
  19: require('../assets/sounds/som19.wav'), 20: require('../assets/sounds/som20.wav'),
  21: require('../assets/sounds/som21.wav'), 22: require('../assets/sounds/som22.wav'),
  23: require('../assets/sounds/som23.wav'), 24: require('../assets/sounds/som24.wav'),
  25: require('../assets/sounds/som25.wav'), 26: require('../assets/sounds/som26.wav'),
  27: require('../assets/sounds/som27.wav'), 28: require('../assets/sounds/som28.wav'),
  29: require('../assets/sounds/som29.wav'), 30: require('../assets/sounds/som30.wav'),
};

const players = new Map<number, ReturnType<typeof createAudioPlayer>>();

function getPlayer(id: number) {
  const safeId = id >= 1 && id <= 30 ? id : 11;
  let player = players.get(safeId);
  if (!player) {
    player = createAudioPlayer(SOURCES[safeId]);
    player.volume = 0.92;
    players.set(safeId, player);
  }
  return player;
}

export function tocarSomConfirmacao(id = 11) {
  try {
    const player = getPlayer(id);
    void player.seekTo(0);
    player.play();
  } catch {
    // O som nunca pode impedir a contagem.
  }
}
''')

# Preferência persistente no store.
store = ROOT / 'lib' / 'tetrazolio-store.ts'
s = store.read_text()
if 'somSelecionado: number;' not in s:
    s = s.replace('  somAtivo: boolean;\n', '  somAtivo: boolean;\n  somSelecionado: number;\n', 1)
if 'somSelecionado: 11,' not in s:
    s = s.replace('  somAtivo: true,\n', '  somAtivo: true,\n  somSelecionado: 11,\n', 1)
if "type: 'SET_SOM_CONTAGEM'" not in s:
    s = s.replace("  | { type: 'TOGGLE_SOM' }\n", "  | { type: 'TOGGLE_SOM' }\n  | { type: 'SET_SOM_CONTAGEM'; som: number }\n", 1)
if "case 'SET_SOM_CONTAGEM':" not in s:
    anchor = "    case 'TOGGLE_SOM':\n      return { ...state, somAtivo: !state.somAtivo };\n"
    repl = anchor + "\n    case 'SET_SOM_CONTAGEM':\n      return { ...state, somSelecionado: Math.max(1, Math.min(30, action.som)) };\n"
    if anchor not in s:
        raise SystemExit('Reducer TOGGLE_SOM não encontrado')
    s = s.replace(anchor, repl, 1)
if 'somSelecionado: typeof loaded.somSelecionado' not in s:
    anchor = '        somAtivo: loaded.somAtivo !== false,\n'
    if anchor not in s:
        raise SystemExit('LOAD_STATE somAtivo não encontrado')
    s = s.replace(anchor, anchor + "        somSelecionado: typeof loaded.somSelecionado === 'number' ? Math.max(1, Math.min(30, loaded.somSelecionado)) : 11,\n", 1)
s = s.replace(
    'return { ...estadoInicial, tema: state.tema, somAtivo: state.somAtivo, analises: state.analises };',
    'return { ...estadoInicial, tema: state.tema, somAtivo: state.somAtivo, somSelecionado: state.somSelecionado, analises: state.analises };',
)
store.write_text(s)

# Todos os pontos de contagem usam o som selecionado.
for rel in ['components/CardClasse.tsx', 'components/ModalDanoMultiplo.tsx', 'components/VoiceCounter.tsx']:
    p = ROOT / rel
    txt = p.read_text()
    txt = txt.replace('tocarSomConfirmacao();', 'tocarSomConfirmacao(estado.somSelecionado);')
    p.write_text(txt)

# Componente de configuração: tocar = selecionar + ouvir prévia.
selector = ROOT / 'components' / 'SoundSelector.tsx'
selector.write_text(r'''import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SOUND_OPTIONS, tocarSomConfirmacao } from '@/lib/confirmation-sound';
import { useStore } from '@/lib/tetrazolio-store';

export function SoundSelector() {
  const { estado, dispatch } = useStore();
  const dark = estado.tema === 'dark';
  const bg = dark ? '#1f1f1f' : '#ffffff';
  const text = dark ? '#f5f5f5' : '#202124';
  const sub = dark ? '#bdbdbd' : '#5f6368';

  return (
    <View style={[styles.box, { backgroundColor: bg }]}> 
      <Text style={[styles.title, { color: text }]}>🔊 ESCOLHER SOM DA CONTAGEM</Text>
      <Text style={[styles.help, { color: sub }]}>Toque em um som para ouvir e selecionar. A escolha fica salva.</Text>
      <View style={styles.grid}>
        {SOUND_OPTIONS.map(item => {
          const selected = estado.somSelecionado === item.id;
          return (
            <TouchableOpacity
              key={item.id}
              style={[
                styles.item,
                {
                  borderColor: selected ? '#2e7d32' : dark ? '#555' : '#d0d0d0',
                  backgroundColor: selected ? (dark ? '#173c1c' : '#e8f5e9') : (dark ? '#292929' : '#fafafa'),
                },
              ]}
              onPress={() => {
                dispatch({ type: 'SET_SOM_CONTAGEM', som: item.id });
                tocarSomConfirmacao(item.id);
              }}
              activeOpacity={0.75}
            >
              <Text style={[styles.number, { color: selected ? '#2e7d32' : sub }]}>{String(item.id).padStart(2, '0')}</Text>
              <Text style={[styles.name, { color: text }]} numberOfLines={2}>{item.name}</Text>
              <Text style={[styles.play, { color: selected ? '#2e7d32' : sub }]}>{selected ? '✓ SELECIONADO' : '▶ OUVIR'}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  box: { borderRadius: 14, padding: 12, marginBottom: 12 },
  title: { fontSize: 14, fontWeight: '900', marginBottom: 4 },
  help: { fontSize: 11, marginBottom: 10 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  item: { width: '48.5%', minHeight: 78, borderWidth: 1.5, borderRadius: 10, padding: 9 },
  number: { fontSize: 10, fontWeight: '900', marginBottom: 2 },
  name: { fontSize: 12, fontWeight: '800', lineHeight: 15, flex: 1 },
  play: { fontSize: 9, fontWeight: '900', marginTop: 5 },
});
''')

# Coloca o seletor na área de configurações do Relatório, logo antes de limpar dados.
report = ROOT / 'app' / '(tabs)' / 'relatorio.tsx'
s = report.read_text()
if "@/components/SoundSelector" not in s:
    lines = s.splitlines()
    last_import = max(i for i, line in enumerate(lines) if line.startswith('import '))
    lines.insert(last_import + 1, "import { SoundSelector } from '@/components/SoundSelector';")
    s = '\n'.join(lines) + '\n'
if '<SoundSelector />' not in s:
    anchor = '        <TouchableOpacity style={styles.btnLimpar} onPress={limparTudo}>'
    if anchor not in s:
        raise SystemExit('Âncora para seletor de sons não encontrada no Relatório')
    s = s.replace(anchor, '        <SoundSelector />\n\n' + anchor, 1)
report.write_text(s)

# Validações obrigatórias.
checks = [
    'somSelecionado: number;' in store.read_text(),
    "type: 'SET_SOM_CONTAGEM'" in store.read_text(),
    'SOUND_OPTIONS' in helper.read_text(),
    "30: require('../assets/sounds/som30.wav')" in helper.read_text(),
    '<SoundSelector />' in report.read_text(),
    'tocarSomConfirmacao(estado.somSelecionado);' in (ROOT / 'components' / 'VoiceCounter.tsx').read_text(),
]
if not all(checks):
    raise SystemExit('Validação v2.5.9 falhou')

print('v2.5.9 aplicada: 30 sons selecionáveis e persistentes na configuração')
