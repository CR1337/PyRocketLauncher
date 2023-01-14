from threading import Event, Thread

import backend.time_util as tu
from backend.instance import Instance
from backend.logger import logger

if Instance.on_pi():
    import RPi.GPIO as GPIO
else:
    from typing import Any

    logger.info("Not on Raspberry Pi. Using Dummy GPIO.")

    class GPIO:
        BCM: Any = 'bcm'
        OUT: Any = 'out'
        LOW: Any = 'low'
        HIGH: Any = 'high'

        @classmethod
        def setmode(cls, mode: Any):
            print(f"Dummy GPIO: set mode to {mode}")

        @classmethod
        def setup(cls, pin: int, mode: Any):
            print(f"Dummy GPIO: set pin {pin} to mode {mode}")

        @classmethod
        def output(cls, pin: int, value: Any):
            print(f"Dummy GPIO: set pin {pin} to value {value}")

        @classmethod
        def cleanup(cls):
            print("Dummy GPIO: cleanup")


class LedController:

    LED_PIN: int = 21

    _thread: Thread = None
    _stop_blink_event: Event
    _instance: 'LedController' = None

    def __init__(self):
        self.__class__._instance = self
        self._stop_blink_event = Event()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.LED_PIN, GPIO.OUT)

    def __del__(self):
        GPIO.cleanup()
        self.__class__._instance = None

    def turn_on(self):
        logger.info("Turning LED on")
        self._stop_blink()
        GPIO.output(self.LED_PIN, GPIO.HIGH)

    def turn_off(self):
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

    def _wait_times(self, period: float, duty: float) -> float:
        switch_time_inside_period = period * duty
        while True:
            timestamp_inside_period = tu.timestamp_now() % period
            if timestamp_inside_period <= switch_time_inside_period:
                yield period * duty - timestamp_inside_period
            else:
                yield period - timestamp_inside_period

    def _thread_handler(self, period: float, duty: float):
        GPIO.output(self.LED_PIN, GPIO.LOW)
        currently_on = False
        wait_times = self._wait_times(period, duty)
        while not self._stop_blink_event.is_set():
            tu.sleep(next(wait_times))
            GPIO.output(self.LED_PIN, GPIO.LOW if currently_on else GPIO.HIGH)
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
