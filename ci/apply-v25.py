from pathlib import Path

ROOT = Path('app-src')


def replace_once(path: Path, old: str, new: str, label: str):
    s = path.read_text()
    if new in s:
        return
    if old not in s:
        raise SystemExit(f'{label}: trecho nao encontrado')
    path.write_text(s.replace(old, new, 1))


# ============================================================
# 1) COMPONENTE DE VOZ
# ============================================================
voice = ROOT / 'components' / 'VoiceCounter.tsx'
voice.write_text(r'''import React, { useEffect, useRef, useState } from 'react';
import { Platform, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import * as Haptics from 'expo-haptics';
import {
  ExpoSpeechRecognitionModule,
  useSpeechRecognitionEvent,
} from 'expo-speech-recognition';
import { CONFIG, getTotalRep, useStore } from '@/lib/tetrazolio-store';
import { tocarSomConfirmacao } from '@/lib/confirmation-sound';
import { useToast } from './Toast';

type Rep = 1 | 2;
type Principal = 'U' | 'P' | 'M';
type Tipo = 'total' | 'U' | 'P' | 'M' | 'UP' | 'UM' | 'UPM' | 'se' | 'sa' | 'he' | 'sd';

type Parsed =
  | { kind: 'add'; classe: number | null; tipo: Tipo; principal?: Principal }
  | { kind: 'undo' }
  | { kind: 'count' }
  | { kind: 'stop' }
  | { kind: 'invalid'; message: string };

function normalizar(texto: string) {
  return texto
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[.,;:!?()]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function temPadrao(t: string, padroes: RegExp[]) {
  return padroes.some(p => p.test(t));
}

function obterClasse(t: string): number | null {
  if (/\b(?:classe\s*)?(?:3\s*r|3r|tres\s*r|tres\s*erre)\b/.test(t)) return 3;

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

  const m = t.match(/\bclasse\s*(1|2|3|4|5|6|7|8|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito)\b/);
  if (!m) return null;
  return mapaNumeros[m[1]] ?? null;
}

function obterExtra(t: string): Tipo | null {
  const curto = t.split(' ').length <= 5;

  if (temPadrao(t, [
    /\bsemente\s+dura\b/, /\bsd\b/, /\bs\s*d\b/,
    ...(curto ? [/\besse\s+de\b/, /\besse\s+d\b/] : []),
  ])) return 'sd';

  if (temPadrao(t, [
    /\bsemente\s+(?:verde|esverdeada)\b/, /\bse\b/, /\bs\s*e\b/,
    ...(curto ? [/\besse\s+e\b/] : []),
  ])) return 'se';

  if (temPadrao(t, [
    /\bsemente\s+anormal\b/, /\bsa\b/, /\bs\s*a\b/,
    ...(curto ? [/\besse\s+a\b/] : []),
  ])) return 'sa';

  if (temPadrao(t, [
    /\bhe\b/, /\bh\s*e\b/, /\baga\s+e\b/,
  ])) return 'he';

  return null;
}

function obterPrincipal(t: string): Principal | undefined {
  if (/\bprincipal\s+(?:umidade|u)\b/.test(t)) return 'U';
  if (/\bprincipal\s+(?:percevejo|p)\b/.test(t)) return 'P';
  if (/\bprincipal\s+(?:mecanico|mecanica|m)\b/.test(t)) return 'M';
  return undefined;
}

function obterDano(t: string): Tipo | null {
  let u = /\bumidade\b/.test(t);
  let p = /\bpercevejo(?:s)?\b/.test(t);
  let m = /\bmecanico\b|\bmecanica\b|\bdano\s+mecanico\b/.test(t);

  if (/\bupm\b|\bu\s+p\s+m\b/.test(t)) { u = true; p = true; m = true; }
  else if (/\bup\b|\bu\s+p\b/.test(t)) { u = true; p = true; }
  else if (/\bum\b|\bu\s+m\b/.test(t)) { u = true; m = true; }

  // Letras isoladas sao aceitas quando vierem depois de "classe" ou "dano".
  if (/\b(?:classe\s+\S+|dano)\s+u\b/.test(t)) u = true;
  if (/\b(?:classe\s+\S+|dano)\s+p\b/.test(t)) p = true;
  if (/\b(?:classe\s+\S+|dano)\s+m\b/.test(t)) m = true;

  if (u && p && m) return 'UPM';
  if (u && p) return 'UP';
  if (u && m) return 'UM';
  if (u) return 'U';
  if (p) return 'P';
  if (m) return 'M';
  return null;
}

function parseCommand(texto: string): Parsed {
  const t = normalizar(texto);
  if (!t) return { kind: 'invalid', message: 'Não entendi. Tente novamente.' };

  if (/\bparar(?:\s+voz)?\b/.test(t)) return { kind: 'stop' };
  if (/\bdesfazer\b|\bvoltar\s+ultimo\b/.test(t)) return { kind: 'undo' };
  if (/\bquantas\b|\bquanto\s+tem\b|\bcontagem\b/.test(t)) return { kind: 'count' };

  const classe = obterClasse(t);
  const extra = obterExtra(t);
  if (extra) return { kind: 'add', classe, tipo: extra };

  if (classe === 0 && !obterDano(t)) {
    return { kind: 'add', classe, tipo: 'total' };
  }

  const dano = obterDano(t);
  if (!dano) {
    return { kind: 'invalid', message: 'Diga a classe e o dano. Ex.: Classe 4 umidade.' };
  }

  return { kind: 'add', classe, tipo: dano, principal: obterPrincipal(t) };
}

export function VoiceCounter({ rep, dark }: { rep: Rep; dark?: boolean }) {
  const { estado, dispatch } = useStore();
  const { showToast } = useToast();
  const [escutando, setEscutando] = useState(false);
  const [mensagem, setMensagem] = useState('Toque no microfone e fale o resultado.');
  const ultimaClasse = useRef<number | null>(null);
  const ultimoProcessado = useRef('');
  const ultimoProcessadoEm = useRef(0);

  const bg = dark ? '#1e1e1e' : '#ffffff';
  const text = dark ? '#f1f1f1' : '#202124';
  const sub = dark ? '#bdbdbd' : '#5f6368';
  const border = escutando ? '#d32f2f' : '#1b5e20';

  function feedbackOk(texto: string) {
    setMensagem(texto);
    showToast(`🎙️ ${texto}`);
    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
    if (estado.somAtivo) tocarSomConfirmacao();
  }

  function executar(texto: string) {
    const parsed = parseCommand(texto);

    if (parsed.kind === 'stop') {
      ExpoSpeechRecognitionModule.stop();
      setMensagem('Modo voz parado.');
      return;
    }

    if (parsed.kind === 'count') {
      const total = getTotalRep(estado.dados, rep);
      const msg = `Contagem: ${total} de ${CONFIG.MAX_TOTAL}`;
      setMensagem(msg);
      showToast(`🔢 ${msg}`);
      return;
    }

    if (parsed.kind === 'undo') {
      const hist = estado.historico[rep];
      const ultimo = hist[hist.length - 1];
      if (!ultimo) {
        setMensagem('Não há lançamento para desfazer.');
        return;
      }
      dispatch({ type: 'DESFAZER', rep, classe: ultimo.classe });
      ultimaClasse.current = ultimo.classe;
      setMensagem(`Desfeito: Classe ${CONFIG.NOMES[ultimo.classe]}`);
      showToast('↩️ Último lançamento desfeito por voz');
      if (Platform.OS !== 'web') Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      return;
    }

    if (parsed.kind === 'invalid') {
      setMensagem(parsed.message);
      return;
    }

    let classe = parsed.classe;
    if (classe == null) classe = ultimaClasse.current;
    if (classe == null) {
      setMensagem('Diga a classe primeiro. Ex.: Classe 4 umidade.');
      return;
    }

    const isComplemento = ['se', 'sa', 'he'].includes(parsed.tipo);
    const isExtra = ['se', 'sa', 'he', 'sd'].includes(parsed.tipo);

    if (isExtra && (classe === 0 || classe === 1)) {
      setMensagem('SE, SA, HE e SD ficam disponíveis a partir da Classe 3.');
      return;
    }

    const total = getTotalRep(estado.dados, rep);
    if (total >= CONFIG.MAX_TOTAL && !isComplemento) {
      setMensagem(`Limite de ${CONFIG.MAX_TOTAL} sementes já atingido.`);
      showToast(`⚠️ Limite de ${CONFIG.MAX_TOTAL} sementes atingido!`);
      return;
    }

    if (classe >= 6 && ['UP', 'UM', 'UPM'].includes(parsed.tipo) && !parsed.principal) {
      setMensagem('Para Classe 6 a 8 com dano múltiplo, diga o principal.');
      showToast('⚠️ Ex.: Classe 7 UP, principal umidade');
      return;
    }

    if (classe !== 0 && parsed.tipo === 'total') {
      setMensagem('Para essa classe, diga também o dano.');
      return;
    }

    dispatch({
      type: 'ADICIONAR',
      rep,
      classe,
      tipo: parsed.tipo,
      danoPrincipal: parsed.principal,
    });
    ultimaClasse.current = classe;

    const nome = CONFIG.NOMES[classe];
    const principal = parsed.principal ? `, principal ${parsed.principal}` : '';
    const novoTotal = total + (isComplemento ? 0 : 1);
    feedbackOk(`Classe ${nome}: ${parsed.tipo.toUpperCase()}${principal} • ${novoTotal}/${CONFIG.MAX_TOTAL}`);
  }

  useSpeechRecognitionEvent('start', () => {
    setEscutando(true);
    setMensagem('Ouvindo… fale o resultado.');
  });

  useSpeechRecognitionEvent('end', () => {
    setEscutando(false);
  });

  useSpeechRecognitionEvent('error', event => {
    if (event.error === 'aborted') return;
    setMensagem(`Erro de voz: ${event.message || event.error}`);
  });

  useSpeechRecognitionEvent('result', event => {
    if (!event.isFinal) return;
    const transcript = event.results[0]?.transcript?.trim();
    if (!transcript) return;

    const agora = Date.now();
    const chave = normalizar(transcript);
    if (chave === ultimoProcessado.current && agora - ultimoProcessadoEm.current < 1500) return;
    ultimoProcessado.current = chave;
    ultimoProcessadoEm.current = agora;
    executar(transcript);
  });

  useEffect(() => {
    return () => {
      try { ExpoSpeechRecognitionModule.abort(); } catch {}
    };
  }, []);

  async function toggleVoz() {
    if (escutando) {
      ExpoSpeechRecognitionModule.stop();
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

    setMensagem('Iniciando microfone…');
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
  }

  return (
    <View style={[styles.box, { backgroundColor: bg, borderColor: border }]}>
      <View style={styles.row}>
        <View style={styles.texts}>
          <Text style={[styles.title, { color: text }]}>🎙️ CONTAGEM POR VOZ</Text>
          <Text style={[styles.status, { color: sub }]} numberOfLines={2}>{mensagem}</Text>
        </View>
        <TouchableOpacity
          style={[styles.button, { backgroundColor: escutando ? '#d32f2f' : '#1b5e20' }]}
          onPress={toggleVoz}
          activeOpacity={0.8}
        >
          <Text style={styles.buttonText}>{escutando ? '⏹ PARAR' : '🎙️ OUVIR'}</Text>
        </TouchableOpacity>
      </View>
      <Text style={[styles.example, { color: sub }]}>Ex.: “Classe 4 umidade” • “Classe 7 UP, principal umidade” • “Desfazer”</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  box: {
    marginHorizontal: 12,
    marginTop: 10,
    marginBottom: 2,
    borderWidth: 2,
    borderRadius: 16,
    padding: 11,
  },
  row: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  texts: { flex: 1 },
  title: { fontSize: 14, fontWeight: '800', marginBottom: 3 },
  status: { fontSize: 12, fontWeight: '600', lineHeight: 16 },
  button: { borderRadius: 12, paddingHorizontal: 13, paddingVertical: 11 },
  buttonText: { color: '#fff', fontSize: 12, fontWeight: '900' },
  example: { fontSize: 10, marginTop: 8, lineHeight: 14 },
});
''')


