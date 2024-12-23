import json
from threading import Event, Thread
from typing import Any, Dict, Union

import backend.time_util as tu
from backend.instance import Instance
from backend.logger import logger

if Instance.on_pi():
    import RPi.GPIO as GPIO
else:
    logger.info("Not on Raspberry Pi. Using Dummy GPIO.")

    class GPIO:
        BCM: Any = 'bcm'
        OUT: Any = 'out'
        LOW: Any = 'low'
        HIGH: Any = 'high'

        DEBUG_VERBOSE: bool = False

        @classmethod
        def setmode(cls, mode: Any):
            if cls.DEBUG_VERBOSE:
                print(f"Dummy GPIO: set mode to {mode}")

        @classmethod
        def setup(cls, pin: int, mode: Any):
            if cls.DEBUG_VERBOSE:
                print(f"Dummy GPIO: set pin {pin} to mode {mode}")

        @classmethod
        def output(cls, pin: int, value: Any):
            if cls.DEBUG_VERBOSE:
                print(f"Dummy GPIO: set pin {pin} to value {value}")

        @classmethod
        def cleanup(cls):
            if cls.DEBUG_VERBOSE:
                print("Dummy GPIO: cleanup")


class LedController:

    LED_PIN: int = 21
    PRESETS_FILENAME: str = "config/led_presets.json"

    _thread: Thread = None
    _stop_blink_event: Event
    _instance: 'LedController' = None
    _presets: Dict[str, Dict[str, Union[str, float]]]

    with open(PRESETS_FILENAME, 'r', encoding='utf-8') as file:
        _presets = json.load(file)

    def __init__(self):
        self.__class__._instance = self
        self._stop_blink_event = Event()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.LED_PIN, GPIO.OUT)

    def __del__(self):
        GPIO.cleanup()
        self.__class__._instance = None

    def on(self):
        logger.info("Turning LED on")
        self._stop_blink()
        GPIO.output(self.LED_PIN, GPIO.HIGH)

    def off(self):
        logger.info("Turning LED off")
        self._stop_blink()
        GPIO.output(self.LED_PIN, GPIO.LOW)

    def blink(self, frequency: float, duty: float):
        logger.info(
            f"Starting LED blink with frequency {frequency} Hz "
            f"and duty {duty * 100} %"
        )
        self._stop_blink()
        self._thread = Thread(
            target=self._thread_handler, args=[1.0 / frequency, duty]
        )
        self._thread.name = "led"
        self._thread.start()

    def load_preset(self, name: str):
        logger.info(f"Loading LED preset '{name}'")
        preset = self._presets[name]
        if preset['pattern'] == 'on':
            self.on()
        elif preset['pattern'] == 'off':
            self.off()
        elif preset['pattern'] == 'blink':
            self.blink(
                frequency=preset['frequency'],
                duty=preset['duty']
            )

    def _led_status(self, period: float, duty: float) -> Any:
        timestamp_inside_period = tu.timestamp_now() % period
        return (
            GPIO.HIGH
            if timestamp_inside_period <= period * duty
            else GPIO.LOW
        )

    def _thread_handler(self, period: float, duty: float):
        GPIO.output(self.LED_PIN, GPIO.LOW)
        currently_on = False
        time_resolution = (period * duty) / 2
        while not self._stop_blink_event.is_set():
            tu.sleep(time_resolution)
            GPIO.output(self.LED_PIN, self._led_status(period, duty))
            currently_on = not currently_on

    def _stop_blink(self):
        if self._thread is None:
            return
        if self._thread.is_alive():
            self._stop_blink_event.set()
            self._thread.join()
            self._thread = None
            self._stop_blink_event.clear()

    @classmethod
    def instance(cls) -> 'LedController':
        return cls._instance
