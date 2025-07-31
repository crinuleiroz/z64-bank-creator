# Tools/audiobin_to_presets.py

import sys
from struct import unpack
from pathlib import Path
import zipfile
import yaml


ROOT_DIR = Path(__file__).resolve().parent.parent

# Add ROOT_DIR to sys.path if needed
sys.path.insert(0, str(ROOT_DIR))


# App/Common
from App.Common.Enums import (
    AudioStorageMedium, AudioCacheLoadType, SampleBankId,
    AudioSampleCodec, AudioSampleLoopCount, EnvelopeOpcode,
    IntEnum
)


#region Audiobin
class Audiobin:
    def __init__(self, game: str, _audiobank: bytearray, _audiobank_table: bytearray, _audiosamples: bytearray, _audiosample_table: bytearray):
        self.game = game
        self.audiobank = _audiobank
        self.audiobank_table = _audiobank_table
        self.audiosamples = _audiosamples
        self.audiosample_table = _audiosample_table

        # List of all audiobanks in the table
        self.audiobank_list: list[Audiobank] = []

        num_banks = int.from_bytes(self.audiobank_table[0:2], 'big')
        for i in range(num_banks):
            table_entry = 0x10 + (0x10 * i) # Offset by 16 as the first line is the number of banks
            current_entry = self.audiobank_table[table_entry:table_entry + 0x10]
            instrument_bank: Audiobank = Audiobank(game, current_entry, self.audiobank)
            self.audiobank_list.append(instrument_bank)

    def skip_bank(self, index: int) -> bool:
        if index in {0x00, 0x01, 0x02}:
            return True

        if self.game == 'OOT' and index == 0x25:
            return True
        if self.game == 'MM' and index == 0x28:
            return True

        return False

    def collect_unique_objects(self):
        unique_instruments: set[Instrument] = set()
        unique_drums: set[Drum] = set()
        unique_effects: set[Effect] = set()
        unique_samples: set[Sample] = set()
        unique_envelopes: set[Envelope] = set()

        for i, bank in enumerate(self.audiobank_list):
            if skip_bank(self.game, i):
                continue

            for inst in bank.instruments:
                if inst is None:
                    continue
                unique_instruments.add(inst)

                for tuned_sample in [inst.low_sample, inst.prim_sample, inst.high_sample]:
                    if tuned_sample and tuned_sample.sample:
                        unique_samples.add(tuned_sample.sample)

                if inst.envelope:
                    unique_envelopes.add(inst.envelope)

            for drum in bank.drums:
                if drum is None:
                    continue
                unique_drums.add(drum)

                if drum.drum_sample and drum.drum_sample.sample:
                    unique_samples.add(drum.drum_sample.sample)

                if drum.envelope:
                    unique_envelopes.add(drum.envelope)

            for effect in bank.effects:
                if effect is None:
                    continue
                unique_effects.add(effect)

                if effect.effect_sample and effect.effect_sample.sample:
                    unique_samples.add(effect.effect_sample.sample)

        return {
            'instruments': unique_instruments,
            'drums': unique_drums,
            'effects': unique_effects,
            'samples': unique_samples,
            'envelopes': unique_envelopes
        }
#endregion


#region Table Entry
class TableEntry:
    def __init__(self, table_entry: bytearray):
        (
            self.address,
            self.size,
            raw_storage_medium,
            raw_cache_load_type,
            _, # The sample bank does not matter
            _, # The sample bank does not matter
            self.num_instruments,
            self.num_drums,
            self.num_effects
        ) = unpack('>2I6BH', table_entry)

        self.storage_medium = AudioStorageMedium(raw_storage_medium)
        self.cache_load_type = AudioCacheLoadType(raw_cache_load_type)
        self.sample_bank_id_1 = SampleBankId.BANK_0
        self.sample_bank_id_2 = SampleBankId.NO_BANK
#endregion


