from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List
from threading import Event, Thread

import backend.time_util as tu

@dataclass
class AbstractPlayerItem(ABC):
    timestamp: float = None


class AbstractPlayer(ABC):

    _items: List[AbstractPlayerItem]

    _origin_timestamp: float
    _pause_started_timestamp: float
    _current_item_index: int

    _paused: bool
    _playing: bool

    _thread: Thread

    _play_event: Event
    _pause_event: Event
    _stop_event: Event
    _destroy_event: Event

    def __init__(self):
        self._origin_timestamp = 0.0
        self._pause_started_timestamp = 0.0
        self._current_item_index = 0  

        self._paused = True
        self._playing = False

        self._play_event = Event()
        self._pause_event = Event()
        self._stop_event = Event()
        self._destroy_event = Event()

        self._thread = Thread(target=self._mainloop, name="ilda_player")

    def __del__(self):
        if self._thread.is_alive():
            self._destroy_event.set()
            self._thread.join()

    def _next_item_index(self, timestamp: float) -> int:
        for i, item in enumerate(self._items):
            if item.timestamp >= timestamp:
                return i
            
    def _mainloop(self):
        while not self._destroy_event.is_set():
            if self._play_event.is_set():
                self._play_event.clear()
                self._playing = True
                self._paused = False
            if self._pause_event.is_set():
                self._pause_event.clear()
                self._playing = False
                self._paused = True
            if self._stop_event.is_set():
                self._stop_event.clear()
                self._playing = False
                self._paused = False

            if self._playing:
                self._tick()

            tu.sleep(tu.TIME_RESOLUTION)

    def _tick(self):
        if self._items[self._current_item_index].timestamp < tu.timestamp_now() - self._origin_timestamp:
            self._play_item()
            self._current_item_index += 1
            if self._current_item_index >= len(self._items):
                self.stop()

    @abstractmethod
    def _play_item(self):
        raise NotImplementedError("@abstractmethod")
    
    def run(self):
        self._thread.start()
            
    def play(self):
        dt = tu.timestamp_now() - self._pause_started_timestamp
        self._origin_timestamp += dt
        self._play_event.set()

    def pause(self):
        self._pause_started_timestamp = tu.timestamp_now()
        self._pause_event.set()

    def stop(self):
        self._origin_timestamp = tu.timestamp_now()
        self._pause_started_timestamp = self._origin_timestamp
        self._current_frame_index = 0
        self._stop_event.set()

    def jump(self, timestamp: float):
        self._origin_timestamp = tu.timestamp_now() - timestamp
        self._current_frame_index = self._search_frame(timestamp)

    def is_playing(self) -> bool:
        return self._playing

    def is_paused(self) -> bool:
        return self._paused

    def current_time(self) -> int:
        return tu.timestamp_now() - self._origin_timestamp

    def total_duration(self) -> int:
        return self._items[-1].timestamp

