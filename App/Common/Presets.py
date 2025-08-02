# App/Common/Presets.py

import yaml

from PySide6.QtCore import QFile, QTextStream

# App/Common
from App.Common.Structs import Instrument, Drum, Drumkit, Effect, TunedSample, Sample, VadpcmLoop, VadpcmBook, Envelope
from App.Common.Audiobank import Audiobank
from App.Common.Serialization import bank_from_dict, drumkit_from_dict, instrument_from_dict, drum_from_dict, effect_from_dict, sample_from_dict, envelope_from_dict

# App/Resources
from App.Resources.Presets.PresetPaths import BANKS_PATHS, DRUMKITS_PATHS, INSTRUMENTS_PATHS, SAMPLES_PATHS, ENVELOPES_PATHS


#region Base Class
class PresetStoreBase:
    def __init__(self):
        self.instruments: dict[int, Instrument] = {}
        self.drums: dict[int, Drum] = {}
        self.effects: dict[int, Effect] = {}
        self.samples: dict[int, Sample] = {}
        self.envelopes: dict[int, Envelope] = {}
        self.drumkits: dict[int, Drumkit] = {}
        self.banks: dict[int, Audiobank] = {}

        self.file_map: dict[int, str] = {}

    def register(self, obj, path=None):
        key = id(obj)
        self.file_map[key] = path

        match obj:
            case Instrument():
                self.instruments[key] = obj
            case Drum():
                self.drums[key] = obj
            case Effect():
                self.effects[key] = obj
            case Sample():
                self.samples[key] = obj
            case Envelope():
                self.envelopes[key] = obj
            case Drumkit():
                self.drumkits[key] = obj
            case Audiobank():
                self.banks[key] = obj

        return obj

    # Name getters
    def get_instrument_by_name(self, name: str) -> Instrument | None:
        return next((i for i in self.instruments.values() if i.name.lower() == name.lower()), None)

    def get_drum_by_name(self, name: str) -> Drum | None:
        return next((d for d in self.drums.values() if d.name.lower() == name.lower()), None)

    def get_effect_by_name(self, name: str) -> Effect | None:
        return next((e for e in self.effects.values() if e.name.lower() == name.lower()), None)

    def get_sample_by_name(self, name: str) -> Sample | None:
        return next((s for s in self.samples.values() if s.name.lower() == name.lower()), None)

    def get_envelope_by_name(self, name: str) -> Envelope | None:
        return next((e for e in self.envelopes.values() if e.name.lower() == name.lower()), None)

    def get_drumkit_by_name(self, name: str) -> list[Drum] | None:
        return next((dk for dk in self.drumkits.values() if dk.name.lower() == name.lower()), None)

    def get_bank_by_name(self, name: str) -> Audiobank | None:
        return next((b for b in self.banks.values() if b.name.lower() == name.lower()), None)

    # Id getters
    def get_instrument(self, key: int):
        return self.instruments.get(key)

    def get_drum(self, key: int):
        return self.drums.get(key)

    def get_effect(self, key: int):
        return self.effects.get(key)

    def get_sample(self, key: int):
        return self.samples.get(key)

    def get_envelope(self, key: int):
        return self.envelopes.get(key)

    def get_drumkit(self, key: int):
        return self.drumkits.get(key)

    def get_bank(self, key: int):
        return self.banks.get(key)

    def get_path(self, key: int):
        return self.file_map.get(key)
#endregion