#region Audiobank
class Audiobank:
    def __init__(self, game: str, table_entry: bytearray, audiobank_file: bytearray):
        self.game = game
        self.table_entry = TableEntry(table_entry)
        offset = self.table_entry.address
        size = self.table_entry.size

        self.bank_data = audiobank_file[offset:offset + size]

        self.drums: list[Drum] = []
        self.effects: list[Effect] = []
        self.instruments: list[Instrument] = []

        # Walk through the bank
        drum_offset = int.from_bytes(self.bank_data[0:4], 'big')
        for i in range(0, self.table_entry.num_drums):
            addr = drum_offset + (4 * i)
            addr = int.from_bytes(self.bank_data[addr:addr + 4], 'big')
            drum = Drum(self.bank_data, addr) if addr != 0 else None
            self.drums.append(drum)

        effect_offset = int.from_bytes(self.bank_data[4:8], 'big')
        for i in range(0, self.table_entry.num_effects):
            addr = effect_offset + (8 * i)
            effect = Effect(self.bank_data, addr) if addr != 0 else None
            self.effects.append(effect)

        for i in range(0, self.table_entry.num_instruments):
            addr = 8 + (4 * i)
            addr = int.from_bytes(self.bank_data[addr:addr + 4], 'big')
            instrument = Instrument(self.bank_data, addr) if addr != 0 else None
            self.instruments.append(instrument)

    def __eq__(self, other):
        if not isinstance(other, Audiobank):
            return False
        return (
            self.game == other.game and
            self.table_entry == other.table_entry and
            self.drums == other.drums and
            self.effects == other.effects and
            self.instruments == other.instruments and
            self.bank_data == other.bank_data
        )

    def __hash__(self):
        return hash((
            self.game,
            self.table_entry,
            tuple(self.drums),
            tuple(self.effects),
            tuple(self.instruments),
            self.bank_data
        ))
#endregion


#region Structures
class Drum:
    def __init__(self, bank_data: bytearray, struct_offset: int):
        (
            self.decay_index,
            self.pan,
            raw_is_relocated,
            # Padding byte
            sample_pointer,
            sample_tuning,
            envelope_pointer
        ) = unpack('>3BxIfI', bank_data[struct_offset:struct_offset + 0x10])

        self.is_relocated = bool(raw_is_relocated)

        assert not self.is_relocated
        assert sample_pointer != 0

        self.drum_sample = TunedSample(bank_data, sample_pointer, sample_tuning)
        self.envelope = Envelope(bank_data, envelope_pointer)

    def __hash__(self):
        return hash((self.decay_index, self.pan, self.drum_sample, self.envelope))

    def __eq__(self, other):
        return (
            isinstance(other, Drum)
            and self.decay_index == other.decay_index
            and self.pan == other.pan
            and self.drum_sample == other.drum_sample
            and self.envelope == other.envelope
        )


class Effect:
    def __init__(self, bank_data, struct_offset: int):
        (
            sample_pointer,
            sample_tuning
        ) = unpack('>If', bank_data[struct_offset: struct_offset + 0x08])

        self.effect_sample = TunedSample(bank_data, sample_pointer, sample_tuning) if sample_pointer != 0 else None

    def __hash__(self):
        return hash(self.effect_sample)

    def __eq__(self, other):
        return isinstance(other, Effect) and self.effect_sample == other.effect_sample


class Instrument:
    def __init__(self, bank_data: bytearray, struct_offset: int):
        (
            raw_is_relocated,
            self.key_region_low,
            self.key_region_high,
            self.decay_index,
            envelope_pointer,
            low_sample_pointer,
            low_sample_tuning,
            prim_sample_pointer,
            prim_sample_tuning,
            high_sample_pointer,
            high_sample_tuning
        ) = unpack('>4B2IfIfIf', bank_data[struct_offset: struct_offset + 0x20])

        self.is_relocated = bool(raw_is_relocated)

        assert not self.is_relocated
        assert not (low_sample_pointer == 0 and low_sample_tuning == 0.0) or self.key_region_low == 0
        assert not (high_sample_pointer == 0 and high_sample_tuning == 0.0) or self.key_region_high == 127

        self.envelope = Envelope(bank_data, envelope_pointer)
        self.low_sample = TunedSample(bank_data, low_sample_pointer, low_sample_tuning) if low_sample_pointer != 0 else None
        self.prim_sample = TunedSample(bank_data, prim_sample_pointer, prim_sample_tuning) if prim_sample_pointer != 0 else None
        self.high_sample = TunedSample(bank_data, high_sample_pointer, high_sample_tuning) if high_sample_pointer != 0 else None

    def __hash__(self):
        return hash((
            self.key_region_low,
            self.key_region_high,
            self.decay_index,
            self.envelope,
            self.low_sample,
            self.prim_sample,
            self.high_sample
        ))

    def __eq__(self, other):
        return (
            isinstance(other, Instrument)
            and self.key_region_low == other.key_region_low
            and self.key_region_high == other.key_region_high
            and self.decay_index == other.decay_index
            and self.envelope == other.envelope
            and self.low_sample == other.low_sample
            and self.prim_sample == other.prim_sample
            and self.high_sample == other.high_sample
        )


