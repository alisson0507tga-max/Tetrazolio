from pathlib import Path

ROOT = Path('app-src')
selector = ROOT / 'components' / 'SoundSelector.tsx'

selector.write_text(r'''import React, { useState } from 'react';
import { Modal, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SOUND_OPTIONS, tocarSomConfirmacao } from '@/lib/confirmation-sound';
import { useStore } from '@/lib/tetrazolio-store';

export function SoundSelector() {
  const { estado, dispatch } = useStore();
  const [aberto, setAberto] = useState(false);
  const dark = estado.tema === 'dark';
  const bg = dark ? '#1f1f1f' : '#ffffff';
  const text = dark ? '#f5f5f5' : '#202124';
  const sub = dark ? '#bdbdbd' : '#5f6368';
  const fieldBg = dark ? '#292929' : '#f5f5f5';
  const border = dark ? '#555' : '#d0d0d0';

  const atual = SOUND_OPTIONS.find(item => item.id === estado.somSelecionado) ?? SOUND_OPTIONS[10];

  function selecionar(id: number) {
    dispatch({ type: 'SET_SOM_CONTAGEM', som: id });
    tocarSomConfirmacao(id);
    setAberto(false);
  }

  return (
    <View style={[styles.box, { backgroundColor: bg }]}> 
      <Text style={[styles.title, { color: text }]}>🔊 SOM DA CONTAGEM</Text>
      <Text style={[styles.help, { color: sub }]}>Escolha o toque usado quando uma semente for contabilizada.</Text>

      <View style={styles.row}>
        <TouchableOpacity
          style={[styles.select, { backgroundColor: fieldBg, borderColor: border }]}
          onPress={() => setAberto(true)}
          activeOpacity={0.75}
        >
          <View style={styles.selectTextWrap}>
            <Text style={[styles.small, { color: sub }]}>SOM SELECIONADO</Text>
            <Text style={[styles.selectedName, { color: text }]} numberOfLines={1}>
              {String(atual.id).padStart(2, '0')} — {atual.name}
            </Text>
          </View>
          <Text style={[styles.arrow, { color: text }]}>▼</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.listenBtn}
          onPress={() => tocarSomConfirmacao(atual.id)}
          activeOpacity={0.75}
        >
          <Text style={styles.listenText}>▶ OUVIR</Text>
        </TouchableOpacity>
      </View>

      <Modal visible={aberto} transparent animationType="fade" onRequestClose={() => setAberto(false)}>
        <View style={styles.overlay}>
          <View style={[styles.modalCard, { backgroundColor: bg }]}> 
            <View style={styles.modalHeader}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.modalTitle, { color: text }]}>Escolher som da contagem</Text>
                <Text style={[styles.modalHelp, { color: sub }]}>Toque em um som para selecionar e ouvir.</Text>
              </View>
              <TouchableOpacity style={styles.closeBtn} onPress={() => setAberto(false)}>
                <Text style={styles.closeText}>✕</Text>
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.list} contentContainerStyle={styles.listContent}>
              {SOUND_OPTIONS.map(item => {
                const selected = estado.somSelecionado === item.id;
                return (
                  <TouchableOpacity
                    key={item.id}
                    style={[
                      styles.option,
                      {
                        borderColor: selected ? '#2e7d32' : border,
                        backgroundColor: selected ? (dark ? '#173c1c' : '#e8f5e9') : fieldBg,
                      },
                    ]}
                    onPress={() => selecionar(item.id)}
                    activeOpacity={0.75}
                  >
                    <Text style={[styles.optionNumber, { color: selected ? '#66bb6a' : sub }]}>
                      {String(item.id).padStart(2, '0')}
                    </Text>
                    <Text style={[styles.optionName, { color: text }]}>{item.name}</Text>
                    <Text style={[styles.optionStatus, { color: selected ? '#66bb6a' : sub }]}>
                      {selected ? '✓' : '▶'}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  box: { borderRadius: 14, padding: 12, marginBottom: 12 },
  title: { fontSize: 14, fontWeight: '900', marginBottom: 4 },
  help: { fontSize: 11, marginBottom: 10 },
  row: { flexDirection: 'row', gap: 8, alignItems: 'stretch' },
  select: { flex: 1, minHeight: 58, borderWidth: 1.5, borderRadius: 11, paddingHorizontal: 12, paddingVertical: 8, flexDirection: 'row', alignItems: 'center' },
  selectTextWrap: { flex: 1, paddingRight: 8 },
  small: { fontSize: 8, fontWeight: '800', marginBottom: 2 },
  selectedName: { fontSize: 13, fontWeight: '900' },
  arrow: { fontSize: 15, fontWeight: '900' },
  listenBtn: { minWidth: 86, borderRadius: 11, backgroundColor: '#2e7d32', alignItems: 'center', justifyContent: 'center', paddingHorizontal: 10 },
  listenText: { color: '#fff', fontSize: 10, fontWeight: '900' },
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.68)', justifyContent: 'center', paddingHorizontal: 18, paddingVertical: 40 },
  modalCard: { borderRadius: 16, padding: 14, maxHeight: '82%' },
  modalHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  modalTitle: { fontSize: 16, fontWeight: '900' },
  modalHelp: { fontSize: 10, marginTop: 2 },
  closeBtn: { width: 36, height: 36, borderRadius: 18, backgroundColor: '#d32f2f', alignItems: 'center', justifyContent: 'center', marginLeft: 8 },
  closeText: { color: '#fff', fontSize: 15, fontWeight: '900' },
  list: { flexGrow: 0 },
  listContent: { gap: 7, paddingBottom: 4 },
  option: { minHeight: 50, borderWidth: 1.5, borderRadius: 10, paddingHorizontal: 11, flexDirection: 'row', alignItems: 'center' },
  optionNumber: { width: 30, fontSize: 10, fontWeight: '900' },
  optionName: { flex: 1, fontSize: 12, fontWeight: '800' },
  optionStatus: { width: 24, textAlign: 'center', fontSize: 14, fontWeight: '900' },
});
''')

final = selector.read_text()
for trecho in [
    'SOM SELECIONADO',
    '▼',
    '▶ OUVIR',
    'Modal visible={aberto}',
    'SOUND_OPTIONS.map',
    "dispatch({ type: 'SET_SOM_CONTAGEM', som: id })",
]:
    if trecho not in final:
        raise SystemExit(f'Validacao seletor compacto falhou: {trecho}')

print('v2.5.12 aplicada: seletor de som compacto com dropdown e botao Ouvir')
