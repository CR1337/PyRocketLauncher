from threading import Event, Thread
from typing import Any, Callable, Dict, List

import backend.time_util as tu
from backend.address import Address
from backend.command import Command
from backend.config import Config
from backend.hardware import Hardware
from backend.logger import logger


class Program:

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

    @classmethod
    def from_json(cls, name: str, json_data: List) -> 'Program':
        program = cls(name)
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

    def __init__(self, name: str):
        self._name = name
        self._command_list = []
        self._thread = Thread(target=self._thread_handler)
        self._thread.name = f"program_{self._name}"
        self._pause_event = Event()
        self._paused = False
        self._continue_event = Event()
        self._stop_event = Event()
        self._start_timestamp = None
        self._last_current_timestamp_before_pause = None
        self._callback = None
        self._seconds_paused = 0

    def add_command(self, command: Command):
        self._command_list.append(command)

    def run(self, callback: Callable):
        self._callback = callback
        self._thread.start()

    def pause(self):
        self._pause_event.set()

    def continue_(self):
        self._continue_event.set()

    def stop(self):
        self._stop_event.set()
        self._thread.join()

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
        return self._thread.is_alive()

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
