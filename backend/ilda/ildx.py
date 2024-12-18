import ctypes
import enum


class IldxFormatCode(enum.IntEnum):
    ILDX_FORMAT_CODE_3D_INDEXED = 0,
    ILDX_FORMAT_CODE_2D_INDEXED = 1,
    ILDX_FORMAT_CODE_COLOR_PALETTE = 2,
    ILDX_FORMAT_CODE_3D_TRUE_COLOR = 4,
    ILDX_FORMAT_CODE_2D_TRUE_COLOR = 5


ILDX_MAGIC = 0x494C4458
ILDX_STATUS_CODE_LAST_POINT_MASK = 0b10000000
ILDX_STATUS_CODE_BLANKING_MASK = 0b01000000


class IldxHeader(ctypes.BigEndianStructure):
    _fields_ = [
        ("ildxMagix", ctypes.c_uint32),
        ("startTimestamp", ctypes.c_uint8 * 3),
        ("formatCode", ctypes.c_uint8),
        ("frameOrPaletteName", ctypes.c_char * 8),
        ("companyName", ctypes.c_char * 8),
        ("numberOfRecords", ctypes.c_uint16),
        ("frameOrPaletteNumber", ctypes.c_uint16),
        ("totalFrames", ctypes.c_uint16),
        ("projectorNumber", ctypes.c_uint8),
        ("framesPerSecondOrFrameAmount", ctypes.c_uint8)
    ]


class Ildx3dIndexedRecord(ctypes.BigEndianStructure):
    _fields_ = [
        ("x", ctypes.c_int16),
        ("y", ctypes.c_int16),
        ("z", ctypes.c_int16),
        ("statusCode", ctypes.c_uint8),
        ("colorIndex", ctypes.c_uint8)
    ]


class Ildx2dIndexedRecord(ctypes.BigEndianStructure):
    _fields_ = [
        ("x", ctypes.c_int16),
        ("y", ctypes.c_int16),
        ("statusCode", ctypes.c_uint8),
        ("colorIndex", ctypes.c_uint8)
    ]


class IldxColorPlatteRecord(ctypes.BigEndianStructure):
    _fields_ = [
        ("r", ctypes.c_uint8),
        ("g", ctypes.c_uint8),
        ("b", ctypes.c_uint8)
    ]


class Ildx3dTrueColorRecord(ctypes.BigEndianStructure):
    _fields_ = [
        ("x", ctypes.c_int16),
        ("y", ctypes.c_int16),
        ("z", ctypes.c_int16),
        ("statusCode", ctypes.c_uint8),
        ("r", ctypes.c_uint8),
        ("g", ctypes.c_uint8),
        ("b", ctypes.c_uint8)
    ]


class Ildx2dTrueColorRecord(ctypes.BigEndianStructure):
    _fields_ = [
        ("x", ctypes.c_int16),
        ("y", ctypes.c_int16),
        ("statusCode", ctypes.c_uint8),
        ("r", ctypes.c_uint8),
        ("g", ctypes.c_uint8),
        ("b", ctypes.c_uint8)
    ]


def decode_start_timestamp(header: IldxHeader) -> int:
    return (
        (header.startTimestamp[0] << 16) 
        | (header.startTimestamp[1] << 8)
        | (header.startTimestamp[2] << 0)
    )