class TunedSample:
    def __init__(self, bank_data: bytearray, sample_pointer, sample_tuning):
        self.sample = Sample(bank_data, sample_pointer) if sample_pointer != 0 else None
        self.tuning = sample_tuning if self.sample else 0.0

    def __hash__(self):
        return hash((self.sample, self.tuning))

    def __eq__(self, other):
        return isinstance(other, TunedSample) and self.sample == other.sample and self.tuning == other.tuning


class Sample:
    def __init__(self, bank_data: bytearray, struct_offset: int):
        (
            bitfield,
            self.vrom_address,
            self.vadpcmloop_pointer,
            self.vadpcmbook_pointer

        ) = unpack('>4I', bank_data[struct_offset:struct_offset + 0x10])

        self.unk_0        = (bitfield >> 31) & 0b1
        self.codec        = AudioSampleCodec((bitfield >> 28) & 0b111)
        self.medium       = AudioStorageMedium((bitfield >> 26) & 0b11)
        self.is_cached    = bool((bitfield >> 25) & 1)
        self.is_relocated = bool((bitfield >> 24) & 1)
        self.size         = (bitfield >> 0) & 0b111111111111111111111111

        assert self.vadpcmloop_pointer != 0
        assert self.vadpcmbook_pointer != 0
        assert self.codec in (AudioSampleCodec.ADPCM, AudioSampleCodec.SMALL_ADPCM)
        assert self.medium is AudioStorageMedium.RAM
        assert not self.is_relocated

        self.vadpcm_loop = VadpcmLoop(bank_data, self.vadpcmloop_pointer)
        self.vadpcm_book = VadpcmBook(bank_data, self.vadpcmbook_pointer)

    def __hash__(self):
        return hash((
            self.unk_0,
            self.codec,
            self.medium,
            self.is_cached,
            self.is_relocated,
            self.size,
            self.vrom_address,
            self.vadpcm_loop.loop_start,
            self.vadpcm_loop.loop_end,
            self.vadpcm_loop.loop_count,
            self.vadpcm_loop.num_samples,
            tuple(self.vadpcm_loop.predictors or []),
            self.vadpcm_book.order,
            self.vadpcm_book.num_predictors,
            tuple(self.vadpcm_book.predictors)
        ))

    def __eq__(self, other):
        return isinstance(other, Sample) and hash(self) == hash(other)

    def equals_ignore_vrom(self, other: 'Sample') -> bool:
        if not isinstance(other, Sample):
            return False

        return (
            self.unk_0 == other.unk_0 and
            self.codec == other.codec and
            self.medium == other.medium and
            self.is_cached == other.is_cached and
            self.is_relocated == other.is_relocated and
            self.size == other.size and
            self.vadpcm_loop.loop_start == other.vadpcm_loop.loop_start and
            self.vadpcm_loop.loop_end == other.vadpcm_loop.loop_end and
            self.vadpcm_loop.loop_count == other.vadpcm_loop.loop_count and
            self.vadpcm_loop.num_samples == other.vadpcm_loop.num_samples and
            (self.vadpcm_loop.predictors or []) == (other.vadpcm_loop.predictors or []) and
            self.vadpcm_book.order == other.vadpcm_book.order and
            self.vadpcm_book.num_predictors == other.vadpcm_book.num_predictors and
            self.vadpcm_book.predictors == other.vadpcm_book.predictors
        )

    def hash_ignore_vrom(self):
        return hash((
            self.unk_0, self.codec, self.medium, self.is_cached,
            self.is_relocated, self.size,
            self.vadpcm_loop.loop_start,
            self.vadpcm_loop.loop_end,
            self.vadpcm_loop.loop_count,
            self.vadpcm_loop.num_samples,
            tuple(self.vadpcm_loop.predictors or []),
            self.vadpcm_book.order,
            self.vadpcm_book.num_predictors,
            tuple(self.vadpcm_book.predictors)
        ))


class VadpcmLoop:
    def __init__(self, bank_data: bytearray, struct_offset: int):
        (
            self.loop_start,
            self.loop_end,
            raw_loop_count,
            self.num_samples
        ) = unpack('>2IiI', bank_data[struct_offset:struct_offset + 0x10])

        self.loop_count = AudioSampleLoopCount(raw_loop_count)

        if self.loop_start != 0:
            p_offset = struct_offset + 0x10
            self.predictors = list(unpack('>16h', bank_data[p_offset:p_offset + 0x20]))
        else:
            self.predictors = None


class VadpcmBook:
    def __init__(self, bank_data: bytearray, struct_offset: int):
        (
            self.order,
            self.num_predictors
        ) = unpack('>2i', bank_data[struct_offset: struct_offset + 0x08])

        num_p = 8 * self.order * self.num_predictors
        num_s16 = num_p // 2

        start = struct_offset + 0x08
        end = start + num_p

        self.predictors = list(unpack(f'>{num_s16}h', bank_data[start:end]))


