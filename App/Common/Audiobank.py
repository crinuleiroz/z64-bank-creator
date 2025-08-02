# App/Common/Audiobank.py

from pathlib import Path
from dataclasses import dataclass, field
import struct

# App/Common
from App.Common.Structs import (
    Instrument, Drum, Effect, TunedSample,
    Sample, VadpcmLoop, VadpcmBook, Envelope,
    isInstrument, isDrum, isEffect, isTunedSample,
    isSample, isVadpcmLoop, isVadpcmBook, isEnvelope
)
from App.Common.Enums import AudioStorageMedium, AudioCacheLoadType, SampleBankId
from App.Common.MemAllocator import MemAllocator
from App.Common.Addresses import AUDIO_SAMPLE_ADDRESSES
from App.Common.Helpers import align_to_16


@dataclass
class Pointer:
    offset: int = 0


#region Table Entry
@dataclass
class TableEntry:
    storageMedium: AudioStorageMedium = AudioStorageMedium.CART
    cacheLoadType: AudioCacheLoadType = AudioCacheLoadType.TEMPORARY
    sampleBankId_1: SampleBankId = SampleBankId.BANK_1
    sampleBankId_2: SampleBankId = SampleBankId.NO_BANK
    numInstruments: int = 0
    numDrums: int = 0
    numEffects: int = 0

    def compile(self) -> bytearray:
        return struct.pack(
            '>6BH',
            self.storageMedium.value,
            self.cacheLoadType.value,
            self.sampleBankId_1.value,
            self.sampleBankId_2.value,
            self.numInstruments,
            self.numDrums,
            self.numEffects
        )
#endregion


