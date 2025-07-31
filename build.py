# Tools/build.py

import sys
import subprocess
from pathlib import Path


# === Configuration ===
ROOT_DIR = Path(__file__).resolve().parent

# Internal resource locations
PRESET_PATH_BUILDER = ROOT_DIR / 'Tools' / 'generate_preset_paths.py'
BUILTIN_HASH_BUILDER = ROOT_DIR / 'Tools' / 'generate_builtin_preset_hashes.py'
RSRC_QRC_FILE = ROOT_DIR / 'App' / 'Resources' / 'resources.qrc'
RSRC_PY_FILE = ROOT_DIR / 'App' / 'Common' / 'Resources.py'

# Compile flag
COMPILE_EXE = False

# version.res and compile information
OUTPUT_DIR = ROOT_DIR / 'Tools' / 'Compile'
VERSION_FILE = ROOT_DIR / 'Tools' / 'Compile' / 'version.res'
ICO_FILE = ROOT_DIR / 'App' / 'Resources' / 'Icons' / 'clef_icon.ico'
FILE_DESCRIPTION = 'Zelda64 Bank Creator'
FILE_VERSION = '0.1.0.0'
PRODUCT_NAME = 'Zelda64 Bank Creator'
PRODUCT_VERSION = '0.1.0.0'
LEGAL_COPYRIGHT = 'Copyright © 2025 Crinuleiroz'
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

    # Compile executable file
    if COMPILE_EXE:
        compiler_args = [
            '--mingw64', # Compiler
            '--enable-plugin=pyside6',
            '--mode=app', # Compile type
            # '--follow-imports',
            '--windows-console-mode=disable', # CLI mode
            f'--windows-icon-from-ico={str(ICO_FILE)}', # App icon
            f'--output-dir={OUTPUT_DIR}', # Output directory
            f'--output-filename={PRODUCT_NAME}', # Original name
            f'--file-description={FILE_DESCRIPTION}', # File description
            f'--file-version={FILE_VERSION}', # File version
            f'--product-name={PRODUCT_NAME}', # Prod name
            f'--product-version={PRODUCT_VERSION}', # Prod version
            f'--copyright={LEGAL_COPYRIGHT}', # Copyright
            str(APP_FILE) # main.py
        ]

        run([sys.executable, '-m', 'nuitka'] + compiler_args, 'Compiling executable with nuitka')
