import ctypes

DMX_MAGIC: int = 0x444D5820

class DmxHeader(ctypes.Structure):
    _fields_ = [
        ('magic', ctypes.c_uint32),
        ('__padding', ctypes.c_uint16),
        ('universe', ctypes.c_uint16),
        ('elementAmount', ctypes.c_uint32),
        ('duration', ctypes.c_uint32)
    ]


class DmxElement(ctypes.Structure):
    _fields_ = [
        ('timestamp', ctypes.c_uint32),
        ('valueAmount', ctypes.c_uint16)
    ]


class DmxValue(ctypes.Structure):
    _fields_ = [
        ('channel', ctypes.c_uint16),
        ('value', ctypes.c_uint8)
    ]
