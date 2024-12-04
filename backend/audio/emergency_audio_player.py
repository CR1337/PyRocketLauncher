import subprocess
import os
import sys
import signal
import tempfile
import pydub
from threading import Thread


class AudioPlayer:

    APLAY_EXECUTABLE: str = "aplay"
    FILE_FORMAT: str = "wav"
    TEMP_FILE_PREFIX: str = "audio-player-"

    STATE_READY: str = 'ready'
    STATE_PLAYING: str = 'playing'
    STATE_PAUSED: str = 'paused'

    _wav_file: tempfile.NamedTemporaryFile
    _state: str
    _process: subprocess.Popen
    _thread: Thread

    def __init__(self, filename: str):
        self._wav_file = tempfile.NamedTemporaryFile(
            prefix=self.TEMP_FILE_PREFIX, suffix=f".{self.FILE_FORMAT}"
        )
        audio_segment = pydub.AudioSegment.from_file(filename)
        audio_segment.export(self._wav_file.name, format=self.FILE_FORMAT)
        self._state = self.STATE_READY
        self._thread = None

    def __del__(self):
        self.stop()
        if self._thread and self._thread.is_alive():
            self._thread.join()
        self._thread = None

    def play(self):
        if self._state != self.STATE_READY:
            return
        self._process = subprocess.Popen(
            [self.APLAY_EXECUTABLE, self._wav_file.name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self._thread = Thread(target=self._wait_for_process_termination)
        self._thread.start()
        self._state = self.STATE_PLAYING

    def pause(self):
        if self._state != self.STATE_PLAYING:
            return
        os.kill(self._process.pid, signal.SIGSTOP)
        self._state = self.STATE_PAUSED

    def continue_(self):
        if self._state != self.STATE_PAUSED:
            return
        os.kill(self._process.pid, signal.SIGCONT)
        self._state = self.STATE_PLAYING

    def stop(self):
        if self._state not in (self.STATE_PLAYING, self.STATE_PAUSED):
            return
        self._process.terminate()
        if self._thread and self._thread.is_alive():
            self._thread.join()

    def _wait_for_process_termination(self):
        self._process.wait()
        self._state = self.STATE_READY


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"USAGE: {sys.argv[0]} FILENAME")
        exit(1)

    filename = sys.argv[1]

    print("Building WAV file...")
    player = AudioPlayer(filename)
    print("Done. Press [Enter] to play.")
    input()
    player.play()

    while True:
        choice = input("Enter 'p' to pause, 'c' to continue, 's' to stop: ")
        if choice == 'p':
            player.pause()
        elif choice == 'c':
            player.continue_()
        elif choice == 's':
            player.stop()
            break
