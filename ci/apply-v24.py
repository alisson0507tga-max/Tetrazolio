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
# 1) PREFERENCIA DE SOM PERSISTENTE
# ============================================================
store = ROOT / 'lib' / 'tetrazolio-store.ts'
s = store.read_text()

old = "  tema: 'light' | 'dark';\n  analises: AnaliseHistorico[];"
new = "  tema: 'light' | 'dark';\n  somAtivo: boolean;\n  analises: AnaliseHistorico[];"
if 'somAtivo: boolean;' not in s:
    if old not in s:
        raise SystemExit('Estado: ponto somAtivo nao encontrado')
    s = s.replace(old, new, 1)

old = "  tema: 'light',\n  analises: [],"
new = "  tema: 'light',\n  somAtivo: true,\n  analises: [],"
if 'somAtivo: true,' not in s:
    if old not in s:
        raise SystemExit('estadoInicial: ponto somAtivo nao encontrado')
    s = s.replace(old, new, 1)

old = "  | { type: 'TOGGLE_TEMA' }\n  | { type: 'SET_EXTRAS'; extras: Partial<ExtrasData> }"
new = "  | { type: 'TOGGLE_TEMA' }\n  | { type: 'TOGGLE_SOM' }\n  | { type: 'SET_EXTRAS'; extras: Partial<ExtrasData> }"
if "type: 'TOGGLE_SOM'" not in s:
    if old not in s:
        raise SystemExit('Action: TOGGLE_SOM ponto nao encontrado')
    s = s.replace(old, new, 1)

old = "    case 'TOGGLE_TEMA':\n      return { ...state, tema: state.tema === 'light' ? 'dark' : 'light' };\n\n    case 'SET_EXTRAS':"
new = "    case 'TOGGLE_TEMA':\n      return { ...state, tema: state.tema === 'light' ? 'dark' : 'light' };\n\n    case 'TOGGLE_SOM':\n      return { ...state, somAtivo: !state.somAtivo };\n\n    case 'SET_EXTRAS':"
if "case 'TOGGLE_SOM':" not in s:
    if old not in s:
        raise SystemExit('Reducer: TOGGLE_SOM ponto nao encontrado')
    s = s.replace(old, new, 1)

# Compatibilidade: dados antigos da 2.3 e anteriores recebem som ligado por padrao.
old = "        extras: { ...estadoInicial.extras, ...(loaded.extras ?? {}) },\n      };"
new = "        extras: { ...estadoInicial.extras, ...(loaded.extras ?? {}) },\n        somAtivo: loaded.somAtivo !== false,\n      };"
if 'somAtivo: loaded.somAtivo !== false' not in s:
    if old not in s:
        raise SystemExit('LOAD_STATE: compatibilidade som nao encontrada')
    s = s.replace(old, new, 1)

old = "      return { ...estadoInicial, tema: state.tema, analises: state.analises };"
new = "      return { ...estadoInicial, tema: state.tema, somAtivo: state.somAtivo, analises: state.analises };"
if new not in s:
    if old not in s:
        raise SystemExit('LIMPAR_TUDO: preservacao do som nao encontrada')
    s = s.replace(old, new, 1)

store.write_text(s)


# ============================================================
# 2) BIP SOMENTE QUANDO A PREFERENCIA ESTIVER LIGADA
# ============================================================
card = ROOT / 'components' / 'CardClasse.tsx'
s = card.read_text()
old = "    dispatch({ type: 'ADICIONAR', rep, classe: classeIdx, tipo });\n    tocarSomConfirmacao();"
new = "    dispatch({ type: 'ADICIONAR', rep, classe: classeIdx, tipo });\n    if (estado.somAtivo) tocarSomConfirmacao();"
if new not in s:
    if old not in s:
        raise SystemExit('CardClasse: chamada do som nao encontrada')
    s = s.replace(old, new, 1)
card.write_text(s)

modal = ROOT / 'components' / 'ModalDanoMultiplo.tsx'
s = modal.read_text()
old = "    dispatch({ type: 'ADICIONAR', rep, classe, tipo, danoPrincipal: letra });\n    tocarSomConfirmacao();"
new = "    dispatch({ type: 'ADICIONAR', rep, classe, tipo, danoPrincipal: letra });\n    if (estado.somAtivo) tocarSomConfirmacao();"
if new not in s:
    if old not in s:
        raise SystemExit('ModalDanoMultiplo: chamada do som nao encontrada')
    s = s.replace(old, new, 1)
modal.write_text(s)


# ============================================================
# 3) BOTAO SOM LIGADO/DESLIGADO NO RELATORIO
# ============================================================
report = ROOT / 'app' / '(tabs)' / 'relatorio.tsx'
s = report.read_text()
anchor = """        <TouchableOpacity style={styles.btnLimpar} onPress={limparTudo}>
          <Text style={styles.btnLimparText}>🗑️ LIMPAR TODOS OS DADOS</Text>
        </TouchableOpacity>"""
sound_button = """        <TouchableOpacity
          style={[
            styles.actionBtn,
            {
              backgroundColor: estado.somAtivo ? '#1565c0' : '#616161',
              marginBottom: 8,
              flexDirection: 'row',
              gap: 8,
            },
          ]}
          onPress={() => {
            if (Platform.OS !== 'web') {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            }
            dispatch({ type: 'TOGGLE_SOM' });
            showToast(estado.somAtivo ? '🔇 Som de contagem desligado' : '🔊 Som de contagem ligado');
          }}
          activeOpacity={0.8}
        >
          <Text style={styles.actionBtnText}>
            {estado.somAtivo ? '🔊 Som de contagem: Ligado' : '🔇 Som de contagem: Desligado'}
          </Text>
        </TouchableOpacity>

""" + anchor
if 'Som de contagem: Ligado' not in s:
    if anchor not in s:
        raise SystemExit('Relatorio: ponto do botao de som nao encontrado')
    s = s.replace(anchor, sound_button, 1)