# ============================================================
# 2) COLOCA O CONTROLE NAS DUAS REPETICOES
# ============================================================
for rel, rep in [('app/(tabs)/index.tsx', 1), ('app/(tabs)/rep2.tsx', 2)]:
    p = ROOT / rel
    s = p.read_text()
    import_anchor = "import { CardClasse } from '@/components/CardClasse';"
    import_new = import_anchor + "\nimport { VoiceCounter } from '@/components/VoiceCounter';"
    if "@/components/VoiceCounter" not in s:
      if import_anchor not in s:
          raise SystemExit(f'{rel}: import CardClasse nao encontrado')
      s = s.replace(import_anchor, import_new, 1)

    header = f'<AppHeader rep={{{rep}}} label="REPETIÇÃO {"I" if rep == 1 else "II"}" />'
    combo = header + f'\n      <VoiceCounter rep={{{rep}}} dark={{dark}} />'
    if '<VoiceCounter ' not in s:
      if header not in s:
          raise SystemExit(f'{rel}: AppHeader nao encontrado')
      s = s.replace(header, combo, 1)
    p.write_text(s)


# ============================================================
# 3) CONFIG PLUGIN / PERMISSAO ANDROID
# ============================================================
cfg = ROOT / 'app.config.ts'
s = cfg.read_text()
if '"RECORD_AUDIO"' not in s:
    s = s.replace('permissions: ["POST_NOTIFICATIONS"],', 'permissions: ["POST_NOTIFICATIONS", "RECORD_AUDIO"],', 1)
