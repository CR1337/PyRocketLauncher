import ctypes

from dataclasses import dataclass
from typing import List, Tuple, Type

from backend.abstract_player import AbstractPlayer, AbstractPlayerItem
from backend.dmx.ftdi_dmx_interface import FtdiDmxInterface
from backend.dmx.dmx import DmxHeader, DmxElement, DmxValue

@dataclass
class DmxFrame(AbstractPlayerItem):
    values: List[Tuple[int, int]] = None


class DmxPlayer(AbstractPlayer):
    HEADER_SIZE: int = ctypes.sizeof(DmxHeader)
    ELEMENT_SIZE: int = ctypes.sizeof(DmxElement)
    VALUE_SIZE: int = ctypes.sizeof(DmxValue)

    _interface: Type[FtdiDmxInterface] = FtdiDmxInterface
    
    def __init__(self, dmx_filename: str):
        with open(dmx_filename, 'rb') as file:
            dmx_data = file.read()
        self._read_dmx_data(dmx_data)
        super().__init__()

    def __del__(self):
        self._interface.destroy()

    def _read_dmx_data(self, dmx_data: bytes):
        header = DmxHeader.from_buffer_copy(dmx_data[:self.HEADER_SIZE])
        element_amount = header.elementAmount

        self._items = []
        offset = self.HEADER_SIZE
        for _1 in range(element_amount):
            dmx_element = DmxElement.from_buffer_copy(dmx_data[offset:offset + self.ELEMENT_SIZE])
            offset += self.ELEMENT_SIZE
            timestamp = dmx_element.timestamp / 1000.0
            value_amount = dmx_element.valueAmount
            values = []
            
            for _2 in range(value_amount):
                dmx_value = DmxValue.from_buffer_copy(dmx_data[offset:offset + self.VALUE_SIZE])
                offset += self.VALUE_SIZE
                values.append((dmx_value.channel, dmx_value.value))
            self._items.append(DmxFrame(timestamp, values))

    def _play_item(self):
        frame = self._items[self._current_item_index]
        for channel, value in frame.values:
            self._interface.set_channel(channel, value)
        self._interface.render()

    def _start_playing(self):
        self._interface.initialize()

    def _end_playing(self):
        self._interface.blackout()
