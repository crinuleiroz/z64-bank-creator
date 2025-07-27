# App/Common/Serialization

from typing import Optional

# App/Common
from App.Common.Enums import AudioStorageMedium, AudioCacheLoadType, SampleBankId, AudioSampleCodec, AudioSampleLoopCount, EnvelopeOpcode
from App.Common.Structs import Drumkit, Instrument, Drum, Effect, TunedSample, Sample, VadpcmLoop, VadpcmBook, Envelope
from App.Common.Audiobank import TableEntry, Audiobank


#region Enum Helpers
def parse_envelope_array(arr):
    result = []
    for val in arr:
        if isinstance(val, str):
            match val.upper():
                case 'DISABLE':
                    result.append(EnvelopeOpcode.DISABLE)
                case 'HANG':
                    result.append(EnvelopeOpcode.HANG)
                case 'GOTO':
                    result.append(EnvelopeOpcode.GOTO)
                case 'RESTART':
                    result.append(EnvelopeOpcode.RESTART)
        else:
            result.append(val)
    return result


def parse_medium(value) -> AudioStorageMedium:
    if isinstance(value, str):
        match value.upper():
            case 'RAM':
                return AudioStorageMedium.RAM
            case 'UNK':
                return AudioStorageMedium.UNK
            case 'CART':
                return AudioStorageMedium.CART
            case 'DISK_DRIVE':
                return AudioStorageMedium.DISK_DRIVE
            case 'RAM_UNLOADED':
                return AudioStorageMedium.RAM_UNLOADED
            case _:
                raise ValueError(f"Invalid storage_medium string: {value}")
    else:
        return AudioStorageMedium(value)


def parse_cache_type(value) -> AudioCacheLoadType:
    if isinstance(value, str):
        match value.upper():
            case 'PERMANENT':
                return AudioCacheLoadType.PERMANENT
            case 'PERSISTENT':
                return AudioCacheLoadType.PERSISTENT
            case 'TEMPORARY':
                return AudioCacheLoadType.TEMPORARY
            case 'EITHER':
                return AudioCacheLoadType.EITHER
            case 'EITHER_NOSYNC':
                return AudioCacheLoadType.EITHER_NOSYNC
            case _:
                raise ValueError(f"Invalid cache_load_type string: {value}")
    else:
        return AudioCacheLoadType(value)


def parse_bank_id(value) -> SampleBankId:
    if isinstance(value, str):
        match value.upper():
            case 'BANK_0':
                return SampleBankId.BANK_0
            case 'BANK_1':
                return SampleBankId.BANK_1
            case 'BANK_2':
                return SampleBankId.BANK_2
            case 'BANK_3':
                return SampleBankId.BANK_3
            case 'BANK_4':
                return SampleBankId.BANK_4
            case 'BANK_5':
                return SampleBankId.BANK_5
            case 'BANK_6':
                return SampleBankId.BANK_6
            case 'NO_BANK':
                return SampleBankId.NO_BANK
            case _:
                raise ValueError(f'Invalid sample_bank_id string: {value}')
    else:
        return SampleBankId(value)


def parse_codec(value) -> AudioSampleCodec:
    if isinstance(value, str):
        match value.upper():
            case 'ADPCM':
                return AudioSampleCodec.ADPCM
            case 'S8':
                return AudioSampleCodec.S8
            case 'S16_INMEM':
                return AudioSampleCodec.S16_INMEM
            case 'SMALL_ADPCM':
                return AudioSampleCodec.SMALL_ADPCM
            case 'REVERB':
                return AudioSampleCodec.REVERB
            case 'S16':
                return AudioSampleCodec.S16
            case 'UNK6':
                return AudioSampleCodec.UNK6
            case 'UNK7':
                return AudioSampleCodec.UNK7
            case _:
                raise ValueError(f"Invalid loop_count string: {value}")
    else:
        return AudioStorageMedium(value)


def parse_loop_count(value) -> AudioSampleLoopCount:
    if isinstance(value, str):
        match value.upper():
            case 'NO_LOOP':
                return AudioSampleLoopCount.NO_LOOP
            case 'INDEFINITE':
                return AudioSampleLoopCount.INDEFINITE
            case _:
                raise ValueError(f"Invalid loop_count string: {value}")
    else:
        return AudioSampleLoopCount(value)
#endregion


#region Preset Helpers
def get_registry():
    from App.Common.Presets import presetRegistry
    return presetRegistry


