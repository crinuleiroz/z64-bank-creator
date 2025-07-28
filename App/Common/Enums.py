# App/Common/Enums.py

from enum import Enum, IntEnum


class AudioStorageMedium(IntEnum):
    RAM = 0
    UNK = 1
    CART = 2
    DISK_DRIVE = 3
    RAM_UNLOADED = 5


class AudioSampleCodec(IntEnum):
    ADPCM = 0
    S8 = 1
    S16_INMEM = 2
    SMALL_ADPCM = 3
    REVERB = 4
    S16 = 5
    UNK6 = 6
    UNK7 = 7


class AudioCacheLoadType(IntEnum):
    PERMANENT = 0
    PERSISTENT = 1
    TEMPORARY = 2
    EITHER = 3
    EITHER_NOSYNC = 4


class SampleBankId(IntEnum):
    BANK_0 = 0
    BANK_1 = 1
    BANK_2 = 2
    BANK_3 = 3
    BANK_4 = 4
    BANK_5 = 5
    BANK_6 = 6
    NO_BANK = 255


class AudioSampleLoopCount(IntEnum):
    NO_LOOP = 0
    INDEFINITE = -1


class EnvelopeOpcode(IntEnum):
    DISABLE = 0
    HANG = -1
    GOTO = -2
    RESTART = -3
