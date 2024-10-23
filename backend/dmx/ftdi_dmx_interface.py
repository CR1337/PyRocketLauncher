import ctypes
from threading import Event, Lock, Thread
from typing import List, Tuple

from pylibftdi import Device


class Timespec(ctypes.Structure):
    _fields_ = [
        ("seconds", ctypes.c_long),
        ("nanoseconds", ctypes.c_long)
    ]


class FtdiDmxInterface:

    LIBC = ctypes.cdll.LoadLibrary("libc.so.6")
    MS_PER_S: int = 1_000_000  # ms/s
    NS_PER_MS: int = 1_000  # ns/ms
    US_PER_MS: int = 1_000  # µs/ms

    BAUDRATE: int = 250_000  # kbits/s
    BUS_TIMINGS: Tuple[int, int, int] = (96, 8, 2)  # µs, µs, ms
    TIME_RESOLUTION: int = 5  # ms

    BITS_8: int = 8
    STOP_BITS_2: int = 2
    PARITY_NONE: int = 0
    BREAK_OFF: int = 0
    BREAK_ON: int = 1

    CHANNEL_RANGE: Tuple[int, int] = (1, 512)
    VALUE_RANGE: Tuple[int, int] = (0, 255)

    @classmethod
    def _wait_us(cls, microseconds: int):
        sleep_time = Timespec(
            seconds=microseconds // cls.MS_PER_S,
            nanoseconds=(microseconds % cls.MS_PER_S) * cls.NS_PER_MS
        )
        cls.LIBC.nanosleep(ctypes.byref(sleep_time), ctypes.byref(Timespec()))

    @classmethod
    def _wait_ms(cls, milliseconds: int):
        cls._wait_us(milliseconds * cls.US_PER_MS)

    _ftdi_device: Device
    _dmx_channels: List[int]
    _highest_updated_channel: int

    _blackout_on_del: bool
    _stopped: bool

    _thread: Thread
    _lock: Lock
    _render_event: Event
    _ready_event: Event
    _stop_event: Event

    def __init__(
        self,
        blackout_on_init: bool = True,
        blackout_on_del: bool = True
    ):
        self._ftdi_device = Device()
        self._ftdi_device.ftdi_fn.ftdi_set_baudrate(self.BAUDRATE)
        self._ftdi_device.ftdi_fn.ftdi_set_line_property(
            self.BITS_8, self.STOP_BITS_2, self.PARITY_NONE
        )

        self._blackout_on_del = blackout_on_del
        self._stopped = False

        self._thread = Thread(
            target=self._thread_target,
            name="ftdi_dmx_thread"
        )
        self._lock = Lock()
        self._render_event = Event()
        self._ready_event = Event()
        self._stop_event = Event()
        self._thread.start()

        if blackout_on_init:
            self.blackout()

        self._ready_event.set()

    def __del__(self):
        if not self._stopped:
            self.stop()

    def stop(self):
        if self._blackout_on_del:
            self.blackout()
        self._stop_event.set()
        self._thread.join()
        self._ftdi_device.close()
        self._stopped = True

    def set_channel(self, channel: int, value: int):
        if not (self.CHANNEL_RANGE[0] <= channel <= self.CHANNEL_RANGE[-1]):
            raise ValueError(f"Channel {channel} out of range.")
        if not (self.VALUE_RANGE[0] <= value <= self.VALUE_RANGE[-1]):
            raise ValueError(f"Value {value} out of range.")

        with self._lock:
            self._dmx_channels[channel] = value
            self._highest_updated_channel = max(
                self._highest_updated_channel, channel
            )

    def get_channel(self, channel: int) -> int:
        if not (self.CHANNEL_RANGE[0] <= channel <= self.CHANNEL_RANGE[-1]):
            raise ValueError(f"Channel {channel} out of range.")

        with self._lock:
            return self._dmx_channels[channel]

    def __setitem__(self, key: int, value: int):
        self.set_channel(key, value)

    def __getitem__(self, key: int) -> int:
        return self.get_channel(key)

    def blackout(self):
        with self._lock:
            self._dmx_channels = [0] * (self.CHANNEL_RANGE[-1] + 1)
            self._highest_updated_channel = self.CHANNEL_RANGE[-1]
        self.render()

    def render(self):
        with self._lock:
            self._render_event.set()

    def _write_to_bus(self):
        data = bytes(self._dmx_channels[:self._highest_updated_channel + 1])

        self._ftdi_device.ftdi_fn.ftdi_set_line_property2(
            self.BITS_8, self.STOP_BITS_2, self.PARITY_NONE, self.BREAK_ON
        )
        self._wait_us(self.BUS_TIMINGS[0])
        self._ftdi_device.ftdi_fn.ftdi_set_line_property2(
            self.BITS_8, self.STOP_BITS_2, self.PARITY_NONE, self.BREAK_OFF
        )
        self._wait_us(self.BUS_TIMINGS[1])
        self._ftdi_device.write(data)
        self._wait_ms(self.BUS_TIMINGS[2])

        self._highest_updated_channel = 0

    def _thread_target(self):
        while not self._ready_event.is_set():
            self._wait_ms(self.TIME_RESOLUTION)

        while True:
            if self._render_event.is_set():
                with self._lock:
                    self._write_to_bus()
                    self._render_event.clear()

            elif self._stop_event.is_set():
                break

            else:
                with self._lock:
                    tmp_highest_updated_channel = self._highest_updated_channel
                    self._highest_updated_channel = 0
                    self._write_to_bus()
                    self._highest_updated_channel = tmp_highest_updated_channel
                self._wait_ms(self.TIME_RESOLUTION)
