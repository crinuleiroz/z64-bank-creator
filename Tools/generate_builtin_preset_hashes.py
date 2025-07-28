# Tools/generate_builtin_sample_hashes.py

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

# Configuration
ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT_DIR / 'App' / 'Resources' / 'Presets' / 'BuiltinPresetHashes.py'

# Add ROOT_DIR to sys.path if needed
sys.path.insert(0, str(ROOT_DIR))

import App.Common.Resources
from App.Common.Presets import builtinPresetStore


def generate_hash_block(var_name: str, preset_dict: dict, category_prefix: str) -> list[str]:
    lines = [f'{var_name} = {{']
    for _, preset in preset_dict.items():
        preset_hash = preset.get_hash()
        ref = f'@{category_prefix}/{preset.name}'
        lines.append(f'    {repr(preset_hash)}: {repr(ref)},')
    lines.append('}')
    lines.append('')
    return lines


def generate_builtin_preset_hashes():
    app = QApplication(sys.argv)
    builtinPresetStore.load_builtin_presets()

    lines = [
        '# Auto-generated hash map of builtin presets',
        '# Do not edit manually. Regenerate using generate_builtin_preset_hashes.py',
        ''
    ]

    lines += generate_hash_block('BUILTIN_INSTRUMENT_PRESET_HASHES', builtinPresetStore.instruments, 'instrument')
    lines += generate_hash_block('BUILTIN_DRUM_PRESET_HASHES', builtinPresetStore.drums, 'drum')
    lines += generate_hash_block('BUILTIN_EFFECT_PRESET_HASHES', builtinPresetStore.effects, 'effect')
    lines += generate_hash_block('BUILTIN_SAMPLE_PRESET_HASHES', builtinPresetStore.samples, 'sample')
    lines += generate_hash_block('BUILTIN_ENVELOPE_PRESET_HASHES', builtinPresetStore.envelopes, 'envelope')

    OUTPUT_FILE.write_text('\n'.join(lines), encoding='utf-8')


generate_builtin_preset_hashes()
