from datetime import datetime
from threading import Event, Thread
from typing import Any, Callable, Dict

import backend.time_util as tu
from backend.led_controller import LedController
from backend.logger import logger


class Schedule:

    _scheduled_time: str
    _callback: Callable
    _datetime: datetime
    _thread: Thread
    _cancel_event: Event
    _faulty: bool

    def __init__(self, time: str, callback: Callable):
        self._scheduled_time = time
        self._datetime = tu.string_to_datetime(time)
        self._callback = callback
        self._thread = Thread(target=self._thread_handler)
        self._thread.name = "schedule"
        self._cancel_event = Event()
        self._faulty = False

    def start(self):
        self._thread.start()
        LedController.instance().load_preset('scheduled')

    def cancel(self):
        self._cancel_event.set()
        self.join()

    def join(self):
        self._thread.join()
        LedController.instance().load_preset('loaded')

    def _thread_handler(self):
        while not self._cancel_event.is_set():
            if tu.datetime_reached(self._datetime):
                try:
                    logger.debug("Calling schedule callback")
                    self._callback()
                except Exception:
                    logger.exception(
                        "Exception while calling schedule callback"
                    )
                    self._faulty = True
                break
            tu.sleep(tu.TIME_RESOLUTION)

    @property
    def timestamp(self):
        return tu.datetime_to_timestamp(self._datetime)

    @property
    def seconds_left(self) -> float:
        return self.timestamp - tu.timestamp_now()

    def get_state(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'seconds_left': self.seconds_left,
            'faulty': self._faulty,
            'scheduled_time': self._scheduled_time
        }
