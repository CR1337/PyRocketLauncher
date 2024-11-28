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
    _dmx_channels: List[int] = [0] * (CHANNEL_RANGE[-1] + 1)
    _highest_updated_channel: int = CHANNEL_RANGE[-1]

    _stopped: bool

    _thread: Thread
    _lock: Lock
    _render_event: Event
    _ready_event: Event
    _stop_event: Event

    _initialized: bool = False

    @classmethod
    def initialize(cls):
        if cls._initialized:
            return
        
        cls._ftdi_device = Device()
        cls._ftdi_device.ftdi_fn.ftdi_set_baudrate(cls.BAUDRATE)
        cls._ftdi_device.ftdi_fn.ftdi_set_line_property(
            cls.BITS_8, cls.STOP_BITS_2, cls.PARITY_NONE
        )

        cls._dmx_channels = [0] * (cls.CHANNEL_RANGE[-1] + 1)
        cls._highest_updated_channel = cls.CHANNEL_RANGE[-1]

        cls._stopped = False

        cls._thread: Thread = Thread(
            target=cls._thread_target,
            name="ftdi_dmx_thread"
        )
        
        cls._lock = Lock()
        cls._render_event = Event()
        cls._ready_event = Event()
        cls._stop_event = Event()

        cls._thread.start()
        cls.blackout()
        cls._ready_event.set()

        cls._initialized = True

    @classmethod
    def destroy(cls):
        if not cls._initialized:
            return
        if not cls._stopped:
            cls.stop()
        cls._ftdi_device.close()
        cls._initialized = False

    @classmethod
    def stop(cls):
        cls.blackout()
        cls._stop_event.set()
        cls._thread.join()
        cls._stopped = True

    @classmethod
    def set_channel(cls, channel: int, value: int):
        if not (cls.CHANNEL_RANGE[0] <= channel <= cls.CHANNEL_RANGE[-1]):
            raise ValueError(f"Channel {channel} out of range.")
        if not (cls.VALUE_RANGE[0] <= value <= cls.VALUE_RANGE[-1]):
            raise ValueError(f"Value {value} out of range.")

        with cls._lock:
            cls._dmx_channels[channel] = value
            cls._highest_updated_channel = max(
                cls._highest_updated_channel, channel
            )

    @classmethod
    def get_channel(cls, channel: int) -> int:
        if not (cls.CHANNEL_RANGE[0] <= channel <= cls.CHANNEL_RANGE[-1]):
            raise ValueError(f"Channel {channel} out of range.")

        with cls._lock:
            return cls._dmx_channels[channel]

    @classmethod
    def blackout(cls):
        with cls._lock:
            cls._dmx_channels = [0] * (cls.CHANNEL_RANGE[-1] + 1)
            cls._highest_updated_channel = cls.CHANNEL_RANGE[-1]
        cls.render()

    @classmethod
    def render(cls):
        with cls._lock:
            cls._render_event.set()

    @classmethod
    def _write_to_bus(cls):
        data = bytes(cls._dmx_channels[:cls._highest_updated_channel + 1])

        cls._ftdi_device.ftdi_fn.ftdi_set_line_property2(
            cls.BITS_8, cls.STOP_BITS_2, cls.PARITY_NONE, cls.BREAK_ON
        )
        cls._wait_us(cls.BUS_TIMINGS[0])
        cls._ftdi_device.ftdi_fn.ftdi_set_line_property2(
            cls.BITS_8, cls.STOP_BITS_2, cls.PARITY_NONE, cls.BREAK_OFF
        )
        cls._wait_us(cls.BUS_TIMINGS[1])
        cls._ftdi_device.write(data)
        cls._wait_ms(cls.BUS_TIMINGS[2])

        cls._highest_updated_channel = 0

    @classmethod
    def _thread_target(cls):
        while not cls._ready_event.is_set():
            cls._wait_ms(cls.TIME_RESOLUTION)

        while True:
            if cls._render_event.is_set():
                with cls._lock:
                    cls._write_to_bus()
                    cls._render_event.clear()

            elif cls._stop_event.is_set():
                break

            else:
                with cls._lock:
                    tmp_highest_updated_channel = cls._highest_updated_channel
                    cls._highest_updated_channel = 0
                    cls._write_to_bus()
                    cls._highest_updated_channel = tmp_highest_updated_channel
                cls._wait_ms(cls.TIME_RESOLUTION)
