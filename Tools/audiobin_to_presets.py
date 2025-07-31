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
    def __init__(self, _audiobank: bytearray, _audiobank_table: bytearray, _audiosamples: bytearray, _audiosample_table: bytearray):
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
            instrument_bank: Audiobank = Audiobank(current_entry, self.audiobank)
            self.audiobank_list.append(instrument_bank)
#endregion


#region Table Entry
class TableEntry:
    def __init__(self, table_entry: bytearray):
        self.address: int
        self.size: int
        self.storage_medium: AudioStorageMedium
        self.cache_load_type: AudioCacheLoadType
        self.sample_bank_id_1: SampleBankId
        self.sample_bank_id_2: SampleBankId
        self.num_instruments: int
        self.num_drums: int
        self.num_effects: int
        (
            self.address,
            self.size,
            self.storage_medium,
            self.cache_load_type,
            self.sample_bank_id_1,
            self.sample_bank_id_2,
            self.num_instruments,
            self.num_drums,
            self.num_effects
        ) = unpack('>2I6BH', table_entry)
#endregion


#region Audiobank
class Audiobank:
    def __init__(self, table_entry: bytearray, audiobank_file: bytearray):
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


class Effect:
    def __init__(self, bank_data, struct_offset: int):
        (
            sample_pointer,
            sample_tuning
        ) = unpack('>If', bank_data[struct_offset: struct_offset + 0x08])

        self.effect_sample = TunedSample(bank_data, sample_pointer, sample_tuning) if sample_pointer != 0 else None


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


class TunedSample:
    def __init__(self, bank_data: bytearray, sample_pointer, sample_tuning):
        self.sample = Sample(bank_data, sample_pointer) if sample_pointer != 0 else None
        self.tuning = sample_tuning if self.sample else 0.0


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


def serialize_sample(sample: Sample, index: int = 0, region: str = 'Prim'):
    if sample is None:
        return None

    dict = {
        'name': f'Sample_{index}_{region}',
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
#endregion


#region YAML Helpers
def enum_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data.name)
yaml.add_representer(IntEnum, enum_representer)
#endregion


#region YAML Conversion
def dump_instruments_to_yaml(audiobin: Audiobin, output_path: str):
    base = Path(output_path)
    base.mkdir(exist_ok=True)

    for i, bank in enumerate(audiobin.audiobank_list):
        bank_path = base / f'BANK_{i}' / 'Instruments'
        bank_path.mkdir(parents=True, exist_ok=True)

        for j, inst in enumerate(bank.instruments):
            if inst is None:
                continue

            instrument_dict = serialize_instrument(inst, index=j)

            yaml_path = bank_path / f'INSTRUMENT_{j}.yaml'
            with open(yaml_path, 'w') as f:
                yaml.safe_dump(instrument_dict, f, sort_keys=False)
#endregion


#region Output
def load_audiobin_archive(archive_path: Path) -> Audiobin:
    with zipfile.ZipFile(archive_path, 'r') as z_ref:
        audiobank = bytearray(z_ref.read('Audiobank'))
        audiobank_index = bytearray(z_ref.read('Audiobank_index'))
        audiotable = bytearray(z_ref.read('Audiotable'))
        audiotable_index = bytearray(z_ref.read('Audiotable_index'))

    return Audiobin(
        audiobank,
        audiobank_index,
        audiotable,
        audiotable_index
    )
#endregion

if __name__ == '__main__':
    script_dir = Path(__file__).resolve().parent
    oot_audiobin = script_dir / 'Audio Binary' / 'OOT.audiobin'
    mm_audiobin = script_dir / 'Audio Binary' / 'MM.audiobin'

    if oot_audiobin.exists():
        oot_audio_data = load_audiobin_archive(oot_audiobin)
        dump_instruments_to_yaml(oot_audio_data, output_path=script_dir / 'Raw Presets' / 'OOT')