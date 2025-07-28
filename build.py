# Tools/build.py

import sys
import subprocess
from pathlib import Path


# Configuration
ROOT_DIR = Path(__file__).resolve().parent

# Build resources
PRESET_PATH_BUILDER = ROOT_DIR / 'Tools' / 'generate_preset_paths.py'
BUILTIN_HASH_BUILDER = ROOT_DIR / 'Tools' / 'generate_builtin_preset_hashes.py'
RSRC_QRC_FILE = ROOT_DIR / 'App' / 'Resources' / 'resources.qrc'
RSRC_PY_FILE = ROOT_DIR / 'App' / 'Resources' / 'Resources.py'

# Build executable
BUILD_EXE = True
UPX_DIR = ROOT_DIR / 'Tools' / 'Compile' / 'upx-5.0.2-win64'
VERSION_FILE = ROOT_DIR / 'Tools' / 'Compile' / 'version.rc'
ICO_FILE = ROOT_DIR / 'App' / 'Resources' / 'Icons' / 'clef_icon.ico'
APP_FILE = ROOT_DIR / 'gui.pyw'


def run(command: list[str], desc: str):
    print(f'==> {desc}')
    result = subprocess.run(command)
    if result.returncode != 0:
        print(f'⛔ Failed: {desc}')
        sys.exit(result.returncode)
    print(f'✅ Success: {desc}\n')


if __name__ == '__main__':
    # Build resources
    run([sys.executable, str(PRESET_PATH_BUILDER)], 'Generating PresetPaths.py')
    run(["pyside6-rcc", str(RSRC_QRC_FILE), "-o", str(RSRC_PY_FILE)], 'Compiling Qt resource file')
    run([sys.executable, str(BUILTIN_HASH_BUILDER)], 'Generating BuiltinPresetHashes.py')

    if BUILD_EXE:
        if not UPX_DIR.exists():
            print(f'ERROR: UPX directory not found at: {UPX_DIR}')
            sys.exit(1)

        # Build executable
        pyinstaller_cmd = [
            'pyinstaller',
            '--noconfirm',
            '--onefile',
            '--windowed',
            '--icon', str(ICO_FILE),
            '--upx-dir', str(UPX_DIR),
            '--clean',
            '--optimize', '2',
            '--version-file', str(VERSION_FILE),
            str(APP_FILE)
        ]

        run(pyinstaller_cmd, 'Building executable with PyInstaller')
