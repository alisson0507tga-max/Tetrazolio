from pathlib import Path

ROOT = Path('app-src')
assets = ROOT / 'assets' / 'images'
icon = assets / 'tetrazolio-icon.jpg'
if not icon.exists():
    raise SystemExit('Novo icone v2.5.8 nao encontrado')

# ============================================================
# 1) NOVO ICONE + SPLASH COMO NO VIDEO
# ============================================================
cfg = ROOT / 'app.config.ts'
lines = cfg.read_text().splitlines()

# Icone principal.
icon_idx = None
for i, line in enumerate(lines):
    if line.strip().startswith('icon:'):
        indent = line[: len(line) - len(line.lstrip())]
        lines[i] = f'{indent}icon: "./assets/images/tetrazolio-icon.jpg",'
        icon_idx = i
        break
if icon_idx is None:
    raise SystemExit('Propriedade icon nao encontrada no app.config.ts')

# Adaptive icon: usa a imagem completa como fundo para nao cortar o microscopio.
for i, line in enumerate(lines):
    if 'backgroundImage:' in line and 'tetrazolio-icon' in line:
        indent = line[: len(line) - len(line.lstrip())]
        lines[i] = f'{indent}backgroundImage: "./assets/images/tetrazolio-icon.jpg",'
        break

# Remove bloco splash antigo, se existir no nivel principal.
start = None
end = None
for i, line in enumerate(lines):
    if line.strip() == 'splash: {':
        base_indent = len(line) - len(line.lstrip())
        if base_indent <= 2:
            start = i
            depth = 0
            for j in range(i, len(lines)):
                depth += lines[j].count('{')
                depth -= lines[j].count('}')
                if j > i and depth <= 0:
                    end = j
                    break
            break
if start is not None and end is not None:
    del lines[start:end + 1]
    # Reacha o indice do icon apos remover linhas.
    icon_idx = next(i for i, line in enumerate(lines) if line.strip().startswith('icon:'))

splash_block = [
    '  splash: {',
    '    image: "./assets/images/tetrazolio-icon.jpg",',
    '    resizeMode: "contain",',
    '    backgroundColor: "#000000",',
    '  },',
]
lines[icon_idx + 1:icon_idx + 1] = splash_block
cfg.write_text('\n'.join(lines) + '\n')

# ============================================================
# 2) VOZ MAIS AGIL PARA COMANDOS CURTOS
# ============================================================
voice = ROOT / 'components' / 'VoiceCounter.tsx'
s = voice.read_text()

# Agora os comandos sao curtos e estruturados; web_search tende a responder
# melhor que free_form para esse tipo de frase no reconhecedor Android.
s = s.replace(
    "EXTRA_LANGUAGE_MODEL: pendenciaPrincipal.current ? 'web_search' : 'free_form'",
    "EXTRA_LANGUAGE_MODEL: 'web_search'",
    1,
)

# Reduz a espera apos frase final e apos parcial estabilizado. Mantem uma
# folga maior se o usuario terminar momentaneamente em 'e', para nao cortar
# UP / UM / UPM no meio.
s = s.replace(
    'const esperaMs = terminaComE ? 500 : (isFinal ? 220 : 340);',
    'const esperaMs = terminaComE ? 420 : (isFinal ? 140 : 280);',
    1,
)
voice.write_text(s)

# Validacoes obrigatorias.
config_final = cfg.read_text()
voice_final = voice.read_text()
for trecho in [
    'icon: "./assets/images/tetrazolio-icon.jpg"',
    'splash: {',
    'image: "./assets/images/tetrazolio-icon.jpg"',
    'backgroundColor: "#000000"',
]:
    if trecho not in config_final:
        raise SystemExit(f'Validacao visual v2.5.8 falhou: {trecho}')
for trecho in [
    "EXTRA_LANGUAGE_MODEL: 'web_search'",
    'const esperaMs = terminaComE ? 420 : (isFinal ? 140 : 280);',
    "if (u && p && m) return 'UPM';",
    "if (u && p) return 'UP';",
    "if (u && m) return 'UM';",
]:
    if trecho not in voice_final:
        raise SystemExit(f'Validacao voz v2.5.8 falhou: {trecho}')

print('v2.5.8 aplicada: novo icone, splash preto centralizado e voz mais agil')
