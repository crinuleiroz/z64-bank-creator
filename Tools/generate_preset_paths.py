# Tools/generate_preset_paths.py

import sys
from pathlib import Path
from xml.etree import ElementTree as ET

# Configuration
ROOT_DIR = Path(__file__).resolve().parent.parent
QRC_FILE = ROOT_DIR / 'App' / 'Resources' / 'resources.qrc'
OUTPUT_FILE = ROOT_DIR / 'App' / 'Resources' / 'Presets' / 'PresetPaths.py'

# Add ROOT_DIR to sys.path if needed
sys.path.insert(0, str(ROOT_DIR))


def extract_paths_by_category(qrc_path: str) -> dict[str, list[str]]:
    tree = ET.parse(qrc_path)
    root = tree.getroot()

    categories = {
        'banks': [],
        'drumkits': [],
        'instruments': [],
        'drums': [],
        'effects': [],
        'samples': [],
        'envelopes': [],
        'other': []
    }

    match_map = {
        'presets/samples': 'samples',
        'presets/envelopes': 'envelopes',
        'presets/instruments': 'instruments',
        'presets/drums': 'drums',
        'presets/effects': 'effects',
        'presets/banks': 'banks',
        'presets/drumkits': 'drumkits',
    }

    for qresource in root.findall('qresource'):
        qprefix = qresource.attrib.get('prefix', '')
        for file_elem in qresource.findall('file'):
            relative_path = file_elem.text.strip()
            full_path = f':{qprefix}/{relative_path}'.replace('//', '/')

            matched = False
            for key, cat in match_map.items():
                if key in relative_path:
                    categories[cat].append(full_path)
                    matched = True
                    break

            if not matched:
                categories['other'].append(full_path)

    return categories


def generate_path_block(var_name: str, path_list: list[str]) -> list[str]:
    lines = [f'{var_name} = [']
    for path in path_list:
        lines.append(f'    "{path}",')
    lines.append(']')
    lines.append('')
    return lines


def generate_preset_paths_file(qrc_path: str, output_path: str):
    paths_by_cat = extract_paths_by_category(qrc_path)

    lines = [
        '# Auto-generated hash map of builtin presets',
        '# Do not edit manually. Regenerate using generate_preset_paths.py',
        ''
    ]

    for cat, paths in paths_by_cat.items():
        if not paths:
            continue
        var_name = f'{cat}_paths'.upper()
        lines += generate_path_block(var_name, paths)

    output_path.write_text('\n'.join(lines), encoding='utf-8')


if QRC_FILE.exists():
    generate_preset_paths_file(QRC_FILE, OUTPUT_FILE)