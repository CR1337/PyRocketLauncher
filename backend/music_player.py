import os
from tempfile import NamedTemporaryFile
from threading import Event, Thread

import vlc

import backend.time_util as tu
from backend.logger import logger
from backend.rl_exception import RlException


# TODO: change permissions for port 80
# https://gist.github.com/justinmklam/f13bb53be9bb15ec182b4877c9e9958d


class MusicPlayer:

    class MusicLoaded(RlException):
        pass

    class NoMusicLoaded(RlException):
        pass

    _temp_file_path: str
    _is_music_loaded: bool = False
    _player: vlc.MediaPlayer

    _pause_event: Event = Event()
    _continue_event: Event = Event()
    _stop_event: Event = Event()
    _thread: Thread

    def __init__(self):
        self._thread = Thread(target=self._thread_target)
        self._thread.name = 'music_player'

    def __del__(self):
        if self._is_music_loaded:
            self.unload_music()

    def _thread_target(self):
        self._player.play()
        while True:
            tu.sleep(tu.TIME_RESOLUTION)

            if self._stop_event.is_set():
                self._player.stop()
                self._stop_event.clear()
                return

            if self._pause_event.is_set():
                self._player.pause()
                self._pause_event.clear()

                while not self._continue_event.is_set():
                    tu.sleep(tu.TIME_RESOLUTION)
                    if self._stop_event.is_set():
                        self._stop_event.clear()
                        return

                self._player.play()
                self._continue_event.clear()

    def load_music(self, mp3_file: bytes):
        if self._is_music_loaded:
            raise self.MusicLoaded("Music is already loaded")
        with NamedTemporaryFile(delete=False, mode='wb') as file:
            self._temp_file_path = file.name
            file.write(mp3_file)

        self._player = vlc.MediaPlayer()
        media = vlc.Media(self._temp_file_path)
        self._player.set_media(media)

        self._is_music_loaded = True

    def unload_music(self):
        if not self._is_music_loaded:
            raise self.NoMusicLoaded("No music loaded!")
        self._player = None
        os.remove(self._temp_file_path)
        self._is_music_loaded = False

    def play(self):
        logger.info("Play music")
        self._thread.start()

    def pause(self):
        logger.info("Pause music")
        self._pause_event.set()

    def continue_(self):
        logger.info("Continue music")
        self._continue_event.set()

    def stop(self):
        logger.info("Stop music")
        self._stop_event.set()