def unwrap_typed_dict(entry: dict, expected_key: str) -> dict:
    if isinstance(entry, dict) and len(entry) == 1 and expected_key in entry:
        return entry[expected_key]
    return entry


def parse_reference(ref: str) -> tuple[str, str]:
    if not ref.startswith('@') or '/' not in ref:
        raise ValueError(f"Malformed reference string: '{ref}'")
    _, remainder = ref.split('@', 1)
    type_, name = remainder.split('/', 1)
    return type_.lower(), name


def resolve_reference(ref: str):
    from App.Common.Presets import builtinPresetStore, userPresetStore
    type_, name = parse_reference(ref)

    match type_:
        case 'sample':
            return builtinPresetStore.get_sample_by_name(name) or \
                userPresetStore.get_sample_by_name(name)

        case 'envelope':
            return builtinPresetStore.get_envelope_by_name(name) or \
                userPresetStore.get_envelope_by_name(name)

        case 'instrument':
            return builtinPresetStore.get_instrument_by_name(name) or \
                userPresetStore.get_instrument_by_name(name)

        case 'drum':
            return builtinPresetStore.get_drum_by_name(name) or \
                userPresetStore.get_drum_by_name(name)

        case 'effect':
            return userPresetStore.get_effect_by_name(name)

        case 'drumkit':
            return builtinPresetStore.get_drumkit_by_name(name) or \
                userPresetStore.get_drumkit_by_name(name)


def resolve_envelope(data: str | dict, store=None) -> Optional[Envelope]:
    if isinstance(data, str):
        return resolve_reference(data)

    env = envelope_from_dict(data)
    if store:
        store.register(env, None)
    return get_registry().get_or_register(env)


def resolve_tuned_sample(data: dict, store=None) -> Optional[TunedSample]:
    if not data:
        return None

    sample_ref = data.get('sample')
    tuning = data.get('tuning', 0.0)

    sample = None
    if isinstance(sample_ref, str):
        sample =  resolve_reference(sample_ref)

    elif isinstance(sample_ref, dict):
        sample = sample_from_dict(sample_ref)
        if store:
            store.register(sample, None)

    tuned_sample = TunedSample(sample=sample, tuning=tuning) if sample else None
    return get_registry().get_or_register(tuned_sample)


def resolve_drumkit(data: str | dict, store=None) -> list[Drum]:
    if isinstance(data, str):
        drumkit = resolve_reference(data)
        return drumkit if drumkit else []

    return drumkit_from_dict(data, store)
#endregion

#region Deserialization
def vadpcm_loop_from_dict(data: dict) -> VadpcmLoop:
    return VadpcmLoop(
        loop_start=data['loop_start'],
        loop_end=data['loop_end'],
        loop_count=parse_loop_count(data['loop_count']),
        num_samples=data['num_samples'],
        predictors=data.get('predictors')
    )


def vadpcm_book_from_dict(data: dict) -> VadpcmBook:
    return VadpcmBook(**data)


def sample_from_dict(data: dict) -> Sample:
    loop = vadpcm_loop_from_dict(data['vadpcm_loop'])
    book = vadpcm_book_from_dict(data['vadpcm_book'])
    sample = Sample(
        name=data['name'],
        unk_0=data['unk_0'],
        codec=parse_codec(data['codec']),
        medium=parse_medium(data['medium']),
        is_cached=data['is_cached'],
        is_relocated=data['is_relocated'],
        size=data['size'],
        vrom_address=data['vrom_address'],
        vadpcm_loop=loop,
        vadpcm_book=book
    )
    return get_registry().get_or_register(sample)


def tuned_sample_from_dict(data: dict) -> TunedSample:
    sample_data = data.get('sample')
    sample = sample_from_dict(sample_data) if sample_data else None
    tuned_sample = TunedSample(sample=sample, tuning=data['tuning'])
    return get_registry().get_or_register(tuned_sample)


def envelope_from_dict(data: dict) -> Envelope:
    envelope = Envelope(
        name=data['name'],
        array=parse_envelope_array(data['array'])
    )
    return get_registry().get_or_register(envelope)


def instrument_from_dict(data: dict, store=None) -> Instrument:
    instr = Instrument(
        name=data["name"],
        is_relocated=data["is_relocated"],
        key_region_low=data["key_region_low"],
        key_region_high=data["key_region_high"],
        decay_index=data["decay_index"],
        envelope=resolve_envelope(data["envelope"], store),
        low_sample=resolve_tuned_sample(data.get("low_sample"), store),
        prim_sample=resolve_tuned_sample(data.get("prim_sample"), store),
        high_sample=resolve_tuned_sample(data.get("high_sample"), store)
    )

    if store:
        store.register(instr, None)
    return get_registry().get_or_register(instr)


