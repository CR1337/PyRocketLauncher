try:
    from backend.audio.audio import AudioInterface, AudioConfiguration, AudioObject, AudioError, AudioErrorLevel, AudioErrorType
except ImportError:
    from audio import AudioInterface, AudioConfiguration, AudioObject, AudioError, AudioErrorLevel, AudioErrorType
from functools import wraps
import ctypes
import tempfile
import os
# import subprocess
# import sys

from pydub import AudioSegment


class AudioException(Exception):
    error_type: AudioErrorType
    alsa_error_number: int
    message: str

    def __init__(self, audio_error: AudioError):
        self.error_type = audio_error.type
        self.alsa_error_number = audio_error.alsaErrorNumber
        self.message = AudioInterface.audioGetErrorString(
            ctypes.byref(audio_error)
        )

    def __str__(self) -> str:
        return (
            f"type: {self.error_type},\n"
            f"alsa_error_number: {self.alsa_error_number}\n"
            f"message: {self.message}"
        )


class AudioErrorException(AudioException):
    pass


class AudioWarningException(AudioException):
    pass


def handle_error(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        error = AudioInterface.audioGetError(self._audio_object).contents
        if error.level == AudioErrorLevel.AUDIO_ERROR_LEVEL_ERROR.value:
            raise AudioErrorException(error)
        elif error.level == AudioErrorLevel.AUDIO_ERROR_LEVEL_WARNING.value:
            raise AudioWarningException(error)
        return result
    return wrapper


class AudioPlayer:
    SOUND_DEVICE_NAME: str = "default"
    TIME_RESOLUTION: int = 10

    _audio_object: AudioObject = None
    _temp_wav_filename: str = None
    
    def __init__(self, wav_filename: str):
        if wav_filename.endswith('.mp3'):
            wav_filename = self._convert_to_wav(wav_filename)

        with open(wav_filename, 'rb') as file:
            raw_data = file.read()

        raw_data_buffer = ctypes.create_string_buffer(raw_data)
        raw_data_buffer_pointer = ctypes.cast(
            raw_data_buffer, ctypes.c_char_p
        )

        device_name_buffer = ctypes.create_string_buffer(
            bytes(self.SOUND_DEVICE_NAME, encoding='utf-8')
        )
        device_name_buffer_pointer = ctypes.cast(
            device_name_buffer, ctypes.c_char_p
        )

        configuration = AudioConfiguration(
            raw_data_buffer_pointer,
            len(raw_data),
            device_name_buffer_pointer,
            len(self.SOUND_DEVICE_NAME) + 1,
            self.TIME_RESOLUTION
        )
        ConfigurationPointer = ctypes.POINTER(AudioConfiguration)
        configuration_pointer = ConfigurationPointer(configuration)

        self._audio_object = AudioInterface.audioInit(
            configuration_pointer
        )
        if self._audio_object is None:
            raise RuntimeError("Failed to initialize audio")
        
        self._keep_alive = (
            ctypes.cast(self._audio_object, ctypes.py_object),
            ctypes.cast(configuration_pointer, ctypes.py_object),
            ctypes.cast(raw_data_buffer_pointer, ctypes.py_object),
            ctypes.cast(device_name_buffer_pointer, ctypes.py_object)
        )

        error = AudioInterface.audioGetError(self._audio_object).contents
        if error.level == AudioErrorLevel.AUDIO_ERROR_LEVEL_ERROR.value:
            raise AudioErrorException(error)
        
    def _convert_to_wav(self, filename: str) -> str:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        self._temp_wav_filename = temp_file.name
        temp_file.close()

        audio_segment = AudioSegment.from_mp3(filename)
        audio_segment.export(self._temp_wav_filename, format='wav')

        return self._temp_wav_filename

    def __del__(self):
        if self._audio_object is not None:
            AudioInterface.audioDestroy(self._audio_object)
        if self._temp_wav_filename is not None:
            os.remove(self._temp_wav_filename)

    @handle_error
    def play(self) -> bool:
        return AudioInterface.audioPlay(self._audio_object, None)

    @handle_error
    def pause(self) -> bool:
        return AudioInterface.audioPause(self._audio_object, None)

    @handle_error
    def stop(self):
        AudioInterface.audioStop(self._audio_object, None)

    @handle_error
    def jump(self, timestamp: int) -> bool:
        return AudioInterface.audioJump(self._audio_object, None, timestamp)

    @handle_error
    def is_playing(self) -> bool:
        return AudioInterface.audioGetIsPlaying(self._audio_object)

    @handle_error
    def is_paused(self) -> bool:
        return AudioInterface.audioGetIsPaused(self._audio_object)

    @handle_error
    def current_time(self) -> int:
        return AudioInterface.audioGetCurrentTime(self._audio_object)

    @handle_error
    def total_duration(self) -> int:
        return AudioInterface.audioGetTotalDuration(self._audio_object)

    @handle_error
    def get_volume(self) -> int:
        return AudioInterface.audioGetVolume(self._audio_object)

    @handle_error
    def set_volume(self, value: int) -> bool:
        return AudioInterface.audioSetVolume(self._audio_object, value)


if __name__ == '__main__':
    import sys
    import time
    player = AudioPlayer(sys.argv[1])
    player.play()
    while player.is_playing():
        time.sleep(1)
