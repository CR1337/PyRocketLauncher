from threading import Thread

import backend.time_util as tu
from backend.address import Address
from backend.config import Config
from backend.hardware import Hardware
from backend.logger import logger


class Command:

    IGNITION_DURATION: float = Config.get_constant('ignition_duration')

    _address: Address
    _timestamp: float
    _name: str
    _thread: Thread
    _fired: bool
    _fireing: bool
    _faulty: bool
    _faulty_reason: str

    def __init__(self, address: Address, timestamp: float, name: str):
        self._address = address
        self._timestamp = timestamp
        self._name = name
        self._thread = Thread(target=self._thread_handler)
        self._thread.name = f"light_{self._address}"
        self._fired = False
        self._fireing = False
        self._faulty = False
        self._faulty_reason = ""

    def _thread_handler(self):
        self._fireing = True

        try:
            Hardware.light(self._address)
            tu.sleep(self.IGNITION_DURATION)
            Hardware.unlight(self._address)
        except Exception:
            self._faulty = True
            self._faulty_reason = f"Error lighting {self}"
            raise

        self._fired = True
        self._fireing = False

    def light(self):
        logger.debug(f"Light {self}")
        if self._fired or self._fireing:
            self._faulty = True
            if self._fired:
                self._faulty_reason = f"Already fired {self}"
            if self._fireing:
                self._faulty_reason = f"Already fireing {self}"
            raise RuntimeError(f"{self._address} already fired")
        self._thread.start()

    def increase_timestamp(self, offset: float):
        self._timestamp += offset

    @property
    def address(self) -> Address:
        return self._address

    @property
    def timestamp(self) -> float:
        return self._timestamp

    @property
    def seconds_left(self) ->float:
        return self._timestamp - tu.timestamp_now()

    @property
    def name(self) -> str:
        return self._name

    @property
    def fired(self) -> bool:
        return self._fired

    @property
    def fireing(self) -> bool:
        return self._fireing

    def __str__(self):
        return f"{self._name}: {self.address} ({self._timestamp})"

    def get_state(self):
        return {
            'address': {
                'device_id': self._address.device_id,
                'letter': self._address.letter,
                'number': self._address.number
            },
            'timestamp': self._timestamp,
            'seconds_left': self.seconds_left,
            'name': self._name,
            'fired': self._fired,
            'fireing': self._fireing,
            'faulty': self._faulty,
            'faulty_reason': self._faulty_reason
        }