class Envelope:
    def __init__(self, bank_data: bytearray, array_offset: int):
        # Data should just be 4 points in banks
        raw_array = list(unpack('>8h', bank_data[array_offset:array_offset + 0x10]))

        self.array = []
        for i in range(0, len(raw_array), 2):
            t = raw_array[i]
            v = raw_array[i + 1]

            try:
                t = EnvelopeOpcode(t)
            except ValueError:
                pass

            self.array.append(t)
            self.array.append(v)

    def __hash__(self):
        return hash(tuple(self.array))

    def __eq__(self, other):
        return isinstance(other, Envelope) and self.array == other.array
#endregion


#region Serializers
def serialize_envelope(envelope: Envelope, index: int = 0):
    return {
        'name': f'Envelope_{index}',
        'array': [
            val.name if isinstance(val, IntEnum) else val
            for val in envelope.array
        ]
    }


def serialize_sample(sample: Sample, index: int = 0, region: str = ''):
    if sample is None:
        return None

    dict = {
        'name': f'Sample_{index}_{region}' if region else f'Sample_{index}',
        'unk_0': sample.unk_0,
        'codec': sample.codec.name,
        'medium': sample.medium.name,
        'is_cached': sample.is_cached,
        'is_relocated': sample.is_relocated,
        'size': sample.size,
        'vrom_address': sample.vrom_address,
        'vadpcm_loop': {
            'loop_start': sample.vadpcm_loop.loop_start,
            'loop_end': sample.vadpcm_loop.loop_end,
            'loop_count': sample.vadpcm_loop.loop_count.name,
            'num_samples': sample.vadpcm_loop.num_samples
        },
        'vadpcm_book': {
            'order': sample.vadpcm_book.order,
            'num_predictors': sample.vadpcm_book.num_predictors,
            'predictors': sample.vadpcm_book.predictors
        }
    }

    if sample.vadpcm_loop.predictors:
        dict['vadpcm_loop']['predictors'] = sample.vadpcm_loop.predictors

    return dict


def serialize_instrument(instrument: Instrument, index: int = 0):
    dict = {
        'instrument': {
            'name': f'Instrument_{index}',
            'is_relocated': instrument.is_relocated,
            'key_region_low': instrument.key_region_low,
            'key_region_high': instrument.key_region_high,
            'decay_index': instrument.decay_index,

            'envelope': serialize_envelope(instrument.envelope, index=index)
        }
    }

    if instrument.low_sample:
        dict['instrument']['low_sample'] = {
            'sample': serialize_sample(instrument.low_sample.sample, index=index, region='Low'),
            'tuning': instrument.low_sample.tuning
        }

    if instrument.prim_sample:
        dict['instrument']['prim_sample'] = {
            'sample': serialize_sample(instrument.prim_sample.sample, index=index, region='Prim'),
            'tuning': instrument.prim_sample.tuning
        }

    if instrument.high_sample:
        dict['instrument']['high_sample'] = {
            'sample': serialize_sample(instrument.high_sample.sample, index=index, region='High'),
            'tuning': instrument.high_sample.tuning
        }

    return dict


def serialize_drum(drum: Drum, index: int = 0):
    return {
        'drum': {
            'name': f'Drum_{index}',
            'decay_index': drum.decay_index,
            'pan': drum.pan,
            'drum_sample': {
                'sample': serialize_sample(drum.drum_sample.sample, index=index),
                'tuning': drum.drum_sample.tuning
            },
            'envelope': serialize_envelope(drum.envelope, index=index)
        }
    }


def serialize_effect(effect: Effect, index: int = 0):
    if effect and effect.effect_sample is None:
        return None

    return {
        'effect': {
            'name': f'Effect_{index}',
            'effect_sample': {
                'sample': serialize_sample(effect.effect_sample.sample, index=index),
                'tuning': effect.effect_sample.tuning
            }
        }
    }


