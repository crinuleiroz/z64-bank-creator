# App/Common/Structs.py

from dataclasses import dataclass, field
from typing import Optional, Union, List
import uuid

# App/Common
from App.Common.Enums import AudioSampleCodec, AudioStorageMedium, AudioSampleLoopCount, EnvelopeOpcode


#region Structures
@dataclass(eq=False, unsafe_hash=False)
class VadpcmLoop:
    offset: int = field(init=False, default=0)
    loop_start: int
    loop_end: int
    loop_count: Union[int, AudioSampleLoopCount]
    num_samples: int
    predictors: Optional[List[int]] = None

    def get_hash(self) -> str:
        from App.Common.Helpers import stable_hash
        loop_count = self.loop_count.name if hasattr(self.loop_count, 'name') else self.loop_count
        return stable_hash(self.loop_start, self.loop_end, loop_count, self.num_samples, self.predictors or [])


@dataclass(eq=False, unsafe_hash=False)
class VadpcmBook:
    offset: int = field(init=False, default=0)
    order: int
    num_predictors: int
    predictors: List[int]

    def get_hash(self) -> str:
        from App.Common.Helpers import stable_hash
        return stable_hash(self.order, self.num_predictors, self.predictors)


@dataclass(eq=False, unsafe_hash=False)
class Sample:
    offset: int = field(init=False, default=0)
    name: str
    unk_0: int
    codec: AudioSampleCodec
    medium: AudioStorageMedium
    is_cached: bool
    is_relocated: bool
    size: int
    vrom_address: Union[str, int]
    vadpcm_loop: VadpcmLoop
    vadpcm_book: VadpcmBook
    _unique_id: uuid.UUID = field(default_factory=uuid.uuid4, repr=False, compare=False)

    def get_hash(self) -> str:
        from App.Common.Helpers import stable_hash
        return stable_hash(
            self.unk_0,
            self.codec.name,
            self.medium.name,
            self.is_cached,
            self.is_relocated,
            self.size,
            self.vrom_address,
            self.vadpcm_loop.get_hash(),
            self.vadpcm_book.get_hash()
        )

    def __eq__(self, other):
        if isinstance(other, Sample):
            return self is other
        return False

    def __hash__(self):
        return id(self)


@dataclass(eq=False, unsafe_hash=False)
class TunedSample:
    sample: Optional[Sample]
    tuning: float

    def get_hash(self) -> str:
        from App.Common.Helpers import stable_hash
        return stable_hash(self.sample.get_hash() if self.sample else None, self.tuning)


@dataclass(eq=False, unsafe_hash=False)
class Envelope:
    offset: int = field(init=False, default=0)
    name: str
    array: List[Union[int, EnvelopeOpcode]]
    _unique_id: uuid.UUID = field(default_factory=uuid.uuid4, repr=False, compare=False)

    def get_hash(self) -> str:
        from App.Common.Helpers import stable_hash
        arr = [op.name if hasattr(op, 'name') else op for op in self.array]
        return stable_hash(arr)

    def __eq__(self, other):
        if isinstance(other, Envelope):
            return self is other
        return False

    def __hash__(self):
        return id(self)


@dataclass(eq=False, unsafe_hash=False)
class Instrument:
    offset: int = field(init=False, default=0)
    name: str
    is_relocated: bool
    key_region_low: int
    key_region_high: int
    decay_index: int
    envelope: Envelope
    low_sample: Optional[TunedSample] = None
    prim_sample: Optional[TunedSample] = None
    high_sample: Optional[TunedSample] = None
    _unique_id: uuid.UUID = field(default_factory=uuid.uuid4, repr=False, compare=False)

    def get_hash(self) -> str:
        from App.Common.Helpers import stable_hash
        return stable_hash(
            self.is_relocated,
            self.key_region_low,
            self.key_region_high,
            self.decay_index,
            self.envelope.get_hash() if self.envelope else None,
            self.low_sample.get_hash() if self.low_sample else None,
            self.prim_sample.get_hash() if self.prim_sample else None,
            self.high_sample.get_hash() if self.high_sample else None
        )

    def __eq__(self, other):
        if isinstance(other, Instrument):
            return self is other
        return False

    def __hash__(self):
        return id(self)


@dataclass(eq=False, unsafe_hash=False)
class Drum:
    offset: int = field(init=False, default=0)
    name: str
    decay_index: int
    pan: int
    is_relocated: bool
    drum_sample: TunedSample
    envelope: Envelope
    _unique_id: uuid.UUID = field(default_factory=uuid.uuid4, repr=False, compare=False)

    def get_hash(self) -> str:
        from App.Common.Helpers import stable_hash
        return stable_hash(
            self.decay_index,
            self.pan,
            self.is_relocated,
            self.drum_sample.get_hash() if self.drum_sample else None,
            self.envelope.get_hash() if self.envelope else None
        )

    def __eq__(self, other):
        if isinstance(other, Drum):
            return self is other
        return False

    def __hash__(self):
        return id(self)


@dataclass(eq=False, unsafe_hash=False)
class Effect:
    offset: int = field(init=False, default=0)
    name: str
    effect_sample: TunedSample
    _unique_id: uuid.UUID = field(default_factory=uuid.uuid4, repr=False, compare=False)

    def get_hash(self) -> str:
        from App.Common.Helpers import stable_hash
        return stable_hash(self.effect_sample.get_hash() if self.effect_sample else None)

    def __eq__(self, other):
        if isinstance(other, Effect):
            return self is other
        return False

    def __hash__(self):
        return id(self)


@dataclass(eq=False, unsafe_hash=False)
class Drumkit:
    name: str
    game: str
    drums: list[Drum] = field(default_factory=list)
    _unique_id: uuid.UUID = field(default_factory=uuid.uuid4, repr=False, compare=False)

    def get_hash(self) -> str:
        from App.Common.Helpers import stable_hash
        return stable_hash(*(drum.get_hash() if drum else None for drum in self.drums))

    def __eq__(self, other):
        if isinstance(other, Drumkit):
            return self is other
        return False

    def __hash__(self):
        return id(self)
#endregion


#region Type Checking
def isInstrument(obj) -> bool: return isinstance(obj, Instrument)
def isDrumkit(obj) -> bool: return isinstance(obj, Drumkit)
def isDrum(obj) -> bool: return isinstance(obj, Drum)
def isEffect(obj) -> bool: return isinstance(obj, Effect)
def isTunedSample(obj) -> bool: return isinstance(obj, TunedSample)
def isSample(obj) -> bool: return isinstance(obj, Sample)
def isVadpcmLoop(obj) -> bool: return isinstance(obj, VadpcmLoop)
def isVadpcmBook(obj) -> bool: return isinstance(obj, VadpcmBook)
def isEnvelope(obj) -> bool: return isinstance(obj, Envelope)
#endregion