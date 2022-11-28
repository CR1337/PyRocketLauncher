from itertools import product
from string import ascii_lowercase
from typing import Dict, List

from backend.config import Config
from backend.rl_exception import RlException


class Address:

    class AddressTypeError(RlException):
        pass

    class AddressValueError(RlException):
        pass

    LOCK_ADDRESS: int = 0x00
    FUSE_ADDRESSES: List[int] = [0x14, 0x15, 0x16, 0x17]
    NUMBERS_PER_LETTER: int = 16
    FIRST_LETTER: str = 'a'
    BASE_CHIP_ADDRESS: int = 0x60
    DEVICE_LETTERS: Dict[str, List[str]] = [
        letter for letter in ascii_lowercase[:Config.get_value('chip_amount')]
    ]

    _device_id: str
    _letter: str
    _number: int

    @classmethod
    def all_addresses(cls) -> List['Address']:
        device_id = Config.get_value('device_id')
        return [
            cls(device_id, letter, number)
            for letter, number in product(
                cls.DEVICE_LETTERS, range(cls.NUMBERS_PER_LETTER)
            )
        ]

    @classmethod
    def all_chip_addresses(cls) -> List[int]:
        return [
            cls.BASE_CHIP_ADDRESS + i
            for i in range(len(cls.DEVICE_LETTERS))
        ]

    def __init__(self, device_id: str, letter: str, number: int):
        if not isinstance(device_id, str):
            raise self.AddressTypeError("device_id has to be of type str")
        if not isinstance(letter, str):
            raise self.AddressTypeError("letter has to be of type str")
        if not isinstance(number, int):
            raise self.AddressTypeError("number has to be of type int")

        self._device_id = device_id.lower()
        self._letter = letter.lower()
        self._number = number

        self._raise_on_letter()
        self._raise_on_number()

    def _raise_on_letter(self):
        if len(self._letter) != 1:
            raise self.AddressValueError(
                f"letter has to be of length 1: {self._letter}"
            )
        if self._letter not in ascii_lowercase:
            raise self.AddressValueError(
                f"letter has to be an ascii letter: {self._letter}"
            )

    def _raise_on_number(self):
        if self._number < 0 or self._number >= self.NUMBERS_PER_LETTER:
            raise self.AddressValueError(
                f"number has to be a positive integer in "
                f"[0,{self.NUMBERS_PER_LETTER - 1}]: {self._number}"
            )

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def letter(self) -> str:
        return self._letter

    @property
    def number(self) -> int:
        return self._number

    @property
    def chip_address(self) -> int:
        index = ord(self._letter) - ord(self.FIRST_LETTER)
        return self.BASE_CHIP_ADDRESS + index

    @property
    def register_address(self) -> int:
        return self.FUSE_ADDRESSES[self._number // 4]

    @property
    def register_mask(self) -> int:
        return 1 << ((self._number % 4) * 2)

    @property
    def rev_register_mask(self) -> int:
        return 0xff - self.register_mask

    def __str__(self) -> str:
        return f"{self._device_id}::{self._letter}{self._number}"

    def __repr__(self) -> str:
        return f"Address({str(self)})"

    def __eq__(self, other: 'Address') -> bool:
        return (
            self._device_id == other.device_id
            and self._letter == other.letter
            and self._number == other.number
        )
