from pathlib import Path
import base64

ROOT = Path('app-src')
assets = ROOT / 'assets' / 'images'
assets.mkdir(parents=True, exist_ok=True)

# Camada frontal totalmente transparente. O desenho aprovado fica na camada
# de fundo do adaptive icon, evitando o zoom/corte que ocorreu na 2.3.
transparent_png_b64 = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ'
    'AAAADUlEQVR42mNk+M/wHwAF/gL+4VfWAAAAAElFTkSuQmCC'
)
(assets / 'transparent-icon.png').write_bytes(base64.b64decode(transparent_png_b64))

cfg = ROOT / 'app.config.ts'
lines = cfg.read_text().splitlines()

# Garante que o icone normal continue sendo a imagem aprovada exata.
found_main = False
for i, line in enumerate(lines):
    if line.strip().startswith('icon:'):
        indent = line[: len(line) - len(line.lstrip())]
        lines[i] = f'{indent}icon: "./assets/images/tetrazolio-icon.png",'
        found_main = True
        break

if not found_main:
    # Insere logo depois de "name" se o config nao tiver campo icon explicito.
    for i, line in enumerate(lines):
        if line.strip().startswith('name:'):
            indent = line[: len(line) - len(line.lstrip())]
            lines.insert(i + 1, f'{indent}icon: "./assets/images/tetrazolio-icon.png",')
            found_main = True
            break

if not found_main:
    raise SystemExit('Nao foi possivel configurar o icone principal')

# Troca somente o bloco adaptiveIcon. A imagem completa passa a ser background,
# que nao sofre o mesmo zoom da camada foreground nos launchers Android.
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
    f'{indent}  backgroundImage: "./assets/images/tetrazolio-icon.png",',
    f'{indent}  foregroundImage: "./assets/images/transparent-icon.png",',
    f'{indent}}},',
]
lines[start:end + 1] = new_block
cfg.write_text('\n'.join(lines) + '\n')

print('Icone v2.4 configurado sem zoom de foreground')
