# Tools/build.py

import sys
import subprocess
from pathlib import Path


def run(command: list[str], desc: str):
    print(f"==> {desc}")
    result = subprocess.run(command)
    if result.returncode != 0:
        print(f"⛔ Failed: {desc}")
        sys.exit(result.returncode)
    print(f"✅ Success: {desc}\n")


if __name__ == "__main__":
    base = Path(__file__).parent

    # QRC File
    qrc_file = base / "App" / "Resources" / "resources.qrc"
    qrc_py_output = base / "App" / "Common" / "Resources.py"

    # Preset Paths
    preset_path_script = base / "Tools" / "generate_preset_paths.py"

    # Builtin Hashes
    builtin_hash_script = base / "Tools" / "generate_builtin_preset_hashes.py"

    # Execute
    run([sys.executable, str(preset_path_script)], "Generating PresetPaths.py")
    run(["pyside6-rcc", str(qrc_file), "-o", str(qrc_py_output)], "Compiling Qt resource file")
    run([sys.executable, str(builtin_hash_script)], 'Generating BuiltinPresetHashes.py')
