import ctypes
import enum
import os

try:
    standalone = False
    from backend.instance import Instance
except ModuleNotFoundError:
    standalone = True   
    class Instance:
        @staticmethod
        def on_pi():
            return True


class AudioErrorType(enum.Enum):
    AUDIO_ERROR_NO_ERROR = 0,  # No error occurred. 

    # warnings
    AUDIO_WARNING_ALREADY_PLAYING = 1,  # The audio is already playing. 
    AUDIO_WARNING_ALREADY_PAUSED = 2,  # The audio is already paused. 
    AUDIO_WARNING_JUMPED_BEYOND_END = 3,  # The given time is beyond the end of the audio. 

    # errors
    # reading riff file
    AUDIO_ERROR_FILE_TOO_SMALL = 4,  # The file is too small. 
    AUDIO_ERROR_INVALID_RIFF_MAGIC_NUMBER = 5,  # The RIFF magic number is invalid. 
    AUDIO_ERROR_INVALID_WAVE_MAGIC_NUMBER = 6,  # The WAVE magic number is invalid. 
    AUDIO_ERROR_INVALID_FILE_SIZE = 7,  # The file size is invalid. 
    AUDIO_ERROR_IMVALID_FMT_MAGIC_NUMBER = 8,  # The fmt magic number is invalid. 
    AUDIO_ERROR_INVALID_FMT_SIZE = 9,  # The fmt size is invalid. 
    AUDIO_ERROR_NO_PCM_FORMAT = 10,  # The audio is not in PCM format. 
    AUDIO_ERROR_INVALID_BYTE_RATE = 11,  # The byte rate is invalid. 
    AUDIO_ERROR_INVALID_BLOCK_ALIGN = 12,  # The block align is invalid. 
    AUDIO_ERROR_DATA_CHUNK_NOT_FOUND = 13,  # The data chunk was not found. 
    AUDIO_ERROR_INVALID_DATA_MAGIC_NUMBER = 14,  # The data magic number is invalid. 
    AUDIO_ERROR_INVALID_DATA_SIZE = 15,  # The data size is invalid. 
    AUDIO_ERROR_INVALID_FACT_MAGIC_NUMBER = 16,  # The fact magic number is invalid. 
    AUDIO_ERROR_INVALID_FACT_SIZE = 17,  # The fact size is invalid. 
    AUDIO_ERROR_INVALID_NON_PCM_EXTENSION_SIZE = 18,  # The non-PCM extension size is invalid. 
    AUDIO_ERROR_INVALID_EXTENSIBLE_EXTENSION_SIZE = 19,  # The extensible extension size is invalid. 
    AUDIO_ERROR_INVALID_EXTENSIBLE_AUDIO_FORMAT = 20,  # The extensible audio format is invalid. 
    AUDIO_ERROR_INVALID_EXTENSIBLE_GUID = 21,  # The extensible GUID is invalid. 
    AUDIO_ERROR_INVALID_SAMPLES_PER_CHANNEL = 22,  # The samples per channel is invalid. 
    AUDIO_UNSUPPORTED_FORMAT = 23,  # The format is not supported. 
    # alsa
    AUDIO_ERROR_ALSA_ERROR = 24,  # An ALSA error occurred. 
    AUDIO_ERROR_MIXER_ELEMENT_NOT_FOUND = 25,  # The mixer element was not found. 
    # other
    AUDIO_ERROR_MEMORY_ALLOCATION_FAILED = 26,  # Memory allocation failed. 
    AUDIO_UNSUPPORTED_BITS_PER_SAMPLE = 27  # The bits per sample are not supported.


class AudioErrorLevel(enum.Enum):
    AUDIO_ERROR_LEVEL_INFO = 0,
    AUDIO_ERROR_LEVEL_WARNING = 1,
    AUDIO_ERROR_LEVEL_ERROR = 2


class AudioError(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("level", ctypes.c_int),
        ("alsaErrorNumber", ctypes.c_int)
    ]


class AudioConfiguration(ctypes.Structure):
    _fields_ = [
        ("rawData", ctypes.c_char_p),
        ("rawDataSize", ctypes.c_size_t),
        ("soundDeviceName", ctypes.c_char_p),
        ("soundDeviceNameSize", ctypes.c_size_t),
        ("timeResolution", ctypes.c_uint32)
    ]


class pthread_barrier_t(ctypes.Structure):
    _fields_ = []


AudioObject = ctypes.c_void_p

if standalone:
    audio_lib = ctypes.CDLL("./audiolib_arm.so")
else:
    if Instance.on_pi():
        audio_lib = ctypes.CDLL(os.path.join("backend", "audio", "audiolib_arm.so"))
    else:
        audio_lib = ctypes.CDLL(os.path.join("backend", "audio", "audiolib.so"))

audio_lib.audioInit.argtypes = [ctypes.POINTER(AudioConfiguration)]
audio_lib.audioInit.restype = ctypes.POINTER(AudioObject)

audio_lib.audioDestroy.argtypes = [AudioObject]
audio_lib.audioDestroy.restype = None

audio_lib.audioPlay.argtypes = [AudioObject, ctypes.POINTER(pthread_barrier_t)]
audio_lib.audioPlay.restype = ctypes.c_bool

audio_lib.audioPause.argtypes = [AudioObject, ctypes.POINTER(pthread_barrier_t)]
audio_lib.audioPause.restype = ctypes.c_bool

audio_lib.audioStop.argtypes = [AudioObject, ctypes.POINTER(pthread_barrier_t)]
audio_lib.audioStop.restype = None

audio_lib.audioJump.argtypes = [AudioObject, ctypes.POINTER(pthread_barrier_t), ctypes.c_uint32]
audio_lib.audioJump.restype = ctypes.c_bool

audio_lib.audioGetIsPlaying = [AudioObject]
audio_lib.aduiGetIsPlaying = ctypes.c_bool

audio_lib.audioGetIsPaused.argtypes = [AudioObject]
audio_lib.audioGetIsPaused.restype = ctypes.c_bool

audio_lib.audioGetCurrentTime.argtypes = [AudioObject]
audio_lib.audioGetCurrentTime.restype = ctypes.c_uint32

audio_lib.audioGetTotalDuration.argtypes = [AudioObject]
audio_lib.audioGetTotalDuration.restype = ctypes.c_uint32

audio_lib.audioSetVolume.argtypes = [AudioObject, ctypes.c_uint8]
audio_lib.audioSetVolume.restype = ctypes.c_bool

audio_lib.audioGetVolume.argtypes = [AudioObject]
audio_lib.audioGetVolume.restype = ctypes.c_uint8

audio_lib.audioGetError.argtypes = [AudioObject]
audio_lib.audioGetError.restype = ctypes.POINTER(AudioError)

audio_lib.audioGetErrorString.argtypes = [ctypes.POINTER(AudioError)]
audio_lib.audioGetErrorString.restype = ctypes.c_char_p

AudioInterface = audio_lib
