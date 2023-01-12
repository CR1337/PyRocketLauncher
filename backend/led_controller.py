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

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_PIN, GPIO.OUT)

    @classmethod
    def turn_on(cls):
        logger.info("Turning LED on")
        GPIO.output(cls.LED_PIN, GPIO.HIGH)

    @classmethod
    def turn_off(cls):
        logger.info("Turning LED off")
        GPIO.output(cls.LED_PIN, GPIO.LOW)

    @classmethod
    def cleanup(cls):
        GPIO.cleanup()