class Audiobank:
    def __init__(self, name: str, game: str, tableEntry: TableEntry):
        self.name = name
        self.game = game.upper()
        self.tableEntry = tableEntry

        # Init Bank Lists
        self.instruments = [None] * tableEntry.numInstruments
        self.drums = [None] * tableEntry.numDrums
        self.effects = [None] * tableEntry.numEffects

        # Registries
        self.instrumentRegistry = {}
        self.drumRegistry = {}
        self.effectRegistry = {}
        self.sampleRegistry = {}
        self.envelopeRegistry = {}
        self.loopbookRegistry = {}
        self.codebookRegistry = {}

    #region Data Registries
    def _add_to_registry(self, item, hash, registry):
        if hash not in registry:
            registry[hash] = item

    def _register_sample_data(self, sample: Sample):
        if sample is None:
            return

        self._add_to_registry(sample, sample.get_hash(), self.sampleRegistry)
        self._add_to_registry(sample.vadpcm_loop, sample.vadpcm_loop.get_hash(), self.loopbookRegistry)
        self._add_to_registry(sample.vadpcm_book, sample.vadpcm_book.get_hash(), self.codebookRegistry)

    def _register_envelope_data(self, envelope: Envelope):
        if envelope is None:
            return

        self._add_to_registry(envelope, envelope.get_hash(), self.envelopeRegistry)

    def _process_instrument(self, instrument: Instrument):
        if instrument is None:
            return

        self._add_to_registry(instrument, instrument.get_hash(), self.instrumentRegistry)
        self._register_envelope_data(instrument.envelope)
        for attr in ['low_sample', 'prim_sample', 'high_sample']:
            tuned_sample: TunedSample = getattr(instrument, attr)
            if tuned_sample:
                self._register_sample_data(tuned_sample.sample)

    def _process_drum(self, drum: Drum):
        if drum is None:
            return

        self._add_to_registry(drum, drum.get_hash(), self.drumRegistry)
        self._register_envelope_data(drum.envelope)
        self._register_sample_data(drum.drum_sample.sample)

    def _process_effect(self, effect: Effect):
        if effect is None:
            return

        self._add_to_registry(effect, effect.get_hash(), self.effectRegistry)
        if effect.effect_sample:
            self._register_sample_data(effect.effect_sample.sample)

    def reassign_registry_refs(self):
        # Update instrument references
        for instrument in self.instrumentRegistry.values():
            instrument.envelope = self.envelopeRegistry[instrument.envelope.get_hash()]

            for attr in ['low_sample', 'prim_sample', 'high_sample']:
                tuned_sample: TunedSample = getattr(instrument, attr)
                if tuned_sample and tuned_sample.sample:
                    sample = self.sampleRegistry[tuned_sample.sample.get_hash()]
                    tuned_sample.sample = sample

        # Update drum references
        for drum in self.drumRegistry.values():
            drum.envelope = self.envelopeRegistry[drum.envelope.get_hash()]
            if drum.drum_sample and drum.drum_sample.sample:
                drum.drum_sample.sample = self.sampleRegistry[drum.drum_sample.sample.get_hash()]

        # Update sample references
        for sample in self.sampleRegistry.values():
            sample.vadpcm_loop = self.loopbookRegistry[sample.vadpcm_loop.get_hash()]
            sample.vadpcm_book = self.codebookRegistry[sample.vadpcm_book.get_hash()]

        # Update effect references
        for effect in self.effects:
            if effect and effect.effect_sample and effect.effect_sample.sample:
                sample = self.sampleRegistry[effect.effect_sample.sample.get_hash()]
                effect.effect_sample.sample = sample
    #endregion

    #region Offset Assignment
    def assign_offsets(self, allocator: MemAllocator):
        # DO NOT CHANGE THE ORDER OF ITEMS HERE!
        self.instrumentList = Pointer()
        self.instrumentList.offset = 0x00000008

        # Drum list
        self.drumList = Pointer()
        if len(self.drums) > 0:
            self.drumList.offset = align_to_16(self.instrumentList.offset + (len(self.instruments) * 4))
        else:
            self.drumList.offset = 0

        # Effect list
        self.effectList = Pointer()
        if len(self.effects) > 0:
            self.effectList.offset = align_to_16(self.drumList.offset + (len(self.drums) * 4))
        else:
            self.effectList.offset = 0

        # Calculate data offset
        allocator.offset = align_to_16(
            max(
                self.instrumentList.offset + (len(self.instruments) * 4),
                self.drumList.offset + (len(self.drums) * 4) if self.drumList.offset > 0 else 0,
                self.effectList.offset + (len(self.effects) * 8) if self.effectList.offset > 0 else 0
            )
        )

        # The order of items here can be changed, it will change the final
        # structure of the bank, but the data will be where it needs to be.
        #
        # Original order:
        #     Instruments -> Drums -> Samples -> Loops -> Books -> Envelopes
        for instrument in self.instrumentRegistry.values():
            allocator.reserve_mem(instrument, 0x20)

        for drum in self.drumRegistry.values():
            allocator.reserve_mem(drum, 0x10)

        for sample in self.sampleRegistry.values():
            allocator.reserve_mem(sample, 0x10)

        for loop in self.loopbookRegistry.values():
            predictors = loop.predictors or []
            loop_size = 0x10 + (len(predictors) * 2)
            allocator.reserve_mem(loop, loop_size)

        for book in self.codebookRegistry.values():
            book_size = 8 + (len(book.predictors) * 2)
            allocator.reserve_mem(book, book_size, align=0x0F)

        for env in self.envelopeRegistry.values():
            allocator.reserve_mem(env, len(env.array) * 2, align=0x0F)
    #endregion

    #region Binary Writing
    def compile(self, outFolder):
        try:
            if self.game.upper() not in ['OOT', 'MM']:
                self.game = 'OOT'

            # Reference deduplication
            # ———————————————————————————————————————————————————————————————————————————
            # If duplicate data exists in the bank, then the data should be replaced with
            # already known existing data. This gives the smallest binary output possible.
            for instrument in self.instruments:
                self._process_instrument(instrument)

            for drum in self.drums:
                self._process_drum(drum)

            for effect in self.effects:
                self._process_effect(effect)

            self.instruments = [
                self.instrumentRegistry[instrument.get_hash()] if instrument else None
                for instrument in self.instruments
            ]
            self.drums = [
                self.drumRegistry[drum.get_hash()] if drum else None
                for drum in self.drums
            ]
            self.effects = [
                self.effectRegistry[effect.get_hash()] if effect else None
                for effect in self.effects
            ]
            self.reassign_registry_refs()

            # Pointer Allocation
            allocator = MemAllocator()
            self.assign_offsets(allocator)

            # Create the buffer
            buffer = bytearray(align_to_16(allocator.offset))

            # Write drum list and effect list pointers
            struct.pack_into('>2I', buffer, 0x00,
                            self.drumList.offset,
                            self.effectList.offset)

            # Write Pointer Lists
            for i, instrument in enumerate(self.instruments):
                struct.pack_into('>I', buffer, self.instrumentList.offset + i * 4,
                                instrument.offset if instrument else 0)

            for i, drum in enumerate(self.drums):
                struct.pack_into('>I', buffer, self.drumList.offset + i * 4,
                                drum.offset if drum else 0)

            for i, effect in enumerate(self.effects):
                sample_offset = effect.effect_sample.offset if (effect and effect.effect_sample and effect.effect_sample.sample) else 0
                tuning = effect.effect_sample.tuning if (effect and effect.effect_sample) else 0.0
                struct.pack_into('>If', buffer, self.effectList.offset + i * 8, sample_offset, tuning)

            # Write Structures
            for offset, obj in sorted(allocator.entries, key=lambda x: x[0]):
                match obj:
                    case _ if isinstance(obj, Pointer):
                        continue

                    case _ if isEnvelope(obj):
                        for i, val in enumerate(obj.array):
                            struct.pack_into('>h', buffer, obj.offset + (i * 2), val)

                    case _ if isVadpcmLoop(obj):
                        preds = obj.predictors or []
                        struct.pack_into(
                            '>4i', buffer, obj.offset,
                            obj.loop_start,
                            obj.loop_end,
                            obj.loop_count,
                            obj.num_samples
                        )
                        for i, p in enumerate(preds):
                            struct.pack_into('>h', buffer, obj.offset + 0x10 + (i * 2), p)

                    case _ if isVadpcmBook(obj):
                        struct.pack_into('>2i', buffer, obj.offset, obj.order, obj.num_predictors)
                        for i, p in enumerate(obj.predictors):
                            struct.pack_into('>h', buffer, obj.offset + 0x08 + (i * 2), p)

                    case _ if isSample(obj):
                        bitfield  = 0
                        bitfield |= (obj.unk_0 & 0b1) << 31
                        bitfield |= (obj.codec & 0b111) << 28
                        bitfield |= (obj.medium & 0b11) << 26
                        bitfield |= (int(obj.is_cached) & 1) << 25
                        bitfield |= (int(obj.is_relocated) & 1) << 24
                        bitfield |= (obj.size & 0b111111111111111111111111)

                        struct.pack_into(
                            '>4I', buffer, obj.offset,
                            bitfield,
                            resolve_sample_address(obj.vrom_address, self.game),
                            obj.vadpcm_loop.offset,
                            obj.vadpcm_book.offset
                        )

                    case _ if isDrum(obj):
                        struct.pack_into(
                            '>3BxIfI', buffer, obj.offset,
                            obj.decay_index,
                            obj.pan,
                            int(obj.is_relocated),
                            obj.drum_sample.sample.offset,
                            obj.drum_sample.tuning,
                            obj.envelope.offset
                        )

                    case _ if isInstrument(obj):
                        struct.pack_into(
                            '>4BI', buffer, obj.offset,
                            int(obj.is_relocated),
                            obj.key_region_low,
                            obj.key_region_high,
                            obj.decay_index,
                            obj.envelope.offset
                        )

                        for j, attr in enumerate(['low_sample', 'prim_sample', 'high_sample']):
                            tuned_sample = getattr(obj, attr)
                            sample_offset = tuned_sample.sample.offset if tuned_sample and tuned_sample.sample else 0
                            tuning = tuned_sample.tuning if tuned_sample else 0.0
                            struct.pack_into('If', buffer, obj.offset + 8 + (j * 8), sample_offset, tuning)

                    case _:
                        raise TypeError()

            # Write out the binary file
            # Output folder
            outFolder = Path(outFolder)
            bankFolder = outFolder / self.game / self.name
            bankFolder.mkdir(parents=True, exist_ok=True)

            # File paths
            bankmetaPath = bankFolder / f'{self.name}.bankmeta'
            bankPath = bankFolder / f'{self.name}.zbank'

            tableEntryBytes = self.tableEntry.compile()
            bankBytes = buffer

            with open(bankmetaPath, 'wb') as bankmeta:
                bankmeta.write(tableEntryBytes)

            with open(bankPath, 'wb') as zbank:
                zbank.write(bankBytes)

            return True, None
        except Exception as ex:
            return False, ex
    #endregion


#region Helpers
def resolve_sample_address(addr, game):
    result = addr
    if isinstance(addr, str):
        sample_dict = AUDIO_SAMPLE_ADDRESSES.get(addr.upper())
        if sample_dict is not None:
            result = sample_dict.get(game.upper(), 0)
        else:
            result = 0
    return result
#endregion