report.write_text(s)


# ============================================================
# 4) CONFERENCIA FINAL ANTES DE SALVAR NO HISTORICO
# ============================================================
hist = ROOT / 'app' / '(tabs)' / 'historico.tsx'
s = hist.read_text()

old_import = "import { useStore } from '@/lib/tetrazolio-store';"
new_import = "import { calcularResultados, CONFIG, formatarMedia, getTotalRep, useStore } from '@/lib/tetrazolio-store';"
if new_import not in s:
    if old_import not in s:
        raise SystemExit('Historico: import do store nao encontrado')
    s = s.replace(old_import, new_import, 1)

start = s.find('  function salvarAnalise() {')
end = s.find('\n  function deletarAnalise', start)
if start == -1 or end == -1:
    raise SystemExit('Historico: funcao salvarAnalise nao localizada')

new_save = """  function efetivarSalvamento() {
    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
    dispatch({ type: 'SALVAR_ANALISE' });
    showToast('💾 Análise salva no histórico');
  }

  function salvarAnalise() {
    if (!estado.extras.amostra) {
      Alert.alert('⚠️ ATENÇÃO', 'Preencha o número da amostra antes de salvar');
      return;
    }

    const totalI = getTotalRep(estado.dados, 1);
    const totalII = getTotalRep(estado.dados, 2);
    const resultados = calcularResultados(estado.dados);
    const vigorMed = formatarMedia((resultados.vigor[0] + resultados.vigor[1]) / 2);
    const pgMed = formatarMedia((resultados.pg[0] + resultados.pg[1]) / 2);
    const completas = totalI === CONFIG.MAX_TOTAL && totalII === CONFIG.MAX_TOTAL;

    const mensagem = [
      `Rep I: ${totalI}/${CONFIG.MAX_TOTAL} ${totalI === CONFIG.MAX_TOTAL ? '✅' : '⚠️'}`,
      `Rep II: ${totalII}/${CONFIG.MAX_TOTAL} ${totalII === CONFIG.MAX_TOTAL ? '✅' : '⚠️'}`,
      '',
      `Vigor: I ${resultados.vigor[0]}% • II ${resultados.vigor[1]}% • Méd ${vigorMed}%`,
      `P.G.: I ${resultados.pg[0]}% • II ${resultados.pg[1]}% • Méd ${pgMed}%`,
      completas ? '' : '',
      completas ? 'Confira os dados antes de confirmar.' : '⚠️ Uma ou mais repetições ainda não chegaram a 50 sementes.',
    ].filter(Boolean).join('\\n');

    Alert.alert(
      completas ? '✅ Conferir análise' : '⚠️ Análise incompleta',
      mensagem,
      [
        { text: 'Voltar', style: 'cancel' },
        {
          text: completas ? 'Confirmar e salvar' : 'Salvar mesmo assim',
          onPress: efetivarSalvamento,
        },
      ]
    );
  }
"""
s = s[:start] + new_save + s[end:]
hist.write_text(s)


# ============================================================
# 5) SAFE AREA DA TELA TABELA
# Rep I/II usam AppHeader com insets; Historico usa ScreenContainer;
# Relatorio ja foi corrigido na 2.3.
# ============================================================
tabela = ROOT / 'app' / '(tabs)' / 'tabela.tsx'
s = tabela.read_text()
old = "<View style={[styles.header, { backgroundColor: cardBg, borderBottomColor: borderColor }]} >"
# formato real nao tem espaco antes do >; mantemos duas alternativas
if 'paddingTop: insets.top + 14' not in s:
    target = "<View style={[styles.header, { backgroundColor: cardBg, borderBottomColor: borderColor }]} >"
    target2 = "<View style={[styles.header, { backgroundColor: cardBg, borderBottomColor: borderColor }]}>")
    replacement = "<View style={[styles.header, { backgroundColor: cardBg, borderBottomColor: borderColor, paddingTop: insets.top + 14 }]}>")
    if target2 in s:
        s = s.replace(target2, replacement, 1)
    elif target in s:
        s = s.replace(target, replacement, 1)
    else:
        raise SystemExit('Tabela: cabecalho para safe area nao encontrado')
tabela.write_text(s)


# ============================================================
# VALIDACOES BASICAS DE INTEGRIDADE
# ============================================================
checks = {
    'store-som': 'somAtivo: boolean;' in store.read_text(),
    'card-som': 'if (estado.somAtivo) tocarSomConfirmacao();' in card.read_text(),
    'modal-som': 'if (estado.somAtivo) tocarSomConfirmacao();' in modal.read_text(),
    'toggle-som': 'Som de contagem: Ligado' in report.read_text(),
    'conferencia': 'Confirmar e salvar' in hist.read_text(),
    'tabela-safe': 'paddingTop: insets.top + 14' in tabela.read_text(),
}
falhas = [k for k, ok in checks.items() if not ok]
if falhas:
    raise SystemExit('Validacoes v2.4 falharam: ' + ', '.join(falhas))

print('Melhorias v2.4 aplicadas com sucesso (sem alterar regras de contagem)')