#region Built-in Presets
class BuiltinPresetStore(PresetStoreBase):
    def __init__(self):
        # Stores
        super().__init__()

        # Internal Paths
        self.loaded_paths: set[str] = set()

    def load_builtin_yaml(self, path: str):
        if path in self.loaded_paths:
            return

        file = QFile(path)
        if not file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            raise IOError(f'Failed to open builtin preset: {path}')

        stream = QTextStream(file)
        content = stream.readAll()
        file.close()

        raw = yaml.safe_load(content)
        if not isinstance(raw, dict) or len(raw) != 1:
            return

        key = next(iter(raw))
        data = raw[key]

        match key.lower():
            case 'envelope':
                obj = envelope_from_dict(data)
                self.register(obj, path)
            case 'sample':
                obj = sample_from_dict(data)
                self.register(obj, path)
            case 'instrument':
                obj = instrument_from_dict(data, self)
                self.register(obj, path)
            case 'drum':
                obj = drum_from_dict(data, self)
                self.register(obj, path)
            case 'effect':
                obj = effect_from_dict(data, self)
                self.register(obj, path)
            case 'drumkit':
                obj = drumkit_from_dict(data, self)
                self.register(obj, path)
            case 'bank':
                obj = bank_from_dict(data, self)
                self.register(obj, path)

        self.loaded_paths.add(path)

    def load_builtin_presets(self):
        for path in (ENVELOPES_PATHS + SAMPLES_PATHS + INSTRUMENTS_PATHS + DRUMKITS_PATHS + BANKS_PATHS):
            self.load_builtin_yaml(path)

    def get_builtin_preset_list(self, game_id: str, preset_type: str):
        from App.Common.Helpers import has_valid_address

        builtin_dict = getattr(self, preset_type, {})
        builtin_list = [
            p for p in builtin_dict.values()
            if has_valid_address(p, game_id, preset_type)
        ]

        return builtin_list
#endregion


#region User-defined Presets
class UserPresetStore(PresetStoreBase):
    def __init__(self):
        super().__init__()

    def clear(self):
        self.__init__()

    def load_user_presets(self, preset_dir):
        self.clear()

        type_map = {
            'bank': bank_from_dict,
            'drumkit': drumkit_from_dict,
            'instrument': instrument_from_dict,
            'drum': drum_from_dict,
            'effect': effect_from_dict,
            'sample': lambda data, _: sample_from_dict(data),
            'envelope': lambda data, _: envelope_from_dict(data),
        }

        yaml_files = list(preset_dir.rglob('*.yaml')) + list(preset_dir.rglob('*.yml'))
        for file in yaml_files:
            if not file.is_file():
                continue

            with open(file, 'r', encoding='utf-8') as f:
                raw = yaml.safe_load(f)

            if not isinstance(raw, dict) or len(raw) != 1:
                continue

            root_key = next(iter(raw))
            from_dict = type_map.get(root_key.lower())

            if not from_dict:
                continue

            data = raw[root_key]
            try:
                obj = from_dict(data, self)
                self.register(obj, str(file))
            except Exception as ex:
                print(f"[UserPresetStore] Failed to load {root_key} from {file}: {ex}")

    def get_user_preset_list(self, game_id: str, preset_type: str):
        from App.Common.Helpers import has_valid_address

        user_dict = getattr(self, preset_type, {})
        user_list = list(user_dict.values)

        return user_list

    def add_preset(self, obj, path=None):
        self.register(obj, path)

    def remove_preset(self, obj):
        key = id(obj)

        match obj:
            case Instrument():
                self.instruments.pop(key, None)
            case Drum():
                self.drums.pop(key, None)
            case Effect():
                self.effects.pop(key, None)
            case Sample():
                self.samples.pop(key, None)
            case Envelope():
                self.envelopes.pop(key, None)
            case Drumkit():
                self.drumkits.pop(key, None)
            case Audiobank():
                self.banks.pop(key, None)

        self.file_map.pop(key, None)

    def replace_preset(self, old_preset, new_preset):
        self.remove_preset(old_preset)
        self.add_preset(new_preset)
#endregion


#region Preset Registry
class PresetRegistry:
    def __init__(self):
        self._registry = {}
        self.id_map: dict[int, object] = {}

    def get_or_register(self, obj):
        key = id(obj)
        if key in self._registry:
            return self._registry[key]

        self._registry[key] = obj
        self.id_map[key] = obj
        return obj

    def get_by_id(self, key: int):
        return self.id_map.get(key)

    def get_id(self, obj) -> int:
        return id(obj)
#endregion


#region Instantiate
presetRegistry = PresetRegistry()
builtinPresetStore = BuiltinPresetStore()
userPresetStore = UserPresetStore()
#endregion