def drum_from_dict(data: dict, store=None) -> Drum:
    drum_sample = resolve_tuned_sample(data.get('drum_sample'), store)

    # Drums must have a sample, otherwise the game crashes
    if not drum_sample:
        raise ValueError()

    drum = Drum(
        name=data["name"],
        decay_index=data["decay_index"],
        pan=data["pan"],
        is_relocated=data["is_relocated"],
        drum_sample=drum_sample,
        envelope=resolve_envelope(data["envelope"], store)
    )
    if store:
        store.register(drum, None)
    return get_registry().get_or_register(drum)


def effect_from_dict(data: dict, store=None) -> Effect:
    effect = Effect(
        name=data["name"],
        effect_sample=resolve_tuned_sample(data.get('effect_sample'), store)
    )
    if store:
        store.register(effect, None)
    return get_registry().get_or_register(effect)


def drumkit_from_dict(data: dict, store=None) -> list[Drum]:
    name = data.get('name')
    game = data.get('game')
    drum_entries = data.get('drums', [])

    drums: list[Drum] = []
    for i, entry in enumerate(drum_entries):
        try:
            if isinstance(entry, str):
                drum = resolve_reference(entry)
                if not drum:
                    raise ValueError(f'Failed to resolve drum reference: {entry}')
            elif isinstance(entry, dict):
                entry = unwrap_typed_dict(entry, 'drum')
                drum = drum_from_dict(entry, store)
            else:
                raise ValueError(f'Invalid drum entry at index {i}: {entry}')

            drums.append(drum)

        except Exception as e:
            print(f'[Drumkit:{name}] Failed to load drum at index {i}: {e}')
            continue

    return Drumkit(name=name, game=game, drums=drums)


def bank_from_dict(data: dict, store) -> Audiobank:
    tbl_data = data['table_entry']

    bank = Audiobank(
        name=data.get('name'),
        game=data['game'],
        tableEntry=TableEntry(
            storageMedium=parse_medium(tbl_data['storage_medium']),
            cacheLoadType=parse_cache_type(tbl_data['cache_load_type']),
            sampleBankId_1=parse_bank_id(tbl_data['sample_bank_id_1']),
            sampleBankId_2=parse_bank_id(tbl_data['sample_bank_id_2']),
            numInstruments=tbl_data['num_instruments'],
            numDrums=tbl_data['num_drums'],
            numEffects=tbl_data['num_effects']
        )
    )

    # instruments is now a list
    instrument_data = data.get("instruments", [])
    for i in range(bank.tableEntry.numInstruments):
        if i < len(instrument_data):
            entry = instrument_data[i]
        else:
            entry = None

        if entry is None or entry == "~":
            bank.instruments[i] = None
        elif isinstance(entry, str):
            instrument = resolve_reference(entry)
            if not instrument:
                raise ValueError(f"Failed to resolve instrument reference: {entry}")
            bank.instruments[i] = instrument
        elif isinstance(entry, dict):
            entry = unwrap_typed_dict(entry, 'instrument')
            bank.instruments[i] = instrument_from_dict(entry, store)
        else:
            raise TypeError(f"Invalid instrument value at index {i}: {entry}")

    # drums is also expected to be a list
    drum_data = data.get("drums", [])
    if isinstance(drum_data, str):
        resolved = resolve_reference(drum_data)
        if isinstance(resolved, Drumkit):
            bank.drums = resolved.drums
        else:
            raise TypeError()
    elif isinstance(drum_data, list):
        bank.drums = [
            drum_from_dict(d['drum']) if isinstance(d, dict) and 'drum' in d else None
            for d in drum_data
        ]
    else:
        raise TypeError()

    # effects is expected to be a list
    effect_data = data.get("effects", [])
    for i in range(bank.tableEntry.numEffects):
        if i < len(effect_data):
            entry = effect_data[i]
        else:
            entry = None

        if entry is None or entry == "~":
            bank.effects[i] = None
        elif isinstance(entry, str):
            effect = resolve_reference(entry)
            if not effect:
                raise ValueError(f"Failed to resolve effect reference: {entry}")
            bank.effects[i] = effect
        elif isinstance(entry, dict):
            entry = unwrap_typed_dict(entry, 'effect')
            bank.effects[i] = effect_from_dict(entry, store)
        else:
            raise TypeError(f"Invalid effect value at index {i}: {entry}")

    return bank
#endregion