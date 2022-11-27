from functools import wraps
from threading import Lock
from typing import Dict

from smbus2 import SMBus

from backend.address import Address
from backend.config import Config
from backend.instance import Instance
from backend.logger import logger


class DummySMBus:

    _chip_count = Config.get_value('chip_amount')
    _locked: Dict[int, bool]

    def __init__(self, _):
        self._locked = [True for _ in range(self._chip_count)]

    def write_byte_data(
        self, chip_address: int, register_address: int, value: int
    ):
        if register_address == 0x00:
            self._locked[chip_address - Address.BASE_CHIP_ADDRESS] = \
                value & Hardware.LOCK_VALUE

    def read_byte_data(self, chip_address: int, register_address: int) -> int:
        if register_address == 0x00:
            return (
                Hardware.LOCK_VALUE
                if self._locked[chip_address - Address.BASE_CHIP_ADDRESS]
                else 0x00
            )
        return 0x00


def lock_bus(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        Hardware._lock.acquire(blocking=True)
        logger.info("Bus locked")
        result = func(*args, **kwargs)
        Hardware._lock.release()
        logger.info("Bus unlocked")
        return result
    return wrapper


class Hardware:

    _lock: Lock = Lock()
    BUS_ADDRESS: int = Config.get_constant('bus_address')
    LOCK_VALUE: int = 0x10
    UNLOCK_VALUE: int = 0x00

    try:
        if Instance.on_pi():
            BUS: SMBus = SMBus(BUS_ADDRESS)
        else:
            BUS = DummySMBus(BUS_ADDRESS)
    except (TypeError, OSError):
        raise
    except Exception:
        raise

    @classmethod
    def _write(cls, chip_address: int, register_address: int, value: int):
        logger.info(
            f"Write value {value:02x} to "
            f"{chip_address:02x}::{register_address:02x}"
        )
        cls.BUS.write_byte_data(chip_address, register_address, value)

    @classmethod
    def _read(cls, chip_address: int, register_address: int) -> int:
        logger.info(f"Read from {chip_address:02x}::{register_address:02x}")
        return cls.BUS.read_byte_data(chip_address, register_address)

    @classmethod
    @lock_bus
    def lock(cls):
        logger.info("Lock Hardware")
        for chip_address in Address.all_chip_addresses():
            cls._write(chip_address, Address.LOCK_ADDRESS, cls.LOCK_VALUE)

    @classmethod
    @lock_bus
    def unlock(cls):
        logger.info("Unlock Hardware")
        for chip_address in Address.all_chip_addresses():
            cls._write(chip_address, Address.LOCK_ADDRESS, cls.UNLOCK_VALUE)

    @classmethod
    @lock_bus
    def is_locked(cls) -> bool:
        logger.info("Check Lock Status")
        locked_states = []
        for chip_address in Address.all_chip_addresses():
            register_value = cls._read(chip_address, Address.LOCK_ADDRESS)
            locked_states.append(bool(register_value & cls.LOCK_VALUE))
        if all(locked_states):

            return True
        if not any(locked_states):

            return False
        return None

    @classmethod
    @lock_bus
    def light(cls, address: Address):
        logger.info(f"Light {address}")
        value = cls._read(address.chip_address, address.register_address)
        value &= address.rev_register_mask
        value |= address.register_mask
        cls._write(address.chip_address, address.register_address, value)

    @classmethod
    @lock_bus
    def unlight(cls, address: Address):
        logger.info(f"Unlight {address}")
        value = cls._read(address.chip_address, address.register_address)
        value &= address.rev_register_mask
        cls._write(address.chip_address, address.register_address, value)

    @classmethod
    def get_state(cls):
        return {
            'is_locked': cls.is_locked()
        }