def serialize_bank(game: str, bank: Audiobank, index: int = 0):
    table_entry_dict = {
        'storage_medium': bank.table_entry.storage_medium.name,
        'cache_load_type': bank.table_entry.cache_load_type.name,
        'sample_bank_id_1': bank.table_entry.sample_bank_id_1.name,
        'sample_bank_id_2': bank.table_entry.sample_bank_id_2.name,
        'num_instruments': bank.table_entry.num_instruments,
        'num_drums': bank.table_entry.num_drums,
        'num_effects': bank.table_entry.num_effects
    }

    instrument_data = []
    for i, inst in enumerate(bank.instruments or []):
        if inst is None:
            instrument_data.append(None)
        else:
            instrument_data.append(serialize_instrument(inst, index=i))

    drum_data = []
    for i, drum in enumerate(bank.drums or []):
        if drum is None:
            drum_data.append(None)
        else:
            drum_data.append(serialize_drum(drum, index=i))

    effect_data = []
    for i, effect in enumerate(bank.effects or []):
        if effect is None:
            effect_data.append(None)
        else:
            effect_data.append(serialize_effect(effect, index=i))

    bank_dict = {
        'bank': {
            'name': f'BANK_{index}',
            'game': game,
            'table_entry': table_entry_dict,
        }
    }

    if instrument_data:
        bank_dict['bank']['instruments'] = instrument_data
    if drum_data:
        bank_dict['bank']['drums'] = drum_data
    if effect_data:
        bank_dict['bank']['effects'] = effect_data

    return bank_dict


def serialize_unique_envelope(envelope: Envelope, index: int = 0):
    return { 'envelope': serialize_envelope(envelope, index) }


def serialize_unique_sample(sample: Sample, index: int = 0):
    return { 'sample': serialize_sample(sample, index) }


def serialize_unique_instrument(instrument: Instrument, index: int = 0):
    return serialize_instrument(instrument, index)


def serialize_unique_drum(drum: Drum, index: int = 0):
    return serialize_drum(drum, index)


def serialize_unique_effect(effect: Effect, index: int = 0):
    return serialize_effect(effect, index)
#endregion


#region YAML Helpers
def skip_bank(game: str, index: int) -> bool:
    if index in {0x00, 0x01, 0x02}:
        return True

    if game == 'OOT' and index == 0x25:
        return True
    if game == 'MM' and index == 0x28:
        return True

    return False
#endregion


#region YAML Conversion
def dump_unique_objects_to_yaml(unique_objects: dict, base_path: Path):

    def dump_category(objects, subfolder: str, serializer, prefix: str):
        out_dir = base_path / subfolder
        out_dir.mkdir(parents=True, exist_ok=True)

        for i, obj in enumerate(objects):
            if obj is None:
                continue

            data = serializer(obj, index=i)
            if data is not None:
                file_path = out_dir / f'{prefix}_{i}.yaml'
                with open(file_path, 'w') as f:
                    yaml.safe_dump(data, f)

    dump_category(unique_objects.get('instruments', []), 'Instruments', serialize_unique_instrument, 'Instrument')
    dump_category(unique_objects.get('drums', []), 'Drums', serialize_unique_drum, 'Drum')
    dump_category(unique_objects.get('effects', []), 'Effects', serialize_unique_effect, 'Effect')
    dump_category(unique_objects.get('samples', []), 'Samples', serialize_unique_sample, 'Sample')
    dump_category(unique_objects.get('envelopes', []), 'Envelopes', serialize_unique_envelope, 'Envelope')


def dump_banks_to_yaml(game: str, audiobin: Audiobin, base_path: Path):
    out_dir = base_path / 'Banks'
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, bank in enumerate(audiobin.audiobank_list):
        if audiobin.skip_bank(i):
            continue

        bank_data = serialize_bank(game, bank, index=i)
        file_path = out_dir / f'Bank_{i}.yaml'

        with open(file_path, 'w') as f:
            yaml.safe_dump(bank_data, f)
#endregion


#region Audiobin
def load_audiobin_archive(game: str, archive_path: Path) -> Audiobin:
    with zipfile.ZipFile(archive_path, 'r') as z_ref:
        audiobank = bytearray(z_ref.read('Audiobank'))
        audiobank_index = bytearray(z_ref.read('Audiobank_index'))
        audiotable = bytearray(z_ref.read('Audiotable'))
        audiotable_index = bytearray(z_ref.read('Audiotable_index'))

    return Audiobin(
        game,
        audiobank,
        audiobank_index,
        audiotable,
        audiotable_index
    )
#endregion

if __name__ == '__main__':
    script_dir = Path(__file__).resolve().parent
    audiobin_dir = script_dir / 'Audio Binary'
    output_root = script_dir / 'Raw Presets'

    for game_code, filename in [('OOT', 'OOT.audiobin'), ('MM', 'MM.audiobin')]:
        audiobin_path = audiobin_dir / filename
        if not audiobin_path.exists():
            continue

        audiobin = load_audiobin_archive(game_code, audiobin_path)
        unique_objects = audiobin.collect_unique_objects()

        dump_banks_to_yaml(game_code, audiobin, output_root / game_code)
        dump_unique_objects_to_yaml(unique_objects, output_root / game_code)