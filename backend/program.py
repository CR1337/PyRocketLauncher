from threading import Event, Thread
from typing import Any, Callable, Dict, List
import zipfile
import tempfile
import shutil
import json
import os
import io

import backend.time_util as tu
from backend.address import Address
from backend.command import Command
from backend.config import Config
from backend.hardware import Hardware
from backend.led_controller import LedController
from backend.logger import logger
from backend.instance import Instance

from backend.audio.audio_player import AudioPlayer
from backend.ilda.ilda_player import IldaPlayer
from backend.dmx.dmx_player import DmxPlayer

from backend.zipfile_handler import ZipfileHandler


class Program:

    LOCAL_PROGRAM_PATH: str = "programs/local_program.zip"

    class InvalidProgram(Exception):
        pass

    _name: str
    _command_list: List[Command]
    _thread: Thread
    _pause_event: Event
    _paused: bool
    _continue_event: Event
    _stop_event: Event
    _start_timestamp: float
    _last_current_timestamp_before_pause: float
    _callback: Callable
    _seconds_paused: float
    _command_idx: int
    _zipfile_handler: ZipfileHandler

    _has_fuses: bool
    _has_music: bool
    _has_ilda: bool
    _has_dmx: bool

    _audio_player: AudioPlayer
    _ilda_player: IldaPlayer
    _dmx_player: DmxPlayer

    local_program: 'Program' = None

    @classmethod
    def raise_on_json(cls, json_data: List):
        if not isinstance(json_data, list):
            raise cls.InvalidProgram("A program has to be a list!")

        for idx, event in enumerate(json_data):
            if not isinstance(event, Dict):
                raise cls.InvalidProgram(f"Element {idx}: has to be a dict!")

            for key in ['name', 'device_id', 'letter', 'number', 'timestamp']:
                if key not in event.keys():
                    raise cls.InvalidProgram(
                        f"Element {idx}: Key '{key}' missing!"
                    )

            if not isinstance(event['name'], str):
                raise cls.InvalidProgram(
                    f"Element {idx}: 'name' has to be a string!"
                )
            if not isinstance(event['device_id'], str):
                raise cls.InvalidProgram(
                    f"Element {idx}: 'device_id' has to be a string!"
                )

            try:
                number = int(event['number'])
                if not 0 <= number <= 15:
                    raise cls.InvalidProgram(
                        f"Element {idx}: 'number' {number} out of range!"
                    )
            except ValueError:
                raise cls.InvalidProgram(
                    f"Element {idx}: 'number' has to be an integer!"
                )
            try:
                timestamp = float(event['timestamp'])
                if timestamp < 0.0:
                    raise cls.InvalidProgram(
                        f"Element {idx}: 'timestamp' {timestamp} is negative!"
                    )
            except ValueError:
                raise cls.InvalidProgram(
                    f"Element {idx}: 'timestamp' has to be a float!"
                )
            
    @classmethod
    def build_local_program(cls):
        def thread_target():
            with open(cls.LOCAL_PROGRAM_PATH, 'rb') as local_program_file:
                local_program_data = local_program_file.read()
            cls.local_program = cls.from_zip("Local-Program", local_program_data)
            print("Local program ready")
        thread = Thread(target=thread_target, name="local_program_builder")
        thread.start()
            
    @classmethod
    def from_zip(cls, name: str, zip_data: bytes) -> 'Program':
        zipfile_handler = ZipfileHandler(zip_data)
        device_id = Config.get_value('device_id')

        if zipfile_handler.has_fuses and device_id in zipfile_handler.fuses_device_ids:
            with open(zipfile_handler.fuses_filename, 'r') as fuses_file:
                fuses = json.load(fuses_file)
            program = cls.from_json(name, fuses, zipfile_handler)
        else:
            program = cls(name, zipfile_handler)

        if zipfile_handler.has_music and device_id == zipfile_handler.music_device_id:
            program.add_music(zipfile_handler.music_filename)

        if zipfile_handler.has_ilda and device_id == zipfile_handler.ilda_device_id:
            program.add_ilda(zipfile_handler.ilda_filename)

        if zipfile_handler.has_dmx and device_id in zipfile_handler.dmx_device_ids:
            program.add_dmx(zipfile_handler.dmx_filename)

        return program

    @classmethod
    def from_json(
        cls, 
        name: str, 
        json_data: List, 
        zipfile_handler: ZipfileHandler = None
    ) -> 'Program':
        program = cls(name, zipfile_handler)
        for event in json_data:
            address = Address(
                event['device_id'],
                event['letter'],
                event['number']
            )
            if address.device_id != Config.get_value('device_id'):
                continue
            command = Command(
                address,
                event['timestamp'],
                event['name']
            )
            program.add_command(command)
        return program

    @classmethod
    def testloop_program(cls) -> 'Program':
        testloop = cls("Testloop")
        for idx, address in enumerate(Address.all_addresses()):
            command = Command(address, idx / 4, str(address))
            testloop.add_command(command)
        return testloop

    def __init__(self, name: str, zipfile_handler: ZipfileHandler = None):
        self._name = name
        self._command_list = []
        self._thread = None
        self._pause_event = Event()
        self._paused = False
        self._continue_event = Event()
        self._stop_event = Event()
        self._start_timestamp = None
        self._last_current_timestamp_before_pause = None
        self._callback = None
        self._seconds_paused = 0
        self._zipfile_handler = zipfile_handler

        self._has_fuses = False
        self._has_music = False
        self._has_ilda = False
        self._has_dmx = False

        self._audio_player = None
        self._ilda_player = None
        self._dmx_player = None

    def _reset_commands(self):
        for command in self._command_list:
            command.reset()

    def add_command(self, command: Command):
        self._has_fuses = True
        self._command_list.append(command)

    def add_music(self, filename: str):
        print("Adding music")
        self._has_music = True
        self._audio_player = AudioPlayer(filename)

    def add_ilda(self, filename: str):
        print("Adding ilda")
        self._has_ilda = True
        self._ilda_player = IldaPlayer(filename)

    def add_dmx(self, filename: str):
        print("Adding dmx")
        self._has_dmx = True
        self._dmx_player = DmxPlayer(filename)

    def run(self, callback: Callable):
        self._command_list.sort(key=lambda c: c.timestamp)
        self._reset_commands()
        self._callback = callback
        self._thread = Thread(target=self._thread_handler)
        self._thread.name = f"program_{self._name}"
        self._thread.start()
        if self._audio_player:
            self._audio_player.play()
        if self._ilda_player:
            self._ilda_player.play()
        if self._dmx_player:
            self._dmx_player.play()
        LedController.instance().load_preset('running')

    def pause(self):
        self._pause_event.set()
        if self._audio_player:
            self._audio_player.pause()
        if self._ilda_player:
            self._ilda_player.pause()
        if self._dmx_player:
            self._dmx_player.pause()

    def continue_(self):
        self._continue_event.set()
        if self._audio_player:
            self._audio_player.play()
        if self._ilda_player:
            self._ilda_player.play()
        if self._dmx_player:
            self._dmx_player.play()

    def stop(self):
        self._stop_event.set()
        if self._audio_player:
            self._audio_player.stop()
        if self._ilda_player:
            self._ilda_player.stop()
        if self._dmx_player:
            self._dmx_player.stop()
        self.join()

    def join(self):
        self._thread.join()
        self._thread = None
        LedController.instance().load_preset('idle')

    @property
    def _current_total_seconds(self) -> float:
        return tu.timestamp_now()

    @property
    def _current_timestamp(self) -> float:
        if self._paused:
            return self._last_current_timestamp_before_pause
        if self._start_timestamp is None:
            return None
        return self._current_total_seconds - self._start_timestamp

    def _pause_handler(self) -> float:
        self._last_current_timestamp_before_pause = self._current_timestamp
        self._paused = True
        pause_started_timestamp = self._current_total_seconds
        while not self._continue_event.is_set():
            if self._stop_event.is_set():
                pause_ended_timestamp = self._current_total_seconds
                return pause_ended_timestamp - pause_started_timestamp
            tu.sleep(tu.TIME_RESOLUTION)
        self._pause_event.clear()
        self._continue_event.clear()
        pause_ended_timestamp = self._current_total_seconds
        self._paused = False
        return pause_ended_timestamp - pause_started_timestamp

    def _thread_handler(self):
        self._seconds_paused = 0
        self._command_idx = 0
        self._start_timestamp = self._current_total_seconds

        hardware_was_locked = Hardware.is_locked()
        if hardware_was_locked:
            Hardware.unlock()
        try:
            self._program_mainloop()
        finally:
            if hardware_was_locked:
                tu.sleep(Config.get_constant('ignition_duration') * 2)
                Hardware.lock()

        self._callback()

    def _program_mainloop(self):
        while (not self._stop_event.is_set()) and self._command_list:

            if self._pause_event.is_set():
                self._seconds_paused += self._pause_handler()
                for command in self._command_list:
                    command.increase_timestamp(self._seconds_paused)
                if self._stop_event.is_set():
                    break

            tu.sleep(tu.TIME_RESOLUTION)

            command = self._command_list[self._command_idx]
            if command.timestamp <= self._current_timestamp:
                try:
                    logger.debug(f"Light {command}")
                    command.light()
                except Exception:
                    logger.exception(f"Exception while fireing {command}")
                self._command_idx += 1
                if self._command_idx >= len(self._command_list):
                    break

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def name(self) -> str:
        return self._name

    def get_state(self) -> Dict[str, Any]:
        return {
            'name': self._name,
            'command_list': [
                cmd.get_state()
                for cmd in self._command_list
            ],
            'time_paused': self._seconds_paused,
            'start_timestamp': self._start_timestamp,
            'current_timestamp': self._current_timestamp,
            'is_running': self.is_running
        }

    def __str__(self) -> str:
        string = "Program:\n"
        for command in self._command_list:
            string += (
                f"\n{command.timestamp} - {command.name} - {command.address}"
            )
        return string


if not Instance.is_master():
    Program.build_local_program()