if '"expo-speech-recognition"' not in s:
    s = s.replace('plugins: [\n    "expo-router",', 'plugins: [\n    "expo-router",\n    ["expo-speech-recognition", { microphonePermission: "Permitir que o Tetrazólio use o microfone para contagem por voz." }],', 1)
cfg.write_text(s)


# ============================================================
# 4) VALIDACOES
# ============================================================
checks = {
    'voice-file': voice.exists(),
    'rep1': '<VoiceCounter rep={1} dark={dark} />' in (ROOT / 'app/(tabs)/index.tsx').read_text(),
    'rep2': '<VoiceCounter rep={2} dark={dark} />' in (ROOT / 'app/(tabs)/rep2.tsx').read_text(),
    'plugin': 'expo-speech-recognition' in cfg.read_text(),
    'permission': 'RECORD_AUDIO' in cfg.read_text(),
    'principal': 'Classe 7 UP, principal umidade' in voice.read_text(),
    'limit': 'total >= CONFIG.MAX_TOTAL && !isComplemento' in voice.read_text(),
}
falhas = [k for k, ok in checks.items() if not ok]
if falhas:
    raise SystemExit('Validacoes v2.5 falharam: ' + ', '.join(falhas))

print('Tetrazolio v2.5 voz aplicado com sucesso')
